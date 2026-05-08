# Design: PQ / E2E Test Tier Refactor — Mock LLM + IQ/OQ/PQ Structure

**Date:** 2026-05-02
**Branch:** sprint-31
**Status:** Approved

---

## Problem

The current `tests/e2e/pq/` tests require a real LLM via OpenRouter. They take 5–9 minutes and cost real money per run. This conflates two separate concerns:

1. **UI journey correctness** — does navigation, state transitions, testids, and button states work end to end?
2. **LLM output validity** — does the real LLM return parseable, schema-valid JSON?

Concern 1 belongs in the PQ tier (browser journeys with mocked LLM). Concern 2 belongs in the integration tier (API-level tests with real LLM, manually triggered).

Additionally, the existing `tests/e2e/` directory mixes `iq/`, `oq/`, `pq/` subdirectories under an "e2e" umbrella label — confusing, because OQ tests are not end-to-end journey tests. The tier names should be first-class, not subcategories.

---

## Target Architecture

### Directory structure

```
tests/
├── unit/           ← pytest; pure business logic, no Docker
├── integration/    ← pytest; API-level + real-LLM validation (INTEGRATION_LLM=1)
├── iq/             ← Playwright; Docker startup and installation checks
├── oq/             ← Playwright; individual feature and interface tests
├── pq/             ← Playwright; full persona journey tests (mock LLM)
└── fixtures/       ← shared test data (CVs, JDs, photos)
```

The `tests/e2e/` directory is removed. All files are relocated to the appropriate tier.

### CI pipeline (ordered, fail-fast)

| Stage | Command | Docker? | LLM | Duration |
|-------|---------|---------|-----|----------|
| 1 — Unit | `pytest tests/unit/` | No | Mocked (AsyncMock) | ~30s |
| 2 — IQ | `docker compose up` → `playwright --config playwright.config.ts --project iq` | Yes | Mock provider | ~2min |
| 3 — OQ | `playwright --config playwright.config.ts --project oq` + `pytest tests/integration/` | Yes | Mock provider | ~3min |
| 4 — PQ | `playwright --config playwright.config.pq.ts` | Yes | Mock provider | ~5min |
| Manual | `INTEGRATION_LLM=1 pytest tests/integration/` | Yes | Real LLM | ~8min |

Stages 2–4 share the same Docker stack (started once in Stage 2, torn down after Stage 4).

### Playwright configs (both at repo root)

**`playwright.config.ts`** — runs IQ + OQ:
- `testDir: './tests'` with `testMatch: ['**/iq/**/*.spec.ts', '**/oq/**/*.spec.ts']`
- Remove `testIgnore: ['**/pq/**']`
- Timeout: 60s per test (OQ tests are targeted, not full journeys)

**`playwright.config.pq.ts`** — runs PQ journeys:
- `testDir: './tests/pq'`
- `use.baseURL: 'http://localhost'` (nginx, unchanged)
- Timeout: 120s per test (full journeys traverse many pages)
- Docker stack uses `.env.ci` (mock LLM) in CI; `.env.dev` only for manual real-LLM runs

---

## Changes Required

### 1. MockLLMProvider — add cover letter fingerprint

**File:** `backend/applire/providers/llm/mock.py`

The cover letter system prompt opens with `"You are an expert DACH career coach writing a professional Bewerbungsschreiben"`. No existing fingerprint matches this — the mock falls back to `{"mock": True}` which fails schema validation and breaks the full Marcus journey.

Add fingerprint and canned response:

```python
if "dach career coach" in system_lower:   # cover letter generation
    return dict(_COVER_LETTER_RESPONSE)
```

`_COVER_LETTER_RESPONSE` must satisfy the cover letter JSON schema: `header`, `salutation`, `body` (list of paragraphs), `closing`. Values can be static/German-language fixture data.

### 2. File movements

| From | To | Notes |
|------|----|-------|
| `tests/e2e/iq/startup.spec.ts` | `tests/iq/startup.spec.ts` | No content change |
| `tests/e2e/oq/*.spec.ts` (8 files) | `tests/oq/*.spec.ts` | No content change |
| `tests/e2e/test_admin_appearance.spec.ts` | `tests/oq/admin-appearance.spec.ts` | Rename to match convention |
| `tests/e2e/test_profile_enrichment.spec.ts` | `tests/oq/profile-enrichment.spec.ts` | Rename to match convention |
| `tests/e2e/pq/*.spec.ts` (6 files) | `tests/pq/*.spec.ts` | Reorganise into persona subdirs |
| `tests/e2e/sprint29-dashboard.spec.ts` | **Delete** | Covered by Felix PQ journey |

PQ persona subdirectory layout:
```
tests/pq/
├── marcus/
│   ├── markus-complete-journey.spec.ts
│   └── marcus-new-user-journey.spec.ts
└── felix/
    ├── cover-letter.spec.ts
    ├── felix-cv-design.spec.ts
    ├── felix-cv-templates.spec.ts
    └── felix-dashboard-sprint29.spec.ts
```

Remove `tests/e2e/` once all files are relocated.

### 3. playwright.config.ts update

- Change `testDir` from `'./tests/e2e'` to an array: `['./tests/iq', './tests/oq']`
- Remove `testIgnore: ['**/pq/**']`
- No other changes

### 4. playwright.config.pq.ts update

- Change `testDir` from `'./tests/e2e/pq'` to `'./tests/pq'`
- No other changes

### 5. Integration test expansion

**File:** `tests/integration/test_happy_path.py`

Extend the existing `test_happy_path_new_user` to continue through the full journey after gap analysis:

- **Interview:** `POST /api/session` with `job_id` → `POST /api/session/{session_id}/message` (one answer) → `POST /api/flow/{flow_id}/advance` to transition out of interview
- **CV generation:** `POST /api/cv/generate` with `job_id` → poll `GET /api/cv/{cv_id}/status` until `status=ready`
- **Cover letter:** `POST /api/cover-letter/generate` with `job_id` → poll `GET /api/cover-letter/{cl_id}/status` until `status=ready`

All assertions are schema-level: correct status codes, required fields present, IDs valid UUIDs. No content assertions (LLM output is non-deterministic).

When run with `INTEGRATION_LLM=1`: validates real LLM returns parseable JSON for all steps.
When run without (mock provider): validates API contract and state machine transitions.

---

## What Is Not Changed

- `MockLLMProvider` fingerprints for all other services (job analysis, CV parsing, gap analysis, response parser, CV tailoring, gap clustering, interview questions) — already correct
- `.env.ci` — already sets `LLM_PROVIDER=mock`
- `docker-compose.ci.yml` — already uses `.env.ci`
- Unit test mock patterns (`AsyncMock` + `dependency_overrides`) — unchanged
- Test fixture files in `tests/fixtures/` — unchanged
- All PQ test logic — no content changes to `.spec.ts` files

---

## Acceptance Criteria

- `pytest tests/unit/` passes without Docker
- `npx playwright test` (IQ + OQ) passes against mock-LLM Docker stack in under 5 minutes
- `npx playwright test --config playwright.config.pq.ts` (full journeys) passes against mock-LLM Docker stack without any `OPENROUTER_API_KEY`
- `INTEGRATION_LLM=1 pytest tests/integration/` covers the full journey (upload → gaps → interview → CV → cover letter) at API level with real LLM
- `tests/e2e/` directory no longer exists

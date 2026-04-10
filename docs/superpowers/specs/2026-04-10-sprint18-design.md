# Sprint 18 Design Spec — Gap Color Fix & Test Structure Overhaul

**Date:** 2026-04-10
**Sprint:** 18
**Status:** Approved

---

## 1. Overview

Sprint 18 addresses two independent concerns:

1. **Bug fix:** Severity dot colors on the gaps page are swapped — Category C (missing skills) shows yellow instead of red, Category B (likely matches) shows teal instead of yellow.
2. **Test structure overhaul:** Replace the iteration-based, skip-heavy test layout with a V-model-aligned structure that provides reliable, deterministic CI coverage and a clear separation between automated and LLM-dependent tests.

---

## 2. Bug Fix — Gap Severity Colors

### Problem

In `frontend/app/flow/[flowId]/gaps/page.tsx`, the colored dot preceding each gap item uses the wrong Tailwind color class:

| Category | Meaning | Current dot | Correct dot |
|---|---|---|---|
| Category B | Likely match | `bg-teal` (green) | `bg-warning` (yellow) |
| Category C | Gap to address | `bg-warning` (yellow) | `bg-critical` (red) |

The detailed breakdown section (`<details>`) already uses the correct colors (`border-t-warning` for B, `border-t-critical` for C). Only the main list dots are wrong.

### Fix

Two single-line changes in `gaps/page.tsx`:
- Line 475: `bg-warning` → `bg-critical`
- Line 508: `bg-teal` → `bg-warning`

---

## 3. Test Structure — V-Model Alignment

### 3.1 Tier Definitions

| Tier | Scope | Runs in CI | LLM | Blocking |
|---|---|---|---|---|
| **Unit (DQ)** | Individual functions and components in isolation | Yes | No | Yes |
| **IQ** | Docker stack starts cleanly; health endpoint responds; UI is reachable | Yes | No | Yes |
| **OQ** | Critical UI flows with all API routes mocked via `page.route()` | Yes | No | Yes |
| **PQ** | Marcus happy-path end-to-end with real LLM (OpenRouter) | Manual only (`workflow_dispatch`) | Yes | No |

**LLM boundary rule:** OQ tests never call an LLM. All `/api/session`, `/api/job/*/gaps`, `/api/flow/*/advance`, and related routes are intercepted with `page.route()` and return deterministic fixtures. PQ tests always call a real LLM and are never run in the standard CI job.

### 3.2 E2E Folder Structure

```
tests/e2e/
├── iq/
│   └── startup.spec.ts
├── oq/
│   ├── match-page.spec.ts           (renamed from match-smoke.spec.ts)
│   ├── cv-preview.spec.ts           (moved, name unchanged)
│   ├── cv-section-editor.spec.ts    (merged finetuner-sprint9 + finetuner-sprint10)
│   ├── photo-management.spec.ts     (renamed from photo-sprint14.spec.ts)
│   ├── gaps-page.spec.ts            NEW — high-risk, sprint 18
│   └── upload-flow.spec.ts          NEW — high-risk, sprint 18
└── pq/
    └── marcus-new-user-journey.spec.ts  (consolidates interview-sprint5 + marcus-persona)
```

`playwright.config.ts` standard run uses `testIgnore: ['**/pq/**']`. A separate `playwright.config.pq.ts` targets only `pq/` and reads `OPENROUTER_API_KEY` from the environment.

### 3.3 Backend Test Renames

#### Unit tests (`tests/unit/`)

| Current | New |
|---|---|
| `test_iter6_llm_providers.py` | `test_llm_providers.py` |
| `test_iter7_mcp_tools.py` | `test_mcp_tools.py` |
| `test_iter7_mcp_resources.py` | `test_mcp_resources.py` |
| `test_iter8_scraper.py` | `test_scraper_service.py` |
| `test_iter9_linkedin_parser.py` | `test_linkedin_parser.py` |
| `test_iter10_auth.py` | `test_auth_provider.py` |
| `test_iter10_retention.py` | `test_retention_worker.py` |
| `test_iter11_profile.py` | `test_profile_service.py` |
| `test_iter12_upload.py` | `test_cv_upload.py` |
| `test_iter13_gap.py` | `test_gap_analysis.py` |
| `test_iter15_flow_orchestrator.py` | `test_flow_orchestrator.py` |
| `test_iter16_llm_provider.py` | `test_llm_provider_integration.py` |
| `test_iter17_application.py` | `test_application_service.py` |
| `test_iter17_retention.py` | `test_retention_service.py` |
| `test_iter20_cv_sprint6.py` | `test_cv_generation.py` |
| `test_iter21_sprint7_mcp.py` | `test_mcp_endpoints.py` |
| `test_iter24_assist_microsession.py` | `test_micro_session.py` |
| `test_sprint13_coverage.py` | `test_response_parser.py` |
| `test_sprint14_photo.py` | `test_photo_service.py` |
| `test_sprint15_interview.py` | `test_interview_service.py` |
| `test_matching_service.py` | unchanged |
| `test_session_service_coverage.py` | `test_session_service.py` |

#### Integration tests (`tests/`)

| Current | New |
|---|---|
| `test_iter0_skeleton.py` | `test_health.py` |
| `test_iter1_jd_analysis.py` | `test_jd_analysis.py` |
| `test_iter2_profile_import.py` | `test_profile_import.py` |
| `test_iter3_gap_analysis.py` | `test_gap_analysis.py` |
| `test_iter4_gap_fill_interview.py` | `test_interview_flow.py` |
| `test_iter5_cv_generation.py` | `test_cv_generation.py` |
| `test_iter6_llm_providers.py` | `test_llm_providers.py` |
| `test_iter7_mcp_server.py` | `test_mcp_server.py` |
| `test_iter8_jd_url_intake.py` | `test_jd_url_intake.py` |
| `test_iter9_second_template_linkedin.py` | `test_linkedin_template.py` |
| `test_iter10_auth_retention.py` | `test_auth_retention.py` |
| `test_iter12_cv_upload.py` | `test_cv_upload.py` |
| `test_iter13_gap_detection.py` | `test_gap_detection.py` |
| `test_iter15_flow_orchestrator.py` | `test_flow_orchestrator.py` |
| `test_iter16_llm_provider.py` | `test_llm_provider.py` |
| `test_iter17_application.py` | `test_application.py` |
| `test_iter20_cv_generation_ui.py` | `test_cv_generation_ui.py` |
| `test_iter21_sprint7_endpoints.py` | `test_mcp_endpoints.py` |
| `test_iter21_sprint7_gdpr.py` | `test_gdpr.py` |

### 3.4 OQ Spec Content — New Tests (Sprint 18)

#### `oq/gaps-page.spec.ts`

All routes mocked. Covers:
- Gaps page loads and displays gap categories (A, B, C)
- Category B dot is `bg-warning` (yellow), Category C dot is `bg-critical` (red)
- "Generate CV Now" button is visible and calls `POST /api/flow/:id/advance` then navigates to `/flow/:id/cv`
- "Quick Interview" button is visible for new users with gaps and navigates to `/flow/:id/interview`
- Resolved gap appears with green checkmark after micro-session completes

#### `oq/upload-flow.spec.ts`

All routes mocked. Covers:
- Home page renders upload area and JD input
- Submit button disabled until both CV file and JD text are provided
- Submit triggers `POST /api/upload` and `POST /api/flow`, then navigates to `/flow/:id/gaps`
- Processing overlay is shown during submission
- Error state renders when API returns non-200

### 3.5 IQ Spec Content

#### `iq/startup.spec.ts`

Requires running Docker stack. Covers:
- `GET /health` returns HTTP 200
- Frontend root `/` returns HTTP 200
- Upload area (`data-testid="file-input"`) is present in the DOM

### 3.6 PQ Workflow

A new GitHub Actions workflow `.github/workflows/pq.yml` is added:
- Trigger: `workflow_dispatch` only (never runs automatically)
- Requires `OPENROUTER_API_KEY` GitHub Actions secret
- Runs `npx playwright test --config=playwright.config.pq.ts`
- Uploads Playwright report as artifact

A `.github/PULL_REQUEST_TEMPLATE.md` adds a checklist item:
> `[ ] PQ tests run locally and passed (or changes do not affect LLM-dependent flows)`

### 3.7 Persona Roadmap for PQ

| Persona | Journey | PQ scope |
|---|---|---|
| **Marcus** | New user: upload → gaps → interview → CV | Sprint 18 |
| **Emma** | Returning user: dashboard → one-click tailoring → version history | Future (when returning-user flow is built) |
| **Priya** | International relocator: cultural adaptation flow | Future |

---

## 4. Documentation Updates

### `docs/TESTING.md`

Fully rewritten. Replaces the outdated March 2026 version. Documents:
- V-model tier definitions and the LLM boundary rule
- Folder layout for all test tiers
- How to run each tier locally
- How to trigger the PQ workflow in GitHub Actions
- Naming convention (module-based, not iteration-based)

### `docs/TRACEABILITY.md`

New file. Maps Epic/User Story IDs to test IDs at each tier. Seeded with features covered by sprint 18 tests; extended in future sprints.

---

## 5. Out of Scope

- Frontend Vitest unit test renames (already use descriptive names)
- Emma, Priya PQ journeys (not yet implemented in the product)
- Visual regression testing, accessibility testing, load testing
- Mutation testing

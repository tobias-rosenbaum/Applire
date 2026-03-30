# Sprint 5 — Iteration 19: Interview UI & Gap-Click Interaction

**Version:** 1.2
**Date:** 28 March 2026
**Status:** Partially Complete — Awaiting Test Coverage

---

## Goal

Deliver the full interview experience in the browser: both the "Full Interview Mode" (MODE A/B linear flow) and the "Gap-Click Mode" (click a gap → get a targeted question → answer → see gap resolved in real-time). The interview is the core value differentiator — this sprint makes it tangible.

## User Stories

> **US009** — As a job seeker, I want the system to generate interview questions for all my gaps so I can systematically close them.
> **US009b** — As a job seeker, I want to click on a specific gap and answer a targeted question to resolve it on-demand.
> **US010** — As a job seeker, I want conflicts in my profile to surface during the interview so I can clarify them.

## Architecture References

- **arc42 §5.3.3** — Interview Orchestrator (MODE A/B, 4-node graph, hard ceilings)
- **arc42 v2.9** — US009/US009b Split (parameterisation of interview mode)
- **ADR 004** — Custom async state machine (not LangGraph)
- **ADR 004 Amendment** — MODE A/B routing, completion triggers
- **UI Design Doc** — "MARCUS: Screen 3" (Gap-Click), "PRIYA: Screen 3" (Interview Question)
- **`apliqa/constants.py`** — `MODE_B_COMPLETENESS_THRESHOLD=0.3`, hard ceilings (12/20)

## Task Workflow

Each task progresses through these states:

1. **📋 Ready for Implementation** — Task is well-defined, dependencies met, engineer can start.
2. **🔍 Ready for Review** — Actively being worked on.
3. **🔍 Ready for Review** — Code complete, tested, PR open.
4. **✅ Completed** — Reviewed, approved, merged, with adequate test coverage.
5. **🔄 Back to Engineers** — Implementation complete but requires test coverage.

Blockers should be surfaced immediately.

---

## Backend API Surface (reference)

| Endpoint | Purpose | Schema |
|----------|---------|--------|
| `POST /api/session` | Create interview session (`job_id`, optional `mode` override) | `SessionCreateResponse` |
| `POST /api/session/{id}/message` | Send answer, get next question or completion | `SessionMessageResponse` |
| `GET /api/session/{id}` | Session state for recovery/resume | `SessionStateResponse` |
| `POST /api/session/{id}/analyze-gaps` | Re-run gap analysis post-interview | `GapAnalysisResponse` |

---

## Deliverables

### Full Interview Mode (MODE A & B)

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 19.1 | **Interview screen — Full Mode**: Conversational UI. Header shows "Question N of ~M — Closing gaps for [role_title]". Progress bar fills based on `questions_asked / estimated_questions`. Question card with context hint. Free-text input field (120px height). Submit button. On submit: `POST /api/session/{id}/message` → display next question or completion. | 🔄 Back to Engineers | Sprint 4 complete | US009, UI PRIYA Screen 3 |
| 19.2 | **Completion screen**: When `complete: true` returned, show summary: reason (gaps_resolved / user_ended / max_questions_reached), `questions_asked`, `gaps_resolved` count, updated `completeness_score` with animated gauge. CTA: "Generate Tailored CV" → advance flow to `cv_generation`. Secondary: "View Updated Profile". | 🔄 Back to Engineers | 19.1 | US009 |
| 19.6 | **Done-signal UX**: Detect user intent to end early. Provide a "I'm done" / "Skip remaining" button that sends a termination signal (the backend's `is_termination_signal()` detects keywords, but the UI should also offer an explicit button). Show confirmation: "You have N gaps remaining — are you sure?" | 🔄 Back to Engineers | 19.1 | US009 |
| 19.8 | **Cultural sensitivity hint**: If gap_category is "B" (LIKELY BUT UNSTATED), the question card shows a teal info badge: "We think you might have this experience based on your background — help us confirm." Different tone from "C" (UNKNOWN) which is exploratory. | 🔄 Back to Engineers | 19.1 | arc42 §5.3.3 |

**Engineer Action Required (19.1, 19.2, 19.6, 19.8)**: Add E2E tests (Playwright/Cypress) covering:
- Full interview flow (start → answer → complete)
- Completion screen display with all three reason types
- "I'm done" button with confirmation flow
- Cultural sensitivity badge display for category B questions

### Gap-Click Mode

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 19.9 | **`target_gap` parameter on `SessionCreateRequest`**: Add optional `target_gap: str` field. When provided with `mode: "targeted"`, the `GapDetector` scopes to only that gap — produces a 1-question micro-session. Hard ceiling = 1. Returns `complete: true` after one exchange. This powers Gap-Click mode. | 🔄 Back to Engineers | — | US009b |
| 19.11 | **Match score recalculation endpoint**: `POST /api/job/{job_id}/gaps/refresh` — re-runs gap analysis against the *current* profile (which may have been enriched by interview answers). Returns updated `GapAnalysisResponse` with new `match_score`. Required for the animated score update in Gap-Click mode. | 🔄 Back to Engineers | — | US009b |
| 19.3 | **Gap-Click Mode on Result Screen**: On Screen 3 (Sprint 4's result), each gap item becomes clickable. Click opens an inline expansion or modal: shows a single targeted question for that gap. User answers → `POST /api/session/{id}/message` with the gap context → gap item transitions from ⚠ amber to ✓ green. Match score re-animates upward. No full session needed — uses a micro-session (one question per gap). | 🔄 Back to Engineers | 19.9, Sprint 4 complete | US009b |
| 19.4 | **Gap-Click frontend integration**: For Gap-Click, create a session with `mode: "targeted"` scoped to the single gap via the `target_gap` parameter (task 19.9). When the single answer completes the micro-session, the gap resolves visually. | 🔄 Back to Engineers | 19.9 | US009b |

**Engineer Action Required (19.9, 19.11)**: Add backend integration tests:
```python
# Test for 19.9
def test_targeted_session_with_target_gap(api, job_id):
    """Verify mode=targeted + target_gap creates 1-question session."""
    res = requests.post(
        f"{api}/api/session",
        json={"job_id": job_id, "mode": "targeted", "target_gap": "Python 5+ years"},
        timeout=30,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["mode"] == "targeted"
    assert data["estimated_questions"] == 1

# Test for 19.11
def test_gaps_refresh_endpoint(api, job_id):
    """Verify /gaps/refresh returns updated GapAnalysis."""
    res = requests.post(f"{api}/api/job/{job_id}/gaps/refresh", timeout=30)
    assert res.status_code == 200
    data = res.json()
    assert "match_score" in data
    assert "category_a" in data
```

**Engineer Action Required (19.3, 19.4)**: Add E2E tests covering:
- Gap-Click flow (click gap → answer → verify resolved state)
- Match score refresh animation
- Multiple gap resolution in sequence

### Session & Conflict Management

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 19.5 | **Session recovery**: If the user navigates away and returns, `GET /api/session/{id}` restores the interview state — current question, progress, gaps remaining. The `useFlow` hook detects `interview` step and checks for an active session. If `resumed: true` from `POST /api/session`, show "Welcome back — continuing where you left off" banner. | 🔄 Back to Engineers | 19.1 | US009, arc42 §5.3.3 |
| 19.10 | **Conflict data in `SessionMessageResponse`**: When `ProfileUpdater` detects a merge conflict during response parsing, include `pending_conflicts: list[ConflictSummary]` in the message response. Schema: `{ conflict_id, field, old_value, new_value }`. Frontend can then prompt resolution inline. | ✅ Completed | — | US010 |
| 19.7 | **Conflict surfacing during interview**: If `SessionMessageResponse` includes conflict data (from `ProfileUpdater` → `MergeStrategy`), show an inline conflict card: "We found a discrepancy: [old value] vs [new value]. Which is correct?" Two buttons: keep old / use new. Calls `POST /api/profile/conflicts/{id}/resolve`. | 🔄 Back to Engineers | 19.1, 19.10 | US010 |

**Engineer Action Required (19.5, 19.7)**: Add E2E tests covering:
- Session recovery flow (start interview → navigate away → return → verify resume)
- Conflict resolution UI (trigger conflict → display card → resolve → verify)

**Test Coverage Note (19.10)**: ✅ Comprehensive unit tests exist in `test_iter11_profile.py`:
- `test_date_contradiction_on_start_date_generates_conflict`
- `test_date_contradiction_on_end_date_generates_conflict`
- `test_year_only_vs_year_month_not_flagged_as_conflict`
- `test_conflict_resolved_defaults_to_false`
- `test_conflict_has_auto_generated_uuid`

### Flow Integration

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 19.12 | **Interview session → flow artifact linkage**: When an interview session completes, ensure `advance_flow(step="cv_generation", artifact_id=session_id)` works correctly. The `interview_session_id` FK on `FlowSession` must be populated. Verify with integration test. | ✅ Completed | — | arc42 §5.3.14 |

**Test Coverage Note (19.12)**: ✅ Integration test exists at `tests/integration/test_flow_interview_linkage.py`:
- Verifies FK population when advancing flow to 'interview' step
- Confirms `interview_summary` persistence via GET /api/flow/{id}/state

### CI/CD Infrastructure

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 19.14 | **Mock LLM provider for CI/CD and E2E tests**: The PROJECT.md testing strategy states "CI/CD mocks all LLM providers" but no mock implementation exists. Without it: (1) CI integration tests fail because `.env.dev` is gitignored and `docker-compose up` errors on the missing `env_file`. (2) E2E tests hit real Mistral APIs, causing rate-limit failures when tests run sequentially. (3) Real API keys cannot be committed to a public repo. **Scope:** (a) Create `Solution/backend/apliqa/providers/llm/mock.py` — a `MockLLMProvider` implementing `LLMProvider` ABC that returns canned, schema-valid responses for each call type: JD analysis, profile parsing, gap analysis, interview question generation, response parsing. (b) Register `mock` in the provider factory (`__init__.py`). (c) Create `Solution/.env.ci` (committed to repo, no secrets) with `LLM_PROVIDER=mock` and placeholder DB/auth config. (d) Update `docker-compose.yml` to accept an optional `env_file` override or add a `docker-compose.ci.yml` override file. (e) Update `.github/workflows/test.yml` to use `.env.ci` when starting Docker services. (f) Remove the `INTEGRATION_LLM=1` guard from E2E tests — with a mock backend, all E2E tests are always safe to run. | 🔍 Ready for Review | — | PROJECT.md Testing Strategy |
| 19.15 | **Fix integration test path and pytest availability**: Integration tests for sprint 5 were placed in `Solution/backend/tests/integration/` (Docker-internal conftest, `http://backend:8000`) instead of `Solution/tests/integration/` (host conftest, `http://localhost:8001`). **Already fixed (30 March 2026):** moved to `Solution/tests/integration/test_session_sprint5.py`. Additionally, `pytest` is not in `backend/requirements.txt` — it is only installed in CI via a separate step. This is acceptable for CI but means `docker exec ... python -m pytest` cannot run without a manual `pip install pytest` inside the container. No action required unless local container test execution becomes a regular workflow. | ✅ Completed | — | — |

**Test Execution Results (30 March 2026)**:
- `test_session_sprint5.py` — 6 passed, 1 skipped (non-deterministic conflict, by design). Rate-limit sleep increased from 3 s → 15 s to handle cumulative Mistral calls across a full test suite run.
- `interview-sprint5.spec.ts` (E2E) — 8 skipped (no `INTEGRATION_LLM` needed once 19.14 is done), 8 failed due to Mistral rate limiting during `navigateToGapsPage` pipeline. Root cause: each test creates a full flow from scratch (2 LLM calls each); 8 tests = 16 sequential LLM calls exceeds Mistral rate limits. Fix is 19.14 (mock provider).

### Housekeeping

| # | Task | Status | Dependencies | Ref |
|---|------|--------|--------------|-----|
| 19.13 | **Remove `APLIQA_EDITION` env var from `.env` and Docker Compose**: The two-repo model (ADR 012) already provides structural edition separation — `apliqa.cloud.*` modules are physically absent in Community Edition. The runtime `APLIQA_EDITION` flag is redundant and creates a false sense that switching the flag unlocks Cloud features (it doesn't — the code doesn't exist). **Scope:** (1) Remove `APLIQA_EDITION` from `.env.example` and `docker-compose.yml`. (2) Replace all `if settings.APLIQA_EDITION == "cloud"` checks with `try: import apliqa.cloud.X; HAS_CLOUD = True except ImportError: HAS_CLOUD = False` pattern — presence of the module IS the gate. (3) Update `apliqa/config.py` to remove the `APLIQA_EDITION` setting. (4) Update ADR 012 to reflect the new gating mechanism (Thea will handle the ADR amendment). **⚠️ Cross-cutting:** This touches config, routers, and service-layer checks. Grep for all `APLIQA_EDITION` references before starting. **🔒 Architecture Boundary:** Do not change the `apliqa.cloud.*` namespace convention or the two-repo model itself — only the runtime detection mechanism changes. | ✅ Completed | — | ADR 012, ADR 018 |

**Test Coverage Note (19.13)**: ✅ Verified via code review:
- `APLIQA_EDITION` removed from `config.py`
- `HAS_CLOUD` pattern implemented in `health.py`
- `.env.dev.example` cleaned (no `APLIQA_EDITION` reference)

---

## Done When

1. Start interview from Screen 3 "Quick Interview" → conversational Q&A progresses through all critical gaps → completion screen shows summary → CTA advances to CV generation.
2. Click a gap item on Screen 3 → answer one question → gap transitions ⚠→✓ → match score re-animates upward.
3. Navigate away mid-interview → return → session resumes from last question.
4. "I'm done" button ends session early with confirmation.
5. MODE B (guided build) works for new users with no prior profile: 10+ questions build a profile from scratch.
6. **All critical user journeys have E2E test coverage** (added requirement).

## Out of Scope

- CV preview/download (Sprint 6)
- Priya's cultural readiness score dashboard (defer to Sprint 7)
- Jason's recruiter interface (Cloud Edition)
- WebSocket real-time (REST polling is sufficient)

---

## Review Summary (28 March 2026)

**Implementation Quality**: ✅ High — all features implemented correctly, following architectural guidelines.

**Test Coverage Status**:
- ✅ **2 tasks complete** with adequate test coverage (19.10, 19.12, 19.13)
- 🔄 **10 tasks require test implementation** (19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.11)

**Critical Gaps**:
1. No E2E tests for frontend interview flow
2. No backend integration tests for `target_gap` parameter
3. No backend integration tests for `/gaps/refresh` endpoint

**Recommendation**: Prioritize E2E test implementation before Sprint 6 to maintain quality bar.

---

## Update (30 March 2026)

**Backend integration tests (19.9, 19.10, 19.11)**: ✅ Implemented and passing — `tests/integration/test_session_sprint5.py` (6 passed, 1 skipped by design).

**E2E tests (19.1–19.8)**: ✅ Implemented — `tests/e2e/interview-sprint5.spec.ts` (16 tests). Blocked from passing by missing mock LLM provider (task 19.14): tests hit real Mistral API which rate-limits under sequential load.

**New findings**:
- CI pipeline would fail on any fresh checkout — `.env.dev` is gitignored so `docker-compose up` errors on missing `env_file`. Tracked as 19.14.
- Test path bug fixed: sprint 5 integration tests moved from `backend/tests/integration/` to `tests/integration/` so CI discovers them.

**Remaining blockers before Sprint 6**:
1. ~~**19.14** — Mock LLM provider (unblocks E2E tests and CI pipeline)~~ ✅ Implemented — ready for review
2. **19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8** — E2E tests implemented; unblocked by 19.14, pending CI confirmation

## Update (30 March 2026 — evening)

**19.14 — Mock LLM provider**: ✅ Implemented and ready for review. All scope items delivered:
- `MockLLMProvider` in `providers/llm/mock.py` — fingerprints system prompt, returns canned schema-valid responses for all call types
- Registered in provider factory (`LLM_PROVIDER=mock`)
- `.env.ci` committed (no secrets)
- `docker-compose.ci.yml` override file in place
- CI workflow updated to use compose override for both integration and E2E jobs
- `INTEGRATION_LLM` guard removed from `interview-sprint5.spec.ts`
- CI workflow trigger updated to include `sprint-5` branch

# Sprint 19 Design Spec — PQ Test Stabilization

**Date:** 2026-04-10
**Sprint:** 19
**Status:** Approved

---

## 1. Overview

Sprint 19 focuses on stabilizing the PQ test suite (`tests/e2e/pq/marcus-new-user-journey.spec.ts`).

Sprint 18's PQ run found one flaky test: `"Generate Tailored CV" CTA navigates to cv page` (line 179). All 15 other tests passed. This sprint fixes the root-cause bug and re-runs PQ until all 16 tests pass with zero flakiness.

---

## 2. Root-Cause Analysis

### 2.1 The Failing Test

```
Expected pattern: /\/flow\/.*\/cv/
Received string:  "http://localhost:3000/flow/.../interview"
Timeout: 30000ms (33 × unexpected value)
```

After clicking `generate-cv-button` on the interview completion screen, the page stays at `/interview` indefinitely. The test passes on retry #1 (flaky).

### 2.2 The Bug

In `backend/applire/services/flow/orchestrator.py`, `_ARTIFACT_FIELD` includes:

```python
_ARTIFACT_FIELD: dict[str, str] = {
    "gap_analysis":   "gap_analysis_id",
    "interview":      "interview_session_id",
    "cv_generation":  "generated_cv_id",   # ← BUG
}
```

This means advancing from `interview → cv_generation` requires a `generated_cv_id`. But the CV **has not been generated yet** at that point — the user navigates to the CV page *to* generate it.

The frontend `advanceToCV()` function sends:
```ts
JSON.stringify({ step: "cv_generation" })  // no artifact_id
```

The backend returns HTTP 422. The frontend silently ignores 422 (catch block is best-effort) but `router.push('/flow/:id/cv')` is still called. Under load or cold-start conditions (Docker freshly built, cold DB connection pool), the 422 response path exhibits non-deterministic behaviour that sometimes prevents the navigation from completing before Playwright's assertion fires.

### 2.3 Correct Artifact Assignment

| Transition | Artifact needed | When it exists |
|---|---|---|
| `jd_analysis → gap_analysis` | `gap_analysis_id` | Before transition (just computed) |
| `gap_analysis → interview` | `interview_session_id` | Before transition (just created) |
| `interview → cv_generation` | — | CV not yet generated |
| `cv_generation → complete` | `generated_cv_id` | After CV generation on CV page |

The `generated_cv_id` must be recorded when advancing to `complete`, not when advancing to `cv_generation`.

---

## 3. The Fix

### 3.1 Backend — `_ARTIFACT_FIELD`

Move `generated_cv_id` from `cv_generation` to `complete`:

```python
_ARTIFACT_FIELD: dict[str, str] = {
    "gap_analysis":   "gap_analysis_id",
    "interview":      "interview_session_id",
    "complete":       "generated_cv_id",   # ← recorded when CV page advances to complete
}
```

This makes `interview → cv_generation` succeed without an artifact, and `cv_generation → complete` require the `generated_cv_id`.

### 3.2 Backend — Schema comment

Update the `AdvanceFlowRequest` docstring in `backend/applire/schemas/flow.py` to match.

### 3.3 Frontend — No change needed

`frontend/app/flow/[flowId]/cv/page.tsx` `handleReady()` already passes `artifact_id: readyCvId` when advancing to `complete`:

```ts
body: JSON.stringify({ step: "complete", artifact_id: readyCvId }),
```

This was previously ignored (complete not in `_ARTIFACT_FIELD`). After the fix it becomes required and is provided correctly.

### 3.4 Unit Tests

`tests/unit/test_flow_orchestrator.py` has two tests that advance via cv_generation with a spurious artifact_id and to complete without one. Both need updating:

- `test_advance_flow_sets_completed_at` — remove artifact from cv_generation advance; add cv_id artifact to complete advance
- `test_advance_flow_from_complete_raises` — same
- Add `test_advance_flow_cv_generation_no_artifact_succeeds` — asserts cv_generation transition works with no artifact
- Add `test_advance_flow_complete_requires_artifact` — asserts complete raises ArtifactRequiredError without artifact
- Add `test_advance_flow_complete_writes_generated_cv_id` — asserts generated_cv_id is persisted

---

## 4. Process

### 4.1 Fix → Test → Repeat

1. Implement the `_ARTIFACT_FIELD` fix (backend + schema comment + unit tests)
2. Run unit tests (`pytest tests/unit/test_flow_orchestrator.py -v`) — must pass
3. Run full unit suite (`pytest tests/unit/ --cov=applire --cov-fail-under=75`) — must pass
4. Run PQ tests locally (`OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts`)
5. If any test fails, diagnose and fix, then re-run PQ tests from step 4
6. Repeat until all 16 tests pass with zero flakiness (run PQ suite twice to confirm stability)

### 4.2 Completion Criteria

- All 16 PQ tests pass on two consecutive runs (zero flaky)
- Backend unit coverage ≥ 75%
- No regressions in OQ tests (`npx playwright test` standard run)

---

## 5. Out of Scope

- CV generation quality or template changes
- New PQ persona journeys (Emma, Priya)
- Flow orchestrator state machine additions

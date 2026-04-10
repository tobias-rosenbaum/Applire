# Sprint 19 — PQ Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the `interview → cv_generation` artifact bug so all 16 PQ tests pass with zero flakiness.

**Architecture:** Move `generated_cv_id` tracking from the `cv_generation` transition to the `complete` transition in `_ARTIFACT_FIELD`. The CV page already passes `artifact_id` when advancing to `complete`, so no frontend change is needed beyond the backend fix.

**Tech Stack:** Python/FastAPI (backend), pytest (unit tests), Playwright (PQ E2E)

---

### Task 1: Fix `_ARTIFACT_FIELD` in Flow Orchestrator

**Files:**
- Modify: `backend/applire/services/flow/orchestrator.py:57-63`
- Modify: `backend/applire/schemas/flow.py:64-70`

- [ ] **Step 1: Write failing unit test first**

Add to `tests/unit/test_flow_orchestrator.py` before the existing `test_advance_flow_sets_completed_at`:

```python
@pytest.mark.asyncio
async def test_advance_flow_cv_generation_no_artifact_succeeds(db, user_and_job):
    """interview → cv_generation requires no artifact_id."""
    _, job = user_and_job
    flow_resp = await create_flow(CreateFlowRequest(job_id=job.id), _STUB_USER_ID, db)
    flow_id = flow_resp.flow_id

    await advance_flow(flow_id, AdvanceFlowRequest(step="gap_analysis", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="interview", artifact_id=uuid.uuid4()), db)

    # cv_generation must succeed without artifact_id
    result = await advance_flow(flow_id, AdvanceFlowRequest(step="cv_generation"), db)
    assert result.current_step == "cv_generation"


@pytest.mark.asyncio
async def test_advance_flow_complete_requires_artifact(db, user_and_job):
    """cv_generation → complete requires artifact_id (generated_cv_id)."""
    _, job = user_and_job
    flow_resp = await create_flow(CreateFlowRequest(job_id=job.id), _STUB_USER_ID, db)
    flow_id = flow_resp.flow_id

    await advance_flow(flow_id, AdvanceFlowRequest(step="gap_analysis", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="interview", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="cv_generation"), db)

    with pytest.raises(ArtifactRequiredError) as exc_info:
        await advance_flow(flow_id, AdvanceFlowRequest(step="complete"), db)

    assert exc_info.value.step == "complete"
    assert exc_info.value.field == "generated_cv_id"


@pytest.mark.asyncio
async def test_advance_flow_complete_writes_generated_cv_id(db, user_and_job):
    """generated_cv_id is persisted on the flow record when advancing to complete."""
    from applire.models.flow import FlowSession
    from sqlalchemy import select

    _, job = user_and_job
    flow_resp = await create_flow(CreateFlowRequest(job_id=job.id), _STUB_USER_ID, db)
    flow_id = flow_resp.flow_id
    cv_id = uuid.uuid4()

    await advance_flow(flow_id, AdvanceFlowRequest(step="gap_analysis", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="interview", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="cv_generation"), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="complete", artifact_id=cv_id), db)

    result = await db.execute(select(FlowSession).where(FlowSession.id == flow_id))
    flow = result.scalar_one()
    assert flow.generated_cv_id == cv_id
    assert flow.completed_at is not None
```

- [ ] **Step 2: Run the new tests to confirm they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution
PYTHONPATH=backend pytest tests/unit/test_flow_orchestrator.py::test_advance_flow_cv_generation_no_artifact_succeeds tests/unit/test_flow_orchestrator.py::test_advance_flow_complete_requires_artifact tests/unit/test_flow_orchestrator.py::test_advance_flow_complete_writes_generated_cv_id -v
```

Expected: 3 FAILED (cv_generation currently requires artifact, complete currently does not).

- [ ] **Step 3: Fix `_ARTIFACT_FIELD` in orchestrator.py**

In `backend/applire/services/flow/orchestrator.py`, replace lines 57-63:

```python
# Steps that require an artifact_id when advanced into — field name on FlowSession
_ARTIFACT_FIELD: dict[str, str] = {
    "gap_analysis":   "gap_analysis_id",
    "interview":      "interview_session_id",
    # generated_cv_id is recorded when the CV page advances to complete
    "complete":       "generated_cv_id",
}
```

- [ ] **Step 4: Update schema comment in `schemas/flow.py`**

In `backend/applire/schemas/flow.py`, update the `AdvanceFlowRequest` comment:

```python
class AdvanceFlowRequest(BaseModel):
    step: str
    # Required when advancing into a step that produces an artifact:
    #   gap_analysis    → gap_analysis_id
    #   interview       → interview_session_id
    #   complete        → generated_cv_id
    artifact_id: uuid.UUID | None = None
```

- [ ] **Step 5: Fix the two existing unit tests that relied on old behaviour**

In `tests/unit/test_flow_orchestrator.py`:

Replace `test_advance_flow_sets_completed_at` (lines 289-306):

```python
@pytest.mark.asyncio
async def test_advance_flow_sets_completed_at(db, user_and_job):
    """Advancing to 'complete' sets completed_at."""
    from applire.models.flow import FlowSession
    from sqlalchemy import select

    _, job = user_and_job
    flow_resp = await create_flow(CreateFlowRequest(job_id=job.id), _STUB_USER_ID, db)
    flow_id = flow_resp.flow_id

    # Drive to complete step; cv_generation requires no artifact, complete requires generated_cv_id
    await advance_flow(flow_id, AdvanceFlowRequest(step="gap_analysis", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="interview", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="cv_generation"), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="complete", artifact_id=uuid.uuid4()), db)

    result = await db.execute(select(FlowSession).where(FlowSession.id == flow_id))
    flow = result.scalar_one()
    assert flow.completed_at is not None
    assert flow.current_step == "complete"
```

Replace `test_advance_flow_from_complete_raises` (lines 335-351):

```python
@pytest.mark.asyncio
async def test_advance_flow_from_complete_raises(db, user_and_job):
    """No transitions are allowed from the terminal 'complete' step."""
    _, job = user_and_job
    flow_resp = await create_flow(CreateFlowRequest(job_id=job.id), _STUB_USER_ID, db)
    flow_id = flow_resp.flow_id

    # Reach complete; cv_generation requires no artifact, complete requires generated_cv_id
    await advance_flow(flow_id, AdvanceFlowRequest(step="gap_analysis", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="interview", artifact_id=uuid.uuid4()), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="cv_generation"), db)
    await advance_flow(flow_id, AdvanceFlowRequest(step="complete", artifact_id=uuid.uuid4()), db)

    with pytest.raises(InvalidTransitionError) as exc_info:
        await advance_flow(flow_id, AdvanceFlowRequest(step="cv_generation"), db)

    assert exc_info.value.current == "complete"
    assert exc_info.value.allowed == []
```

- [ ] **Step 6: Run all flow orchestrator unit tests**

```bash
cd /home/apliqa/Documents/Applire/Solution
PYTHONPATH=backend pytest tests/unit/test_flow_orchestrator.py -v
```

Expected: All tests PASS (including the 3 new ones and the 2 updated ones).

- [ ] **Step 7: Run full unit test suite with coverage gate**

```bash
cd /home/apliqa/Documents/Applire/Solution
PYTHONPATH=backend pytest tests/unit/ backend/tests/unit/ \
  --ignore=tests/conftest.py \
  --ignore=backend/tests/conftest.py \
  --cov=applire \
  --cov-config=backend/.coveragerc \
  --cov-report=term-missing \
  --cov-fail-under=75 \
  -v
```

Expected: PASS with ≥ 75% coverage.

- [ ] **Step 8: Commit**

```bash
git add backend/applire/services/flow/orchestrator.py \
        backend/applire/schemas/flow.py \
        tests/unit/test_flow_orchestrator.py
git commit -m "fix(flow): move generated_cv_id tracking from cv_generation to complete transition"
```

---

### Task 2: Run PQ Tests and Fix Any Additional Failures

**Files:** Depends on what PQ run reveals — investigate as needed.

- [ ] **Step 1: Start Docker stack (full rebuild)**

```bash
cd /home/apliqa/Documents/Applire/Solution
docker compose down -v
docker compose up -d --build
```

Wait for backend and frontend to be ready:
```bash
timeout 300 bash -c 'until curl -sf http://localhost:8001/health; do sleep 3; done' && echo "Backend ready"
timeout 180 bash -c 'until curl -sf http://localhost:3000; do sleep 2; done' && echo "Frontend ready"
docker compose exec backend python -m alembic upgrade head
```

- [ ] **Step 2: Run full PQ suite — first run**

```bash
cd /home/apliqa/Documents/Applire/Solution
OPENROUTER_API_KEY=<your_key> npx playwright test --config=playwright.config.pq.ts
```

Expected: 16 passed, 0 failed, 0 flaky.

If any test fails:
- Read the error carefully
- Check `test-results-pq/` for screenshots and error context
- Diagnose root cause in the relevant source file
- Fix the bug, commit, then continue to Step 3

- [ ] **Step 3: Run full PQ suite — second run (stability confirmation)**

Rerun the same command without restarting Docker to confirm no flakiness on warm stack:

```bash
OPENROUTER_API_KEY=<your_key> npx playwright test --config=playwright.config.pq.ts
```

Expected: 16 passed, 0 failed, 0 flaky.

If still flaky: investigate timing/race conditions in the affected component. Common causes:
- Fetch without timeout that hangs on first run (cold DB/backend)
- Missing `await` on async state updates
- Race between two concurrent fetch calls in `useEffect`

- [ ] **Step 4: Run OQ tests to confirm no regressions**

```bash
cd /home/apliqa/Documents/Applire/Solution
npx playwright test
```

Expected: All OQ/IQ tests pass (pq/ is excluded by default `testIgnore`).

- [ ] **Step 5: Commit any additional fixes**

If Task 2 required code changes beyond Task 1, commit them:

```bash
git add <changed files>
git commit -m "fix(<scope>): <description of additional fix found during PQ run>"
```

---

### Task 3: Final Verification

- [ ] **Step 1: Run backend unit tests one final time**

```bash
PYTHONPATH=backend pytest tests/unit/ --cov=applire --cov-config=backend/.coveragerc --cov-fail-under=75 -q
```

Expected: PASS.

- [ ] **Step 2: Confirm git log**

```bash
git log --oneline -5
```

Sprint 19 commits should be visible on `main`.

---

## Notes for Implementer

### Why `cv_generation` can't require `generated_cv_id` at transition time

The `interview → cv_generation` transition happens when the user clicks "Generate Tailored CV" on the interview completion screen. At this point no CV exists yet. The CV is generated on the `/cv` page (user picks a template, then `POST /api/cv/generate` runs). Only after the CV is ready does `handleReady(cvId)` on the CV page advance to `complete` with the `generated_cv_id`.

The previous `_ARTIFACT_FIELD["cv_generation"]` entry was architecturally incorrect — it assumed the CV was generated *before* navigating to the CV page.

### Frontend `handleReady` is already correct

`frontend/app/flow/[flowId]/cv/page.tsx` `handleReady()` at line 94-108 already calls:
```ts
body: JSON.stringify({ step: "complete", artifact_id: readyCvId }),
```

This was previously ignored (complete not in `_ARTIFACT_FIELD`). After the fix it becomes the required artifact path. No frontend change needed.

### Flakiness mechanism

The advance to `cv_generation` returns 422 → frontend silently ignores → `router.push` fires. Under cold-start conditions the 422 response handling has non-deterministic timing with the Next.js App Router soft navigation. Fixing the 422 source (the artifact requirement) makes the advance succeed with 200, which is synchronous and deterministic.

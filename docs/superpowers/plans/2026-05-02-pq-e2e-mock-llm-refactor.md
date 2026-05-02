# PQ / E2E Mock-LLM Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate real LLM calls from all browser tests by completing the `MockLLMProvider`, restructuring the test tier directories from `tests/e2e/iq|oq|pq/` to `tests/iq/`, `tests/oq/`, `tests/pq/`, and expanding the integration test to cover the full journey at API level.

**Architecture:** The `MockLLMProvider` already handles all services except cover letter generation (missing fingerprint). Once that fingerprint is added, the PQ browser tests can run against the CI Docker stack (which uses `LLM_PROVIDER=mock`) without any real API key. File movements are `git mv` operations — no content changes to test files. The CI workflow is updated to run IQ → OQ → PQ in sequence after unit tests.

**Tech Stack:** Python 3.12 / pytest (unit + integration), Playwright TypeScript (IQ/OQ/PQ), FastAPI, GitHub Actions.

---

## File Map

| Action | Path |
|--------|------|
| Modify | `backend/applire/providers/llm/mock.py` |
| Modify | `tests/unit/test_llm_providers.py` |
| `git mv` | `tests/e2e/iq/startup.spec.ts` → `tests/iq/startup.spec.ts` |
| `git mv` | `tests/e2e/oq/*.spec.ts` (8 files) → `tests/oq/` |
| `git mv` | `tests/e2e/test_admin_appearance.spec.ts` → `tests/oq/admin-appearance.spec.ts` |
| `git mv` | `tests/e2e/test_profile_enrichment.spec.ts` → `tests/oq/profile-enrichment.spec.ts` |
| `git mv` | `tests/e2e/pq/markus-complete-journey.spec.ts` → `tests/pq/marcus/markus-complete-journey.spec.ts` |
| `git mv` | `tests/e2e/pq/marcus-new-user-journey.spec.ts` → `tests/pq/marcus/marcus-new-user-journey.spec.ts` |
| `git mv` | `tests/e2e/pq/cover-letter.spec.ts` → `tests/pq/felix/cover-letter.spec.ts` |
| `git mv` | `tests/e2e/pq/felix-cv-design.spec.ts` → `tests/pq/felix/felix-cv-design.spec.ts` |
| `git mv` | `tests/e2e/pq/felix-cv-templates.spec.ts` → `tests/pq/felix/felix-cv-templates.spec.ts` |
| `git mv` | `tests/e2e/pq/felix-dashboard-sprint29.spec.ts` → `tests/pq/felix/felix-dashboard-sprint29.spec.ts` |
| Delete | `tests/e2e/sprint29-dashboard.spec.ts` |
| Delete | `tests/e2e/` (directory, empty after moves) |
| Modify | `playwright.config.ts` |
| Modify | `playwright.config.pq.ts` |
| Modify | `.github/workflows/test.yml` |
| Modify | `.github/workflows/pq.yml` |
| Modify | `tests/integration/test_happy_path.py` |

---

## Task 1: Add cover letter fingerprint to MockLLMProvider

The `MockLLMProvider.aparse_json` dispatches on system-prompt fingerprints. The cover letter system prompt starts with `"You are an expert DACH career coach writing a professional Bewerbungsschreiben"` — no fingerprint exists for it, so the mock returns `{"mock": True}` which fails schema validation.

**Files:**
- Modify: `backend/applire/providers/llm/mock.py`
- Modify: `tests/unit/test_llm_providers.py`

- [ ] **Step 1: Write the failing test**

Open `tests/unit/test_llm_providers.py` and add at the end of the file:

```python
# ---------------------------------------------------------------------------
# MockLLMProvider — cover letter fingerprint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_cover_letter_fingerprint():
    """MockLLMProvider must return a schema-valid cover letter dict."""
    from applire.providers.llm.mock import MockLLMProvider

    provider = MockLLMProvider()
    result = await provider.aparse_json(
        "Generate a cover letter.",
        system="You are an expert DACH career coach writing a professional Bewerbungsschreiben (German cover letter).",
    )

    assert isinstance(result, dict), "Expected a dict"
    for key in ("header", "recipient", "body", "signature"):
        assert key in result, f"Missing key: {key}"

    header = result["header"]
    assert "name" in header and "address" in header

    body = result["body"]
    assert "paragraphs" in body
    assert isinstance(body["paragraphs"], list)
    assert len(body["paragraphs"]) >= 3

    signature = result["signature"]
    assert "closing" in signature and "name" in signature
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
pytest tests/unit/test_llm_providers.py::test_mock_cover_letter_fingerprint -v
```

Expected: `FAILED` — the mock returns `{"mock": True}`, missing all required keys.

- [ ] **Step 3: Add `_COVER_LETTER_RESPONSE` constant and fingerprint**

Open `backend/applire/providers/llm/mock.py`. After the `_QUESTION_RESPONSE` block and before the `_INTERVIEW_QUESTION` line, add:

```python
_COVER_LETTER_RESPONSE: dict[str, Any] = {
    "header": {
        "name": "Anna Bauer",
        "address": "Hauptstraße 42, 10115 Berlin",
        "phone": "+49 170 1234567",
        "email": "anna.bauer@example.de",
        "photo_url": None,
    },
    "recipient": {
        "name": "Herr Dr. Müller",
        "title": "Personalleiter",
        "company": "TechVision GmbH",
        "address": "Unter den Linden 1, 10117 Berlin",
        "date": "02. Mai 2026",
    },
    "body": {
        "paragraphs": [
            (
                "Sehr geehrter Herr Dr. Müller, mit großem Interesse habe ich Ihre "
                "Stellenausschreibung als Senior Software Engineer gelesen und bewerbe "
                "mich hiermit auf diese Position."
            ),
            (
                "Als erfahrene Software-Ingenieurin mit über sechs Jahren Praxis in "
                "Python und FastAPI bringe ich die gesuchten Kernkompetenzen vollständig "
                "mit. Bei TechVision GmbH habe ich skalierbare REST-APIs entwickelt und "
                "CI/CD-Prozesse eingeführt, die die Deployment-Zeit um 40 % reduzierten."
            ),
            (
                "Ihr Fokus auf Microservice-Architekturen und agile Entwicklungsmethoden "
                "spricht mich besonders an, da ich in diesem Umfeld bereits erfolgreich "
                "gearbeitet habe und weitere Impulse setzen möchte."
            ),
            (
                "Über die Möglichkeit, mich in einem persönlichen Gespräch vorzustellen, "
                "würde ich mich sehr freuen. Meine Gehaltsvorstellung liegt bei "
                "95.000 € brutto jährlich."
            ),
        ]
    },
    "signature": {
        "closing": "Mit freundlichen Grüßen",
        "name": "Anna Bauer",
    },
}
```

Then in the `aparse_json` method, add this branch **before** the fallback return, after the `"expert career coach"` check:

```python
        if "dach career coach" in system_lower:
            return dict(_COVER_LETTER_RESPONSE)
```

Also update the module docstring fingerprint list at the top of the file to include the new entry:

```python
  "expert dach career coach"  → cover letter         (aparse_json → dict)
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
pytest tests/unit/test_llm_providers.py::test_mock_cover_letter_fingerprint -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full unit suite to check for regressions**

```bash
pytest tests/unit/ -v --tb=short -q
```

Expected: all tests pass (including pre-existing mock provider tests).

- [ ] **Step 6: Commit**

```bash
git add backend/applire/providers/llm/mock.py tests/unit/test_llm_providers.py
git commit -m "feat(mock): add cover letter fingerprint to MockLLMProvider"
```

---

## Task 2: Restructure test directories

Move all files out of `tests/e2e/` into their correct tier directories. Use `git mv` so git tracks the renames.

**Files:** All moves listed in the File Map above.

- [ ] **Step 1: Create destination directories**

```bash
mkdir -p tests/iq tests/oq tests/pq/marcus tests/pq/felix
```

- [ ] **Step 2: Move IQ tests**

```bash
git mv tests/e2e/iq/startup.spec.ts tests/iq/startup.spec.ts
```

- [ ] **Step 3: Move OQ tests**

```bash
git mv tests/e2e/oq/cv-color.spec.ts         tests/oq/cv-color.spec.ts
git mv tests/e2e/oq/cv-preview.spec.ts        tests/oq/cv-preview.spec.ts
git mv tests/e2e/oq/cv-section-editor.spec.ts tests/oq/cv-section-editor.spec.ts
git mv tests/e2e/oq/gaps-page.spec.ts         tests/oq/gaps-page.spec.ts
git mv tests/e2e/oq/jd-url-error.spec.ts      tests/oq/jd-url-error.spec.ts
git mv tests/e2e/oq/match-page.spec.ts        tests/oq/match-page.spec.ts
git mv tests/e2e/oq/photo-management.spec.ts  tests/oq/photo-management.spec.ts
git mv tests/e2e/oq/upload-flow.spec.ts       tests/oq/upload-flow.spec.ts
git mv tests/e2e/test_admin_appearance.spec.ts   tests/oq/admin-appearance.spec.ts
git mv tests/e2e/test_profile_enrichment.spec.ts tests/oq/profile-enrichment.spec.ts
```

- [ ] **Step 4: Move PQ tests into persona subdirectories**

```bash
git mv tests/e2e/pq/markus-complete-journey.spec.ts   tests/pq/marcus/markus-complete-journey.spec.ts
git mv tests/e2e/pq/marcus-new-user-journey.spec.ts   tests/pq/marcus/marcus-new-user-journey.spec.ts
git mv tests/e2e/pq/cover-letter.spec.ts              tests/pq/felix/cover-letter.spec.ts
git mv tests/e2e/pq/felix-cv-design.spec.ts           tests/pq/felix/felix-cv-design.spec.ts
git mv tests/e2e/pq/felix-cv-templates.spec.ts        tests/pq/felix/felix-cv-templates.spec.ts
git mv tests/e2e/pq/felix-dashboard-sprint29.spec.ts  tests/pq/felix/felix-dashboard-sprint29.spec.ts
```

- [ ] **Step 5: Delete the stray dashboard test and remove tests/e2e/**

```bash
git rm tests/e2e/sprint29-dashboard.spec.ts
rmdir tests/e2e/pq tests/e2e/oq tests/e2e/iq tests/e2e
```

- [ ] **Step 6: Verify the directory tree**

```bash
find tests/iq tests/oq tests/pq -name "*.spec.ts" | sort
```

Expected output (12 files total):
```
tests/iq/startup.spec.ts
tests/oq/admin-appearance.spec.ts
tests/oq/cv-color.spec.ts
tests/oq/cv-preview.spec.ts
tests/oq/cv-section-editor.spec.ts
tests/oq/gaps-page.spec.ts
tests/oq/jd-url-error.spec.ts
tests/oq/match-page.spec.ts
tests/oq/photo-management.spec.ts
tests/oq/profile-enrichment.spec.ts
tests/oq/upload-flow.spec.ts
tests/pq/felix/cover-letter.spec.ts
tests/pq/felix/felix-cv-design.spec.ts
tests/pq/felix/felix-cv-templates.spec.ts
tests/pq/felix/felix-dashboard-sprint29.spec.ts
tests/pq/marcus/marcus-new-user-journey.spec.ts
tests/pq/marcus/markus-complete-journey.spec.ts
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor(tests): promote IQ/OQ/PQ tiers to top-level test directories"
```

---

## Task 3: Update playwright.config.ts

`playwright.config.ts` currently sets `testDir: './tests/e2e'` and ignores `**/pq/**`. After this task it points at `tests/` with a testMatch covering `iq/` and `oq/` only.

**Files:**
- Modify: `playwright.config.ts`

- [ ] **Step 1: Replace testDir and remove testIgnore**

Open `playwright.config.ts`. Make these two changes:

**Change 1** — replace the `testDir` line:
```typescript
// Before:
testDir: './tests/e2e',
testIgnore: ['**/pq/**'], // PQ tests require real LLM — run via workflow_dispatch only

// After:
testDir: './tests',
testMatch: ['**/iq/**/*.spec.ts', '**/oq/**/*.spec.ts'],
```

**Change 2** — update the comment block at the top of the file to reflect the new config purpose:
```typescript
/**
 * Playwright Configuration — IQ + OQ tiers
 *
 * Runs installation checks (tests/iq/) and operational feature tests (tests/oq/).
 * Uses the CI Docker stack (LLM_PROVIDER=mock) — no API key required.
 * For full persona journey tests, use: npx playwright test --config=playwright.config.pq.ts
 */
```

- [ ] **Step 2: Verify the config resolves correctly (dry run)**

```bash
npx playwright test --list 2>&1 | head -40
```

Expected: lists only files under `tests/iq/` and `tests/oq/`. If the Docker stack is not running, Playwright will list tests without executing them — that is expected.

- [ ] **Step 3: Commit**

```bash
git add playwright.config.ts
git commit -m "config(playwright): point standard config at tests/iq + tests/oq"
```

---

## Task 4: Update playwright.config.pq.ts

`playwright.config.pq.ts` currently sets `testDir: './tests/e2e/pq'`. Update it to `./tests/pq`. Remove the `OPENROUTER_API_KEY` dependency note.

**Files:**
- Modify: `playwright.config.pq.ts`

- [ ] **Step 1: Update testDir and comments**

Open `playwright.config.pq.ts`. Make these changes:

```typescript
// Before:
/**
 * PQ (Performance Qualification) Playwright config.
 * Runs only tests/e2e/pq/ using a real LLM via OpenRouter.
 * Never run automatically in CI — trigger via GitHub Actions workflow_dispatch.
 *
 * Requires: OPENROUTER_API_KEY environment variable
 * Requires: Full Docker stack running (docker compose up -d)
 */
export default defineConfig({
  testDir: './tests/e2e/pq',

// After:
/**
 * Playwright Configuration — PQ tier (persona journey tests)
 *
 * Runs full persona journey tests (tests/pq/). Uses the CI Docker stack
 * (LLM_PROVIDER=mock) — no API key required.
 * Runs automatically in CI after IQ and OQ tiers pass.
 * For manual runs: docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d
 */
export default defineConfig({
  testDir: './tests/pq',
```

- [ ] **Step 2: Verify the config resolves correctly**

```bash
npx playwright test --config=playwright.config.pq.ts --list 2>&1 | head -30
```

Expected: lists files under `tests/pq/marcus/` and `tests/pq/felix/`.

- [ ] **Step 3: Commit**

```bash
git add playwright.config.pq.ts
git commit -m "config(playwright): update PQ config to tests/pq, remove real-LLM requirement"
```

---

## Task 5: Update CI workflows

`test.yml` currently runs playwright with the old `tests/e2e/` path and runs `pytest tests/ --ignore=tests/e2e`. Both need updating. `pq.yml` is repurposed from manual real-LLM trigger to an automated PQ step that integrates into the main test job.

**Files:**
- Modify: `.github/workflows/test.yml`
- Modify: `.github/workflows/pq.yml`

- [ ] **Step 1: Update pytest invocation in test.yml**

Find the "Run integration tests" step in `.github/workflows/test.yml`:

```yaml
# Before:
      - name: Run integration tests
        run: |
          pytest tests/ \
            --ignore=tests/e2e \
            --ignore=tests/unit \
            --junitxml=integration-test-results.xml \
            -v \
            --tb=short

# After:
      - name: Run integration tests
        run: |
          pytest tests/integration/ \
            --junitxml=integration-test-results.xml \
            -v \
            --tb=short
```

- [ ] **Step 2: Split the single Playwright step into three named steps in test.yml**

Find the "Run Playwright E2E tests" step and replace it with three steps:

```yaml
# Before:
      - name: Run Playwright E2E tests
        run: node_modules/.bin/playwright test
        env:
          CI: true

# After:
      - name: Run Playwright IQ tests
        run: node_modules/.bin/playwright test tests/iq/
        env:
          CI: true

      - name: Run Playwright OQ tests
        run: node_modules/.bin/playwright test tests/oq/
        env:
          CI: true

      - name: Run Playwright PQ tests
        run: node_modules/.bin/playwright test --config=playwright.config.pq.ts
        env:
          CI: true
```

- [ ] **Step 3: Repurpose pq.yml for real-LLM integration testing**

Replace the entire contents of `.github/workflows/pq.yml` with:

```yaml
name: Real-LLM Integration Tests (Manual)

on:
  workflow_dispatch:
    inputs:
      reason:
        description: "Reason for running (e.g. pre-release, provider change)"
        required: false
        default: "Manual trigger"

jobs:
  real-llm-integration:
    name: Full Journey — Real LLM
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      checks: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.12.3
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.3'
          cache: 'pip'
          cache-dependency-path: 'backend/requirements.txt'

      - name: Install backend dependencies
        working-directory: backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio requests

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Create .env.dev with real LLM provider
        run: |
          cp .env.ci .env.dev
          echo "LLM_PROVIDER=openrouter" >> .env.dev
          echo "OPENROUTER_API_KEY=${{ secrets.OPENROUTER_API_KEY }}" >> .env.dev

      - name: Start Docker services
        run: docker compose up -d --build

      - name: Wait for application to be ready
        run: |
          timeout 300 bash -c 'until curl -sf http://localhost:8001/health; do sleep 3; done'

      - name: Run database migrations
        run: docker compose exec backend python -m alembic upgrade head

      - name: Run real-LLM integration tests
        run: |
          INTEGRATION_LLM=1 pytest tests/integration/ \
            --junitxml=real-llm-test-results.xml \
            -v \
            --tb=short

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: real-llm-integration-results
          path: real-llm-test-results.xml
          retention-days: 30

      - name: Tear down Docker services
        if: always()
        run: docker compose down -v
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml .github/workflows/pq.yml
git commit -m "ci: split e2e into IQ/OQ/PQ steps; repurpose pq.yml for real-LLM gate"
```

---

## Task 6: Expand integration test to cover full journey

Extend `tests/integration/test_happy_path.py` to continue the journey after gap analysis: interview session → CV generation → cover letter generation. All at API level via `requests`. When run without `INTEGRATION_LLM=1` (mock provider), validates API contracts and state-machine transitions. When run with `INTEGRATION_LLM=1`, validates real LLM output parses correctly.

**Files:**
- Modify: `tests/integration/test_happy_path.py`

Context on the flow state machine:
- `VALID_TRANSITIONS["gap_analysis"] = ["interview", "cv_generation"]`
- Advancing to `"interview"` requires `artifact_id = session_id` (the interview session)
- Advancing to `"cv_generation"` requires no artifact
- Advancing to `"complete"` requires `artifact_id = generated_cv_id`
- `POST /api/session` body: `{"job_id": "<uuid>"}` — returns `{"session_id": ..., "first_question": ...}`
- `POST /api/session/{session_id}/message` body: `{"message": "<text>"}` — returns status
- `POST /api/cv/generate` body: `{"job_id": "<uuid>"}` — returns `{"cv_id": ..., "status": "pending", ...}`
- `GET /api/cv/{cv_id}/status` — returns `{"cv_id": ..., "status": "pending"|"ready"|"error"}`
- `POST /api/cover-letter/generate` body: `{"job_id": "<uuid>", "salary": "..."}` — returns `{"cover_letter_id": ..., "status": "pending"}`
- `GET /api/cover-letter/{cl_id}/status` — returns `{"cover_letter_id": ..., "status": "pending"|"ready"|"error", "letter_data": {...}}`

- [ ] **Step 1: Remove the module-level skip marker and add `import time`**

Open `tests/integration/test_happy_path.py`. The file currently has:

```python
# Skip all tests in this module unless INTEGRATION_LLM is set
pytestmark = pytest.mark.skipif(
    not os.getenv("INTEGRATION_LLM"),
    reason="Set INTEGRATION_LLM=1 to run integration tests with real LLM"
)
```

**Remove those three lines entirely.** The test now runs with mock LLM in normal CI and with real LLM when `INTEGRATION_LLM=1` is set (both modes use the same code path; the provider is chosen by the Docker stack's `LLM_PROVIDER` env var). The other integration test files (`test_session_sprint5.py`, `test_session_sprint6.py`) retain their own skip markers and remain real-LLM-only.

Also ensure `import time` is in the imports:

```python
import os
import time
from pathlib import Path

import pytest
import requests
```

- [ ] **Step 2: Extend `test_happy_path_new_user` with interview steps**

In `tests/integration/test_happy_path.py`, the existing test ends after verifying `match_score`. Add these steps immediately after the final assertion in the existing function body (after `assert 0.0 <= match_score <= 1.0`):

```python
    # Step 8: Create interview session
    r = requests.post(
        f"{api}/api/session",
        json={"job_id": str(job_id)},
        timeout=60,
    )
    assert r.status_code == 201, f"Session creation failed: {r.text}"
    session_data = r.json()
    session_id = session_data["session_id"]
    assert session_data.get("first_question"), "Session must return a first question"

    # Step 9: Advance flow to interview, linking the session
    r = requests.post(
        f"{api}/api/flow/{flow_id}/advance",
        json={"step": "interview", "artifact_id": str(session_id)},
        timeout=30,
    )
    assert r.status_code == 200, f"Flow advance to interview failed: {r.text}"
    assert r.json()["current_step"] == "interview"

    # Step 10: Send one interview answer
    r = requests.post(
        f"{api}/api/session/{session_id}/message",
        json={"message": (
            "Ich habe über 8 Jahre Erfahrung in der professionellen Softwareentwicklung "
            "mit Python, davon 5 Jahre mit FastAPI in produktiven Microservice-Umgebungen."
        )},
        timeout=60,
    )
    assert r.status_code == 200, f"Session message failed: {r.text}"

    # Step 11: Advance flow to cv_generation (ends interview)
    r = requests.post(
        f"{api}/api/flow/{flow_id}/advance",
        json={"step": "cv_generation"},
        timeout=30,
    )
    assert r.status_code == 200, f"Flow advance to cv_generation failed: {r.text}"
    assert r.json()["current_step"] == "cv_generation"

    # Step 12: Trigger CV generation
    r = requests.post(
        f"{api}/api/cv/generate",
        json={"job_id": str(job_id)},
        timeout=60,
    )
    assert r.status_code == 201, f"CV generation failed: {r.text}"
    cv_id = r.json()["cv_id"]
    assert cv_id, "CV ID must be present"

    # Step 13: Poll CV status until ready (max 60 s)
    cv_ready = False
    for _ in range(60):
        r = requests.get(f"{api}/api/cv/{cv_id}/status", timeout=10)
        assert r.status_code == 200, f"CV status check failed: {r.text}"
        if r.json()["status"] == "ready":
            cv_ready = True
            break
        assert r.json()["status"] != "error", f"CV generation errored: {r.text}"
        time.sleep(1)
    assert cv_ready, "CV did not reach 'ready' within 60 s"

    # Step 14: Trigger cover letter generation
    r = requests.post(
        f"{api}/api/cover-letter/generate",
        json={"job_id": str(job_id), "salary": "95.000 € p.a."},
        timeout=60,
    )
    assert r.status_code == 201, f"Cover letter generation failed: {r.text}"
    cl_id = r.json()["cover_letter_id"]
    assert cl_id, "Cover letter ID must be present"

    # Step 15: Poll cover letter status until ready (max 60 s)
    cl_ready = False
    for _ in range(60):
        r = requests.get(f"{api}/api/cover-letter/{cl_id}/status", timeout=10)
        assert r.status_code == 200, f"Cover letter status check failed: {r.text}"
        status_data = r.json()
        if status_data["status"] == "ready":
            cl_ready = True
            assert status_data.get("letter_data"), "Ready cover letter must have letter_data"
            letter = status_data["letter_data"]
            for section in ("header", "recipient", "body", "signature"):
                assert section in letter, f"Missing cover letter section: {section}"
            break
        assert status_data["status"] != "error", f"Cover letter generation errored: {r.text}"
        time.sleep(1)
    assert cl_ready, "Cover letter did not reach 'ready' within 60 s"
```

- [ ] **Step 3: Run the integration test with mock LLM to verify it passes**

The Docker stack must be running with `LLM_PROVIDER=mock` (`.env.ci`). If not running locally, trigger in CI.

```bash
pytest tests/integration/test_happy_path.py -v --tb=short
```

Expected: `PASSED` — mock provider handles all steps instantly.

If the Docker stack uses `.env.dev` locally, override temporarily:

```bash
# In a separate terminal:
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --build
# Wait for ready, then run the test
pytest tests/integration/test_happy_path.py -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_happy_path.py
git commit -m "test(integration): extend happy path to cover interview, CV, and cover letter steps"
```

---

## Task 7: Smoke verify — run full PQ suite against mock LLM

With all changes in place, verify the full PQ browser journey completes without any real LLM call.

**Prerequisite:** Docker stack running with mock LLM (`.env.ci`):
```bash
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --build
docker compose exec backend python -m alembic upgrade head
```

- [ ] **Step 1: Run IQ + OQ suite**

```bash
npx playwright test --timeout=60000
```

Expected: all IQ and OQ tests pass. No `OPENROUTER_API_KEY` set or needed.

- [ ] **Step 2: Run PQ suite**

```bash
npx playwright test --config=playwright.config.pq.ts
```

Expected: all persona journey tests pass (Marcus + Felix). No `OPENROUTER_API_KEY` set or needed. Target: completes in under 8 minutes.

- [ ] **Step 3: Confirm tests/e2e/ is gone**

```bash
ls tests/e2e 2>&1
```

Expected: `No such file or directory`

- [ ] **Step 4: Confirm unit tests still pass**

```bash
pytest tests/unit/ -q --tb=short
```

Expected: all green.

- [ ] **Step 5: Final commit — update TESTING.md**

Open `docs/TESTING.md`. Update the tier documentation to reflect the new structure. Replace any references to `tests/e2e/` with the new `tests/iq/`, `tests/oq/`, `tests/pq/` paths. Add the CI pipeline table from the spec.

```bash
git add docs/TESTING.md
git commit -m "docs: update TESTING.md to reflect IQ/OQ/PQ tier restructure"
```

# Marcus Complete Journey — E2E Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `tests/e2e/pq/markus-complete-journey.spec.ts` — a single Playwright PQ test file that drives the full Marcus happy path: CV upload + JD paste → gap analysis → one interview answer → CV generation → cover letter generation.

**Architecture:** One new test file with a `setupCompleteJourney` helper function that drives the full UI flow and returns the `flowId`. Three independent test cases call the helper and assert end-state landmarks. No existing files are modified.

**Tech Stack:** Playwright TypeScript, `playwright.config.pq.ts`, fixtures at `tests/fixtures/profiles/sample_cv.pdf` and `tests/fixtures/JDs/sample_jd.txt`.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `tests/e2e/pq/markus-complete-journey.spec.ts` | Full test file: helper + 3 test cases |

No other files are created or modified.

---

### Task 1: Create the file scaffold with imports, constants, and helpers

**Files:**
- Create: `tests/e2e/pq/markus-complete-journey.spec.ts`

- [ ] **Step 1: Create the file with the scaffold (no test cases yet)**

Create `tests/e2e/pq/markus-complete-journey.spec.ts` with the following content:

```typescript
// tests/e2e/pq/markus-complete-journey.spec.ts
import { test, expect, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Marcus — Complete Journey (PQ)
 *
 * Full happy path: CV upload + JD paste → gap analysis → interview (one answer) →
 * CV generation → cover letter generation.
 *
 * PQ tier: requires the full Docker stack AND a real LLM via OpenRouter.
 * Run locally:   OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts tests/e2e/pq/markus-complete-journey.spec.ts
 * Run in CI:     Trigger the "PQ Tests" workflow_dispatch in GitHub Actions.
 *
 * DO NOT run this file with the standard `npx playwright test` command.
 */

const CV_PATH = path.join(__dirname, '../../fixtures/profiles/sample_cv.pdf');
const JD_TEXT = fs.readFileSync(
  path.join(__dirname, '../../fixtures/JDs/sample_jd.txt'),
  'utf-8'
);
const API_BASE = 'http://localhost:8001';

async function resetBackendState(page: Page): Promise<void> {
  await page.request.delete(`${API_BASE}/api/profile`).catch(() => {});
}

/**
 * Drives the full Marcus journey from scratch through to a ready cover letter.
 * Returns the flowId extracted from the URL.
 *
 * Journey: home → gaps → interview (1 answer, end early) → CV generation → cover letter
 */
async function setupCompleteJourney(page: Page): Promise<string> {
  await resetBackendState(page);
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Paste JD (unique token prevents flow-creation idempotency re-using a stale flow)
  const uniqueJD = `${JD_TEXT}\n\n<!-- markus-complete-journey: ${Date.now()} -->`;
  await page.getByRole('button', { name: 'Paste Text' }).click();
  await page
    .locator('textarea[placeholder="Paste the full job description here..."]')
    .fill(uniqueJD);

  // Upload CV
  await page.getByTestId('file-input').setInputFiles(CV_PATH);
  await expect(page.getByTestId('submit-button')).toBeEnabled();
  await page.getByTestId('submit-button').click();

  // Wait for gap analysis
  await expect(page).toHaveURL(/\/flow\/.*\/gaps/, { timeout: 90000 });
  await expect(page.getByTestId('loading-indicator')).not.toBeVisible({
    timeout: 30000,
  });

  // Start interview
  const interviewButton = page.getByTestId('interview-button');
  await expect(interviewButton).toBeVisible({ timeout: 10000 });
  await interviewButton.click();
  await expect(page).toHaveURL(/\/flow\/.*\/interview/, { timeout: 30000 });
  await expect(page.getByTestId('interview-loading')).not.toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByTestId('interview-question')).toBeVisible();

  // Answer one question
  const firstQuestion = await page.getByTestId('interview-question').textContent();
  await page.getByTestId('answer-textarea').fill(
    'Ich habe über 10 Jahre Erfahrung in der Softwareentwicklung, davon 6 Jahre mit ' +
      'Python und FastAPI in produktiven Umgebungen. Ich habe mehrere ' +
      'Microservice-Architekturen entworfen und betrieben.'
  );
  await page.getByTestId('send-button').click();

  // Wait for question to change or completion screen to appear after the answer
  await expect(page.getByTestId('interview-question'))
    .not.toHaveText(firstQuestion ?? '', { timeout: 30000 })
    .catch(() => {});

  // End early if not already on completion screen
  const completionVisible = await page
    .getByTestId('completion-screen')
    .isVisible()
    .catch(() => false);
  if (!completionVisible) {
    await page.getByTestId('done-button').click();
    await expect(page.getByTestId('done-confirm')).toBeVisible();
    await page.getByRole('button', { name: /End interview/i }).click();
  }
  await expect(page.getByTestId('completion-screen')).toBeVisible({
    timeout: 30000,
  });

  // Navigate to CV page
  await page.getByTestId('generate-cv-button').click();
  await expect(page).toHaveURL(/\/flow\/.*\/cv/, { timeout: 60000 });

  // Skip photo prompt if shown
  const skipPhotoBtn = page.getByText('Skip for now');
  if (await skipPhotoBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await skipPhotoBtn.click();
  }

  // Generate CV
  await page.getByText('CV generieren').click({ timeout: 10000 });
  await expect(page.getByTestId('refinement-panel')).toBeVisible({
    timeout: 90000,
  });

  // Open cover letter generation modal
  await page.getByTestId('tab-actions').click();
  await page.getByTestId('generate-cover-letter-btn').click();
  await expect(page.getByTestId('cover-letter-modal')).toBeVisible();

  // Fill minimal inputs and generate
  await page.getByTestId('cl-salary').fill('95.000 € p.a.');
  await page.getByTestId('cl-modal-generate').click();

  // Wait for cover letter page and iframe
  await page.waitForURL(/\/flow\/.*\/cover-letter/, { timeout: 30000 });
  await expect(page.getByTestId('cover-letter-iframe')).toBeVisible({
    timeout: 60000,
  });

  // Extract and return flowId
  const url = page.url();
  const match = url.match(/\/flow\/([^/]+)\//);
  return match ? match[1] : '';
}
```

- [ ] **Step 2: Type-check the file**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
npx tsc --noEmit
```

Expected: no errors. If you see `Cannot find module` errors for `@playwright/test`, run `npm install` in the project root first.

- [ ] **Step 3: Commit the scaffold**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
git add tests/e2e/pq/markus-complete-journey.spec.ts
git commit -m "test(pq): scaffold markus-complete-journey helper"
```

---

### Task 2: Add the three test cases

**Files:**
- Modify: `tests/e2e/pq/markus-complete-journey.spec.ts`

- [ ] **Step 1: Append the test.describe block to the file**

Append the following after the closing `}` of `setupCompleteJourney`:

```typescript
test.describe('Marcus — Complete Journey (PQ)', () => {
  test.setTimeout(5 * 60 * 1000); // 5 min: full journey chains many waits

  test('US-MK01: complete journey ends on cover letter page with iframe visible', async ({
    page,
  }) => {
    await setupCompleteJourney(page);
    await expect(page).toHaveURL(/\/flow\/.*\/cover-letter/);
    await expect(page.getByTestId('cover-letter-iframe')).toBeVisible();
  });

  test('US-MK02: back-to-CV navigation works from cover letter page', async ({
    page,
  }) => {
    const flowId = await setupCompleteJourney(page);
    await expect(page.getByTestId('cl-view-cv-btn')).toBeVisible();
    await page.getByTestId('cl-view-cv-btn').click();
    await page.waitForURL(`**/flow/${flowId}/cv`);
  });

  test('US-MK03: PDF download button is present and enabled after full journey', async ({
    page,
  }) => {
    await setupCompleteJourney(page);
    await expect(page.getByTestId('cl-topbar-download-btn')).toBeVisible();
    await expect(page.getByTestId('cl-topbar-download-btn')).toBeEnabled();
  });
});
```

- [ ] **Step 2: Type-check the complete file**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
git add tests/e2e/pq/markus-complete-journey.spec.ts
git commit -m "test(pq): add marcus complete journey tests US-MK01/02/03"
```

---

### Task 3: Run and verify against the live stack

**Prerequisite:** Docker stack must be running and `OPENROUTER_API_KEY` must be set.

- [ ] **Step 1: Confirm the stack is up**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
docker compose ps
```

Expected: `backend`, `frontend`, `db` containers all show `Up`.

- [ ] **Step 2: Run only the new file in headed mode (first run — watch for surprises)**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
OPENROUTER_API_KEY=<key> npx playwright test \
  --config=playwright.config.pq.ts \
  tests/e2e/pq/markus-complete-journey.spec.ts \
  --headed
```

Expected: all three tests pass (green). The full run takes ~5–8 minutes because each test drives the complete journey independently.

- [ ] **Step 3: If a test fails — check the trace**

```bash
npx playwright show-report /tmp/test-results-pq
```

Common failure causes and fixes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Stuck waiting for `interview-button` | Gaps page showed no gaps | Check `sample_cv.pdf` matches `sample_jd.txt` — gaps must exist |
| `done-button` not found | LLM resolved all gaps with 1 answer → already on completion screen | The `completionVisible` guard handles this; check test trace for actual state |
| `refinement-panel` timeout | CV generation slow on this machine | Increase `timeout` on that assertion from 90000 to 120000 |
| `cover-letter-iframe` timeout | Cover letter generation slow | Increase `timeout` from 60000 to 90000 |

- [ ] **Step 4: Run the full PQ suite to check for regressions**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts
```

Expected: all existing PQ tests still pass.

- [ ] **Step 5: Commit if any timeout adjustments were made during step 3**

```bash
cd /home/applire-adm/Projekte/applire/applire-core
git add tests/e2e/pq/markus-complete-journey.spec.ts
git commit -m "test(pq): adjust timeouts based on live run"
```

Skip this step if no changes were needed.

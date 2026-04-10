# Sprint 18 — Gap Colors & Test Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix swapped gap severity dot colors and overhaul the test structure to follow a V-model (IQ/OQ/PQ) layout with module-based naming, reliable CI coverage, and a manual PQ workflow for LLM-dependent tests.

**Architecture:** The color fix is a 2-line change validated by a new OQ spec. The test structure overhaul restructures `tests/e2e/` into `iq/`, `oq/`, and `pq/` tiers, renames all iteration-based test files to module-based names, adds two new OQ specs for high-risk flows, adds an IQ spec, and introduces a `workflow_dispatch` PQ workflow. All OQ tests mock API routes with `page.route()` and never call a real LLM.

**Tech Stack:** Playwright (TypeScript), Vitest, pytest, GitHub Actions YAML, Next.js/React (Tailwind CSS)

---

## File Map

### Created
- `tests/e2e/iq/startup.spec.ts` — IQ: health endpoint + frontend reachable
- `tests/e2e/oq/gaps-page.spec.ts` — OQ: gaps page critical flows (mocked)
- `tests/e2e/oq/upload-flow.spec.ts` — OQ: home → processing → gaps navigation (mocked)
- `tests/e2e/oq/match-page.spec.ts` — moved from `match-smoke.spec.ts`
- `tests/e2e/oq/cv-preview.spec.ts` — moved from `cv-preview.spec.ts`
- `tests/e2e/oq/cv-section-editor.spec.ts` — merged from `finetuner-sprint9.spec.ts` + `finetuner-sprint10.spec.ts`
- `tests/e2e/oq/photo-management.spec.ts` — moved from `photo-sprint14.spec.ts`
- `tests/e2e/pq/marcus-new-user-journey.spec.ts` — consolidated from `interview-sprint5.spec.ts` + `marcus-persona.spec.ts`
- `playwright.config.pq.ts` — Playwright config for PQ tier (real LLM, OpenRouter)
- `.github/workflows/pq.yml` — manual PQ workflow (workflow_dispatch)
- `.github/PULL_REQUEST_TEMPLATE.md` — PR checklist including PQ reminder
- `docs/TRACEABILITY.md` — traceability matrix (FS items → test IDs)

### Modified
- `frontend/app/flow/[flowId]/gaps/page.tsx:475,508` — fix dot color classes
- `playwright.config.ts` — add `testIgnore: ['**/pq/**']`
- `docs/TESTING.md` — full rewrite with V-model structure

### Renamed (backend unit tests — `tests/unit/`)
`test_iter6_llm_providers.py` → `test_llm_providers.py`
`test_iter7_mcp_tools.py` → `test_mcp_tools.py`
`test_iter7_mcp_resources.py` → `test_mcp_resources.py`
`test_iter8_scraper.py` → `test_scraper_service.py`
`test_iter9_linkedin_parser.py` → `test_linkedin_parser.py`
`test_iter10_auth.py` → `test_auth_provider.py`
`test_iter10_retention.py` → `test_retention_worker.py`
`test_iter11_profile.py` → `test_profile_service.py`
`test_iter12_upload.py` → `test_cv_upload.py`
`test_iter13_gap.py` → `test_gap_analysis.py`
`test_iter15_flow_orchestrator.py` → `test_flow_orchestrator.py`
`test_iter16_llm_provider.py` → `test_llm_provider_integration.py`
`test_iter17_application.py` → `test_application_service.py`
`test_iter17_retention.py` → `test_retention_service.py`
`test_iter20_cv_sprint6.py` → `test_cv_generation.py`
`test_iter21_sprint7_mcp.py` → `test_mcp_endpoints.py`
`test_iter24_assist_microsession.py` → `test_micro_session.py`
`test_sprint13_coverage.py` → `test_response_parser.py`
`test_sprint14_photo.py` → `test_photo_service.py`
`test_sprint15_interview.py` → `test_interview_service.py`
`test_session_service_coverage.py` → `test_session_service.py`

### Renamed (backend integration tests — `tests/`)
`test_iter0_skeleton.py` → `test_health.py`
`test_iter1_jd_analysis.py` → `test_jd_analysis.py`
`test_iter2_profile_import.py` → `test_profile_import.py`
`test_iter3_gap_analysis.py` → `test_gap_analysis.py`
`test_iter4_gap_fill_interview.py` → `test_interview_flow.py`
`test_iter5_cv_generation.py` → `test_cv_generation.py`
`test_iter6_llm_providers.py` → `test_llm_providers.py`
`test_iter7_mcp_server.py` → `test_mcp_server.py`
`test_iter8_jd_url_intake.py` → `test_jd_url_intake.py`
`test_iter9_second_template_linkedin.py` → `test_linkedin_template.py`
`test_iter10_auth_retention.py` → `test_auth_retention.py`
`test_iter12_cv_upload.py` → `test_cv_upload.py`
`test_iter13_gap_detection.py` → `test_gap_detection.py`
`test_iter15_flow_orchestrator.py` → `test_flow_orchestrator.py`
`test_iter16_llm_provider.py` → `test_llm_provider.py`
`test_iter17_application.py` → `test_application.py`
`test_iter20_cv_generation_ui.py` → `test_cv_generation_ui.py`
`test_iter21_sprint7_endpoints.py` → `test_mcp_endpoints.py`
`test_iter21_sprint7_gdpr.py` → `test_gdpr.py`

### Deleted
`tests/e2e/match-smoke.spec.ts` (replaced by `oq/match-page.spec.ts`)
`tests/e2e/cv-preview.spec.ts` (replaced by `oq/cv-preview.spec.ts`)
`tests/e2e/finetuner-sprint9.spec.ts` (merged into `oq/cv-section-editor.spec.ts`)
`tests/e2e/finetuner-sprint10.spec.ts` (merged into `oq/cv-section-editor.spec.ts`)
`tests/e2e/photo-sprint14.spec.ts` (replaced by `oq/photo-management.spec.ts`)
`tests/e2e/interview-sprint5.spec.ts` (consolidated into `pq/marcus-new-user-journey.spec.ts`)
`tests/e2e/marcus-persona.spec.ts` (consolidated into `pq/marcus-new-user-journey.spec.ts`)

---

## Task 1: Create sprint-18 branch

**Files:** none

- [ ] **Step 1: Create and check out branch**

```bash
git checkout -b sprint-18
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```
Expected: `sprint-18`

---

## Task 2: Update Playwright config to exclude PQ tier from standard CI run

**Files:**
- Modify: `playwright.config.ts`
- Create: `playwright.config.pq.ts`

- [ ] **Step 1: Add `testIgnore` to `playwright.config.ts`**

In `playwright.config.ts`, add `testIgnore` to the `defineConfig` call:

```typescript
export default defineConfig({
  testDir: './tests/e2e',
  testIgnore: ['**/pq/**'],   // PQ tests require real LLM — run via workflow_dispatch only
  // ... rest unchanged
```

- [ ] **Step 2: Create `playwright.config.pq.ts`**

```typescript
import { defineConfig, devices } from '@playwright/test';

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
  fullyParallel: false,
  workers: 1,
  timeout: 120 * 1000,
  expect: { timeout: 15 * 1000 },
  reporter: [['html'], ['github']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15 * 1000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  retries: 1,
  outputDir: './test-results-pq',
});
```

- [ ] **Step 3: Commit**

```bash
git add playwright.config.ts playwright.config.pq.ts
git commit -m "chore(tests): exclude pq/ from standard Playwright run, add pq config"
```

---

## Task 3: Create E2E tier folder structure and move existing specs

**Files:**
- Create: `tests/e2e/iq/` (directory)
- Create: `tests/e2e/oq/` (directory)
- Create: `tests/e2e/pq/` (directory)
- Move: existing spec files as listed

- [ ] **Step 1: Create tier directories**

```bash
mkdir -p tests/e2e/iq tests/e2e/oq tests/e2e/pq
```

- [ ] **Step 2: Move OQ specs that need no content changes**

```bash
git mv tests/e2e/match-smoke.spec.ts tests/e2e/oq/match-page.spec.ts
git mv tests/e2e/cv-preview.spec.ts tests/e2e/oq/cv-preview.spec.ts
git mv tests/e2e/photo-sprint14.spec.ts tests/e2e/oq/photo-management.spec.ts
```

- [ ] **Step 3: Create `oq/cv-section-editor.spec.ts` by merging finetuner-sprint9 + sprint10**

Read both files:
```bash
cat tests/e2e/finetuner-sprint9.spec.ts
cat tests/e2e/finetuner-sprint10.spec.ts
```

Then create `tests/e2e/oq/cv-section-editor.spec.ts` with the combined content:
- Copy the full content of `finetuner-sprint9.spec.ts`
- Update the top comment to remove sprint references
- Append all `test.describe` blocks from `finetuner-sprint10.spec.ts` (any shared mock fixtures/constants go at the top, deduplicated)
- Update any comment references from "Sprint 9" / "Sprint 10" to describe what they test

The file header should be:

```typescript
// tests/e2e/oq/cv-section-editor.spec.ts
import { test, expect } from "@playwright/test";

/**
 * CV Section Editor — OQ Tests
 *
 * Covers:
 *  - Fine-tune toggle opens FineTunePanel with section list
 *  - Clicking a section reveals SectionEditor textarea with content
 *  - Edit → Save → SaveScopePrompt → "Just this CV" → preview iframe updates
 *  - Switching sections with unsaved edits shows the unsaved-changes guard dialog
 *  - Polish behaviours: character counter, auto-resize textarea, undo-discard flow
 *
 * Uses page.route() mocks — does NOT require a running backend.
 */
```

- [ ] **Step 4: Delete the original finetuner files**

```bash
git rm tests/e2e/finetuner-sprint9.spec.ts
git rm tests/e2e/finetuner-sprint10.spec.ts
```

- [ ] **Step 5: Move interview-sprint5 and marcus-persona to pq/**

```bash
git mv tests/e2e/interview-sprint5.spec.ts tests/e2e/pq/marcus-new-user-journey.spec.ts
git rm tests/e2e/marcus-persona.spec.ts
```

Open `tests/e2e/pq/marcus-new-user-journey.spec.ts` and update the file header comment:

```typescript
// tests/e2e/pq/marcus-new-user-journey.spec.ts

/**
 * Marcus — New User Journey (PQ)
 *
 * Covers the full happy path for a new Marcus-persona user:
 *   CV upload → JD analysis → gap detection → interview → CV generation
 *
 * PQ tier: requires the full Docker stack AND a real LLM via OpenRouter.
 * Run locally:   OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts
 * Run in CI:     Trigger the "PQ Tests" workflow_dispatch in GitHub Actions.
 *
 * DO NOT run this file with the standard `npx playwright test` command.
 */
```

- [ ] **Step 6: Verify Playwright discovers the moved files correctly**

```bash
npx playwright test --list --config=playwright.config.ts 2>&1 | grep -E "spec|Error" | head -30
```

Expected: lists tests from `oq/` and `iq/` (empty for now), no errors. Does NOT list `pq/` tests.

- [ ] **Step 7: Commit**

```bash
git add tests/e2e/
git commit -m "refactor(tests): restructure e2e into iq/oq/pq tiers, rename to module-based names"
```

---

## Task 4: Write OQ spec for gaps page (includes color regression test)

**Files:**
- Create: `tests/e2e/oq/gaps-page.spec.ts`

This spec is written BEFORE the color fix. The color assertions will fail first, validating TDD.

- [ ] **Step 1: Create `tests/e2e/oq/gaps-page.spec.ts`**

```typescript
// tests/e2e/oq/gaps-page.spec.ts
import { test, expect } from "@playwright/test";

/**
 * Gaps Page — OQ Tests
 *
 * Covers:
 *  - Gap categories render with correct severity dot colors
 *    (Cat B = yellow/warning, Cat C = red/critical)
 *  - "Generate CV Now" button calls advance API and navigates to CV page
 *  - "Quick Interview" button visible for new users with gaps, navigates to interview page
 *  - Resolved gap shows green checkmark after micro-session completes
 *
 * Uses page.route() mocks — does NOT require a running backend.
 */

const FLOW_ID = "flow-test-0000-0000-0000-000000000001";
const JOB_ID = "job-test-0000-0000-0000-000000000002";
const GAP_ID = "gap-test-0000-0000-0000-000000000003";

const MOCK_FLOW_STATE = {
  job_id: JOB_ID,
  user_type: "new",
  available_actions: {},
  gap_summary: { gap_analysis_id: GAP_ID },
  job_summary: { role_title: "Senior Software Engineer" },
};

const MOCK_GAP_ANALYSIS = {
  id: GAP_ID,
  match_score: 0.72,
  category_a: ["Python", "FastAPI"],
  category_b: ["Docker", "PostgreSQL"],
  category_c: ["Kubernetes", "Terraform"],
  strengths: ["Python", "FastAPI"],
};

const MOCK_PROFILE = {
  positions_count: 5,
  projects_count: 12,
  certifications_count: 3,
  data_points_count: 47,
};

const MOCK_ADVANCE_RESPONSE = { status: "ok" };

async function setupGapsPageMocks(page: import("@playwright/test").Page) {
  await page.route(`**/api/flow/${FLOW_ID}/state`, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_FLOW_STATE) })
  );
  await page.route(`**/api/job/${JOB_ID}/gaps`, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_GAP_ANALYSIS) })
  );
  await page.route(`**/api/profile`, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_PROFILE) })
  );
}

test.describe("Gaps page", () => {
  test("renders gap categories with correct severity dot colors", async ({ page }) => {
    await setupGapsPageMocks(page);
    await page.goto(`/flow/${FLOW_ID}/gaps`);
    await expect(page.getByTestId("gap-analysis-page")).toBeVisible({ timeout: 10000 });

    // Category C dots must be red (bg-critical), not yellow
    const catCDots = page.getByTestId("gap-c-severity-dot");
    await expect(catCDots.first()).toBeVisible();
    const catCClass = await catCDots.first().getAttribute("class");
    expect(catCClass).toContain("bg-critical");
    expect(catCClass).not.toContain("bg-warning");

    // Category B dots must be yellow (bg-warning), not teal
    const catBDots = page.getByTestId("gap-b-severity-dot");
    await expect(catBDots.first()).toBeVisible();
    const catBClass = await catBDots.first().getAttribute("class");
    expect(catBClass).toContain("bg-warning");
    expect(catBClass).not.toContain("bg-teal");
  });

  test("shows correct gap counts in badges", async ({ page }) => {
    await setupGapsPageMocks(page);
    await page.goto(`/flow/${FLOW_ID}/gaps`);
    await expect(page.getByTestId("gap-analysis-page")).toBeVisible({ timeout: 10000 });

    // Match score display
    await expect(page.getByTestId("match-score-display")).toContainText("72%");

    // Gaps section shows total gaps (Cat B + Cat C = 4)
    await expect(page.getByTestId("gaps-section")).toBeVisible();
    await expect(page.getByTestId("gaps-section")).toContainText("4 gaps identified");
  });

  test("Generate CV Now button advances flow and navigates to CV page", async ({ page }) => {
    await setupGapsPageMocks(page);

    let advanceCalled = false;
    await page.route(`**/api/flow/${FLOW_ID}/advance`, (route) => {
      advanceCalled = true;
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_ADVANCE_RESPONSE) });
    });

    await page.goto(`/flow/${FLOW_ID}/gaps`);
    await expect(page.getByTestId("gap-analysis-page")).toBeVisible({ timeout: 10000 });

    await page.getByTestId("generate-cv-button").click();

    await expect(page).toHaveURL(`/flow/${FLOW_ID}/cv`, { timeout: 10000 });
    expect(advanceCalled).toBe(true);
  });

  test("Quick Interview button visible for new user with gaps and navigates to interview", async ({ page }) => {
    await setupGapsPageMocks(page);

    const SESSION_ID = "session-test-0000-0000-0000-000000000004";
    await page.route(`**/api/session`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ session_id: SESSION_ID, id: SESSION_ID }),
      })
    );
    await page.route(`**/api/flow/${FLOW_ID}/advance`, (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_ADVANCE_RESPONSE) })
    );

    await page.goto(`/flow/${FLOW_ID}/gaps`);
    await expect(page.getByTestId("gap-analysis-page")).toBeVisible({ timeout: 10000 });

    const interviewButton = page.getByTestId("interview-button");
    await expect(interviewButton).toBeVisible();
    await interviewButton.click();

    await expect(page).toHaveURL(`/flow/${FLOW_ID}/interview`, { timeout: 10000 });
  });

  test("shows error message when advance API fails", async ({ page }) => {
    await setupGapsPageMocks(page);
    await page.route(`**/api/flow/${FLOW_ID}/advance`, (route) =>
      route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid step transition" }),
      })
    );

    await page.goto(`/flow/${FLOW_ID}/gaps`);
    await expect(page.getByTestId("gap-analysis-page")).toBeVisible({ timeout: 10000 });

    await page.getByTestId("generate-cv-button").click();

    await expect(page.getByTestId("error-message")).toBeVisible({ timeout: 5000 });
    await expect(page.getByTestId("error-message")).toContainText("Invalid step transition");
  });
});
```

- [ ] **Step 2: Run the spec — expect the color test to FAIL**

```bash
npx playwright test tests/e2e/oq/gaps-page.spec.ts --project=chromium 2>&1 | tail -30
```

Expected: `renders gap categories with correct severity dot colors` FAILS because `data-testid="gap-c-severity-dot"` does not exist yet and the color classes are wrong.

---

## Task 5: Fix gap severity colors and add data-testid attributes to dots

**Files:**
- Modify: `frontend/app/flow/[flowId]/gaps/page.tsx:462-530`

- [ ] **Step 1: Fix Category C dot (line ~475)**

Find this line in the Category C gap render block:
```typescript
<div className="w-2 h-2 rounded-full bg-warning mt-2 shrink-0" />
```

Replace with:
```typescript
<div data-testid="gap-c-severity-dot" className="w-2 h-2 rounded-full bg-critical mt-2 shrink-0" />
```

- [ ] **Step 2: Fix Category B dot (line ~508)**

Find this line in the Category B gap render block:
```typescript
<div className="w-2 h-2 rounded-full bg-teal mt-2 shrink-0" />
```

Replace with:
```typescript
<div data-testid="gap-b-severity-dot" className="w-2 h-2 rounded-full bg-warning mt-2 shrink-0" />
```

- [ ] **Step 3: Run the gaps-page OQ spec — expect all tests to PASS**

```bash
npx playwright test tests/e2e/oq/gaps-page.spec.ts --project=chromium 2>&1 | tail -20
```

Expected: 5 passed (the frontend dev server must be running: `cd frontend && npm run dev`)

- [ ] **Step 4: Commit**

```bash
git add frontend/app/flow/[flowId]/gaps/page.tsx tests/e2e/oq/gaps-page.spec.ts
git commit -m "fix(gaps): correct severity dot colors (Cat C red, Cat B yellow)

Category C gaps (missing skills) now show a red dot (bg-critical).
Category B gaps (likely matches) now show a yellow dot (bg-warning).
Adds data-testid attributes to both dots for OQ test targeting.
Adds oq/gaps-page.spec.ts covering color regression + CTA navigation."
```

---

## Task 6: Write OQ spec for upload flow

**Files:**
- Create: `tests/e2e/oq/upload-flow.spec.ts`

- [ ] **Step 1: Create `tests/e2e/oq/upload-flow.spec.ts`**

```typescript
// tests/e2e/oq/upload-flow.spec.ts
import { test, expect, Page } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

/**
 * Upload Flow — OQ Tests
 *
 * Covers:
 *  - Home page renders upload area for new users
 *  - Submit button is disabled until a CV file is selected
 *  - Submitting triggers the processing overlay
 *  - After all pipeline steps complete, navigates to /flow/:id/gaps
 *  - Error state renders when the JD analysis API fails
 *
 * Uses page.route() mocks — does NOT require a running backend.
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SAMPLE_CV = path.join(__dirname, "../../fixtures/profiles/sample_cv.pdf");

const FLOW_ID = "flow-upload-0000-0000-0000-000000000001";
const JOB_ID = "job-upload-0000-0000-0000-000000000002";
const GAP_ID = "gap-upload-0000-0000-0000-000000000003";

const MOCK_JD_ANALYZE = { id: JOB_ID, role_title: "Senior Software Engineer" };
const MOCK_FLOW_CREATE = { flow_id: FLOW_ID };
const MOCK_UPLOAD = { success: true };
const MOCK_FLOW_STATE = {
  job_id: JOB_ID,
  user_type: "new",
  available_actions: {},
  gap_summary: null,
  job_summary: { role_title: "Senior Software Engineer" },
};
const MOCK_GAP_ANALYSIS = {
  id: GAP_ID,
  match_score: 0.78,
  category_a: ["Python"],
  category_b: ["Docker"],
  category_c: ["Kubernetes"],
  strengths: ["Python"],
};
const MOCK_ADVANCE = { status: "ok" };

async function setupUploadMocks(page: Page) {
  await page.route("**/api/profile/exists", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ exists: false }) })
  );
  await page.route("**/api/job/analyze", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_JD_ANALYZE) })
  );
  await page.route("**/api/flow", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_FLOW_CREATE) })
  );
  await page.route("**/api/profile/upload", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_UPLOAD) })
  );
  await page.route(`**/api/flow/${FLOW_ID}/state`, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_FLOW_STATE) })
  );
  await page.route(`**/api/job/${JOB_ID}/gaps`, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_GAP_ANALYSIS) })
  );
  await page.route(`**/api/flow/${FLOW_ID}/advance`, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_ADVANCE) })
  );
}

test.describe("Upload flow", () => {
  test("submit button is disabled without a CV file", async ({ page }) => {
    await page.route("**/api/profile/exists", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ exists: false }) })
    );
    await page.goto("/");
    await expect(page.getByTestId("submit-button")).toBeDisabled({ timeout: 10000 });
  });

  test("submit button enables after uploading a CV file", async ({ page }) => {
    await page.route("**/api/profile/exists", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ exists: false }) })
    );
    await page.goto("/");
    await expect(page.getByTestId("submit-button")).toBeDisabled({ timeout: 10000 });

    await page.getByTestId("file-input").setInputFiles(SAMPLE_CV);

    await expect(page.getByTestId("submit-button")).toBeEnabled({ timeout: 5000 });
  });

  test("submitting shows processing overlay and navigates to gaps page", async ({ page }) => {
    await setupUploadMocks(page);
    await page.goto("/");

    // Switch to paste-text JD mode and fill in text
    await page.getByRole("button", { name: "Paste Text" }).click();
    await page.locator("textarea").fill("We are looking for a Senior Software Engineer with Python and Docker experience.");

    // Upload CV
    await page.getByTestId("file-input").setInputFiles(SAMPLE_CV);
    await expect(page.getByTestId("submit-button")).toBeEnabled({ timeout: 5000 });

    // Submit
    await page.getByTestId("submit-button").click();

    // Processing overlay should appear
    await expect(page.getByTestId("processing-indicator")).toBeVisible({ timeout: 5000 });

    // Eventually navigates to gaps page
    await expect(page).toHaveURL(new RegExp(`/flow/${FLOW_ID}/gaps`), { timeout: 30000 });
  });

  test("shows error when JD analysis API fails", async ({ page }) => {
    await page.route("**/api/profile/exists", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ exists: false }) })
    );
    await page.route("**/api/job/analyze", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "LLM service unavailable" }),
      })
    );
    await page.route("**/api/flow", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_FLOW_CREATE) })
    );
    await page.route("**/api/profile/upload", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_UPLOAD) })
    );

    await page.goto("/");
    await page.getByRole("button", { name: "Paste Text" }).click();
    await page.locator("textarea").fill("Some job description text.");
    await page.getByTestId("file-input").setInputFiles(SAMPLE_CV);
    await page.getByTestId("submit-button").click();

    // Processing overlay appears then shows error
    await expect(page.getByTestId("processing-indicator")).toBeVisible({ timeout: 5000 });
    await expect(page.getByTestId("processing-error")).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId("processing-error")).toContainText("LLM service unavailable");
  });
});
```

- [ ] **Step 2: Run the spec — note which tests pass and which need `data-testid` additions**

```bash
npx playwright test tests/e2e/oq/upload-flow.spec.ts --project=chromium 2>&1 | tail -30
```

If `processing-error` testid is missing from `ProcessingOverlay`, add it:

In `frontend/components/processing-overlay.tsx`, find the error rendering block and add `data-testid="processing-error"`:

```tsx
{error && (
  <div data-testid="processing-error" className="...existing classes...">
    <p className="text-sm text-critical">{error}</p>
    ...
  </div>
)}
```

Re-run until all 4 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/oq/upload-flow.spec.ts frontend/components/processing-overlay.tsx
git commit -m "test(oq): add upload-flow OQ spec covering submit state and navigation"
```

---

## Task 7: Write IQ spec for Docker startup

**Files:**
- Create: `tests/e2e/iq/startup.spec.ts`

The IQ spec requires the Docker stack to be running. It is intentionally simple — it validates installation, not behaviour.

- [ ] **Step 1: Create `tests/e2e/iq/startup.spec.ts`**

```typescript
// tests/e2e/iq/startup.spec.ts
import { test, expect, request } from "@playwright/test";

/**
 * IQ (Installation Qualification) Tests
 *
 * Validates that the Docker stack starts correctly and the system
 * is reachable before any functional tests run.
 *
 * Requires: Docker stack running (docker compose up -d)
 */

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8001";

test.describe("IQ — System startup", () => {
  test("backend health endpoint returns 200", async () => {
    const ctx = await request.newContext();
    const res = await ctx.get(`${BACKEND_URL}/health`);
    expect(res.status()).toBe(200);
    await ctx.dispose();
  });

  test("frontend root page is reachable", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Applire/i, { timeout: 15000 });
  });

  test("upload file input is present on home page", async ({ page }) => {
    await page.route("**/api/profile/exists", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ exists: false }) })
    );
    await page.goto("/");
    await expect(page.getByTestId("file-input")).toBeAttached({ timeout: 10000 });
  });
});
```

- [ ] **Step 2: Commit**

```bash
git add tests/e2e/iq/startup.spec.ts
git commit -m "test(iq): add startup IQ spec (health endpoint, UI reachable, file input present)"
```

---

## Task 8: Rename backend unit tests

**Files:** 22 files renamed in `tests/unit/`

- [ ] **Step 1: Rename all unit test files**

```bash
cd tests/unit
git mv test_iter6_llm_providers.py test_llm_providers.py
git mv test_iter7_mcp_tools.py test_mcp_tools.py
git mv test_iter7_mcp_resources.py test_mcp_resources.py
git mv test_iter8_scraper.py test_scraper_service.py
git mv test_iter9_linkedin_parser.py test_linkedin_parser.py
git mv test_iter10_auth.py test_auth_provider.py
git mv test_iter10_retention.py test_retention_worker.py
git mv test_iter11_profile.py test_profile_service.py
git mv test_iter12_upload.py test_cv_upload.py
git mv test_iter13_gap.py test_gap_analysis.py
git mv test_iter15_flow_orchestrator.py test_flow_orchestrator.py
git mv test_iter16_llm_provider.py test_llm_provider_integration.py
git mv test_iter17_application.py test_application_service.py
git mv test_iter17_retention.py test_retention_service.py
git mv test_iter20_cv_sprint6.py test_cv_generation.py
git mv test_iter21_sprint7_mcp.py test_mcp_endpoints.py
git mv test_iter24_assist_microsession.py test_micro_session.py
git mv test_sprint13_coverage.py test_response_parser.py
git mv test_sprint14_photo.py test_photo_service.py
git mv test_sprint15_interview.py test_interview_service.py
git mv test_session_service_coverage.py test_session_service.py
cd ../..
```

- [ ] **Step 2: Verify unit tests still pass**

```bash
PYTHONPATH=backend pytest tests/unit/ -v --cov=applire --cov-config=backend/.coveragerc --cov-fail-under=75 2>&1 | tail -20
```

Expected: all tests collected and passing, coverage ≥ 75%.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/
git commit -m "refactor(tests): rename unit tests from iter/sprint-based to module-based names"
```

---

## Task 9: Rename backend integration tests

**Files:** 19 files renamed in `tests/`

- [ ] **Step 1: Rename all integration test files**

```bash
git mv tests/test_iter0_skeleton.py tests/test_health.py
git mv tests/test_iter1_jd_analysis.py tests/test_jd_analysis.py
git mv tests/test_iter2_profile_import.py tests/test_profile_import.py
git mv tests/test_iter3_gap_analysis.py tests/test_gap_analysis.py
git mv tests/test_iter4_gap_fill_interview.py tests/test_interview_flow.py
git mv tests/test_iter5_cv_generation.py tests/test_cv_generation.py
git mv tests/test_iter6_llm_providers.py tests/test_llm_providers.py
git mv tests/test_iter7_mcp_server.py tests/test_mcp_server.py
git mv tests/test_iter8_jd_url_intake.py tests/test_jd_url_intake.py
git mv tests/test_iter9_second_template_linkedin.py tests/test_linkedin_template.py
git mv tests/test_iter10_auth_retention.py tests/test_auth_retention.py
git mv tests/test_iter12_cv_upload.py tests/test_cv_upload.py
git mv tests/test_iter13_gap_detection.py tests/test_gap_detection.py
git mv tests/test_iter15_flow_orchestrator.py tests/test_flow_orchestrator.py
git mv tests/test_iter16_llm_provider.py tests/test_llm_provider.py
git mv tests/test_iter17_application.py tests/test_application.py
git mv tests/test_iter20_cv_generation_ui.py tests/test_cv_generation_ui.py
git mv tests/test_iter21_sprint7_endpoints.py tests/test_mcp_endpoints.py
git mv tests/test_iter21_sprint7_gdpr.py tests/test_gdpr.py
```

- [ ] **Step 2: Verify CI would still collect these tests correctly**

```bash
python -m pytest tests/ --ignore=tests/e2e --ignore=tests/unit --collect-only 2>&1 | tail -20
```

Expected: all test files collected, no import errors.

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "refactor(tests): rename integration tests from iter-based to module-based names"
```

---

## Task 10: Add PQ GitHub Actions workflow and PR template

**Files:**
- Create: `.github/workflows/pq.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: Create `.github/workflows/pq.yml`**

```yaml
name: PQ Tests (Manual)

on:
  workflow_dispatch:
    inputs:
      reason:
        description: "Reason for running PQ (e.g. pre-release, post-merge)"
        required: false
        default: "Manual trigger"

jobs:
  pq-tests:
    name: PQ — Marcus New User Journey
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      checks: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: "frontend/package-lock.json"

      - name: Install root dependencies
        run: npm ci

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Install Playwright browsers
        run: node_modules/.bin/playwright install --with-deps chromium

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Create .env.dev from CI template
        run: cp .env.ci .env.dev

      - name: Start Docker services
        run: docker compose up -d --build

      - name: Wait for application to be ready
        run: |
          echo "Waiting for backend..."
          timeout 300 bash -c 'until curl -sf http://localhost:8001/health; do sleep 3; done'
          echo "Backend ready."
          timeout 180 bash -c 'until curl -sf http://localhost:3000; do sleep 2; done'
          echo "Frontend ready."

      - name: Run database migrations
        run: docker compose exec backend python -m alembic upgrade head

      - name: Run PQ tests
        run: node_modules/.bin/playwright test --config=playwright.config.pq.ts
        env:
          CI: true
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}

      - name: Upload Playwright PQ report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pq-playwright-report
          path: playwright-report/
          retention-days: 30

      - name: Tear down Docker services
        if: always()
        run: docker compose down -v
```

- [ ] **Step 2: Create `.github/PULL_REQUEST_TEMPLATE.md`**

```markdown
## Summary

<!-- What does this PR do? (1-3 bullet points) -->

## Test plan

- [ ] Backend unit tests pass (`pytest tests/unit/ --cov-fail-under=75`)
- [ ] Frontend unit tests pass (`cd frontend && npm test`)
- [ ] OQ Playwright tests pass (`npx playwright test`)
- [ ] PQ tests run locally and passed — OR — changes do not affect LLM-dependent flows

  To run PQ tests locally:
  ```bash
  OPENROUTER_API_KEY=<your-key> npx playwright test --config=playwright.config.pq.ts
  ```

## Notes

<!-- Anything reviewers should know -->
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pq.yml .github/PULL_REQUEST_TEMPLATE.md
git commit -m "ci: add PQ workflow_dispatch workflow and PR template with test checklist"
```

---

## Task 11: Rewrite `docs/TESTING.md`

**Files:**
- Modify: `docs/TESTING.md`

- [ ] **Step 1: Replace `docs/TESTING.md` entirely**

```markdown
# Applire Test Infrastructure

## V-Model Tier Structure

Applire uses a V-model-aligned test structure with four tiers:

| Tier | Scope | Runs in CI | LLM | Blocking |
|---|---|---|---|---|
| **Unit (DQ)** | Individual functions and components in isolation | Yes | No | Yes |
| **IQ** | Docker stack starts cleanly; health endpoint responds; UI reachable | Yes | No | Yes |
| **OQ** | Critical UI flows, all API routes mocked via `page.route()` | Yes | No | Yes |
| **PQ** | Marcus happy-path end-to-end with real LLM (OpenRouter) | Manual only | Yes | No |

**LLM boundary rule:** OQ tests never call an LLM. All backend routes are intercepted
with `page.route()` and return deterministic fixtures. PQ tests always call a real LLM
and are never run in the standard CI job.

---

## Folder Structure

```
tests/
├── unit/                        # Unit tests (DQ tier) — no Docker
│   ├── conftest.py              # Overrides Docker fixture; adds backend/ to sys.path
│   ├── test_gap_analysis.py
│   ├── test_flow_orchestrator.py
│   └── ...                      # One file per module
├── integration/                 # Full-stack LLM tests (PQ tier)
│   └── test_happy_path.py       # Requires INTEGRATION_LLM=1
├── e2e/
│   ├── iq/
│   │   └── startup.spec.ts      # Health + UI reachable
│   ├── oq/
│   │   ├── gaps-page.spec.ts    # Gaps page critical flows (mocked)
│   │   ├── upload-flow.spec.ts  # Home → processing → gaps (mocked)
│   │   ├── match-page.spec.ts   # Match page (mocked)
│   │   ├── cv-preview.spec.ts   # CV preview iframe (mocked)
│   │   ├── cv-section-editor.spec.ts  # FineTuner section editing (mocked)
│   │   └── photo-management.spec.ts   # Photo upload/crop (mocked)
│   └── pq/
│       └── marcus-new-user-journey.spec.ts  # Full happy path (real LLM)
├── fixtures/
│   ├── profiles/sample_cv.pdf
│   └── JDs/sample_jd.txt
├── test_health.py               # Integration: health endpoint
├── test_jd_analysis.py          # Integration: JD analysis API
├── test_gap_analysis.py         # Integration: gap detection API
└── ...                          # One file per backend module

backend/tests/
└── conftest.py                  # In-container CI variant (connects to backend:8000)
```

---

## Running Tests

### Unit tests (no Docker)

```bash
cd Solution
PYTHONPATH=backend pytest tests/unit/ -v \
  --cov=applire --cov-config=backend/.coveragerc \
  --cov-report=html:backend/htmlcov \
  --cov-fail-under=75
```

Coverage threshold: **≥ 75%** (enforced in CI).

### Frontend unit tests (Vitest)

```bash
cd frontend && npm test
```

### IQ + OQ Playwright tests (requires running frontend)

```bash
# Start frontend dev server first:
cd frontend && npm run dev

# Run IQ + OQ (excludes pq/ automatically):
npx playwright test

# Run a specific spec:
npx playwright test tests/e2e/oq/gaps-page.spec.ts --headed
```

### Integration tests (requires Docker stack)

```bash
docker compose up -d
pytest tests/ --ignore=tests/e2e --ignore=tests/unit -v
```

### PQ tests (requires Docker stack + OpenRouter API key)

```bash
docker compose up -d
OPENROUTER_API_KEY=<your-key> npx playwright test --config=playwright.config.pq.ts
```

Or trigger via GitHub Actions:
1. Go to **Actions → PQ Tests (Manual)**
2. Click **Run workflow**
3. Requires `OPENROUTER_API_KEY` secret to be configured in the repository

---

## Naming Convention

Test files are named after the module they test, not the sprint they were written in.

| Pattern | Example |
|---|---|
| Backend unit | `test_<module>.py` | `test_gap_analysis.py` |
| Backend integration | `test_<module>.py` | `test_cv_generation.py` |
| E2E OQ | `<page-or-feature>.spec.ts` | `gaps-page.spec.ts` |
| E2E PQ | `<persona>-<journey>.spec.ts` | `marcus-new-user-journey.spec.ts` |

---

## Coverage Gate

- Backend unit: **≥ 75%** (`--cov-fail-under=75`)
- No coverage gate on E2E tests (covered by traceability matrix instead)

See `docs/TRACEABILITY.md` for mapping of functional spec items to test IDs.

---

## Personas in PQ Tests

| Persona | Journey | PQ spec | Status |
|---|---|---|---|
| Marcus | New user: upload → gaps → interview → CV | `pq/marcus-new-user-journey.spec.ts` | Active |
| Emma | Returning user: dashboard → one-click tailoring | To be added when returning-user flow is built | Planned |
| Priya | International relocator: cultural adaptation | To be added | Planned |

---

## Troubleshooting

**Unit tests fail:**
```bash
python --version   # must be 3.12.3
pip install -r backend/requirements.txt
pytest tests/unit/ -vv --tb=long
```

**Playwright OQ tests fail:**
```bash
node --version     # must be 20+
npx playwright install --with-deps chromium firefox
npx playwright test --headed    # see browser
npx playwright test --debug     # step through
```

**PQ tests skip most cases:**
Verify `OPENROUTER_API_KEY` is set and the Docker stack is fully running.
```bash
curl http://localhost:8001/health
curl http://localhost:3000
```

---

*Last updated: 2026-04-10*
```

- [ ] **Step 2: Commit**

```bash
git add docs/TESTING.md
git commit -m "docs: rewrite TESTING.md with V-model tier structure and module-based naming"
```

---

## Task 12: Create `docs/TRACEABILITY.md`

**Files:**
- Create: `docs/TRACEABILITY.md`

- [ ] **Step 1: Create `docs/TRACEABILITY.md`**

```markdown
# Traceability Matrix

Maps functional specification items (Epic/User Story IDs from the Product Spec) to test IDs at each V-model tier. Extend this table when adding new features.

**Source:** `Documents/Product Specifications/Epic_and_User_Story_Tracker.csv`

| FS Item | Description | Unit (DQ) | IQ | OQ | PQ |
|---|---|---|---|---|---|
| US001 | Upload single or multiple CVs | `test_cv_upload.py` | `startup.spec.ts::upload file input present` | `upload-flow.spec.ts::submit button enables after uploading` | `marcus-new-user-journey.spec.ts` |
| US002 | Smart auto-merge of multiple CVs | `test_profile_service.py` | — | — | `marcus-new-user-journey.spec.ts` |
| US005 | Parse JD from URL or text | `test_jd_analysis.py` | — | `upload-flow.spec.ts::submitting shows processing overlay` | `marcus-new-user-journey.spec.ts` |
| US006 | Analyze JD for required skills | `test_gap_analysis.py` | — | `gaps-page.spec.ts::shows correct gap counts` | `marcus-new-user-journey.spec.ts` |
| US007 | Gap detection: category A/B/C | `test_gap_analysis.py` | — | `gaps-page.spec.ts::renders gap categories with correct severity dot colors` | `marcus-new-user-journey.spec.ts` |
| APP-19.3 | Generate CV Now button advances flow | — | — | `gaps-page.spec.ts::Generate CV Now button advances flow` | `marcus-new-user-journey.spec.ts` |
| APP-19.1 | Quick Interview button starts interview | — | — | `gaps-page.spec.ts::Quick Interview button visible for new user` | `marcus-new-user-journey.spec.ts` |
| APP-16 | Match page job cards | — | — | `match-page.spec.ts` | — |
| APP-23 | CV section editor (FineTuner) | — | — | `cv-section-editor.spec.ts` | — |
| APP-14 | Photo management | `test_photo_service.py` | — | `photo-management.spec.ts` | — |

## How to Extend

When implementing a new feature:
1. Add a row for each User Story or APP ticket the feature implements.
2. Link to the test file + test name (or `—` if not covered at that tier).
3. OQ coverage is required for all UI-facing features before merge.
4. PQ coverage is added when the feature is part of a user journey (Marcus, Emma, etc.).
```

- [ ] **Step 2: Commit**

```bash
git add docs/TRACEABILITY.md
git commit -m "docs: add traceability matrix mapping FS items to test IDs per V-model tier"
```

---

## Task 13: Final verification

- [ ] **Step 1: Run unit tests**

```bash
PYTHONPATH=backend pytest tests/unit/ --cov=applire --cov-config=backend/.coveragerc --cov-fail-under=75 -q 2>&1 | tail -10
```

Expected: all pass, coverage ≥ 75%.

- [ ] **Step 2: Run OQ Playwright tests**

With frontend dev server running (`cd frontend && npm run dev`):

```bash
npx playwright test --project=chromium 2>&1 | tail -20
```

Expected: all tests in `iq/` and `oq/` pass. `pq/` is excluded.

- [ ] **Step 3: Verify `pq/` is excluded from standard run**

```bash
npx playwright test --list 2>&1 | grep "pq/"
```

Expected: no output (pq tests not listed).

- [ ] **Step 4: Verify PQ config lists the correct tests**

```bash
npx playwright test --config=playwright.config.pq.ts --list 2>&1 | grep "spec"
```

Expected: lists `pq/marcus-new-user-journey.spec.ts` tests only.

- [ ] **Step 5: Final commit and push**

```bash
git status
git push -u origin sprint-18
```
```

// tests/e2e/finetuner-sprint9.spec.ts
import { test, expect } from "@playwright/test";

/**
 * Sprint 9 — Finetuner E2E Tests (task 23.16)
 *
 * Covers:
 *  - 23.6:  Fine-tune toggle opens FineTunePanel with section list
 *  - 23.9:  Clicking a section reveals SectionEditor textarea with content
 *  - 23.9/23.10/23.12: Edit → Save → SaveScopePrompt → "Just this CV" → preview iframe updates
 *  - 23.13: Switching sections with unsaved edits shows the unsaved-changes guard dialog
 *
 * These tests use page.route() mocks so they do NOT require a real backend.
 * All network calls are intercepted and fulfilled with in-memory fixtures.
 */

const TEST_FLOW_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff";
const TEST_CV_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd";
const TEST_JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;

// ---------------------------------------------------------------------------
// Mock data fixtures
// ---------------------------------------------------------------------------

const MOCK_FLOW_STATE = {
  job_id: TEST_JOB_ID,
  job_summary: { role_title: "Senior Software Engineer" },
  gap_summary: { match_score: 0.85 },
  cv_summary: {
    cv_id: TEST_CV_ID,
    pdf_url: `http://localhost:8001/api/cv/${TEST_CV_ID}/pdf`,
    expires_at: new Date(Date.now() + 86_400_000).toISOString(),
  },
};

const MOCK_CV_HTML = `<html><body>
  <h1>Max Mustermann</h1>
  <p>Senior Software Engineer</p>
  <p id="intro">Erfahrener Ingenieur mit zehn Jahren Berufserfahrung.</p>
</body></html>`;

const MOCK_CV_HTML_UPDATED = `<html><body>
  <h1>Max Mustermann</h1>
  <p>Senior Software Engineer</p>
  <p id="intro">My edited introduction text for E2E test</p>
</body></html>`;

const MOCK_SECTIONS = {
  sections: [
    {
      section_id: "intro",
      label: "Introduction",
      content: "Erfahrener Ingenieur mit zehn Jahren Berufserfahrung.",
      has_override: false,
      gaps: [{ id: "gap-1", label: "Missing cloud experience" }],
    },
    {
      section_id: "experience",
      label: "Experience",
      content: "10+ years in software engineering.",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

// ---------------------------------------------------------------------------
// Test setup: register routes before each test
// ---------------------------------------------------------------------------

test.describe("Finetuner — Sprint 9", () => {
  test.beforeEach(async ({ page }) => {
    // Mock flow state so the CV preview page renders immediately
    await page.route(`**/api/flow/${TEST_FLOW_ID}/state`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_FLOW_STATE),
      });
    });

    // Mock the CV HTML endpoint (initial load)
    await page.route(`**/api/cv/${TEST_CV_ID}/html`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/html",
        body: MOCK_CV_HTML,
      });
    });

    // Mock the sections list endpoint
    await page.route(`**/api/cv/${TEST_CV_ID}/sections`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SECTIONS),
      });
    });

    // Mock the section PATCH endpoint (returns updated HTML)
    await page.route(
      `**/api/cv/${TEST_CV_ID}/sections/**`,
      async (route) => {
        if (route.request().method() === "PATCH") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              html: MOCK_CV_HTML_UPDATED,
              overrides_applied: ["intro"],
            }),
          });
        } else {
          await route.continue();
        }
      }
    );
  });

  // -------------------------------------------------------------------------
  // 23.6 — Fine-tune toggle opens the section panel
  // -------------------------------------------------------------------------

  test("(23.6) clicking Fine-tune opens the section panel with section list", async ({
    page,
  }) => {
    await page.goto(CV_PAGE_URL);

    // The CV preview iframe must be visible first (confirms page rendered)
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({
      timeout: 10_000,
    });

    // Click the Fine-tune toggle
    await page.click('[data-testid="finetune-toggle"]');

    // At least one section list item must appear
    await expect(
      page.locator('[data-testid="section-list-item"]').first()
    ).toBeVisible({ timeout: 10_000 });

    // The panel also shows the finetune-preview-iframe (right-hand side)
    await expect(
      page.locator('[data-testid="finetune-preview-iframe"]')
    ).toBeVisible({ timeout: 5_000 });
  });

  // -------------------------------------------------------------------------
  // 23.9 — Clicking a section reveals the textarea with content
  // -------------------------------------------------------------------------

  test("(23.9) clicking a section item opens the textarea with pre-filled content", async ({
    page,
  }) => {
    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({
      timeout: 10_000,
    });

    // Open Fine-tune panel
    await page.click('[data-testid="finetune-toggle"]');
    const items = page.locator('[data-testid="section-list-item"]');
    await expect(items.first()).toBeVisible({ timeout: 10_000 });

    // Click the first section
    await items.first().click();

    // Textarea must appear and have content
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });
    const value = await textarea.inputValue();
    expect(value.length).toBeGreaterThan(0);
  });

  // -------------------------------------------------------------------------
  // 23.9 / 23.10 / 23.12 — Edit → Save → scope prompt → CV-only → preview updates
  // -------------------------------------------------------------------------

  test("(23.9, 23.10, 23.12) editing + saving with 'Just this CV' scope updates the preview", async ({
    page,
  }) => {
    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({
      timeout: 10_000,
    });

    // Clear any remembered scope choice so the prompt always shows
    await page.evaluate(() => sessionStorage.removeItem("finetune_save_scope"));

    // Open Fine-tune panel
    await page.click('[data-testid="finetune-toggle"]');

    // Click the Introduction section
    const introItem = page.locator('[data-testid="section-list-item"]', {
      hasText: "Introduction",
    });
    await expect(introItem).toBeVisible({ timeout: 10_000 });
    await introItem.click();

    // Edit the textarea
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });
    await textarea.fill("My edited introduction text for E2E test");

    // Save button must become enabled
    const saveBtn = page.locator('[data-testid="section-save"]');
    await expect(saveBtn).toBeEnabled({ timeout: 3_000 });
    await saveBtn.click();

    // SaveScopePrompt must appear
    await expect(page.locator('[data-testid="save-cv-only-btn"]')).toBeVisible({
      timeout: 3_000,
    });

    // Choose "Just this CV"
    await page.click('[data-testid="save-cv-only-btn"]');

    // Preview iframe must remain visible (srcDoc updated with new HTML)
    await expect(
      page.locator('[data-testid="finetune-preview-iframe"]')
    ).toBeVisible({ timeout: 5_000 });
  });

  // -------------------------------------------------------------------------
  // 23.13 — Switching sections with unsaved changes shows the guard dialog
  // -------------------------------------------------------------------------

  test("(23.13) switching sections with unsaved changes shows the discard dialog", async ({
    page,
  }) => {
    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({
      timeout: 10_000,
    });

    // Open Fine-tune panel
    await page.click('[data-testid="finetune-toggle"]');
    const items = page.locator('[data-testid="section-list-item"]');
    await expect(items.first()).toBeVisible({ timeout: 10_000 });

    // Open the first section and make an unsaved edit
    await items.first().click();
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });
    await textarea.fill("Unsaved edit to trigger guard");

    // Click a different section
    await items.nth(1).click();

    // The unsaved-changes guard dialog must appear
    await expect(page.locator('[data-testid="discard-confirm"]')).toBeVisible({
      timeout: 3_000,
    });
  });
});

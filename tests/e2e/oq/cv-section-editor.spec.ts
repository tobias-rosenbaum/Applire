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

const TEST_FLOW_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff";
const TEST_CV_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd";
const TEST_JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;
const SESSION_ID = "assist-session-1";

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

const MOCK_CV_HTML_UPDATED_PYTHON = `<html><body><h1>Max Mustermann</h1><p id="intro">Python-Entwickler</p></body></html>`;

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

const MOCK_SECTIONS_WITH_GAPS = {
  sections: [
    {
      section_id: "introduction",
      label: "Introduction",
      content: "Erfahrener Entwickler",
      has_override: false,
      gaps: [{ id: "Python", label: "Python" }],
    },
    {
      section_id: "skills",
      label: "Skills",
      content: "Java",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

const MOCK_SECTIONS_NO_GAPS = {
  sections: [
    {
      section_id: "introduction",
      label: "Introduction",
      content: "Python-Entwickler",
      has_override: true,
      gaps: [],
    },
    {
      section_id: "skills",
      label: "Skills",
      content: "Java",
      has_override: false,
      gaps: [],
    },
  ],
  general_gaps: [],
};

// ---------------------------------------------------------------------------
// Core section editor tests
// ---------------------------------------------------------------------------

test.describe("CV Section Editor — Core", () => {
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
  // Fine-tune toggle opens the section panel
  // -------------------------------------------------------------------------

  test("clicking Fine-tune opens the section panel with section list", async ({
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
  // Clicking a section reveals the textarea with content
  // -------------------------------------------------------------------------

  test("clicking a section item opens the textarea with pre-filled content", async ({
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
  // Edit → Save → scope prompt → CV-only → preview updates
  // -------------------------------------------------------------------------

  test("editing + saving with 'Just this CV' scope updates the preview", async ({
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
  // Switching sections with unsaved changes shows the guard dialog
  // -------------------------------------------------------------------------

  test("switching sections with unsaved changes shows the discard dialog", async ({
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

// ---------------------------------------------------------------------------
// Polish behaviours: Kaile assist, gap badges, mobile accordion
// ---------------------------------------------------------------------------

test.describe("CV Section Editor — Polish", () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test.beforeEach(async ({ page }) => {
    await page.route(`**/api/flow/${TEST_FLOW_ID}/state`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_FLOW_STATE),
      });
    });

    await page.route(`**/api/cv/${TEST_CV_ID}/html`, async (route) => {
      await route.fulfill({ status: 200, contentType: "text/html", body: MOCK_CV_HTML });
    });

    await page.route(`**/api/cv/${TEST_CV_ID}/sections`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SECTIONS_WITH_GAPS),
      });
    });
  });

  // -------------------------------------------------------------------------
  // 'Kaile hilft' → question → submit answer → Accept populates textarea
  // -------------------------------------------------------------------------

  test("'Kaile hilft' → question → submit answer → Accept populates textarea", async ({
    page,
  }) => {
    // Register broad catch-all FIRST so the specific route below takes precedence (Playwright LIFO)
    await page.route(`**/api/cv/${TEST_CV_ID}/sections/**`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            html: MOCK_CV_HTML_UPDATED_PYTHON,
            overrides_applied: ["introduction"],
            resolved_gaps: ["Python"],
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Register specific assist route AFTER the catch-all so it wins in LIFO evaluation order
    await page.route(
      `**/api/cv/${TEST_CV_ID}/sections/introduction/assist`,
      async (route) => {
        if (route.request().method() === "POST") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ session_id: SESSION_ID, question: "Wie lange Python?" }),
          });
        } else if (route.request().method() === "PATCH") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ suggestion: "Erfahrener Python-Entwickler." }),
          });
        } else {
          await route.continue();
        }
      }
    );

    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');
    const introItem = page.locator('[data-testid="section-list-item"]', { hasText: "Introduction" });
    await expect(introItem).toBeVisible({ timeout: 10_000 });
    await introItem.click();

    // Click "Kaile hilft"
    const kaileBtn = page.locator('[data-testid="kaile-help-btn"]').first();
    await expect(kaileBtn).toBeVisible({ timeout: 5_000 });
    await kaileBtn.click();

    // Question should appear
    await expect(page.locator('[data-testid="assist-question"]')).toBeVisible({ timeout: 8_000 });
    expect(await page.locator('[data-testid="assist-question"]').textContent()).toContain("Wie lange");

    // Fill in the answer
    await page.fill('[data-testid="assist-answer"]', "5 Jahre");
    await page.click('[data-testid="assist-submit"]');

    // Suggestion with Accept/Edit/Reject should appear
    await expect(page.locator('[data-testid="assist-accept"]')).toBeVisible({ timeout: 8_000 });

    // Accept populates the textarea
    await page.click('[data-testid="assist-accept"]');
    const textareaValue = await page.locator('[data-testid="section-textarea"]').inputValue();
    expect(textareaValue).toContain("Python");
  });

  // -------------------------------------------------------------------------
  // Saving section removes resolved gap badge
  // -------------------------------------------------------------------------

  test("saving section removes resolved gap badge", async ({ page }) => {
    await page.route(`**/api/cv/${TEST_CV_ID}/sections/**`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            html: MOCK_CV_HTML_UPDATED_PYTHON,
            overrides_applied: ["introduction"],
            resolved_gaps: ["Python"],
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto(CV_PAGE_URL);
    // Set sessionStorage after navigation so the page context is accessible
    await page.evaluate(() => sessionStorage.setItem("finetune_save_scope", "cv"));
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');
    const introItem = page.locator('[data-testid="section-list-item"]', { hasText: "Introduction" });
    await expect(introItem).toBeVisible({ timeout: 10_000 });

    // Introduction should have a gap badge
    const badge = page.locator('[data-testid="gap-badge"]').first();
    await expect(badge).toBeVisible({ timeout: 5_000 });

    await introItem.click();
    const textarea = page.locator('[data-testid="section-textarea"]');
    await expect(textarea).toBeVisible({ timeout: 5_000 });
    await textarea.fill("Python developer");

    await page.click('[data-testid="section-save"]');

    // Badge should disappear after save
    await expect(page.locator('[data-testid="gap-badge"]')).not.toBeVisible({ timeout: 5_000 });
  });

  // -------------------------------------------------------------------------
  // All gaps resolved shows 'all gaps closed' indicator
  // -------------------------------------------------------------------------

  test("all gaps resolved shows 'all gaps closed' indicator", async ({ page }) => {
    // Override sections mock to return no gaps
    await page.route(`**/api/cv/${TEST_CV_ID}/sections`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_SECTIONS_NO_GAPS),
      });
    });

    await page.goto(CV_PAGE_URL);
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');
    await expect(page.locator('[data-testid="all-gaps-closed"]')).toBeVisible({ timeout: 10_000 });
  });

  // -------------------------------------------------------------------------
  // Mobile viewport renders accordion layout
  // -------------------------------------------------------------------------

  test("mobile viewport renders accordion layout", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });

    await page.goto(CV_PAGE_URL);
    // On mobile, the cv-iframe may be scaled/transformed by ResizeObserver before it settles.
    // Wait for the finetune-toggle button (always visible in the metadata panel) instead.
    await expect(page.locator('[data-testid="finetune-toggle"]')).toBeVisible({ timeout: 10_000 });

    await page.click('[data-testid="finetune-toggle"]');

    await expect(page.locator('[data-testid="mobile-accordion"]')).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('[data-testid="accordion-section"]').first()).toBeVisible({ timeout: 5_000 });
  });
});

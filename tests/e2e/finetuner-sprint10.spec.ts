// tests/e2e/finetuner-sprint10.spec.ts
import { test, expect } from "@playwright/test";

/**
 * Sprint 10 — Finetuner E2E Tests (task 24.11)
 *
 * Covers:
 *  - 24.4/24.5: "Kaile hilft" → question → answer → suggestion → Accept
 *  - 24.3/24.6: Save section → resolved gap badge disappears
 *  - 24.6:      All gaps resolved → "all-gaps-closed" indicator visible
 *  - 24.7:      Mobile viewport → mobile-accordion renders
 *
 * All tests use page.route() mocks — no live backend required.
 */

const TEST_FLOW_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff";
const TEST_CV_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd";
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;
const SESSION_ID = "assist-session-1";

// ---------------------------------------------------------------------------
// Mock fixtures
// ---------------------------------------------------------------------------

const MOCK_FLOW_STATE = {
  job_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  job_summary: { role_title: "Software Engineer" },
  gap_summary: { match_score: 0.85 },
  cv_summary: {
    cv_id: TEST_CV_ID,
    pdf_url: `http://localhost:8001/api/cv/${TEST_CV_ID}/pdf`,
    expires_at: new Date(Date.now() + 86_400_000).toISOString(),
  },
};

const MOCK_CV_HTML = `<html><body><h1>Max Mustermann</h1><p id="intro">Erfahrener Entwickler</p></body></html>`;
const MOCK_CV_HTML_UPDATED = `<html><body><h1>Max Mustermann</h1><p id="intro">Python-Entwickler</p></body></html>`;

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
// Test setup
// ---------------------------------------------------------------------------

test.describe("Finetuner — Sprint 10", () => {
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
  // 24.4 / 24.5 — Kaile help flow: question → answer → suggestion → Accept
  // -------------------------------------------------------------------------

  test("(24.4, 24.5) 'Kaile hilft' → question → submit answer → Accept populates textarea", async ({
    page,
  }) => {
    // Register broad catch-all FIRST so the specific route below takes precedence (Playwright LIFO)
    await page.route(`**/api/cv/${TEST_CV_ID}/sections/**`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            html: MOCK_CV_HTML_UPDATED,
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
  // 24.3 / 24.6 — Save section → resolved gap badge disappears
  // -------------------------------------------------------------------------

  test("(24.3, 24.6) saving section removes resolved gap badge", async ({ page }) => {
    await page.route(`**/api/cv/${TEST_CV_ID}/sections/**`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            html: MOCK_CV_HTML_UPDATED,
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
  // 24.6 — All gaps resolved → "all-gaps-closed" indicator
  // -------------------------------------------------------------------------

  test("(24.6) all gaps resolved shows 'all gaps closed' indicator", async ({ page }) => {
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
  // 24.7 — Mobile accordion layout at 375px
  // -------------------------------------------------------------------------

  test("(24.7) mobile viewport renders accordion layout", async ({ page }) => {
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

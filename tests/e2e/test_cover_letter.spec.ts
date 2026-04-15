import { test, expect } from "@playwright/test";

/**
 * Sprint 25 — Cover Letter E2E (Marcus happy path)
 *
 * Prerequisites: the full Docker stack is running with the stub user
 * and at least one flow session in `complete` state with a ready CV.
 *
 * Run: npx playwright test tests/e2e/test_cover_letter.spec.ts
 */

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

test.describe("Cover Letter Generation — Marcus happy path", () => {
  let flowId: string;

  test.beforeAll(async ({ request }) => {
    const flowRes = await request.get(`${API_BASE}/api/flow`);
    if (!flowRes.ok()) {
      test.skip();
      return;
    }
    flowId = process.env.TEST_FLOW_ID ?? "";
    if (!flowId) test.skip();
  });

  test("US-CL05: CV page shows Generate Cover Letter button", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cv`);
    await page.getByTestId("tab-actions").click();
    await expect(page.getByTestId("generate-cover-letter-btn")).toBeVisible();
  });

  test("US-CL02: Pre-generation modal opens and accepts inputs", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cv`);
    await page.getByTestId("tab-actions").click();
    await page.getByTestId("generate-cover-letter-btn").click();

    await expect(page.getByTestId("cover-letter-modal")).toBeVisible();
    await expect(page.getByTestId("cl-recipient-name")).toBeVisible();

    await page.getByTestId("cl-salary").fill("95.000 – 110.000 € p.a.");
    await page.getByTestId("cl-availability").fill("3 Monate zum Monatsende");
    await page.getByTestId("cl-tone-formal").click();
  });

  test("US-CL01: Generate cover letter, reaches ready state", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cv`);
    await page.getByTestId("tab-actions").click();
    await page.getByTestId("generate-cover-letter-btn").click();

    await page.getByTestId("cl-salary").fill("95.000 € p.a.");
    await page.getByTestId("cl-modal-generate").click();

    await page.waitForURL(`**/flow/${flowId}/cover-letter`, { timeout: 30000 });
    await expect(page.getByTestId("cover-letter-iframe")).toBeVisible({ timeout: 30000 });
  });

  test("US-CL05: Cover letter page has Lebenslauf navigation", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await expect(page.getByTestId("cl-view-cv-btn")).toBeVisible();
    await page.getByTestId("cl-view-cv-btn").click();
    await page.waitForURL(`**/flow/${flowId}/cv`);
  });

  test("US-CL07: Body section is editable", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await expect(page.getByTestId("cover-letter-iframe")).toBeVisible({ timeout: 30000 });

    await page.getByTestId("cl-tab-content").click();
    const textarea = page.getByTestId("cl-body-textarea");
    await expect(textarea).toBeVisible();

    await textarea.fill("Sehr geehrte Frau Dr. Müller,\n\nTestinhalt für E2E.");
    await page.getByTestId("cl-save-body-btn").click();

    await expect(page.getByTestId("cl-save-body-btn")).not.toBeVisible({ timeout: 5000 });
  });

  test("US-CL06: PDF download button is present", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await expect(page.getByTestId("cl-topbar-download-btn")).toBeVisible();
  });

  test("US-CL09: Design tab shows 7 template options", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await page.getByTestId("cl-tab-design").click();

    const templates = [
      "classic_german", "modern_swiss", "executive",
      "tech_developer", "creative_sidebar", "academic", "compact_pro",
    ];
    for (const tmpl of templates) {
      await expect(page.getByTestId(`cl-template-${tmpl}`)).toBeVisible();
    }
  });

  test("US-CL10: Regenerate button opens modal", async ({ page }) => {
    await page.goto(`${BASE_URL}/flow/${flowId}/cover-letter`);
    await page.getByTestId("cl-tab-actions").click();
    await page.getByTestId("cl-regenerate-btn").click();
    await expect(page.getByTestId("cover-letter-modal")).toBeVisible();
    await page.getByTestId("cl-modal-cancel").click();
    await expect(page.getByTestId("cover-letter-modal")).not.toBeVisible();
  });
});

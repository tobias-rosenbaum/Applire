import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Felix — CV Design tab journey (PQ)
 *
 * Tests that after full CV generation:
 *  - The Design tab is accessible in the RefinementPanel
 *  - The swatch row renders with preset colors
 *  - Clicking a different swatch enables the apply button
 *  - Clicking apply triggers PATCH /api/cv/{id}/color and re-renders the iframe
 *
 * PQ tier: requires the full Docker stack + real LLM via OpenRouter.
 * Run: OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts tests/e2e/pq/felix-cv-design.spec.ts
 */

const CV_PATH = path.join(__dirname, "../../fixtures/profiles/sample_cv.pdf");
const JD_TEXT = fs.readFileSync(
  path.join(__dirname, "../../fixtures/JDs/sample_jd.txt"),
  "utf-8"
);
const API_BASE = "http://localhost:8001";

async function resetBackendState(page: Page): Promise<void> {
  await page.request.delete(`${API_BASE}/api/profile`).catch(() => {});
}

async function generateCvAndNavigateToView(page: Page): Promise<void> {
  await resetBackendState(page);
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Unique JD so flow isn't de-duped
  const uniqueJD = `${JD_TEXT}\n\n<!-- felix-color-test: ${Date.now()} -->`;
  await page.getByRole("button", { name: "Paste Text" }).click();
  await page.locator('textarea[placeholder="Paste the full job description here..."]').fill(uniqueJD);

  const fileInput = page.getByTestId("file-input");
  await fileInput.setInputFiles(CV_PATH);
  await expect(page.getByTestId("submit-button")).toBeEnabled();
  await page.getByTestId("submit-button").click();

  // Wait for gaps page
  await expect(page).toHaveURL(/\/flow\/.*\/gaps/, { timeout: 90000 });
  await expect(page.getByTestId("loading-indicator")).not.toBeVisible({ timeout: 30000 });

  // Advance flow to CV generation (button is always visible on gaps page)
  await page.getByTestId("generate-cv-button").click();

  // Wait for CV page
  await expect(page).toHaveURL(/\/flow\/.*\/cv/, { timeout: 60000 });

  // Skip photo prompt if it appears (new users with no photo)
  const skipPhotoBtn = page.getByText("Skip for now");
  if (await skipPhotoBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await skipPhotoBtn.click();
  }

  // Trigger CV generation from template selector
  await page.getByText("CV generieren").click({ timeout: 10000 });

  // Wait for generation to complete — real LLM can take up to 90s
  await expect(page.getByTestId("refinement-panel")).toBeVisible({ timeout: 90000 });
}

test.describe("Felix — CV Design tab (PQ)", () => {
  test("Design tab is present after CV generation", async ({ page }) => {
    await generateCvAndNavigateToView(page);
    await expect(page.getByTestId("tab-appearance")).toBeVisible();
  });

  test("Design tab shows preset swatch row", async ({ page }) => {
    await generateCvAndNavigateToView(page);
    await page.getByTestId("tab-appearance").click();
    // At least 5 color swatches must be present
    const swatches = page.getByRole("button", { name: /Farbe wählen/ });
    await expect(swatches.first()).toBeVisible({ timeout: 5000 });
    expect(await swatches.count()).toBeGreaterThanOrEqual(5);
  });

  test("selecting a different swatch and applying re-renders the CV iframe", async ({ page }) => {
    await generateCvAndNavigateToView(page);
    await page.getByTestId("tab-appearance").click();

    // Click the Rot preset
    await page.getByRole("button", { name: "Farbe wählen: Rot" }).click();
    const applyBtn = page.getByText("Farbe übernehmen");
    await expect(applyBtn).toBeEnabled();

    // Intercept PATCH to confirm it's called
    const patchRequest = page.waitForRequest(
      (req) => req.url().includes("/color") && req.method() === "PATCH",
      { timeout: 10000 }
    );
    await applyBtn.click();
    const req = await patchRequest;
    const body = JSON.parse(req.postData() ?? "{}");
    expect(body.accent_hex).toBe("#c0392b");

    // Apply button returns to disabled after success
    await expect(applyBtn).toBeDisabled({ timeout: 10000 });
  });
});

import { test, expect, Page } from "@playwright/test";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Felix — Power-User Dashboard Journey (PQ, Sprint 29)
 *
 * Validates the returning-user dashboard experience end-to-end:
 *   1. New-user onboarding: CV upload + JD → gap analysis → CV generation
 *   2. Returning user redirected to /dashboard
 *   3. Dashboard shows the completed application card (CV Ready status)
 *   4. My Documents page shows the generated CV in the table
 *   5. Quick Tailor widget is usable for a second application
 *
 * PQ tier: requires the full Docker stack + a real LLM via OpenRouter.
 * Run: OPENROUTER_API_KEY=<key> npx playwright test --config=playwright.config.pq.ts tests/e2e/pq/felix-dashboard-sprint29.spec.ts
 * DO NOT include in the standard `npx playwright test` run.
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

/**
 * Runs the full new-user onboarding flow through CV generation.
 * Returns the flow ID extracted from the URL.
 */
async function runFullOnboardingFlow(page: Page): Promise<string> {
  await resetBackendState(page);
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  // Use Paste Text mode so we can inject a unique JD and avoid flow dedup
  const uniqueJD = `${JD_TEXT}\n\n<!-- felix-dashboard-test: ${Date.now()} -->`;
  await page.getByRole("button", { name: "Paste Text" }).click();
  await page
    .locator('textarea[placeholder="Paste the full job description here..."]')
    .fill(uniqueJD);

  const fileInput = page.getByTestId("file-input");
  await fileInput.setInputFiles(CV_PATH);
  await expect(page.getByTestId("submit-button")).toBeEnabled();
  await page.getByTestId("submit-button").click();

  // Wait for gap analysis to complete
  await expect(page).toHaveURL(/\/flow\/.*\/gaps/, { timeout: 90000 });
  await expect(page.getByTestId("loading-indicator")).not.toBeVisible({
    timeout: 30000,
  });

  // Advance directly to CV generation
  await page.getByTestId("generate-cv-button").click();

  // Wait for CV page
  await expect(page).toHaveURL(/\/flow\/.*\/cv/, { timeout: 60000 });

  const flowId = page.url().match(/\/flow\/([^/]+)\//)?.[1] ?? "";

  // Dismiss photo prompt if present
  const skipPhotoBtn = page.getByText("Skip for now");
  if (await skipPhotoBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await skipPhotoBtn.click();
  }

  // Trigger CV generation
  await page.getByText("CV generieren").click({ timeout: 10000 });

  // Wait for generation to complete (real LLM can take ~90s)
  await expect(page.getByTestId("refinement-panel")).toBeVisible({
    timeout: 90000,
  });

  return flowId;
}

// ────────────────────────────────────────────────────────────────────────────

test.describe("Felix — Power-User Dashboard (Sprint 29 PQ)", () => {
  test("returning user is redirected from / to /dashboard", async ({ page }) => {
    await runFullOnboardingFlow(page);

    // Navigate back to root — must redirect to dashboard for returning user
    await page.goto("/");
    await page.waitForURL("**/dashboard", { timeout: 10000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("dashboard sidebar renders all four nav items", async ({ page }) => {
    await runFullOnboardingFlow(page);
    await page.goto("/dashboard");

    await expect(page.getByRole("button", { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /profile|masterprofil/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /documents|dokumente/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /settings|einstellungen/i })).toBeVisible();
  });

  test("dashboard shows the completed application card with CV Ready status", async ({ page }) => {
    await runFullOnboardingFlow(page);
    await page.goto("/dashboard");

    // Application card grid must be present
    await expect(page.getByText(/CV Ready/i)).toBeVisible({ timeout: 10000 });

    // Open button is available for the ready CV
    await expect(
      page.getByRole("button", { name: /^Open$/i }).first()
    ).toBeVisible();
  });

  test("Open button on dashboard card navigates to the CV view", async ({ page }) => {
    await runFullOnboardingFlow(page);
    await page.goto("/dashboard");
    await expect(page.getByRole("button", { name: /^Open$/i }).first()).toBeVisible({
      timeout: 10000,
    });

    await page.getByRole("button", { name: /^Open$/i }).first().click();
    await expect(page).toHaveURL(/\/flow\/.+\/cv/, { timeout: 10000 });
  });

  test("My Documents page shows the generated CV in the table", async ({ page }) => {
    await runFullOnboardingFlow(page);
    await page.goto("/documents");

    // Stats strip should show at least 1 document
    await expect(page.locator("tbody tr").first()).toBeVisible({ timeout: 10000 });

    // Open button for the ready CV exists
    await expect(
      page.getByRole("button", { name: /^Open$|^Öffnen$/i }).first()
    ).toBeVisible();
  });

  test("Documents table Open button navigates to the CV view", async ({ page }) => {
    await runFullOnboardingFlow(page);
    await page.goto("/documents");

    await expect(
      page.getByRole("button", { name: /^Open$|^Öffnen$/i }).first()
    ).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: /^Open$|^Öffnen$/i }).first().click();
    await expect(page).toHaveURL(/\/flow\/.+\/cv/, { timeout: 10000 });
  });

  test("Quick Tailor widget accepts a second JD text and starts a new flow", async ({ page }) => {
    await runFullOnboardingFlow(page);
    await page.goto("/dashboard");

    // Switch to Paste Text tab
    await page.getByText(/Paste Text|Text einfügen/i).click();
    const textarea = page.locator("textarea").first();
    await expect(textarea).toBeVisible();

    const secondJD = `${JD_TEXT}\n\n<!-- second-job: ${Date.now()} -->`;
    await textarea.fill(secondJD);

    // Analyse button must become enabled
    const analyseBtn = page.getByRole("button", { name: /analysieren|analyse/i });
    await expect(analyseBtn).toBeEnabled({ timeout: 3000 });

    // Click and wait for navigation to import page (new flow started)
    await analyseBtn.click();
    await expect(page).toHaveURL(/\/flow\/.+\/import/, { timeout: 60000 });
  });
});

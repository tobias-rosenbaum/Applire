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

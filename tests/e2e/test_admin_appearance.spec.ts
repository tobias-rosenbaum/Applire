import { test, expect } from "@playwright/test";

test.describe("Admin appearance page", () => {
  test("loads the appearance page with scheme editor and preview", async ({ page }) => {
    await page.goto("/admin/appearance");
    // Header
    await expect(page.getByRole("heading", { name: "Appearance" })).toBeVisible();
    // Left panel sections
    await expect(page.getByText("Saved Schemes")).toBeVisible();
    await expect(page.getByText("Seed Colors")).toBeVisible();
    await expect(page.getByText("Surface Tint")).toBeVisible();
    await expect(page.getByText("Save Scheme")).toBeVisible();
    // Right panel
    await expect(page.getByText("Live Preview")).toBeVisible();
    // EU Blue scheme should be loaded in the preset picker
    await expect(page.getByText("EU Blue")).toBeVisible();
  });

  test("settings page footer has Admin link", async ({ page }) => {
    await page.goto("/settings");
    const adminLink = page.getByRole("link", { name: "Admin" });
    await expect(adminLink).toBeVisible();
    await adminLink.click();
    await expect(page).toHaveURL(/\/admin\/appearance/);
  });

  test("ThemeProvider injects CSS custom properties on app load", async ({ page }) => {
    await page.goto("/");
    const primaryColor = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim()
    );
    // Should be set (non-empty) — exact value depends on active scheme
    expect(primaryColor).toBeTruthy();
    expect(primaryColor).toMatch(/^#[0-9a-f]{6}$/i);
  });
});

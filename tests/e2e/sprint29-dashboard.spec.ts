import { test, expect } from "@playwright/test";

test.describe("Sprint 29 — Power User Dashboard", () => {

  test("returning user is redirected to /dashboard", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/dashboard", { timeout: 8000 });
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("sidebar renders with all four nav items", async ({ page }) => {
    await page.goto("/dashboard");
    const sidebar = page.locator("aside");
    await expect(sidebar.getByRole("button", { name: /Dashboard/i })).toBeVisible();
    await expect(sidebar.getByRole("button", { name: /Profile|Profil|Masterprofil/i })).toBeVisible();
    await expect(sidebar.getByRole("button", { name: /Documents|Dokumente/i })).toBeVisible();
    await expect(sidebar.getByRole("button", { name: /Settings|Einstellungen/i })).toBeVisible();
  });

  test("Quick Tailor widget has URL and Text tabs", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText(/Quick Tailor/i)).toBeVisible();
    await expect(page.getByText(/Job URL|Job-URL/i)).toBeVisible();
    await expect(page.getByText(/Paste Text|Text einfügen/i)).toBeVisible();
  });

  test("Quick Tailor text tab shows textarea", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=/Paste Text|Text einfügen/");
    await expect(page.locator("textarea")).toBeVisible();
  });

  test("sidebar active item highlights on navigation", async ({ page }) => {
    await page.goto("/dashboard");
    await page.click("text=/Documents|Meine Dokumente/");
    await page.waitForURL("**/documents");
    const docsBtn = page.getByRole("button", { name: /Documents|Meine Dokumente/i });
    // Active nav item has a distinct right-border rail indicator using the theme primary token
    await expect(docsBtn).toHaveClass(/border-primary/);
  });

  test("My Documents page loads with stats strip and table", async ({ page }) => {
    await page.goto("/documents");
    await expect(page.getByText(/Total documents|Dokumente gesamt/i)).toBeVisible();
    await expect(page.getByText(/Expiring|Ablaufend/i)).toBeVisible();
    await expect(page.getByText(/Document|Dokument/i).first()).toBeVisible();
  });

  test("My Documents text filter hides non-matching rows", async ({ page }) => {
    await page.goto("/documents");
    const rows = page.locator("tbody tr");
    const count = await rows.count();
    if (count < 2) {
      test.skip();
      return;
    }
    const searchInput = page.getByPlaceholder(/Filter by role|Nach Stelle/i);
    await searchInput.fill("XXXXXXXXXNOTFOUND");
    await expect(page.getByText(/No documents|Noch keine/i)).toBeVisible();
  });

  test("Open button on a ready document navigates to flow CV page", async ({ page }) => {
    await page.goto("/documents");
    const openBtn = page.getByRole("button", { name: /^Open$|^Öffnen$/i }).first();
    if (await openBtn.isVisible()) {
      await openBtn.click();
      await expect(page).toHaveURL(/\/flow\/.+\/cv/);
    }
  });

});

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
 *  - Error state renders when advance API fails
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

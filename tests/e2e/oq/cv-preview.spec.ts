// tests/e2e/cv-preview.spec.ts
import { test, expect } from '@playwright/test';

const TEST_FLOW_ID = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee';
const TEST_CV_ID = 'cccccccc-cccc-cccc-cccc-cccccccccccc';
const TEST_JOB_ID = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
const CV_PAGE_URL = `/flow/${TEST_FLOW_ID}/cv`;

const MOCK_FLOW_STATE = {
  job_id: TEST_JOB_ID,
  job_summary: { role_title: 'Senior Software Engineer' },
  gap_summary: { match_score: 0.87 },
  cv_summary: {
    cv_id: TEST_CV_ID,
    pdf_url: `http://localhost:8001/api/cv/${TEST_CV_ID}/pdf`,
    expires_at: new Date(Date.now() + 86400000).toISOString(),
  },
};

const MOCK_CV_HTML = `<html><body>
  <h1>Max Mustermann</h1>
  <p>Senior Software Engineer</p>
</body></html>`;

test.describe('CV Preview — srcDoc rendering', () => {
  test.beforeEach(async ({ page }) => {
    // Mock flow state so the page skips to preview phase immediately
    await page.route(`**/api/flow/${TEST_FLOW_ID}/state`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_FLOW_STATE),
      });
    });

    // Mock the CV HTML endpoint
    await page.route(`**/api/cv/${TEST_CV_ID}/html`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: MOCK_CV_HTML,
      });
    });
  });

  test('iframe is present with non-empty srcdoc attribute', async ({ page }) => {
    const cspErrors: string[] = [];
    page.on('console', (msg) => {
      if (
        msg.type() === 'error' &&
        (msg.text().includes('Content-Security-Policy') ||
          msg.text().includes('frame-ancestors') ||
          msg.text().includes('X-Frame-Options'))
      ) {
        cspErrors.push(msg.text());
      }
    });

    await page.goto(CV_PAGE_URL);

    // Wait for iframe to appear
    const iframe = page.locator('[data-testid="cv-iframe"]');
    await expect(iframe).toBeVisible({ timeout: 10000 });

    // srcdoc attribute must be non-empty
    const srcdoc = await iframe.getAttribute('srcdoc');
    expect(srcdoc).toBeTruthy();
    expect(srcdoc!.length).toBeGreaterThan(0);

    // sandbox attribute must be present
    const sandbox = await iframe.getAttribute('sandbox');
    expect(sandbox).toBe('allow-same-origin');

    // No CSP or frame-blocking console errors
    expect(cspErrors).toHaveLength(0);
  });

  test('iframe renders visible text content from CV HTML', async ({ page }) => {
    await page.goto(CV_PAGE_URL);

    const iframe = page.locator('[data-testid="cv-iframe"]');
    await expect(iframe).toBeVisible({ timeout: 10000 });

    // Access the iframe's content frame
    const frame = page.frameLocator('[data-testid="cv-iframe"]');
    await expect(frame.locator('h1')).toHaveText('Max Mustermann', { timeout: 5000 });
  });

  test('download button triggers PDF fetch', async ({ page }) => {
    // Mock the PDF endpoint
    let pdfFetched = false;
    await page.route(`**/api/cv/${TEST_CV_ID}/pdf`, async (route) => {
      pdfFetched = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        headers: {
          'Content-Disposition': `attachment; filename="lebenslauf-test.pdf"`,
        },
        body: Buffer.from('%PDF-1.4 mock content'),
      });
    });

    await page.goto(CV_PAGE_URL);

    // Wait for preview to be ready
    await expect(page.locator('[data-testid="cv-iframe"]')).toBeVisible({
      timeout: 10000,
    });

    // Click download — use waitForEvent to capture the download
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="download-button"]'),
    ]);

    expect(download).toBeTruthy();
    expect(pdfFetched).toBe(true);
  });
});

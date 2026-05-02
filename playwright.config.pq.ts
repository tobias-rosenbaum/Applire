import { defineConfig, devices } from '@playwright/test';

/**
 * PQ (Performance Qualification) Playwright config.
 * Runs only tests/e2e/pq/ using a real LLM via OpenRouter.
 * Never run automatically in CI — trigger via GitHub Actions workflow_dispatch.
 *
 * Requires: OPENROUTER_API_KEY environment variable
 * Requires: Full Docker stack running (docker compose up -d)
 */
export default defineConfig({
  testDir: './tests/e2e/pq',
  fullyParallel: false,
  workers: 1,
  timeout: 120 * 1000,
  expect: { timeout: 15 * 1000 },
  reporter: [['html'], ['github']],
  use: {
    baseURL: 'http://localhost',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15 * 1000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  retries: 1,
  outputDir: '/tmp/test-results-pq',
});

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Apliqa E2E Tests
 * 
 * This config is designed to work in both local development and CI/CD (GitHub Actions) environments.
 * Key settings:
 * - Base URL: http://localhost:3000 (backend running locally or in Docker)
 * - Test directory: ./tests/e2e/
 * - Timeout: 60 seconds per test (accommodates LLM processing in backend)
 * - Screenshots/Videos: Retained only on failure for faster feedback
 * - Retries: 2 on CI (GitHub Actions), 0 locally for faster iteration
 */

export default defineConfig({
  testDir: './tests/e2e',
  
  /**
   * Test execution settings
   */
  fullyParallel: false,
  workers: 1, // Run tests serially to avoid race conditions with shared backend state
  timeout: 60 * 1000, // 60 seconds per test (includes LLM processing)
  expect: {
    timeout: 10 * 1000, // 10 seconds for assertions
  },

  /**
   * Reporter configuration
   * - 'html': Generates detailed HTML report
   * - 'github': GitHub Actions reporter (only active in CI)
   */
  reporter: [
    ['html'],
    ...(process.env.CI ? [['github']] : []), // Add GitHub reporter only in CI
  ],

  /**
   * Shared settings for all projects
   */
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry', // Capture trace only when a test is retried
    screenshot: 'only-on-failure', // Capture screenshots only on failure
    video: 'retain-on-failure', // Record video only on failure
    actionTimeout: 10 * 1000, // 10 seconds for user actions (click, type, etc.)
  },

  /**
   * Test projects
   * Currently using Chromium only. Can be extended to include Firefox, WebKit later.
   */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Uncomment to add Firefox and WebKit testing in the future
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  /**
   * Web Server Configuration (for local development)
   * Commented out because in local development, the user builds/runs docker-compose manually.
   * In CI/CD, the workflow starts the Docker container via docker-compose.
   * 
   * Uncomment and adjust if you want Playwright to manage the server lifecycle:
   */
  // webServer: {
  //   command: 'docker-compose up',
  //   port: 3000,
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000, // 2 minutes to start
  // },

  /**
   * Global configuration for retries
   * - CI environment (GitHub Actions): 2 retries
   * - Local development: 0 retries (faster feedback)
   */
  retries: process.env.CI ? 2 : 0,

  /**
   * Global configuration for parallel execution
   * Set to 1 worker because tests share backend state (same user/flow context)
   * Running in parallel could cause race conditions.
   */

  /**
   * Output directories
   */
  outputDir: './test-results', // Test artifacts (videos, screenshots, traces)
});

/**
 * Usage:
 *
 * Local Development:
 *   npm install
 *   npx playwright install
 *   docker-compose up -d (from Solution/)
 *   npx playwright test
 *   npx playwright test --ui (interactive mode)
 *   npx playwright test --debug (debug mode)
 *
 * GitHub Actions CI/CD:
 *   - Configured in .github/workflows/test.yml
 *   - Automatically installs dependencies and runs tests
 *   - Reports results to GitHub PR checks
 *
 * Debugging:
 *   npx playwright codegen http://localhost:3000 (record new test)
 *   npx playwright test --headed (run with browser visible)
 *   npx playwright test --debug (step through test)
 */

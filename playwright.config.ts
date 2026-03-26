import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables from the stack.
 * Defaults:
 * - frontend: http://localhost:3000
 * - backend: http://localhost:8000
 */
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Run tests in parallel
  fullyParallel: true,
  
  // Fail build on CI if you accidentally left test.only in source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFolder: 'playwright-report', file: 'results.json' }],
    ['list']
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL for frontend
    baseURL: FRONTEND_URL,
    
    // Collect trace on failure
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Default timeout for each action
    actionTimeout: 10000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Firefox and WebKit can be enabled later
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Run local dev server before tests
  // This assumes frontend is already running or started separately
  // webServer: {
  //   command: 'npm run dev',
  //   url: FRONTEND_URL,
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120000,
  // },
});

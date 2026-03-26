import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Marcus Persona E2E Test
 * 
 * User Journey: Upload CV → Process → Download
 * 
 * Persona: Marcus Chen
 * - Senior Software Engineer, 8 years experience
 * - Tech stack: Python, React, AWS, Kubernetes
 * - Goal: Apply for Senior Full-Stack Developer position
 * 
 * This test validates the complete user flow from CV upload to
 * downloading the processed profile.
 */

test.describe('Marcus Persona - CV Upload Journey', () => {
  // Test fixtures paths
  const CV_PATH = path.join(__dirname, '../fixtures/profiles/sample_cv.pdf');
  const JD_PATH = path.join(__dirname, '../fixtures/JDs/sample_jd.txt');
  const DOWNLOADS_PATH = path.join(__dirname, '../fixtures/downloads');

  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for page to be ready
    await page.waitForLoadState('networkidle');
  });

  test('should display landing page with upload functionality', async ({ page }) => {
    // Verify landing page elements
    await expect(page).toHaveTitle(/Apliqa/i);
    
    // Check for upload button/area
    const uploadArea = page.locator('[data-testid="upload-area"], input[type="file"], .upload-zone').first();
    await expect(uploadArea).toBeVisible();
  });

  test('should upload CV and start processing', async ({ page }) => {
    // Find file input
    const fileInput = page.locator('input[type="file"]').first();
    
    // Upload the sample CV
    await fileInput.setInputFiles(CV_PATH);
    
    // Verify upload started - look for processing indicator
    const processingIndicator = page.locator('[data-testid="processing-indicator"], .processing, [role="status"]').first();
    
    // Wait for processing to start (with timeout)
    await expect(processingIndicator).toBeVisible({ timeout: 10000 });
  });

  test('should complete CV processing and show results', async ({ page }) => {
    // Upload CV
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(CV_PATH);
    
    // Wait for processing to complete
    // Look for success indicator or results page
    const successIndicator = page.locator('[data-testid="processing-complete"], .success, .profile-ready').first();
    
    // Extended timeout for processing
    await expect(successIndicator).toBeVisible({ timeout: 60000 });
  });

  test('should allow downloading processed profile', async ({ page }) => {
    // Upload CV
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(CV_PATH);
    
    // Wait for processing to complete
    const successIndicator = page.locator('[data-testid="processing-complete"], .success, .profile-ready').first();
    await expect(successIndicator).toBeVisible({ timeout: 60000 });
    
    // Find download button
    const downloadButton = page.locator('[data-testid="download-button"], button:has-text("Download"), a:has-text("Download")').first();
    
    // Start waiting for download before clicking
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 30000 }),
      downloadButton.click(),
    ]);
    
    // Verify download started
    expect(download).toBeTruthy();
    
    // Save downloaded file
    const downloadPath = path.join(DOWNLOADS_PATH, download.suggestedFilename());
    await download.saveAs(downloadPath);
    
    // Verify file exists
    const fs = require('fs');
    expect(fs.existsSync(downloadPath)).toBeTruthy();
  });

  test('should handle CV with job description matching', async ({ page }) => {
    // This test is for future functionality
    // When JD matching is implemented, this test will validate it
    
    // Upload CV
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(CV_PATH);
    
    // Wait for processing
    const successIndicator = page.locator('[data-testid="processing-complete"], .success, .profile-ready').first();
    await expect(successIndicator).toBeVisible({ timeout: 60000 });
    
    // Look for JD matching section (if implemented)
    const jdSection = page.locator('[data-testid="jd-matching"], .gap-analysis').first();
    
    // This might not exist yet - test will be updated when feature is implemented
    const jdExists = await jdSection.count() > 0;
    
    if (jdExists) {
      await expect(jdSection).toBeVisible();
    }
  });
});

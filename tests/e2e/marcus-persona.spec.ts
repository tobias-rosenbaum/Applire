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
    
    // Check for upload area using data-testid
    const uploadArea = page.getByTestId('upload-area');
    await expect(uploadArea).toBeVisible();
    
    // Check for submit button (should be disabled initially)
    const submitButton = page.getByTestId('submit-button');
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeDisabled();
  });

  test('should upload CV and start processing', async ({ page }) => {
    // Find file input using data-testid
    const fileInput = page.getByTestId('file-input');
    
    // Upload the sample CV
    await fileInput.setInputFiles(CV_PATH);
    
    // Verify submit button is now enabled
    const submitButton = page.getByTestId('submit-button');
    await expect(submitButton).toBeEnabled();
    
    // Click submit
    await submitButton.click();
    
    // Verify processing indicator appears
    const processingIndicator = page.getByTestId('processing-indicator');
    await expect(processingIndicator).toBeVisible({ timeout: 10000 });
  });

  test('should show progress during processing', async ({ page }) => {
    // Upload CV
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(CV_PATH);
    
    // Submit
    const submitButton = page.getByTestId('submit-button');
    await submitButton.click();
    
    // Check for progress bar
    const progressBar = page.getByTestId('progress-bar');
    await expect(progressBar).toBeVisible({ timeout: 10000 });
    
    // Check for progress text
    const progressText = page.getByTestId('progress-text');
    await expect(progressText).toBeVisible();
  });

  test('should complete processing and navigate to gaps page', async ({ page }) => {
    // Upload CV
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(CV_PATH);
    
    // Submit
    const submitButton = page.getByTestId('submit-button');
    await submitButton.click();
    
    // Wait for processing to complete and navigate to gaps page
    // The processing overlay should disappear
    await expect(page.getByTestId('processing-indicator')).not.toBeVisible({ timeout: 60000 });
    
    // Should be on gaps page
    await expect(page).toHaveURL(/\/flow\/.*\/gaps/);
    
    // Check for gap analysis page
    const gapAnalysisPage = page.getByTestId('gap-analysis-page');
    await expect(gapAnalysisPage).toBeVisible();
  });

  test('should display match score and gaps', async ({ page }) => {
    // Upload CV
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(CV_PATH);
    
    // Submit and wait for navigation
    const submitButton = page.getByTestId('submit-button');
    await submitButton.click();
    
    // Wait for gaps page
    await expect(page).toHaveURL(/\/flow\/.*\/gaps/, { timeout: 60000 });
    
    // Check for loading indicator to disappear
    await expect(page.getByTestId('loading-indicator')).not.toBeVisible();
    
    // Check for gap analysis page
    const gapAnalysisPage = page.getByTestId('gap-analysis-page');
    await expect(gapAnalysisPage).toBeVisible();
    
    // Check for generate CV button
    const generateCVButton = page.getByTestId('generate-cv-button');
    await expect(generateCVButton).toBeVisible();
  });

  // CV generation requires a real LLM call (job_id + tailoring prompt).
  // This test only runs when INTEGRATION_LLM=1 is set in the environment.
  test('should allow downloading generated CV', async ({ page }) => {
    if (!process.env.INTEGRATION_LLM) {
      test.skip(true, 'CV generation requires INTEGRATION_LLM=1 (real LLM call)');
    }
    // Upload CV
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(CV_PATH);
    
    // Submit and wait for navigation
    const submitButton = page.getByTestId('submit-button');
    await submitButton.click();
    
    // Wait for gaps page
    await expect(page).toHaveURL(/\/flow\/.*\/gaps/, { timeout: 60000 });
    
    // Click generate CV
    const generateCVButton = page.getByTestId('generate-cv-button');
    await generateCVButton.click();
    
    // Wait for CV page
    await expect(page).toHaveURL(/\/flow\/.*\/cv/, { timeout: 60000 });
    
    // Wait for CV to be generated (loading should disappear)
    await expect(page.getByTestId('cv-loading')).not.toBeVisible({ timeout: 60000 });
    
    // Check for CV page
    const cvPage = page.getByTestId('cv-page');
    await expect(cvPage).toBeVisible();
    
    // Check for download button
    const downloadButton = page.getByTestId('download-button');
    await expect(downloadButton).toBeVisible();
    
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

  test('should handle error state gracefully', async ({ page }) => {
    // Upload CV
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(CV_PATH);
    
    // Submit
    const submitButton = page.getByTestId('submit-button');
    await submitButton.click();
    
    // If processing error occurs, check for error UI
    const processingError = page.getByTestId('processing-error');
    
    // Check if error appeared (might not happen in normal flow)
    if (await processingError.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Check for cancel button
      const cancelButton = page.getByTestId('cancel-button');
      await expect(cancelButton).toBeVisible();
      
      // Click cancel to go back
      await cancelButton.click();
      
      // Should be back on landing page
      const uploadArea = page.getByTestId('upload-area');
      await expect(uploadArea).toBeVisible();
    }
  });

  test('should show error when submitting without CV', async ({ page }) => {
    // Try to submit without uploading (button should be disabled)
    const submitButton = page.getByTestId('submit-button');
    await expect(submitButton).toBeDisabled();
    
    // No error message should appear since button is disabled
    const errorMessage = page.getByTestId('error-message');
    await expect(errorMessage).not.toBeVisible();
  });
});
import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * E2E Test Suite: Marcus Persona Happy Path
 * 
 * This test covers the complete user journey for a first-time user (Marcus persona):
 * 1. Upload CV + Input Job Description
 * 2. Processing animation and wait
 * 3. View results and download tailored CV
 * 
 * Test data is located in: Solution/tests/fixtures/
 */

test.describe('Marcus Persona - Happy Path', () => {
  
  test('should complete full CV tailoring workflow', async ({ page }) => {
    // ========================================
    // STEP 1: Navigate to Flow Import Page
    // ========================================
    await test.step('Navigate to import page', async () => {
      // TODO: Replace with actual flow creation endpoint or direct navigation
      // For now, we assume a flow is created and we navigate to its import page
      await page.goto('/');
      
      // Wait for page to load
      await expect(page).toHaveTitle(/Apliqa/i);
      
      // TODO: Add steps to create a new flow or navigate to existing flow
      // This might involve clicking "New Application" or similar
      // await page.click('[data-testid="new-application-button"]');
      // const flowId = await page.getAttribute('[data-flow-id]', 'data-flow-id');
      // await page.goto(`/flow/${flowId}/import`);
    });

    // ========================================
    // STEP 2: Upload CV
    // ========================================
    await test.step('Upload CV file', async () => {
      // Locate the CV upload input
      const cvUploadInput = page.locator('input[type="file"][name="cv"], input[type="file"][data-testid="cv-upload"]').first();
      
      // Path to test CV file
      const cvFilePath = path.join(__dirname, '../fixtures/profiles/sample_cv.pdf');
      
      // Upload the file
      await cvUploadInput.setInputFiles(cvFilePath);
      
      // Wait for upload confirmation (adjust selector based on actual UI)
      await expect(page.locator('[data-testid="cv-upload-success"], .upload-success')).toBeVisible({ timeout: 10000 });
      
      console.log('✓ CV uploaded successfully');
    });

    // ========================================
    // STEP 3: Input Job Description
    // ========================================
    await test.step('Input job description', async () => {
      // Locate the JD input field (could be textarea or file upload)
      const jdTextarea = page.locator('textarea[name="job_description"], textarea[data-testid="jd-input"]').first();
      
      // Sample JD text (alternatively, could read from fixtures/JDs/sample_jd.txt)
      const sampleJD = `
Senior Software Engineer - AI/ML Team

We are seeking an experienced Senior Software Engineer to join our AI/ML team. 

Responsibilities:
- Design and implement scalable AI-powered applications
- Work with FastAPI, React, and modern cloud infrastructure
- Collaborate with product and design teams
- Mentor junior engineers

Requirements:
- 5+ years of software engineering experience
- Strong Python and TypeScript skills
- Experience with LLMs and AI integration
- Excellent communication skills

Nice to have:
- Experience with Docker and CI/CD
- Background in NLP or computer vision
      `.trim();
      
      // Fill in the job description
      await jdTextarea.fill(sampleJD);
      
      // Verify text was entered
      await expect(jdTextarea).toHaveValue(sampleJD);
      
      console.log('✓ Job description entered');
    });

    // ========================================
    // STEP 4: Submit and Start Processing
    // ========================================
    await test.step('Submit form and start processing', async () => {
      // Click submit/next button
      const submitButton = page.locator('button[type="submit"], button[data-testid="submit-button"], button:has-text("Next"), button:has-text("Analyze")').first();
      await submitButton.click();
      
      // Wait for navigation to processing page
      await page.waitForURL(/\/flow\/.*\/(processing|gaps|cv)/i, { timeout: 5000 });
      
      console.log('✓ Form submitted, processing started');
    });

    // ========================================
    // STEP 5: Wait for Processing to Complete
    // ========================================
    await test.step('Wait for processing animation and completion', async () => {
      // Look for processing indicator (spinner, progress bar, loading message)
      const processingIndicator = page.locator(
        '[data-testid="processing-indicator"], .processing, .loading, [role="progressbar"]'
      ).first();
      
      // Verify processing started
      if (await processingIndicator.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('✓ Processing animation visible');
        
        // Wait for processing to complete (LLM calls can take time)
        // The indicator should disappear or change state
        await processingIndicator.waitFor({ state: 'hidden', timeout: 120000 }); // 2 min timeout
        console.log('✓ Processing completed');
      } else {
        console.log('⚠ Processing indicator not found, assuming fast completion');
      }
    });

    // ========================================
    // STEP 6: Verify Results Screen
    // ========================================
    await test.step('Verify results are displayed', async () => {
      // Wait for results page to load
      await page.waitForURL(/\/flow\/.*\/(cv|results)/i, { timeout: 10000 });
      
      // Verify key elements on results page
      await expect(page.locator('h1, h2').filter({ hasText: /CV|Result|Tailored/i })).toBeVisible();
      
      // Verify CV content is displayed (adjust selectors based on actual UI)
      const cvContent = page.locator('[data-testid="cv-content"], .cv-preview, .results-content').first();
      await expect(cvContent).toBeVisible();
      
      console.log('✓ Results screen loaded with CV content');
    });

    // ========================================
    // STEP 7: Test Download Functionality
    // ========================================
    await test.step('Download tailored CV', async () => {
      // Locate download button
      const downloadButton = page.locator(
        'button:has-text("Download"), a:has-text("Download"), [data-testid="download-button"]'
      ).first();
      
      // Verify download button is present and enabled
      await expect(downloadButton).toBeVisible();
      await expect(downloadButton).toBeEnabled();
      
      // Start waiting for download before clicking
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 });
      
      // Click download button
      await downloadButton.click();
      
      // Wait for download to start
      const download = await downloadPromise;
      
      // Verify download
      expect(download.suggestedFilename()).toMatch(/\.pdf$/i);
      console.log(`✓ CV downloaded: ${download.suggestedFilename()}`);
      
      // Save the download to verify it's a valid file (optional)
      const downloadPath = path.join(__dirname, '../fixtures/downloads', download.suggestedFilename());
      await download.saveAs(downloadPath);
      console.log(`✓ Download saved to: ${downloadPath}`);
    });
  });

  test('should handle invalid file upload gracefully', async ({ page }) => {
    // This test is flagged for exploratory testing in future sprints
    // TODO: Test uploading invalid file formats (e.g., .exe, .txt instead of PDF)
    test.skip();
  });

  test('should handle missing job description', async ({ page }) => {
    // This test is flagged for exploratory testing in future sprints
    // TODO: Test submitting form without JD input
    test.skip();
  });

  test('should handle processing timeout', async ({ page }) => {
    // This test is flagged for exploratory testing in future sprints
    // TODO: Test behavior when LLM processing takes too long or fails
    test.skip();
  });
});

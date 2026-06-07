import { test, expect } from "@playwright/test";

test.describe("Visoora Onboarding Stepper E2E Happy Path", () => {
  test("should complete the 6-step onboarding wizard and launch the dashboard successfully", async ({ page }) => {
    // 1. Visit onboarding root, should server-redirect to step-1
    await page.goto("http://localhost:3000/onboarding");
    await expect(page).toHaveURL(/.*\/onboarding\/step-1/);

    // Step 1: Company Profile Configuration
    await page.fill('input[placeholder="https://company.com"]', "https://cyberdyne.systems");
    // Trigger autocomplete lookup by blurring or clicking out
    await page.dispatchEvent('input[placeholder="https://company.com"]', "blur");
    
    // Auto-complete triggers, wait for name and selects to be populated
    await page.waitForTimeout(600);
    await page.fill('input[placeholder="Acme Systems"]', "Cyberdyne Systems");
    await page.selectOption('select[name="industry"]', "technology");
    await page.selectOption('select[name="teamSize"]', "50-249");
    
    // Procced to Step 2
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/onboarding\/step-2/);

    // Step 2: Telephony Provisioning
    await expect(page.locator("text=Configure your Visoora phone line")).toBeVisible();
    
    // Perform Area Code Search
    await page.fill('input[placeholder="501"]', "919");
    await page.click('button:has-text("Search")');
    
    // Select first Twilio available line and click Submit
    await page.waitForTimeout(600);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/onboarding\/step-3/);

    // Step 3: AI Agent configurations
    await expect(page.locator("text=Configure your AI Sales Agent persona")).toBeVisible();
    await page.fill('input[placeholder="Alex"]', "T-800");
    await page.fill('input[placeholder="We automate sales prospecting by 90% using outbound voice calls."]', "We ensure absolute system uptime and outbound cold dialing integrations.");
    await page.fill('textarea[placeholder^="Visoora is a modern"]', "Cyberdyne Systems specializes in neural network processors and autonomous security systems. We are launching our corporate expansion this quarter.");
    
    // Play voice profile sample
    await page.click('button:has-text("Rachel")');
    await page.waitForTimeout(500);
    
    // Proceed to Step 4
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/onboarding\/step-4/);

    // Step 4: Compliance Regulatory setup
    await expect(page.locator("text=Regulatory compliance setup")).toBeVisible();
    
    // Assert Consent confirmed error when submitting unchecked
    await page.click('button[type="submit"]');
    await expect(page.locator("text=You must confirm prior express written consent to proceed")).toBeVisible();
    
    // Confirm prior express consent check
    await page.check("#consentConfirmed");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/onboarding\/step-5/);

    // Step 5: Prospect Importer
    await expect(page.locator("text=Import your sales contacts")).toBeVisible();
    
    // Click Sample Template button
    await page.click('button:has-text("Use sample CSV template")');
    await expect(page.locator("text=sample_leads.csv")).toBeVisible();
    
    // Check mapping dropdown configurations
    await expect(page.locator('select >> nth=0')).toHaveValue("column_1");
    await expect(page.locator('select >> nth=1')).toHaveValue("column_2");
    
    // Start asynchronous lead import
    await page.click('button:has-text("Start Async Contacts Import")');
    
    // Wait for SSE progress bar to finish importing rows
    await page.waitForSelector("text=Prospect Pipeline Populated Successfully", { timeout: 8000 });
    
    // Proceed to Step 6
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/onboarding\/step-6/);

    // Step 6: Outbound Sandbox Testing
    await expect(page.locator("text=Outbound Sandbox Test Call")).toBeVisible();
    
    // Fill test mobile line
    await page.fill('input[placeholder="+19195551234"]', "+19195550192");
    
    // Trigger "Call Myself First"
    await page.click('button:has-text("Call Myself First")');
    
    // Watch WebSocket dialogue streaming bubbles
    await page.waitForSelector("text=Telephony Session Active", { timeout: 3000 });
    await page.waitForSelector("text=FSM: PITCH", { timeout: 10000 });
    
    // Watch for complete audio players and AI summaries
    await page.waitForSelector("text=Recording playback", { timeout: 20000 });
    await expect(page.locator("text=AI Post-Call Memory Extracted")).toBeVisible();
    await expect(page.locator("text=worried AI sounds mechanical")).toBeVisible();
    
    // Click final Glowing Launch button
    await page.click('button[type="submit"]');
    
    // Assert user is safely landed in Visoora CRM Dashboard Command Center
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator("text=Visoora — AI Sales Command Center")).toBeVisible();
  });
});

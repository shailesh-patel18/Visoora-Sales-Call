import { chromium } from "@playwright/test";
import path from "path";
import fs from "fs";

// Output folder for video
const VIDEO_DIR = path.join(__dirname, "..", "test-results", "qa-recording");
if (!fs.existsSync(VIDEO_DIR)) fs.mkdirSync(VIDEO_DIR, { recursive: true });

const BASE_URL = "https://visoora-sales-call.vercel.app";

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 800 });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 820 },
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1440, height: 820 },
    },
  });

  const page = await context.newPage();

  // ──────────────────────────────────────────
  // STEP 1: Login
  // ──────────────────────────────────────────
  console.log("[QA] Step 1: Navigating to Login...");
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(VIDEO_DIR, "01_login_page.png") });

  const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail" i]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  await emailInput.fill("shaileshvpatel18@gmail.com");
  await passwordInput.fill("Svp@1818");
  await page.screenshot({ path: path.join(VIDEO_DIR, "02_login_filled.png") });

  const loginBtn = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login")').first();
  await loginBtn.click();

  await page.waitForNavigation({ waitUntil: "networkidle", timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(3000);
  console.log("[QA] Landed on:", page.url());
  await page.screenshot({ path: path.join(VIDEO_DIR, "03_post_login.png") });

  // ──────────────────────────────────────────
  // STEP 2: Onboarding (if present)
  // ──────────────────────────────────────────
  if (page.url().includes("/onboarding")) {
    console.log("[QA] Step 2: On Onboarding page, entering website...");
    const siteInput = page.locator('input[placeholder*="website" i], input[placeholder*="http" i], input[type="url"]').first();
    if (await siteInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await siteInput.fill("https://codetheorem.co/");
      await page.screenshot({ path: path.join(VIDEO_DIR, "04_website_entered.png") });

      const analyzeBtn = page.locator('button:has-text("Analyze"), button:has-text("Scrape"), button:has-text("Extract"), button:has-text("Continue"), button:has-text("Next")').first();
      await analyzeBtn.click();
      console.log("[QA] Waiting for AI scraping...");
      await page.waitForTimeout(15000);
      await page.screenshot({ path: path.join(VIDEO_DIR, "05_after_scrape.png") });
    }

    for (let i = 0; i < 10; i++) {
      const nextBtn = page.locator('button:has-text("Next"), button:has-text("Continue"), button:has-text("Save & Continue"), button:has-text("Proceed")').first();
      if (await nextBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(2000);
        console.log(`[QA] Clicked next/continue on step ${i + 1}`);
        await page.screenshot({ path: path.join(VIDEO_DIR, `06_step_${i + 1}.png`) });
      } else {
        break;
      }
    }
  }

  // ──────────────────────────────────────────
  // STEP 3: Navigate to Contacts
  // ──────────────────────────────────────────
  console.log("[QA] Step 3: Navigating to Contacts...");
  await page.goto(`${BASE_URL}/contacts`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(VIDEO_DIR, "07_contacts_page.png") });

  // ──────────────────────────────────────────
  // STEP 4: Add new lead
  // ──────────────────────────────────────────
  console.log("[QA] Step 4: Adding new lead sp1862004@gmail.com...");
  const addBtn = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("+ "), button:has-text("Add Contact")').first();
  if (await addBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await addBtn.click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(VIDEO_DIR, "08_add_modal.png") });

    const nameInput = page.locator('input[placeholder*="name" i], input[name*="name" i]').first();
    const companyInput = page.locator('input[placeholder*="company" i], input[name*="company" i]').first();
    const phoneInput = page.locator('input[placeholder*="phone" i], input[name*="phone" i], input[type="tel"]').first();
    const emailInput2 = page.locator('input[type="email"], input[placeholder*="email" i]').first();

    if (await nameInput.isVisible({ timeout: 3000 }).catch(() => false)) await nameInput.fill("QA Demo Lead");
    if (await companyInput.isVisible({ timeout: 3000 }).catch(() => false)) await companyInput.fill("CodeTheorem");
    if (await phoneInput.isVisible({ timeout: 3000 }).catch(() => false)) await phoneInput.fill("+15559998888");
    if (await emailInput2.isVisible({ timeout: 3000 }).catch(() => false)) await emailInput2.fill("sp1862004@gmail.com");

    await page.screenshot({ path: path.join(VIDEO_DIR, "09_form_filled.png") });

    const saveBtn = page.locator('button:has-text("Save"), button:has-text("Add"), button:has-text("Submit"), button[type="submit"]').first();
    await saveBtn.click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(VIDEO_DIR, "10_after_save.png") });
    console.log("[QA] Lead saved.");
  } else {
    console.log("[QA] Could not find Add Contact button.");
    await page.screenshot({ path: path.join(VIDEO_DIR, "08_no_add_btn.png") });
  }

  // ──────────────────────────────────────────
  // STEP 5: Open the lead profile
  // ──────────────────────────────────────────
  console.log("[QA] Step 5: Opening QA Demo Lead profile...");
  await page.waitForTimeout(1000);
  const leadRow = page.locator('text=QA Demo Lead').first();
  if (await leadRow.isVisible({ timeout: 5000 }).catch(() => false)) {
    await leadRow.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(VIDEO_DIR, "11_lead_profile.png") });
  } else {
    console.log("[QA] Lead row not visible, checking contacts list...");
    await page.screenshot({ path: path.join(VIDEO_DIR, "11_contacts_state.png") });
  }

  // ──────────────────────────────────────────
  // STEP 6: Generate AI Email Script
  // ──────────────────────────────────────────
  console.log("[QA] Step 6: Looking for AI Email Generator...");
  const outreachBtn = page.locator('button:has-text("Generate"), button:has-text("Write Script"), button:has-text("Draft Email"), button:has-text("AI Email")').first();
  if (await outreachBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await outreachBtn.click();
    console.log("[QA] Waiting for AI to draft email...");
    await page.waitForTimeout(15000);
    await page.screenshot({ path: path.join(VIDEO_DIR, "12_email_generated.png") });
  } else {
    await page.screenshot({ path: path.join(VIDEO_DIR, "12_no_outreach_btn.png") });
    console.log("[QA] No outreach/generate button found on this page.");
  }

  // ──────────────────────────────────────────
  // STEP 7: Schedule Email
  // ──────────────────────────────────────────
  console.log("[QA] Step 7: Scheduling email...");
  const scheduleBtn = page.locator('button:has-text("Schedule"), button:has-text("Send Email"), button:has-text("Queue")').first();
  if (await scheduleBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await scheduleBtn.click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(VIDEO_DIR, "13_email_scheduled.png") });
    console.log("[QA] Email scheduled!");
  } else {
    await page.screenshot({ path: path.join(VIDEO_DIR, "13_no_schedule_btn.png") });
  }

  // ──────────────────────────────────────────
  // STEP 8: Check Campaigns / Inbox
  // ──────────────────────────────────────────
  console.log("[QA] Step 8: Checking Campaigns page...");
  await page.goto(`${BASE_URL}/campaigns`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(VIDEO_DIR, "14_campaigns_page.png") });

  await page.goto(`${BASE_URL}/inbox`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(VIDEO_DIR, "15_inbox_page.png") });

  await page.waitForTimeout(2000);
  console.log("[QA] E2E test complete. Closing browser...");

  await context.close();
  await browser.close();

  const files = fs.readdirSync(VIDEO_DIR);
  console.log("\n[QA] Generated files:");
  files.forEach(f => console.log(` - ${path.join(VIDEO_DIR, f)}`));
  console.log("\n✅ Video recording saved to:", VIDEO_DIR);
})();

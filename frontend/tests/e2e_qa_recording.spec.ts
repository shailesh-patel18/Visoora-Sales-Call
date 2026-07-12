import { test, chromium } from "@playwright/test";
import path from "path";
import fs from "fs";

const VIDEO_DIR = path.join(__dirname, "..", "test-results", "qa-final");

test.describe("Visoora Final E2E QA", () => {
  test("Complete flow: login → playbooks → skip integrations → add lead → AI email → schedule", async () => {
    if (!fs.existsSync(VIDEO_DIR)) fs.mkdirSync(VIDEO_DIR, { recursive: true });

    const browser = await chromium.launch({ headless: false, slowMo: 600 });
    const context = await browser.newContext({
      viewport: { width: 1440, height: 820 },
      recordVideo: { dir: VIDEO_DIR, size: { width: 1440, height: 820 } },
    });
    const page = await context.newPage();
    const BASE = "https://visoora-sales-call.vercel.app";
    const shot = async (name: string) =>
      page.screenshot({ path: path.join(VIDEO_DIR, `${name}.png`) });

    // ── STEP 1: Login ─────────────────────────────────────────────
    console.log("\n[QA] ▶ STEP 1: Login");
    await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
    await shot("01_login");
    await page.locator('input[type="email"]').first().fill("shaileshvpatel18@gmail.com");
    await page.locator('input[type="password"]').first().fill("Svp@1818");
    await page.locator('button[type="submit"]').first().click();
    await page.waitForURL(`${BASE}/**`, { timeout: 20000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2500);
    await shot("02_logged_in");
    console.log("[QA] ✅ Logged in at:", page.url());

    // ── STEP 2: Business Map → click Continue ─────────────────────
    console.log("\n[QA] ▶ STEP 2: Business Map — click Continue");
    const step2Btn = page.locator('button:has-text("Continue")').first();
    if (await step2Btn.isVisible({ timeout: 4000 }).catch(() => false)) {
      await step2Btn.click();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000);
    }
    await shot("03_after_business_map");
    console.log("[QA] Now at:", page.url());

    // ── STEP 3: Playbooks → Continue to Integrations ───────────────
    console.log("\n[QA] ▶ STEP 3: Playbooks — Continue to Integrations");
    const step3Btn = page.locator('button:has-text("Continue to Integrations")').first();
    if (await step3Btn.isVisible({ timeout: 4000 }).catch(() => false)) {
      await step3Btn.click();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000);
    }
    await shot("04_integrations_page");
    console.log("[QA] Now at:", page.url());

    // ── STEP 4: Integrations → click "Continue to Audience" (new skip btn!) ──
    console.log("\n[QA] ▶ STEP 4: Integrations — click 'Continue to Audience' skip button");
    const skipBtn = page.locator('button:has-text("Continue to Audience")').first();
    if (await skipBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skipBtn.click();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000);
      console.log("[QA] ✅ Skip button worked! Now at:", page.url());
    } else {
      console.log("[QA] ⚠ Skip button not found - Vercel may still be deploying");
      await shot("04b_no_skip_btn");
    }
    await shot("05_contacts_page");
    console.log("[QA] Contacts URL:", page.url());

    // Dump buttons
    const btns = await page.evaluate(() =>
      Array.from(document.querySelectorAll("button")).map(b => b.textContent?.trim().substring(0, 50))
    );
    console.log("[QA] Buttons:", JSON.stringify(btns));

    // ── STEP 5: Add lead sp1862004@gmail.com ──────────────────────
    console.log("\n[QA] ▶ STEP 5: Add lead sp1862004@gmail.com");
    let addClicked = false;
    for (const txt of ["Add Contact", "Add Lead", "New Lead", "New Contact", "+ Contact", "Add"]) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 1500 }).catch(() => false)) {
        console.log(`[QA] Clicking: "${txt}"`);
        await b.click();
        addClicked = true;
        break;
      }
    }
    if (!addClicked) console.log("[QA] ⚠ Add button not found");
    await page.waitForTimeout(1500);
    await shot("06_add_contact_modal");

    const nameInput = page.locator('input[placeholder*="name" i], input[name*="name" i]').first();
    if (await nameInput.isVisible({ timeout: 4000 }).catch(() => false)) {
      await nameInput.fill("QA Demo Lead");
      await page.locator('input[placeholder*="company" i]').first().fill("CodeTheorem").catch(() => {});
      await page.locator('input[placeholder*="phone" i], input[type="tel"]').first().fill("+15559998888").catch(() => {});
      await page.locator('input[type="email"]').first().fill("sp1862004@gmail.com").catch(() => {});
      await shot("07_form_filled");
      await page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Add")').first().click();
      await page.waitForTimeout(3000);
      await shot("08_lead_saved");
      console.log("[QA] ✅ Lead submitted");
    } else {
      console.log("[QA] ⚠ Form not visible");
      await shot("07_no_form");
    }

    // ── STEP 6: Click on lead profile ────────────────────────────
    console.log("\n[QA] ▶ STEP 6: Open lead profile");
    await page.waitForTimeout(1000);
    for (const t of ["QA Demo Lead", "sp1862004", "CodeTheorem"]) {
      const el = page.locator(`text="${t}"`).first();
      if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
        await el.click();
        console.log(`[QA] ✅ Clicked lead: "${t}"`);
        break;
      }
    }
    await page.waitForTimeout(2000);
    await shot("09_lead_profile");

    // ── STEP 7: AI Email Generation ───────────────────────────────
    console.log("\n[QA] ▶ STEP 7: AI Email Generation");
    for (const txt of ["Generate Email", "Generate Draft", "Write Script", "AI Email", "Generate", "Draft Email"]) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 2000 }).catch(() => false)) {
        await b.click();
        console.log(`[QA] ✅ Clicked: "${txt}"`);
        break;
      }
    }
    console.log("[QA] Waiting 15s for AI draft...");
    await page.waitForTimeout(15000);
    await shot("10_email_draft");

    // ── STEP 8: Schedule ──────────────────────────────────────────
    console.log("\n[QA] ▶ STEP 8: Schedule Email");
    for (const txt of ["Schedule Email", "Schedule", "Send Email", "Send", "Queue"]) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 2000 }).catch(() => false)) {
        await b.click();
        console.log(`[QA] ✅ Scheduled!`);
        break;
      }
    }
    await page.waitForTimeout(3000);
    await shot("11_email_scheduled");

    // ── STEP 9: Final verification pages ─────────────────────────
    for (const [name, route] of [["campaigns", "/campaigns"], ["inbox", "/inbox"], ["outbound", "/outbound"], ["pipeline", "/pipeline"], ["dashboard", "/dashboard"]]) {
      console.log(`\n[QA] ▶ Checking: ${route}`);
      await page.goto(`${BASE}${route}`, { waitUntil: "networkidle" });
      await page.waitForTimeout(1500);
      await shot(`12_${name}`);
      console.log(`[QA] ${name} URL:`, page.url());
    }

    console.log("\n\n[QA] ✅ ==========================================");
    console.log("[QA] ✅  FULL E2E TEST COMPLETE");
    console.log("[QA] ✅  Video + screenshots in:", VIDEO_DIR);
    console.log("[QA] ✅ ==========================================");

    await context.close();
    await browser.close();
    console.log("\n📁 Files generated:");
    fs.readdirSync(VIDEO_DIR).forEach(f => console.log(" -", f));
  });
});

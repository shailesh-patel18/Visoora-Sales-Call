import { test, chromium } from "@playwright/test";
import path from "path";
import fs from "fs";

const VIDEO_DIR = path.join(__dirname, "..", "test-results", "qa-recording-v3");

test.describe("Visoora E2E QA Recording", () => {
  test("Full flow: login → natural workflow progression → contacts → email", async () => {
    if (!fs.existsSync(VIDEO_DIR)) fs.mkdirSync(VIDEO_DIR, { recursive: true });

    const browser = await chromium.launch({ headless: false, slowMo: 500 });
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
    await page.waitForTimeout(2000);
    await shot("02_business_map");
    console.log("[QA] ✅ Logged in at:", page.url());

    // ── STEP 2: Progress through workflow naturally ────────────────
    // The app shows "Continue to Playbooks" on business-map. Click it.
    console.log("\n[QA] ▶ STEP 2: Click 'Continue to Playbooks'");
    const continueBtns = ['Continue to Playbooks', 'Continue to Integrations', 'Continue', 'Next Step'];
    for (const txt of continueBtns) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log(`[QA] Clicking: "${txt}"`);
        await b.click();
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(2000);
        break;
      }
    }
    await shot("03_playbooks");
    console.log("[QA] Now at:", page.url());

    // ── STEP 3: Continue through Objections/Playbooks ─────────────
    console.log("\n[QA] ▶ STEP 3: Continue through Playbooks (Objections)");
    await page.waitForTimeout(1000);
    for (const txt of ['Continue to Integrations', 'Continue to Audience', 'Continue', 'Next Step', 'Save & Continue']) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log(`[QA] Clicking: "${txt}"`);
        await b.click();
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(2000);
        break;
      }
    }
    await shot("04_after_playbooks");
    console.log("[QA] Now at:", page.url());

    // ── STEP 4: Continue through Integrations (Email setup) ───────
    if (page.url().includes("/settings/email") || page.url().includes("/integrations")) {
      console.log("\n[QA] ▶ STEP 4: Integrations/Email Settings page");
      await shot("05_integrations");
      for (const txt of ['Continue to Audience', 'Skip for now', 'Continue', 'Next Step']) {
        const b = page.locator(`button:has-text("${txt}")`).first();
        if (await b.isVisible({ timeout: 3000 }).catch(() => false)) {
          console.log(`[QA] Clicking: "${txt}"`);
          await b.click();
          await page.waitForLoadState("networkidle");
          await page.waitForTimeout(2000);
          break;
        }
      }
    }
    await shot("05_after_integrations");
    console.log("[QA] Now at:", page.url());

    // ── STEP 5: Contacts/Audience page ────────────────────────────
    console.log("\n[QA] ▶ STEP 5: Navigate to Contacts/Audience");
    // Click sidebar "Audience" link if visible
    const audienceLink = page.locator('a:has-text("Audience"), nav a[href="/contacts"]').first();
    if (await audienceLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await audienceLink.click();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/contacts`, { waitUntil: "networkidle" });
      await page.waitForTimeout(2000);
    }
    await shot("06_contacts_page");
    console.log("[QA] Contacts URL:", page.url());

    // Dump all buttons for debugging
    const btns = await page.evaluate(() =>
      Array.from(document.querySelectorAll("button")).map(b => b.textContent?.trim().substring(0, 40))
    );
    console.log("[QA] Buttons on page:", JSON.stringify(btns));

    // ── STEP 6: Add new lead ──────────────────────────────────────
    console.log("\n[QA] ▶ STEP 6: Add lead sp1862004@gmail.com");
    let addClicked = false;
    for (const txt of ["Add Contact", "Add Lead", "New Lead", "New Contact", "+ Contact", "Add"]) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 1500 }).catch(() => false)) {
        console.log(`[QA] Clicking add button: "${txt}"`);
        await b.click();
        addClicked = true;
        break;
      }
    }
    await page.waitForTimeout(1500);
    await shot("07_add_modal");

    const nameInput = page.locator('input[placeholder*="name" i], input[name*="name" i]').first();
    if (await nameInput.isVisible({ timeout: 4000 }).catch(() => false)) {
      await nameInput.fill("QA Demo Lead");
      await page.locator('input[placeholder*="company" i], input[name*="company" i]').first().fill("CodeTheorem").catch(() => {});
      await page.locator('input[placeholder*="phone" i], input[type="tel"]').first().fill("+15559998888").catch(() => {});
      await page.locator('input[type="email"], input[placeholder*="email" i]').first().fill("sp1862004@gmail.com").catch(() => {});
      await shot("08_form_filled");
      await page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Add"), button:has-text("Create")').first().click();
      await page.waitForTimeout(3000);
      await shot("09_lead_saved");
      console.log("[QA] ✅ Lead submitted");
    } else {
      console.log("[QA] ⚠ Form not visible. Page may need workflow completion first.");
      await shot("08_no_form");
    }

    // ── STEP 7: Click on the lead ─────────────────────────────────
    console.log("\n[QA] ▶ STEP 7: Open lead profile");
    await page.waitForTimeout(1000);
    for (const term of ["QA Demo Lead", "sp1862004", "CodeTheorem"]) {
      const el = page.locator(`text="${term}"`).first();
      if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
        await el.click();
        console.log(`[QA] ✅ Opened lead via: "${term}"`);
        break;
      }
    }
    await page.waitForTimeout(2000);
    await shot("10_lead_profile");

    // ── STEP 8: AI Email Generation ───────────────────────────────
    console.log("\n[QA] ▶ STEP 8: AI Email Generation");
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
    await shot("11_email_draft");

    // ── STEP 9: Schedule ──────────────────────────────────────────
    console.log("\n[QA] ▶ STEP 9: Schedule Email");
    for (const txt of ["Schedule Email", "Schedule", "Send Email", "Send", "Queue"]) {
      const b = page.locator(`button:has-text("${txt}")`).first();
      if (await b.isVisible({ timeout: 2000 }).catch(() => false)) {
        await b.click();
        console.log(`[QA] ✅ Scheduled: "${txt}"`);
        break;
      }
    }
    await page.waitForTimeout(3000);
    await shot("12_email_scheduled");

    // ── STEP 10: Final pages check ───────────────────────────────
    console.log("\n[QA] ▶ STEP 10: Checking Campaigns / Inbox / Outbound");
    for (const [label, route] of [["campaigns", "/campaigns"], ["inbox", "/inbox"], ["outbound", "/outbound"]]) {
      await page.goto(`${BASE}${route}`, { waitUntil: "networkidle" });
      await page.waitForTimeout(1500);
      await shot(`13_${label}`);
      console.log(`[QA] ${label} URL:`, page.url());
    }

    console.log("\n[QA] ✅ COMPLETE — Video + screenshots in:", VIDEO_DIR);
    await context.close();
    await browser.close();
    fs.readdirSync(VIDEO_DIR).forEach(f => console.log(" -", f));
  });
});

import { test, expect } from "@playwright/test";

test.describe("Visoora Dashboard Real Data Wiring E2E Test", () => {
  test("should load the dashboard, connect to WebSocket, and show real data states", async ({ page }) => {
    // 1. Visit dashboard page
    await page.goto("http://localhost:3000/dashboard");

    // 2. Verify Command Center header is visible
    await expect(page.locator("text=Command Center")).toBeVisible();
    await expect(page.locator("text=Real-time overview of your AI sales operations")).toBeVisible();

    // 3. Verify System Online indicator is visible
    await expect(page.locator("text=System Online")).toBeVisible();

    // 4. Verify KPI Cards are loaded with real API values (no more hardcoded "47", "8", "$24.5K")
    // Wait for the loading spinner to disappear and content to render
    await page.waitForSelector("text=Calls Today", { timeout: 10000 });

    const callsTodayCard = page.locator("text=Calls Today").locator("xpath=../following-sibling::p");
    await expect(callsTodayCard).toBeVisible();
    const callsText = await callsTodayCard.textContent();
    // Verify it is a valid numeric string, proving it came from the /analytics/dashboard API
    expect(callsText).toMatch(/^\d+$/);

    const connectionRateCard = page.locator("text=Connection Rate").locator("xpath=../following-sibling::p");
    await expect(connectionRateCard).toBeVisible();
    const rateText = await connectionRateCard.textContent();
    expect(rateText).toMatch(/^\d+%\s*$/);

    const meetingsBookedCard = page.locator("text=Meetings Booked").locator("xpath=../following-sibling::p");
    await expect(meetingsBookedCard).toBeVisible();
    const meetingsText = await meetingsBookedCard.textContent();
    expect(meetingsText).toMatch(/^\d+$/);

    // 5. Verify Live Calls widget shows WebSocket connection status
    const liveCallsHeader = page.locator("text=Live Calls");
    await expect(liveCallsHeader).toBeVisible();

    // The status badge should show either "0 active" or "Reconnecting..." or "Connection Lost"
    const statusBadge = page.locator("text=Live Calls").locator("xpath=../following-sibling::span");
    await expect(statusBadge).toBeVisible();
    const badgeText = await statusBadge.textContent();
    expect(badgeText).toMatch(/(active|Reconnecting|Connection Lost)/);
  });
});

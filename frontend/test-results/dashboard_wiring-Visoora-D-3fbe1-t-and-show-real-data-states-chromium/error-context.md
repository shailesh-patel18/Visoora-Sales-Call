# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard_wiring.spec.ts >> Visoora Dashboard Real Data Wiring E2E Test >> should load the dashboard, connect to WebSocket, and show real data states
- Location: tests\dashboard_wiring.spec.ts:4:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Command Center')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=Command Center')

```

```yaml
- main:
  - img
  - heading "Visoora" [level=1]
  - paragraph: AI Employee Call Center Operating System
  - heading "Sign in to your console" [level=2]
  - img
  - paragraph: Demo Admin Account Pre-filled
  - paragraph:
    - text: Skip signing up! Click
    - strong: Sign In
    - text: directly to test dashboard and playbooks.
  - text: Email Address
  - img
  - textbox "admin@visoora.com"
  - text: Password
  - link "Forgot password?":
    - /url: /forgotpass
  - img
  - textbox "••••••••": Visoora@2024
  - button:
    - img
  - checkbox "Keep me signed in" [checked]
  - text: Keep me signed in
  - button "Sign In":
    - text: Sign In
    - img
  - paragraph:
    - text: Don't have an account?
    - link "Create one free":
      - /url: /signup
- status:
  - img
  - text: Static route
  - button "Hide static indicator":
    - img
- alert
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("Visoora Dashboard Real Data Wiring E2E Test", () => {
  4  |   test("should load the dashboard, connect to WebSocket, and show real data states", async ({ page }) => {
  5  |     // 1. Visit dashboard page
  6  |     await page.goto("http://localhost:3000/dashboard");
  7  | 
  8  |     // 2. Verify Command Center header is visible
> 9  |     await expect(page.locator("text=Command Center")).toBeVisible();
     |                                                       ^ Error: expect(locator).toBeVisible() failed
  10 |     await expect(page.locator("text=Real-time overview of your AI sales operations")).toBeVisible();
  11 | 
  12 |     // 3. Verify System Online indicator is visible
  13 |     await expect(page.locator("text=System Online")).toBeVisible();
  14 | 
  15 |     // 4. Verify KPI Cards are loaded with real API values (no more hardcoded "47", "8", "$24.5K")
  16 |     // Wait for the loading spinner to disappear and content to render
  17 |     await page.waitForSelector("text=Calls Today", { timeout: 10000 });
  18 | 
  19 |     const callsTodayCard = page.locator("text=Calls Today").locator("xpath=../following-sibling::p");
  20 |     await expect(callsTodayCard).toBeVisible();
  21 |     const callsText = await callsTodayCard.textContent();
  22 |     // Verify it is a valid numeric string, proving it came from the /analytics/dashboard API
  23 |     expect(callsText).toMatch(/^\d+$/);
  24 | 
  25 |     const connectionRateCard = page.locator("text=Connection Rate").locator("xpath=../following-sibling::p");
  26 |     await expect(connectionRateCard).toBeVisible();
  27 |     const rateText = await connectionRateCard.textContent();
  28 |     expect(rateText).toMatch(/^\d+%\s*$/);
  29 | 
  30 |     const meetingsBookedCard = page.locator("text=Meetings Booked").locator("xpath=../following-sibling::p");
  31 |     await expect(meetingsBookedCard).toBeVisible();
  32 |     const meetingsText = await meetingsBookedCard.textContent();
  33 |     expect(meetingsText).toMatch(/^\d+$/);
  34 | 
  35 |     // 5. Verify Live Calls widget shows WebSocket connection status
  36 |     const liveCallsHeader = page.locator("text=Live Calls");
  37 |     await expect(liveCallsHeader).toBeVisible();
  38 | 
  39 |     // The status badge should show either "0 active" or "Reconnecting..." or "Connection Lost"
  40 |     const statusBadge = page.locator("text=Live Calls").locator("xpath=../following-sibling::span");
  41 |     await expect(statusBadge).toBeVisible();
  42 |     const badgeText = await statusBadge.textContent();
  43 |     expect(badgeText).toMatch(/(active|Reconnecting|Connection Lost)/);
  44 |   });
  45 | });
  46 | 
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: real_first_hardening.spec.ts >> Real-First Hardening Verification >> Nexus: Infrastructure must report real telemetry
- Location: tests/real_first_hardening.spec.ts:22:7

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    5 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e6]:
    - generic [ref=e8]:
      - img [ref=e10]
      - generic [ref=e13]:
        - heading "Sign In" [level=1] [ref=e14]
        - paragraph [ref=e15]: Welcome back to Ettametta
    - generic [ref=e16]:
      - generic [ref=e17]:
        - generic [ref=e18]: Username
        - generic [ref=e19]:
          - textbox "Enter your username" [ref=e20]
          - img [ref=e22]
      - generic [ref=e25]:
        - generic [ref=e26]: Password
        - generic [ref=e27]:
          - textbox "Enter your password" [ref=e28]
          - img [ref=e30]
      - generic [ref=e34] [cursor=pointer]:
        - checkbox "Remember me" [ref=e35]
        - generic [ref=e36]: Remember me
      - button "Sign In" [ref=e37]:
        - generic [ref=e38]: Sign In
    - paragraph [ref=e40]:
      - text: Don't have an account?
      - link "Create account" [ref=e41] [cursor=pointer]:
        - /url: /register
  - region "Notifications alt+T"
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | /**
  4   |  * ettametta: Real-First Hardening E2E Suite
  5   |  * This suite validates that the dashboard is strictly coupled to the Go API Gateway
  6   |  * and that no simulated UI patterns or "dummy" data remain in production-level modules.
  7   |  */
  8   | test.describe('Real-First Hardening Verification', () => {
  9   |   
  10  |   test.beforeEach(async ({ page }) => {
  11  |     // Authenticate using standard credentials
  12  |     await page.goto('/login');
  13  |     // Note: In an real CI environment, these would be pulled from process.env
> 14  |     await page.fill('input[name="email"]', 'test@example.com');
      |                ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  15  |     await page.fill('input[name="password"]', 'testpassword');
  16  |     await page.click('button[type="submit"]');
  17  |     
  18  |     // Ensure dashboard context is established
  19  |     await expect(page).toHaveURL('/', { timeout: 10000 });
  20  |   });
  21  | 
  22  |   test('Nexus: Infrastructure must report real telemetry', async ({ page }) => {
  23  |     await page.goto('/nexus');
  24  |     
  25  |     // The Nexus page must show the real hostname/node ID from the backend
  26  |     // simulated fallbacks use strings like "HOST-SIM-X"
  27  |     const nodeLabel = page.locator('span:has-text("Node_ID")').first();
  28  |     await expect(nodeLabel).toBeVisible();
  29  |     
  30  |     const nodeValue = await page.locator('div:has-text("Node_ID") + h4, h4:has-text("NODE-")').first().innerText();
  31  |     expect(nodeValue).not.toContain('SIM-');
  32  |     expect(nodeValue).not.toContain('LOCAL-DUMMY');
  33  |   });
  34  | 
  35  |   test('Analytics: History must load via withRealFallback without simulated delay', async ({ page }) => {
  36  |     await page.goto('/analytics');
  37  |     
  38  |     // Verify that the posts list is operational
  39  |     const posts = page.locator('tr:has-text("Published")');
  40  |     if (await posts.count() > 0) {
  41  |       await posts.first().click();
  42  |       
  43  |       // Metrics should load. Check for View count visibility
  44  |       await expect(page.locator('h2:has-text("Views")')).toBeVisible();
  45  |       
  46  |       // Ensure no simulated indicators are present
  47  |       const simulatedBadge = page.locator('text=SIMULATED');
  48  |       await expect(simulatedBadge).not.toBeVisible();
  49  |     }
  50  |   });
  51  | 
  52  |   test('Empire: Velocity and Scale must be deterministic', async ({ page }) => {
  53  |     await page.goto('/empire');
  54  |     
  55  |     // Check for the velocity multiplier which is derived from real growth metrics
  56  |     const velocityDisplay = page.locator('p:has-text("x")').filter({ hasText: /^\d+\.\d+x$/ });
  57  |     await expect(velocityDisplay.first()).toBeVisible();
  58  |     
  59  |     // Ensure the "Global Scale" doesn't show a 0 value which would indicate a broken fetch
  60  |     const scaleValue = await page.locator('h2:has-text("Scale")').innerText();
  61  |     expect(parseInt(scaleValue)).toBeGreaterThan(0);
  62  |   });
  63  | 
  64  |   test('Settings: Communications verification must be operational', async ({ page }) => {
  65  |     await page.goto('/settings');
  66  |     
  67  |     const verifyBtn = page.locator('button:has-text("Verify Comms")');
  68  |     await expect(verifyBtn).toBeVisible();
  69  |     
  70  |     // Clicking should trigger a real API call (intercepted here for verification)
  71  |     const [request] = await Promise.all([
  72  |       page.waitForRequest(req => req.url().includes('/settings/verify-comms') && req.method() === 'POST'),
  73  |       verifyBtn.click()
  74  |     ]);
  75  |     
  76  |     expect(request.headers()['authorization']).toContain('Bearer');
  77  |   });
  78  | 
  79  |   test('Admin: Environment synchronization must use real backend signals', async ({ page }) => {
  80  |     await page.goto('/admin');
  81  |     
  82  |     // Scroll to Env Manager
  83  |     await page.locator('h3:has-text("Environment Management")').scrollIntoViewIfNeeded();
  84  |     
  85  |     // Check for 'STABLE' or 'SYNCED' status which implies real check
  86  |     const statusText = page.locator('.glass-card:has-text("System Status") span:has-text("STABLE")');
  87  |     await expect(statusText).toBeVisible();
  88  |   });
  89  | 
  90  |   test('Video Preview: Should handle dynamic status metadata', async ({ page }) => {
  91  |     // Navigate to a page with video previews (Discovery)
  92  |     await page.goto('/discovery');
  93  |     
  94  |     const previewBtn = page.locator('button:has-text("Preview")').first();
  95  |     if (await previewBtn.isVisible()) {
  96  |       await previewBtn.click();
  97  |       
  98  |       // Modal should show status
  99  |       const statusLabel = page.locator('p:has-text("Status") + p');
  100 |       await expect(statusLabel).toBeVisible();
  101 |       
  102 |       // Should default to a real-first value or a backend-provided one
  103 |       const statusText = await statusLabel.innerText();
  104 |       expect(statusText).not.toBe('');
  105 |       expect(statusText).not.toContain('RETICULATING');
  106 |     }
  107 |   });
  108 | 
  109 | });
  110 | 
```
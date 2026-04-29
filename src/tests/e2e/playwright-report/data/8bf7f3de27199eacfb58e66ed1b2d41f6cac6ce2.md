# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: autonomous/simple_autonomous_test.spec.ts >> Simple Autonomous Operations Test >> should navigate to nexus page
- Location: tests/autonomous/simple_autonomous_test.spec.ts:30:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="username"]')
    - waiting for" http://127.0.0.1:3000/login" navigation to finish...
    - navigated to "http://127.0.0.1:3000/login"

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
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Simple Autonomous Operations Test', () => {
  4  |     test('should login and navigate to autonomous page', async ({ page }) => {
  5  |         await page.goto('http://127.0.0.1:3000/login');
  6  |         
  7  |         // Verify login page
  8  |         await expect(page.locator('h1:text("ETTAMETTA")')).toBeVisible();
  9  |         await expect(page.locator('input[name="username"]')).toBeVisible();
  10 |         await expect(page.locator('input[name="password"]')).toBeVisible();
  11 |         
  12 |         // Login
  13 |         await page.fill('input[name="username"]', 'test');
  14 |         await page.fill('input[name="password"]', 'testpassword');
  15 |         await page.click('button[type="submit"]');
  16 |         
  17 |         // Wait for redirect or error
  18 |         try {
  19 |             await page.waitForURL('**/dashboard', { timeout: 5000 });
  20 |         } catch (e) {
  21 |             // If login fails, that's okay for this test
  22 |             // We just want to verify the page loads
  23 |         }
  24 |         
  25 |         // Navigate to autonomous page
  26 |         await page.goto('http://127.0.0.1:3000/autonomous');
  27 |         await expect(page.locator('text=Agent Zero')).toBeVisible();
  28 |     });
  29 | 
  30 |     test('should navigate to nexus page', async ({ page }) => {
  31 |         await page.goto('http://127.0.0.1:3000/login');
  32 |         
  33 |         // Login
> 34 |         await page.fill('input[name="username"]', 'testuser');
     |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  35 |         await page.fill('input[name="password"]', 'testpassword');
  36 |         await page.click('button[type="submit"]');
  37 |         
  38 |         // Wait for redirect or error
  39 |         try {
  40 |             await page.waitForURL('**/dashboard', { timeout: 5000 });
  41 |         } catch (e) {
  42 |             // If login fails, that's okay for this test
  43 |         }
  44 |         
  45 |         // Navigate to nexus page
  46 |         await page.goto('http://127.0.0.1:3000/nexus');
  47 |         await expect(page.locator('text=Nexus Engine')).toBeVisible();
  48 |     });
  49 | });
```
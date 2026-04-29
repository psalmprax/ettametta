# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth/login.spec.ts >> Login >> should show error with invalid credentials
- Location: tests/auth/login.spec.ts:21:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input#username')
    3 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
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
  - button "Open Next.js Dev Tools" [ref=e47] [cursor=pointer]:
    - img [ref=e48]
```

# Test source

```ts
  1  | /**
  2  |  * Authentication E2E Tests
  3  |  * =======================
  4  |  * End-to-end tests for authentication flows
  5  |  */
  6  | 
  7  | import { test, expect } from '@playwright/test';
  8  | 
  9  | test.describe('Login', () => {
  10 |     test.beforeEach(async ({ page }) => {
  11 |         await page.goto('/login');
  12 |     });
  13 | 
  14 |     test('should display login form', async ({ page }) => {
  15 |         await expect(page.locator('h1')).toContainText(/etta/i);
  16 |         await expect(page.locator('input#username')).toBeVisible();
  17 |         await expect(page.locator('input#password')).toBeVisible();
  18 |         await expect(page.locator('button[type="submit"]')).toBeVisible();
  19 |     });
  20 | 
  21 |     test('should show error with invalid credentials', async ({ page }) => {
> 22 |         await page.fill('input#username', 'invaliduser');
     |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  23 |         await page.fill('input#password', 'wrongpassword');
  24 |         await page.click('button[type="submit"]');
  25 | 
  26 |         await expect(page.locator('[class*="bg-red"]')).toBeVisible({ timeout: 10000 });
  27 |     });
  28 | 
  29 |     test('should have register link', async ({ page }) => {
  30 |         await expect(page.locator('text=Register')).toBeVisible();
  31 |     });
  32 | 
  33 |     test('should redirect to register page', async ({ page }) => {
  34 |         await page.click('text=Register');
  35 |         await expect(page).toHaveURL('/register');
  36 |     });
  37 | });
  38 | 
  39 | test.describe('Registration', () => {
  40 |     test.beforeEach(async ({ page }) => {
  41 |         await page.goto('/register');
  42 |     });
  43 | 
  44 |     test('should display registration form', async ({ page }) => {
  45 |         await expect(page.locator('h1')).toContainText(/forge/i);
  46 |     });
  47 | 
  48 |     test('should register new user', async ({ page }) => {
  49 |         const timestamp = Date.now();
  50 |         await page.fill('input#username', `user${timestamp}`);
  51 |         await page.fill('input#email', `user${timestamp}@example.com`);
  52 |         await page.fill('input#password', 'password123');
  53 |         await page.click('button[type="submit"]');
  54 | 
  55 |         await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  56 |     });
  57 | });
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth/login.spec.ts >> Registration >> should display registration form
- Location: tests/auth/login.spec.ts:44:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/register", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e6]:
    - generic [ref=e8]:
      - img [ref=e10]
      - generic [ref=e13]:
        - heading "Create Account" [level=1] [ref=e14]
        - paragraph [ref=e15]: Join Ettametta today
    - generic [ref=e16]:
      - generic [ref=e17]:
        - generic [ref=e18]: Email
        - generic [ref=e19]:
          - textbox "you@example.com" [ref=e20]
          - img [ref=e22]
      - generic [ref=e25]:
        - generic [ref=e26]: Password
        - generic [ref=e27]:
          - textbox "Create a secure password" [ref=e28]
          - img [ref=e30]
      - generic [ref=e33]:
        - paragraph [ref=e34]: "Password Requirements:"
        - list [ref=e35]:
          - listitem [ref=e36]: 8+ characters
          - listitem [ref=e38]: Uppercase and lowercase letters
          - listitem [ref=e40]: At least one number
      - button "Create Account" [ref=e42]:
        - generic [ref=e43]: Create Account
    - paragraph [ref=e45]:
      - text: Already have an account?
      - link "Sign in" [ref=e46] [cursor=pointer]:
        - /url: /login
  - region "Notifications alt+T"
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
  22 |         await page.fill('input#username', 'invaliduser');
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
> 41 |         await page.goto('/register');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
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
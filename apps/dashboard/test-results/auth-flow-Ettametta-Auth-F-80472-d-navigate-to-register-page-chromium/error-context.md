# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-flow.spec.ts >> Ettametta Auth Flow Tests >> should navigate to register page
- Location: tests/auth-flow.spec.ts:18:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Create Account').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=Create Account').first()

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - img [ref=e8]
        - heading "JOIN THE FORGE" [level=1] [ref=e10]
        - paragraph [ref=e11]: Scale your content with AI precision
      - generic [ref=e12]:
        - generic [ref=e13]:
          - text: Username
          - generic [ref=e14]:
            - img [ref=e15]
            - textbox "Username" [ref=e18]:
              - /placeholder: commander
        - generic [ref=e19]:
          - text: Email
          - generic [ref=e20]:
            - img [ref=e21]
            - textbox "Email" [ref=e24]:
              - /placeholder: you@example.com
        - generic [ref=e25]:
          - text: Password
          - generic [ref=e26]:
            - img [ref=e27]
            - textbox "Password" [ref=e30]:
              - /placeholder: ••••••••
        - button "INITIALIZE ACCOUNT" [ref=e31]:
          - text: INITIALIZE ACCOUNT
          - img [ref=e32]
      - paragraph [ref=e34]:
        - text: Already have access?
        - link "Authenticated Login" [ref=e35] [cursor=pointer]:
          - /url: /login
    - region "Notifications alt+T"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Ettametta Auth Flow Tests', () => {
  4  |   const baseURL = process.env.BASE_URL || 'http://localhost:7202';
  5  |   // Note: These tests require the API backend to be running
  6  |   // The tests verify the frontend UI interactions
  7  | 
  8  |   test.beforeEach(async ({ page }) => {
  9  |     await page.goto(baseURL);
  10 |   });
  11 | 
  12 |   test('should navigate to login page', async ({ page }) => {
  13 |     await page.goto(`${baseURL}/login`);
  14 |     await expect(page).toHaveURL(/.*login/);
  15 |     expect(await page.locator('text=Sign In').first()).toBeVisible();
  16 |   });
  17 | 
  18 |   test('should navigate to register page', async ({ page }) => {
  19 |     await page.goto(`${baseURL}/register`);
> 20 |     await expect(page.locator('text=Create Account').first()).toBeVisible();
     |                                                               ^ Error: expect(locator).toBeVisible() failed
  21 |   });
  22 | 
  23 |   test('should show validation error for invalid form submission', async ({ page }) => {
  24 |     await page.goto(`${baseURL}/register`);
  25 |     
  26 |     // Try to submit with invalid email
  27 |     await page.fill('input[type="email"]', 'invalid-email');
  28 |     await page.fill('input[type="password"]', 'short');
  29 |     
  30 |     await page.click('button[type="submit"]');
  31 |     
  32 |     // Form should not redirect on invalid data
  33 |     await page.waitForTimeout(1000);
  34 |     await expect(page).toHaveURL(/.*register/);
  35 |   });
  36 | 
  37 |   test('should have login form fields', async ({ page }) => {
  38 |     await page.goto(`${baseURL}/login`);
  39 |     
  40 |     await expect(page.locator('input[type="text"]')).toBeVisible(); // username field
  41 |     await expect(page.locator('input[type="password"]')).toBeVisible();
  42 |     await expect(page.locator('button[type="submit"]')).toBeVisible();
  43 |   });
  44 | 
  45 |   test('should have register form fields', async ({ page }) => {
  46 |     await page.goto(`${baseURL}/register`);
  47 |     
  48 |     await expect(page.locator('input[type="email"]')).toBeVisible();
  49 |     await expect(page.locator('input[type="password"]')).toBeVisible();
  50 |     await expect(page.locator('button[type="submit"]')).toBeVisible();
  51 |   });
  52 | });
  53 | 
  54 | 
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth_flow.spec.ts >> Authentication Flow >> should show error with invalid credentials
- Location: tests/auth_flow.spec.ts:29:7

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

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
  3  | test.describe('Authentication Flow', () => {
  4  |   test('should register a new user', async ({ page }) => {
  5  |     await page.goto('/register');
  6  |     
  7  |     const randomId = Date.now();
  8  |     await page.getByPlaceholder('you@example.com').fill(`test${randomId}@example.com`);
  9  |     await page.getByPlaceholder('Create a secure password').fill('TestPassword123!');
  10 |     
  11 |     await page.click('button[type="submit"]');
  12 |     
  13 |     // Registration redirects to login with ?registered=true
  14 |     await expect(page).toHaveURL(/\/login/);
  15 |     await expect(page).toHaveURL(/registered=true/);
  16 |   });
  17 | 
  18 |   test('should login with valid credentials', async ({ page }) => {
  19 |     await page.goto('/login');
  20 |     
  21 |     await page.getByPlaceholder('Enter your username').fill('samuelolle@yahoo.com');
  22 |     await page.getByPlaceholder('Enter your password').fill('Single123.');
  23 |     await page.click('button[type="submit"]');
  24 |     
  25 |     await expect(page).toHaveURL(/\/dashboard/);
  26 |     await expect(page.locator('h1')).toContainText(/Intelligence OS/i);
  27 |   });
  28 | 
  29 |   test('should show error with invalid credentials', async ({ page }) => {
> 30 |     await page.goto('/login');
     |                ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  31 |     
  32 |     await page.getByPlaceholder('Enter your username').fill('invalid@example.com');
  33 |     await page.getByPlaceholder('Enter your password').fill('wrongpassword');
  34 |     await page.click('button[type="submit"]');
  35 |     
  36 |     await expect(page.getByRole('alert').filter({ hasText: /incorrect|invalid/i })).toBeVisible();
  37 |   });
  38 | 
  39 |   test('should logout successfully', async ({ page }) => {
  40 |     const randomId = Date.now();
  41 |     const email = `logout${randomId}@example.com`;
  42 |     const password = 'TestPassword123!';
  43 | 
  44 |     // Register
  45 |     await page.goto('/register');
  46 |     await page.getByPlaceholder('you@example.com').fill(email);
  47 |     await page.getByPlaceholder('Create a secure password').fill(password);
  48 |     await page.click('button[type="submit"]');
  49 |     await expect(page).toHaveURL(/\/login/);
  50 | 
  51 |     // Login
  52 |     await page.getByPlaceholder('Enter your username').fill(email);
  53 |     await page.getByPlaceholder('Enter your password').fill(password);
  54 |     await page.click('button[type="submit"]');
  55 |     await expect(page).toHaveURL(/\/dashboard/);
  56 |     
  57 |     // Logout
  58 |     await page.getByRole('button', { name: /sign out/i }).click();
  59 |     await expect(page).toHaveURL(/\/login/);
  60 |   });
  61 | });
```
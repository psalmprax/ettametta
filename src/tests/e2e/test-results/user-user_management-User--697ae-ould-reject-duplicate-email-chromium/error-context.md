# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: user/user_management.spec.ts >> User Management - Register >> should reject duplicate email
- Location: tests/user/user_management.spec.ts:40:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="username"]')
    - waiting for" http://localhost:3000/register" navigation to finish...

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
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('User Management - Register', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/register');
  6   |     });
  7   | 
  8   |     test('should display registration form', async ({ page }) => {
  9   |         await expect(page.locator('h1')).toContainText(/register/i);
  10  |         await expect(page.locator('input[name="username"]')).toBeVisible();
  11  |         await expect(page.locator('input[name="email"]')).toBeVisible();
  12  |         await expect(page.locator('input[name="password"]')).toBeVisible();
  13  |     });
  14  | 
  15  |     test('should register new user', async ({ page }) => {
  16  |         const timestamp = Date.now();
  17  |         await page.fill('input[name="username"]', `user${timestamp}`);
  18  |         await page.fill('input[name="email"]', `user${timestamp}@example.com`);
  19  |         await page.fill('input[name="password"]', 'password123');
  20  |         await page.click('button[type="submit"]');
  21  |         await expect(page).toHaveURL('/');
  22  |     });
  23  | 
  24  |     test('should validate email format', async ({ page }) => {
  25  |         await page.fill('input[name="username"]', 'testuser');
  26  |         await page.fill('input[name="email"]', 'invalid-email');
  27  |         await page.fill('input[name="password"]', 'password123');
  28  |         await page.click('button[type="submit"]');
  29  |         await expect(page.locator('[data-testid="error-message"]')).toContainText(/email/i);
  30  |     });
  31  | 
  32  |     test('should validate password strength', async ({ page }) => {
  33  |         await page.fill('input[name="username"]', 'testuser');
  34  |         await page.fill('input[name="email"]', 'test@example.com');
  35  |         await page.fill('input[name="password"]', 'weak');
  36  |         await page.click('button[type="submit"]');
  37  |         await expect(page.locator('[data-testid="error-message"]')).toContainText(/password/i);
  38  |     });
  39  | 
  40  |     test('should reject duplicate email', async ({ page }) => {
  41  |         const timestamp = Date.now();
> 42  |         await page.fill('input[name="username"]', `user${timestamp}`);
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  43  |         await page.fill('input[name="email"]', `duplicate${timestamp}@example.com`);
  44  |         await page.fill('input[name="password"]', 'password123');
  45  |         await page.click('button[type="submit"]');
  46  |         // Register again with same email
  47  |         await page.goto('/register');
  48  |         await page.fill('input[name="username"]', `user2${timestamp}`);
  49  |         await page.fill('input[name="email"]', `duplicate${timestamp}@example.com`);
  50  |         await page.fill('input[name="password"]', 'password123');
  51  |         await page.click('button[type="submit"]');
  52  |         await expect(page.locator('[data-testid="error-message"]')).toContainText(/email/i);
  53  |     });
  54  | });
  55  | 
  56  | test.describe('User Management - Login', () => {
  57  |     test.beforeEach(async ({ page }) => {
  58  |         await page.goto('/login');
  59  |     });
  60  | 
  61  |     test('should display login form', async ({ page }) => {
  62  |         await expect(page.locator('h1')).toContainText(/login/i);
  63  |         await expect(page.locator('input[name="email"]')).toBeVisible();
  64  |         await expect(page.locator('input[name="password"]')).toBeVisible();
  65  |     });
  66  | 
  67  |     test('should login with valid credentials', async ({ page }) => {
  68  |         await page.fill('input[name="email"]', 'test@example.com');
  69  |         await page.fill('input[name="password"]', 'testpassword123');
  70  |         await page.click('button[type="submit"]');
  71  |         await expect(page).toHaveURL('/');
  72  |     });
  73  | 
  74  |     test('should show error with invalid credentials', async ({ page }) => {
  75  |         await page.fill('input[name="email"]', 'invalid@example.com');
  76  |         await page.fill('input[name="password"]', 'wrongpassword');
  77  |         await page.click('button[type="submit"]');
  78  |         await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  79  |     });
  80  | 
  81  |     test('should redirect to register', async ({ page }) => {
  82  |         await page.click('text=Register');
  83  |         await expect(page).toHaveURL('/register');
  84  |     });
  85  | 
  86  |     test('should have forgot password option', async ({ page }) => {
  87  |         await expect(page.locator('text=Forgot Password')).toBeVisible();
  88  |     });
  89  | });
  90  | 
  91  | test.describe('User Management - OAuth', () => {
  92  |     const requiresCredentials = process.env.GOOGLE_CLIENT_ID;
  93  | 
  94  |     test.beforeEach(async ({ page }) => {
  95  |         await page.goto('/login');
  96  |     });
  97  | 
  98  |     test.skip(!requiresCredentials, 'OAuth credentials not configured');
  99  | 
  100 |     test('should show Google login option', async ({ page }) => {
  101 |         await expect(page.locator('[data-testid="google-login"]')).toBeVisible();
  102 |     });
  103 | 
  104 |     test('should initiate Google OAuth', async ({ page }) => {
  105 |         await page.click('[data-testid="google-login"]');
  106 |         await expect(page).toHaveURL(/accounts\.google\.com/);
  107 |     });
  108 | 
  109 |     test('should handle OAuth callback', async ({ page }) => {
  110 |         await page.goto('/auth/google/callback?code=mock_code&state=mock_state');
  111 |         await expect(page).toHaveURL('/');
  112 |     });
  113 | });
  114 | 
  115 | test.describe('User Management - Settings', () => {
  116 |     test.beforeEach(async ({ page }) => {
  117 |         await page.goto('/login');
  118 |         await page.fill('input[name="email"]', 'test@example.com');
  119 |         await page.fill('input[name="password"]', 'testpassword');
  120 |         await page.click('button[type="submit"]');
  121 |         await page.waitForURL('/');
  122 |     });
  123 | 
  124 |     test('should display settings page', async ({ page }) => {
  125 |         await page.goto('/settings');
  126 |         await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
  127 |     });
  128 | 
  129 |     test('should update profile information', async ({ page }) => {
  130 |         await page.goto('/settings');
  131 |         await page.click('text=Profile');
  132 |         await page.fill('input[name="full_name"]', 'Updated Name');
  133 |         await page.click('button:has-text("Save")');
  134 |         await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  135 |     });
  136 | 
  137 |     test('should change email', async ({ page }) => {
  138 |         await page.goto('/settings');
  139 |         await page.click('text=Email');
  140 |         await page.fill('input[name="new_email"]', 'newemail@example.com');
  141 |         await page.click('button:has-text("Update Email")');
  142 |         await expect(page.locator('[data-testid="confirmation-sent"]')).toBeVisible();
```
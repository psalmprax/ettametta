# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth/oauth.spec.ts >> Token Refresh >> should automatically refresh expired token
- Location: tests/auth/oauth.spec.ts:74:9

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
  1  | /**
  2  |  * OAuth Flow E2E Tests
  3  |  * ===================
  4  |  * End-to-end tests for OAuth authentication flows
  5  |  * 
  6  |  * Note: These tests require OAuth credentials to be configured.
  7  |  * In CI, we use mock OAuth services.
  8  |  */
  9  | 
  10 | import { test, expect } from '@playwright/test';
  11 | 
  12 | test.describe('OAuth Flows', () => {
  13 |     const requiresCredentials = process.env.GOOGLE_CLIENT_ID && process.env.TIKTOK_CLIENT_KEY;
  14 | 
  15 |     test.skip(!requiresCredentials, 'OAuth credentials not configured');
  16 | 
  17 |     test.describe('YouTube OAuth', () => {
  18 |         test('should initiate YouTube OAuth flow', async ({ page }) => {
  19 |             // Navigate to settings or publishing page where OAuth is available
  20 |             await page.goto('/settings');
  21 | 
  22 |             // Click connect YouTube button
  23 |             await page.click('[data-testid="connect-youtube"]');
  24 | 
  25 |             // Should redirect to Google OAuth
  26 |             await expect(page).toHaveURL(/accounts\.google\.com/);
  27 |         });
  28 | 
  29 |         test('should handle OAuth callback', async ({ page }) => {
  30 |             // This test simulates the OAuth callback
  31 |             // In production, this would be triggered by Google's redirect
  32 | 
  33 |             // Navigate to callback URL with mock auth code
  34 |             await page.goto('/publish/auth/youtube/callback?code=mock_auth_code&state=mock_state');
  35 | 
  36 |             // Should show success or redirect to settings
  37 |             // The exact behavior depends on implementation
  38 |         });
  39 |     });
  40 | 
  41 |     test.describe('TikTok OAuth', () => {
  42 |         test('should initiate TikTok OAuth flow', async ({ page }) => {
  43 |             await page.goto('/settings');
  44 | 
  45 |             // Click connect TikTok button
  46 |             await page.click('[data-testid="connect-tiktok"]');
  47 | 
  48 |             // Should redirect to TikTok OAuth
  49 |             await expect(page).toHaveURL(/\.tiktok\.com/);
  50 |         });
  51 |     });
  52 | 
  53 |     test.describe('OAuth Error Handling', () => {
  54 |         test('should handle denied OAuth', async ({ page }) => {
  55 |             // Navigate to callback with error (user denied)
  56 |             await page.goto('/publish/auth/youtube/callback?error=access_denied&error_description=User+denied+access');
  57 | 
  58 |             // Should show error message
  59 |             await expect(page.locator('[data-testid="oauth-error"]')).toBeVisible();
  60 |             await expect(page.locator('[data-testid="oauth-error"]')).toContainText(/denied/i);
  61 |         });
  62 | 
  63 |         test('should handle invalid state parameter', async ({ page }) => {
  64 |             // Navigate to callback with invalid state (CSRF protection)
  65 |             await page.goto('/publish/auth/youtube/callback?code=valid_code&state=invalid_state');
  66 | 
  67 |             // Should show security error
  68 |             await expect(page.locator('[data-testid="oauth-error"]')).toBeVisible();
  69 |         });
  70 |     });
  71 | });
  72 | 
  73 | test.describe('Token Refresh', () => {
  74 |     test('should automatically refresh expired token', async ({ page }) => {
  75 |         // Login first
> 76 |         await page.goto('/login');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  77 |         await page.fill('input[name="email"]', 'test@example.com');
  78 |         await page.fill('input[name="password"]', 'testpassword');
  79 |         await page.click('button[type="submit"]');
  80 | 
  81 |         // Wait for dashboard
  82 |         await expect(page).toHaveURL('/');
  83 | 
  84 |         // Navigate to settings
  85 |         await page.goto('/settings');
  86 | 
  87 |         // Check connected accounts
  88 |         await expect(page.locator('[data-testid="youtube-status"]')).toContainText(/connected/i);
  89 | 
  90 |         // Perform an action that requires the token
  91 |         await page.goto('/publish');
  92 | 
  93 |         // Should work without re-authentication (token was refreshed)
  94 |         await expect(page.locator('[data-testid="publish-form"]')).toBeVisible();
  95 |     });
  96 | });
  97 | 
```
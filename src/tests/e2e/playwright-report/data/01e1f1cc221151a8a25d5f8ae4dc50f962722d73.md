# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: billing/billing.spec.ts >> Billing - Cancel Subscription >> should confirm cancellation
- Location: tests/billing/billing.spec.ts:85:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    3 × waiting for" http://localhost:3000/login" navigation to finish...
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
  3   | test.describe('Billing - Subscribe Plan', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
  6   |         await page.fill('input[name="email"]', 'test@example.com');
  7   |         await page.fill('input[name="password"]', 'testpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display subscription plans', async ({ page }) => {
  13  |         await page.goto('/billing/subscribe');
  14  |         await expect(page.locator('[data-testid="plan-grid"]')).toBeVisible();
  15  |     });
  16  | 
  17  |     test('should select and subscribe to a plan', async ({ page }) => {
  18  |         await page.goto('/billing/subscribe');
  19  |         await page.click('[data-testid="plan-card"]:has-text("Pro")');
  20  |         await page.click('button:has-text("Subscribe")');
  21  |         await expect(page.locator('[data-testid="checkout-modal"]')).toBeVisible();
  22  |     });
  23  | 
  24  |     test('should show feature comparison', async ({ page }) => {
  25  |         await page.goto('/billing/subscribe');
  26  |         await expect(page.locator('[data-testid="feature-comparison"]')).toBeVisible();
  27  |     });
  28  | 
  29  |     test('should display current plan status', async ({ page }) => {
  30  |         await page.goto('/billing');
  31  |         await expect(page.locator('[data-testid="current-plan"]')).toBeVisible();
  32  |     });
  33  | });
  34  | 
  35  | test.describe('Billing - View Subscription', () => {
  36  |     test.beforeEach(async ({ page }) => {
  37  |         await page.goto('/login');
  38  |         await page.fill('input[name="email"]', 'test@example.com');
  39  |         await page.fill('input[name="password"]', 'testpassword');
  40  |         await page.click('button[type="submit"]');
  41  |         await page.waitForURL('/');
  42  |     });
  43  | 
  44  |     test('should display subscription details', async ({ page }) => {
  45  |         await page.goto('/billing');
  46  |         await expect(page.locator('[data-testid="subscription-details"]')).toBeVisible();
  47  |     });
  48  | 
  49  |     test('should show billing history', async ({ page }) => {
  50  |         await page.goto('/billing');
  51  |         await expect(page.locator('[data-testid="billing-history"]')).toBeVisible();
  52  |     });
  53  | 
  54  |     test('should display next billing date', async ({ page }) => {
  55  |         await page.goto('/billing');
  56  |         await expect(page.locator('[data-testid="next-billing-date"]')).toBeVisible();
  57  |     });
  58  | 
  59  |     test('should show payment method', async ({ page }) => {
  60  |         await page.goto('/billing');
  61  |         await expect(page.locator('[data-testid="payment-method"]')).toBeVisible();
  62  |     });
  63  | });
  64  | 
  65  | test.describe('Billing - Cancel Subscription', () => {
  66  |     test.beforeEach(async ({ page }) => {
  67  |         await page.goto('/login');
> 68  |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  69  |         await page.fill('input[name="password"]', 'testpassword');
  70  |         await page.click('button[type="submit"]');
  71  |         await page.waitForURL('/');
  72  |     });
  73  | 
  74  |     test('should display cancel option', async ({ page }) => {
  75  |         await page.goto('/billing');
  76  |         await expect(page.locator('[data-testid="cancel-subscription"]')).toBeVisible();
  77  |     });
  78  | 
  79  |     test('should show confirmation before cancel', async ({ page }) => {
  80  |         await page.goto('/billing');
  81  |         await page.click('button:has-text("Cancel Subscription")');
  82  |         await expect(page.locator('[data-testid="cancel-confirm-modal"]')).toBeVisible();
  83  |     });
  84  | 
  85  |     test('should confirm cancellation', async ({ page }) => {
  86  |         await page.goto('/billing');
  87  |         await page.click('button:has-text("Cancel Subscription")');
  88  |         await page.click('button:has-text("Confirm Cancel")');
  89  |         await expect(page.locator('[data-testid="cancelled-message"]')).toBeVisible();
  90  |     });
  91  | 
  92  |     test('should retain access until period end', async ({ page }) => {
  93  |         await page.goto('/billing');
  94  |         await expect(page.locator('[data-testid="access-until"]')).toBeVisible();
  95  |     });
  96  | });
  97  | 
  98  | test.describe('Billing - Webhook Handling', () => {
  99  |     test('should handle payment success webhook', async ({ page }) => {
  100 |         await page.goto('/webhooks/stripe');
  101 |         await expect(page.locator('[data-testid="webhook-status"]')).toBeVisible();
  102 |     });
  103 | 
  104 |     test('should handle subscription update webhook', async ({ page }) => {
  105 |         await page.goto('/webhooks/stripe');
  106 |         await expect(page.locator('[data-testid="webhook-log"]')).toBeVisible();
  107 |     });
  108 | 
  109 |     test('should handle payment failure webhook', async ({ page }) => {
  110 |         await page.goto('/webhooks/stripe');
  111 |         await expect(page.locator('[data-testid="webhook-status"]')).toBeVisible();
  112 |     });
  113 | });
```
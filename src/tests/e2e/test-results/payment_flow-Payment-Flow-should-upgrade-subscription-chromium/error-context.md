# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: payment_flow.spec.ts >> Payment Flow >> should upgrade subscription
- Location: tests/payment_flow.spec.ts:55:7

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    5 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"
    - waiting for" http://localhost:3000/login" navigation to finish...

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
  3   | test.describe('Payment Flow', () => {
  4   |   const testCard = {
  5   |     number: '4242424242424242',
  6   |     expiry: '1228',
  7   |     cvc: '123'
  8   |   };
  9   | 
  10  |   test.beforeEach(async ({ page }) => {
  11  |     await page.goto('/login');
> 12  |     await page.fill('input[name="email"]', 'test@example.com');
      |                ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  13  |     await page.fill('input[name="password"]', 'testpassword');
  14  |     await page.click('button[type="submit"]');
  15  |     await page.waitForURL('/');
  16  |   });
  17  | 
  18  |   test('should display subscription plans', async ({ page }) => {
  19  |     await page.goto('/credits');
  20  |     
  21  |     await expect(page.locator('[data-testid="subscription-plans"]')).toBeVisible();
  22  |     await expect(page.locator('[data-testid="plan-creator"]')).toBeVisible();
  23  |     await expect(page.locator('[data-testid="plan-empire"]')).toBeVisible();
  24  |   });
  25  | 
  26  |   test('should purchase credits with valid card', async ({ page }) => {
  27  |     await page.goto('/credits');
  28  |     
  29  |     await page.click('[data-testid="buy-credits-button"]');
  30  |     await page.selectOption('select[name="credits-amount"]', '100');
  31  |     
  32  |     await page.fill('input[name="card-number"]', testCard.number);
  33  |     await page.fill('input[name="card-expiry"]', testCard.expiry);
  34  |     await page.fill('input[name="card-cvc"]', testCard.cvc);
  35  |     
  36  |     await page.click('button[type="submit"]');
  37  |     
  38  |     await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  39  |     await expect(page.locator('[data-testid="credits-balance"]')).toContainText('100');
  40  |   });
  41  | 
  42  |   test('should show error with invalid card', async ({ page }) => {
  43  |     await page.goto('/credits');
  44  |     
  45  |     await page.click('[data-testid="buy-credits-button"]');
  46  |     await page.fill('input[name="card-number"]', '4000000000000002');
  47  |     await page.fill('input[name="card-expiry"]', '1228');
  48  |     await page.fill('input[name="card-cvc"]', '123');
  49  |     
  50  |     await page.click('button[type="submit"]');
  51  |     
  52  |     await expect(page.locator('[data-testid="error-message"]')).toContainText(/declined|invalid/i);
  53  |   });
  54  | 
  55  |   test('should upgrade subscription', async ({ page }) => {
  56  |     await page.goto('/settings');
  57  |     await page.click('[data-testid="billing-tab"]');
  58  |     
  59  |     await page.click('[data-testid="upgrade-to-empire"]');
  60  |     await page.selectOption('select[name="plan"]', 'empire');
  61  |     
  62  |     await page.fill('input[name="card-number"]', testCard.number);
  63  |     await page.fill('input[name="card-expiry"]', testCard.expiry);
  64  |     await page.fill('input[name="card-cvc"]', testCard.cvc);
  65  |     
  66  |     await page.click('button[type="submit"]');
  67  |     
  68  |     await expect(page.locator('[data-testid="success-message"]')).toContainText(/upgraded|success/i);
  69  |   });
  70  | 
  71  |   test('should cancel subscription', async ({ page }) => {
  72  |     await page.goto('/settings');
  73  |     await page.click('[data-testid="billing-tab"]');
  74  |     
  75  |     await page.click('[data-testid="cancel-subscription"]');
  76  |     await page.click('button:has-text("Confirm Cancel")');
  77  |     
  78  |     await expect(page.locator('[data-testid="cancellation-notice"]')).toBeVisible();
  79  |   });
  80  | 
  81  |   test('should view invoice history', async ({ page }) => {
  82  |     await page.goto('/settings');
  83  |     await page.click('[data-testid="billing-tab"]');
  84  |     
  85  |     await page.click('[data-testid="view-invoices"]');
  86  |     
  87  |     await expect(page.locator('[data-testid="invoice-list"]')).toBeVisible();
  88  |     await expect(page.locator('[data-testid="invoice-item"]')).toHaveCount(0);
  89  |   });
  90  | });
  91  | 
  92  | test.describe('Stripe Webhook', () => {
  93  |   test('should handle payment success webhook', async ({ request }) => {
  94  |     const response = await request.post('/api/v1/webhooks/stripe', {
  95  |       data: {
  96  |         type: 'payment_intent.succeeded',
  97  |         data: {
  98  |           object: {
  99  |             id: 'pi_test123',
  100 |             amount: 1000,
  101 |             currency: 'usd'
  102 |           }
  103 |         }
  104 |       }
  105 |     });
  106 |     
  107 |     expect(response.status()).toBe(200);
  108 |   });
  109 | 
  110 |   test('should handle subscription created webhook', async ({ request }) => {
  111 |     const response = await request.post('/api/v1/webhooks/stripe', {
  112 |       data: {
```
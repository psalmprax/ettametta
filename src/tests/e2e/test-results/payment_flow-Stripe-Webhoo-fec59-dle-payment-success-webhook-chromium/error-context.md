# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: payment_flow.spec.ts >> Stripe Webhook >> should handle payment success webhook
- Location: tests/payment_flow.spec.ts:93:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 200
Received: 500
```

# Test source

```ts
  7   |     cvc: '123'
  8   |   };
  9   | 
  10  |   test.beforeEach(async ({ page }) => {
  11  |     await page.goto('/login');
  12  |     await page.fill('input[name="email"]', 'test@example.com');
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
> 107 |     expect(response.status()).toBe(200);
      |                               ^ Error: expect(received).toBe(expected) // Object.is equality
  108 |   });
  109 | 
  110 |   test('should handle subscription created webhook', async ({ request }) => {
  111 |     const response = await request.post('/api/v1/webhooks/stripe', {
  112 |       data: {
  113 |         type: 'customer.subscription.created',
  114 |         data: {
  115 |           object: {
  116 |             id: 'sub_test123',
  117 |             status: 'active'
  118 |           }
  119 |         }
  120 |       }
  121 |     });
  122 |     
  123 |     expect(response.status()).toBe(200);
  124 |   });
  125 | });
```
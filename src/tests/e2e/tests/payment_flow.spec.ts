import { test, expect } from '@playwright/test';

test.describe('Payment Flow', () => {
  const testCard = {
    number: '4242424242424242',
    expiry: '1228',
    cvc: '123'
  };

  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should display subscription plans', async ({ page }) => {
    await page.goto('/credits');
    
    await expect(page.locator('[data-testid="subscription-plans"]')).toBeVisible();
    await expect(page.locator('[data-testid="plan-creator"]')).toBeVisible();
    await expect(page.locator('[data-testid="plan-empire"]')).toBeVisible();
  });

  test('should purchase credits with valid card', async ({ page }) => {
    await page.goto('/credits');
    
    await page.click('[data-testid="buy-credits-button"]');
    await page.selectOption('select[name="credits-amount"]', '100');
    
    await page.fill('input[name="card-number"]', testCard.number);
    await page.fill('input[name="card-expiry"]', testCard.expiry);
    await page.fill('input[name="card-cvc"]', testCard.cvc);
    
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="credits-balance"]')).toContainText('100');
  });

  test('should show error with invalid card', async ({ page }) => {
    await page.goto('/credits');
    
    await page.click('[data-testid="buy-credits-button"]');
    await page.fill('input[name="card-number"]', '4000000000000002');
    await page.fill('input[name="card-expiry"]', '1228');
    await page.fill('input[name="card-cvc"]', '123');
    
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/declined|invalid/i);
  });

  test('should upgrade subscription', async ({ page }) => {
    await page.goto('/settings');
    await page.click('[data-testid="billing-tab"]');
    
    await page.click('[data-testid="upgrade-to-empire"]');
    await page.selectOption('select[name="plan"]', 'empire');
    
    await page.fill('input[name="card-number"]', testCard.number);
    await page.fill('input[name="card-expiry"]', testCard.expiry);
    await page.fill('input[name="card-cvc"]', testCard.cvc);
    
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toContainText(/upgraded|success/i);
  });

  test('should cancel subscription', async ({ page }) => {
    await page.goto('/settings');
    await page.click('[data-testid="billing-tab"]');
    
    await page.click('[data-testid="cancel-subscription"]');
    await page.click('button:has-text("Confirm Cancel")');
    
    await expect(page.locator('[data-testid="cancellation-notice"]')).toBeVisible();
  });

  test('should view invoice history', async ({ page }) => {
    await page.goto('/settings');
    await page.click('[data-testid="billing-tab"]');
    
    await page.click('[data-testid="view-invoices"]');
    
    await expect(page.locator('[data-testid="invoice-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="invoice-item"]')).toHaveCount(0);
  });
});

test.describe('Stripe Webhook', () => {
  test('should handle payment success webhook', async ({ request }) => {
    const response = await request.post('/api/v1/webhooks/stripe', {
      data: {
        type: 'payment_intent.succeeded',
        data: {
          object: {
            id: 'pi_test123',
            amount: 1000,
            currency: 'usd'
          }
        }
      }
    });
    
    expect(response.status()).toBe(200);
  });

  test('should handle subscription created webhook', async ({ request }) => {
    const response = await request.post('/api/v1/webhooks/stripe', {
      data: {
        type: 'customer.subscription.created',
        data: {
          object: {
            id: 'sub_test123',
            status: 'active'
          }
        }
      }
    });
    
    expect(response.status()).toBe(200);
  });
});
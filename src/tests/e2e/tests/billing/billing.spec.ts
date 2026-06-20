import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../../helpers/auth';

test.describe('Billing - Subscribe Plan', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display subscription plans', async ({ page }) => {
        await page.goto('/billing/subscribe');
        await expect(page.locator('[data-testid="plan-grid"]')).toBeVisible();
    });

    test('should select and subscribe to a plan', async ({ page }) => {
        await page.goto('/billing/subscribe');
        await page.click('[data-testid="plan-card"]:has-text("Pro")');
        await page.click('button:has-text("Subscribe")');
        await expect(page.locator('[data-testid="checkout-modal"]')).toBeVisible();
    });

    test('should show feature comparison', async ({ page }) => {
        await page.goto('/billing/subscribe');
        await expect(page.locator('[data-testid="feature-comparison"]')).toBeVisible();
    });

    test('should display current plan status', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="current-plan"]')).toBeVisible();
    });
});

test.describe('Billing - View Subscription', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display subscription details', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="subscription-details"]')).toBeVisible();
    });

    test('should show billing history', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="billing-history"]')).toBeVisible();
    });

    test('should display next billing date', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="next-billing-date"]')).toBeVisible();
    });

    test('should show payment method', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="payment-method"]')).toBeVisible();
    });
});

test.describe('Billing - Cancel Subscription', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display cancel option', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="cancel-subscription"]')).toBeVisible();
    });

    test('should show confirmation before cancel', async ({ page }) => {
        await page.goto('/billing');
        await page.click('button:has-text("Cancel Subscription")');
        await expect(page.locator('[data-testid="cancel-confirm-modal"]')).toBeVisible();
    });

    test('should confirm cancellation', async ({ page }) => {
        await page.goto('/billing');
        await page.click('button:has-text("Cancel Subscription")');
        await page.click('button:has-text("Confirm Cancel")');
        await expect(page.locator('[data-testid="cancelled-message"]')).toBeVisible();
    });

    test('should retain access until period end', async ({ page }) => {
        await page.goto('/billing');
        await expect(page.locator('[data-testid="access-until"]')).toBeVisible();
    });
});

test.describe('Billing - Webhook Handling', () => {
    test('should handle payment success webhook', async ({ page }) => {
        await page.goto('/webhooks/stripe');
        await expect(page.locator('[data-testid="webhook-status"]')).toBeVisible();
    });

    test('should handle subscription update webhook', async ({ page }) => {
        await page.goto('/webhooks/stripe');
        await expect(page.locator('[data-testid="webhook-log"]')).toBeVisible();
    });

    test('should handle payment failure webhook', async ({ page }) => {
        await page.goto('/webhooks/stripe');
        await expect(page.locator('[data-testid="webhook-status"]')).toBeVisible();
    });
});
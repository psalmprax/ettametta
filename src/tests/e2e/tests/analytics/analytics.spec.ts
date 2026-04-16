import { test, expect } from '@playwright/test';

test.describe('Analytics', () => {
    test('should display analytics page', async ({ page }) => {
        await page.goto('/analytics');
        await expect(page.getByRole('link', { name: 'Analytics' })).toBeVisible({ timeout: 15000 });
    });

    test('should display dashboard', async ({ page }) => {
        await page.goto('/');
        await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    });

    test('should display credits page', async ({ page }) => {
        await page.goto('/credits');
        await expect(page.getByRole('link', { name: 'Credits' })).toBeVisible({ timeout: 15000 });
    });

    test('should display empire page', async ({ page }) => {
        await page.goto('/empire');
        await expect(page.getByRole('link', { name: 'Empire' })).toBeVisible({ timeout: 15000 });
    });
});
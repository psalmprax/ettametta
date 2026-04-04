import { test, expect } from '@playwright/test';

test.describe('Content Discovery', () => {
    test('should display discovery page', async ({ page }) => {
        await page.goto('/discovery');
        await expect(page.getByRole('link', { name: 'Discovery' })).toBeVisible({ timeout: 15000 });
    });

    test('should display dashboard page', async ({ page }) => {
        await page.goto('/');
        await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible({ timeout: 15000 });
    });

    test('should display creation page', async ({ page }) => {
        await page.goto('/creation');
        await expect(page.getByRole('link', { name: 'Creation' })).toBeVisible({ timeout: 15000 });
    });

    test('should display analytics page', async ({ page }) => {
        await page.goto('/analytics');
        await expect(page.getByRole('link', { name: 'Analytics' })).toBeVisible({ timeout: 15000 });
    });

    test('should display publishing page', async ({ page }) => {
        await page.goto('/publishing');
        await expect(page.getByRole('link', { name: 'Publishing' })).toBeVisible({ timeout: 15000 });
    });

    test('should display credits page', async ({ page }) => {
        await page.goto('/credits');
        await expect(page.getByRole('link', { name: 'Credits' })).toBeVisible({ timeout: 15000 });
    });
});
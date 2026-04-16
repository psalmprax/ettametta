/**
 * Authentication E2E Tests
 * =======================
 * End-to-end tests for authentication flows
 */

import { test, expect } from '@playwright/test';

test.describe('Login', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
    });

    test('should display login form', async ({ page }) => {
        await expect(page.locator('h1')).toContainText(/etta/i);
        await expect(page.locator('input#username')).toBeVisible();
        await expect(page.locator('input#password')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should show error with invalid credentials', async ({ page }) => {
        await page.fill('input#username', 'invaliduser');
        await page.fill('input#password', 'wrongpassword');
        await page.click('button[type="submit"]');

        await expect(page.locator('[class*="bg-red"]')).toBeVisible({ timeout: 10000 });
    });

    test('should have register link', async ({ page }) => {
        await expect(page.locator('text=Register')).toBeVisible();
    });

    test('should redirect to register page', async ({ page }) => {
        await page.click('text=Register');
        await expect(page).toHaveURL('/register');
    });
});

test.describe('Registration', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/register');
    });

    test('should display registration form', async ({ page }) => {
        await expect(page.locator('h1')).toContainText(/forge/i);
    });

    test('should register new user', async ({ page }) => {
        const timestamp = Date.now();
        await page.fill('input#username', `user${timestamp}`);
        await page.fill('input#email', `user${timestamp}@example.com`);
        await page.fill('input#password', 'password123');
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });
});
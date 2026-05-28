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
        await expect(page.locator('h1')).toContainText(/sign in/i);
        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should show error with invalid credentials', async ({ page }) => {
        await page.fill('input[name="username"]', 'invaliduser');
        await page.fill('input[name="password"]', 'wrongpassword');
        await page.click('button[type="submit"]');

        await expect(page.locator('text=Incorrect username/email or password')).toBeVisible({ timeout: 10000 });
    });

    test('should have register link', async ({ page }) => {
        await expect(page.locator('text=Create account')).toBeVisible();
    });

    test('should redirect to register page', async ({ page }) => {
        await page.click('text=Create account');
        await expect(page).toHaveURL('/register');
    });
});

test.describe('Registration', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/register');
    });

    test('should display registration form', async ({ page }) => {
        await expect(page.locator('h1')).toContainText(/create account/i);
    });

    test('should register new user', async ({ page }) => {
        const timestamp = Date.now();
        await page.getByPlaceholder('you@example.com').fill(`user${timestamp}@example.com`);
        await page.getByPlaceholder('Choose a display name').fill(`user${timestamp}`);
        await page.getByPlaceholder('Create a secure password').fill('password123');
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });
});
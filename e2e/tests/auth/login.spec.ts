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
        await expect(page.locator('h1')).toContainText(/login/i);
        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should show error with invalid credentials', async ({ page }) => {
        await page.fill('input[name="email"]', 'invalid@example.com');
        await page.fill('input[name="password"]', 'wrongpassword');
        await page.click('button[type="submit"]');

        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });

    test('should login with valid credentials', async ({ page }) => {
        // Note: This test requires a registered user
        // In CI, we should use test users
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword123');
        await page.click('button[type="submit"]');

        // Should redirect to dashboard
        await expect(page).toHaveURL('/');
        await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
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
        await expect(page.locator('h1')).toContainText(/register/i);
        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should register new user', async ({ page }) => {
        const timestamp = Date.now();
        await page.fill('input[name="username"]', `user${timestamp}`);
        await page.fill('input[name="email"]', `user${timestamp}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');

        // Should redirect to dashboard after registration
        await expect(page).toHaveURL('/');
    });

    test('should show error for existing email', async ({ page }) => {
        // First register
        const timestamp = Date.now();
        await page.fill('input[name="username"]', `user${timestamp}`);
        await page.fill('input[name="email"]', `duplicate${timestamp}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');

        // Try to register again with same email
        await page.goto('/register');
        await page.fill('input[name="username"]', `user2${timestamp}`);
        await page.fill('input[name="email"]', `duplicate${timestamp}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');

        await expect(page.locator('[data-testid="error-message"]')).toContainText(/email/i);
    });
});

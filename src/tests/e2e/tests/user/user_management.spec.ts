import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../../helpers/auth';

test.describe('User Management - Register', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/register');
    });

    test('should display registration form', async ({ page }) => {
        await expect(page.locator('h1')).toContainText(/register/i);
        await expect(page.locator('input[name="username"]')).toBeVisible();
        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
    });

    test('should register new user', async ({ page }) => {
        const timestamp = Date.now();
        await page.fill('input[name="username"]', `user${timestamp}`);
        await page.fill('input[name="email"]', `user${timestamp}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('/');
    });

    test('should validate email format', async ({ page }) => {
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="email"]', 'invalid-email');
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="error-message"]')).toContainText(/email/i);
    });

    test('should validate password strength', async ({ page }) => {
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'weak');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="error-message"]')).toContainText(/password/i);
    });

    test('should reject duplicate email', async ({ page }) => {
        const timestamp = Date.now();
        await page.fill('input[name="username"]', `user${timestamp}`);
        await page.fill('input[name="email"]', `duplicate${timestamp}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');
        // Register again with same email
        await page.goto('/register');
        await page.fill('input[name="username"]', `user2${timestamp}`);
        await page.fill('input[name="email"]', `duplicate${timestamp}@example.com`);
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="error-message"]')).toContainText(/email/i);
    });
});

test.describe('User Management - Login', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
    });

    test('should display login form', async ({ page }) => {
        await expect(page.locator('h1')).toContainText(/login/i);
        await expect(page.locator('input[name="email"]')).toBeVisible();
        await expect(page.locator('input[name="password"]')).toBeVisible();
    });

    test('should login with valid credentials', async ({ page }) => {
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword123');
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL('/');
    });

    test('should show error with invalid credentials', async ({ page }) => {
        await page.fill('input[name="email"]', 'invalid@example.com');
        await page.fill('input[name="password"]', 'wrongpassword');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });

    test('should redirect to register', async ({ page }) => {
        await page.click('text=Register');
        await expect(page).toHaveURL('/register');
    });

    test('should have forgot password option', async ({ page }) => {
        await expect(page.locator('text=Forgot Password')).toBeVisible();
    });
});

test.describe('User Management - OAuth', () => {
    const requiresCredentials = process.env.GOOGLE_CLIENT_ID;

    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
    });

    test.skip(!requiresCredentials, 'OAuth credentials not configured');

    test('should show Google login option', async ({ page }) => {
        await expect(page.locator('[data-testid="google-login"]')).toBeVisible();
    });

    test('should initiate Google OAuth', async ({ page }) => {
        await page.click('[data-testid="google-login"]');
        await expect(page).toHaveURL(/accounts\.google\.com/);
    });

    test('should handle OAuth callback', async ({ page }) => {
        await page.goto('/auth/google/callback?code=mock_code&state=mock_state');
        await expect(page).toHaveURL('/');
    });
});

test.describe('User Management - Settings', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display settings page', async ({ page }) => {
        await page.goto('/settings');
        await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    });

    test('should update profile information', async ({ page }) => {
        await page.goto('/settings');
        await page.click('text=Profile');
        await page.fill('input[name="full_name"]', 'Updated Name');
        await page.click('button:has-text("Save")');
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    });

    test('should change email', async ({ page }) => {
        await page.goto('/settings');
        await page.click('text=Email');
        await page.fill('input[name="new_email"]', 'newemail@example.com');
        await page.click('button:has-text("Update Email")');
        await expect(page.locator('[data-testid="confirmation-sent"]')).toBeVisible();
    });

    test('should change password', async ({ page }) => {
        await page.goto('/settings');
        await page.click('text=Password');
        await page.fill('input[name="current_password"]', 'testpassword123');
        await page.fill('input[name="new_password"]', 'newpassword123');
        await page.fill('input[name="confirm_password"]', 'newpassword123');
        await page.click('button:has-text("Update Password")');
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    });

    test('should manage notification preferences', async ({ page }) => {
        await page.goto('/settings');
        await page.click('text=Notifications');
        await page.check('input[name="email_notifications"]');
        await page.click('button:has-text("Save")');
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    });

    test('should delete account', async ({ page }) => {
        await page.goto('/settings');
        await page.click('text=Delete Account');
        await page.fill('input[name="confirm_delete"]', 'DELETE');
        await page.click('button:has-text("Delete")');
        await expect(page).toHaveURL('/');
    });
});
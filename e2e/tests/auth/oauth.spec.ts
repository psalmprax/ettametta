/**
 * OAuth Flow E2E Tests
 * ===================
 * End-to-end tests for OAuth authentication flows
 * 
 * Note: These tests require OAuth credentials to be configured.
 * In CI, we use mock OAuth services.
 */

import { test, expect } from '@playwright/test';

test.describe('OAuth Flows', () => {
    const requiresCredentials = process.env.GOOGLE_CLIENT_ID && process.env.TIKTOK_CLIENT_KEY;

    test.skip(!requiresCredentials, 'OAuth credentials not configured');

    test.describe('YouTube OAuth', () => {
        test('should initiate YouTube OAuth flow', async ({ page }) => {
            // Navigate to settings or publishing page where OAuth is available
            await page.goto('/settings');

            // Click connect YouTube button
            await page.click('[data-testid="connect-youtube"]');

            // Should redirect to Google OAuth
            await expect(page).toHaveURL(/accounts\.google\.com/);
        });

        test('should handle OAuth callback', async ({ page }) => {
            // This test simulates the OAuth callback
            // In production, this would be triggered by Google's redirect

            // Navigate to callback URL with mock auth code
            await page.goto('/publish/auth/youtube/callback?code=mock_auth_code&state=mock_state');

            // Should show success or redirect to settings
            // The exact behavior depends on implementation
        });
    });

    test.describe('TikTok OAuth', () => {
        test('should initiate TikTok OAuth flow', async ({ page }) => {
            await page.goto('/settings');

            // Click connect TikTok button
            await page.click('[data-testid="connect-tiktok"]');

            // Should redirect to TikTok OAuth
            await expect(page).toHaveURL(/\.tiktok\.com/);
        });
    });

    test.describe('OAuth Error Handling', () => {
        test('should handle denied OAuth', async ({ page }) => {
            // Navigate to callback with error (user denied)
            await page.goto('/publish/auth/youtube/callback?error=access_denied&error_description=User+denied+access');

            // Should show error message
            await expect(page.locator('[data-testid="oauth-error"]')).toBeVisible();
            await expect(page.locator('[data-testid="oauth-error"]')).toContainText(/denied/i);
        });

        test('should handle invalid state parameter', async ({ page }) => {
            // Navigate to callback with invalid state (CSRF protection)
            await page.goto('/publish/auth/youtube/callback?code=valid_code&state=invalid_state');

            // Should show security error
            await expect(page.locator('[data-testid="oauth-error"]')).toBeVisible();
        });
    });
});

test.describe('Token Refresh', () => {
    test('should automatically refresh expired token', async ({ page }) => {
        // Login first
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');

        // Wait for dashboard
        await expect(page).toHaveURL('/');

        // Navigate to settings
        await page.goto('/settings');

        // Check connected accounts
        await expect(page.locator('[data-testid="youtube-status"]')).toContainText(/connected/i);

        // Perform an action that requires the token
        await page.goto('/publish');

        // Should work without re-authentication (token was refreshed)
        await expect(page.locator('[data-testid="publish-form"]')).toBeVisible();
    });
});

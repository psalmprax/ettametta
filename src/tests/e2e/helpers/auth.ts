import { Page } from '@playwright/test';

/**
 * Shared E2E login helper — replaces the 37 identical beforeEach blocks
 * scattered across spec files. Navigates to /login, fills credentials,
 * submits, and waits for redirect.
 */
export async function loginAsTestUser(page: Page): Promise<void> {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
}



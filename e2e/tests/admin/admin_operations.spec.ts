import { test, expect } from '@playwright/test';

test.describe('Admin Operations - User Management', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'admin@example.com');
        await page.fill('input[name="password"]', 'adminpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display admin panel', async ({ page }) => {
        await page.goto('/admin');
        await expect(page.locator('[data-testid="admin-dashboard"]')).toBeVisible();
    });

    test('should list all users', async ({ page }) => {
        await page.goto('/admin/users');
        await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
    });

    test('should search users', async ({ page }) => {
        await page.goto('/admin/users');
        await page.fill('[data-testid="search-input"]', 'test');
        await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
    });

    test('should edit user details', async ({ page }) => {
        await page.goto('/admin/users');
        await page.click('[data-testid="user-row"]:first-child');
        await page.click('button:has-text("Edit")');
        await page.fill('input[name="full_name"]', 'Updated Name');
        await page.click('button:has-text("Save")');
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    });

    test('should change user tier', async ({ page }) => {
        await page.goto('/admin/users');
        await page.click('[data-testid="user-row"]:first-child');
        await page.selectOption('select[name="tier"]', 'sovereign');
        await page.click('button:has-text("Update Tier")');
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    });

    test('should suspend user', async ({ page }) => {
        await page.goto('/admin/users');
        await page.click('[data-testid="user-row"]:first-child');
        await page.click('button:has-text("Suspend")');
        await expect(page.locator('[data-testid="user-suspended"]')).toBeVisible();
    });
});

test.describe('Admin Operations - System Monitoring', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'admin@example.com');
        await page.fill('input[name="password"]', 'adminpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display system metrics', async ({ page }) => {
        await page.goto('/admin/monitoring');
        await expect(page.locator('[data-testid="system-metrics"]')).toBeVisible();
    });

    test('should show API health status', async ({ page }) => {
        await page.goto('/admin/monitoring');
        await expect(page.locator('[data-testid="api-health"]')).toBeVisible();
    });

    test('should show database health', async ({ page }) => {
        await page.goto('/admin/monitoring');
        await expect(page.locator('[data-testid="db-health"]')).toBeVisible();
    });

    test('should display queue status', async ({ page }) => {
        await page.goto('/admin/monitoring');
        await expect(page.locator('[data-testid="queue-status"]')).toBeVisible();
    });

    test('should show storage usage', async ({ page }) => {
        await page.goto('/admin/monitoring');
        await expect(page.locator('[data-testid="storage-usage"]')).toBeVisible();
    });
});

test.describe('Admin Operations - Audit Logs', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'admin@example.com');
        await page.fill('input[name="password"]', 'adminpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display audit logs', async ({ page }) => {
        await page.goto('/admin/audit-logs');
        await expect(page.locator('[data-testid="audit-log-list"]')).toBeVisible();
    });

    test('should filter logs by date', async ({ page }) => {
        await page.goto('/admin/audit-logs');
        await page.fill('[data-testid="date-from"]', '2026-04-01');
        await page.fill('[data-testid="date-to"]', '2026-04-02');
        await page.click('button:has-text("Apply Filter")');
        await expect(page.locator('[data-testid="filtered-logs"]')).toBeVisible();
    });

    test('should filter logs by user', async ({ page }) => {
        await page.goto('/admin/audit-logs');
        await page.fill('[data-testid="user-filter"]', 'testuser');
        await expect(page.locator('[data-testid="filtered-logs"]')).toBeVisible();
    });

    test('should export audit logs', async ({ page }) => {
        await page.goto('/admin/audit-logs');
        await page.click('button:has-text("Export")');
        await expect(page.locator('[data-testid="export-downloaded"]')).toBeVisible();
    });
});

test.describe('Admin Operations - Content Moderation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'admin@example.com');
        await page.fill('input[name="password"]', 'adminpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should list pending content', async ({ page }) => {
        await page.goto('/admin/moderation');
        await expect(page.locator('[data-testid="pending-content"]')).toBeVisible();
    });

    test('should approve content', async ({ page }) => {
        await page.goto('/admin/moderation');
        await page.click('[data-testid="content-row"]:first-child');
        await page.click('button:has-text("Approve")');
        await expect(page.locator('[data-testid="content-approved"]')).toBeVisible();
    });

    test('should reject content', async ({ page }) => {
        await page.goto('/admin/moderation');
        await page.click('[data-testid="content-row"]:first-child');
        await page.click('button:has-text("Reject")');
        await expect(page.locator('[data-testid="content-rejected"]')).toBeVisible();
    });

    test('should flag content for review', async ({ page }) => {
        await page.goto('/admin/moderation');
        await page.click('[data-testid="content-row"]:first-child');
        await page.click('button:has-text("Flag")');
        await expect(page.locator('[data-testid="content-flagged"]')).toBeVisible();
    });
});
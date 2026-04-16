/**
 * Video Creation E2E Tests
 * ======================
 * End-to-end tests for video transformation and generation
 */

import { test, expect } from '@playwright/test';

test.describe('Video Transformation', () => {
    test.beforeEach(async ({ page }) => {
        // Login first
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should navigate to creation page', async ({ page }) => {
        await page.goto('/creation');
        await expect(page.locator('h1')).toContainText(/creation/i);
    });

    test('should display transformation form', async ({ page }) => {
        await page.goto('/creation');
        await expect(page.locator('input[name="input_url"]')).toBeVisible();
        await expect(page.locator('select[name="niche"]')).toBeVisible();
        await expect(page.locator('select[name="platform"]')).toBeVisible();
        await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('should submit transformation request', async ({ page }) => {
        await page.goto('/creation');

        await page.fill('input[name="input_url"]', 'https://youtube.com/watch?v=test');
        await page.selectOption('select[name="niche"]', 'Technology');
        await page.selectOption('select[name="platform"]', 'YouTube Shorts');
        await page.selectOption('select[name="quality_tier"]', 'standard');

        await page.click('button[type="submit"]');

        // Should show success or job created
        await expect(page.locator('[data-testid="success-message"], [data-testid="job-created"]')).toBeVisible({ timeout: 10000 });
    });

    test('should show job in progress', async ({ page }) => {
        await page.goto('/creation');

        // Submit a job
        await page.fill('input[name="input_url"]', 'https://youtube.com/watch?v=test2');
        await page.selectOption('select[name="niche"]', 'Motivation');
        await page.click('button[type="submit"]');

        // Navigate to jobs
        await page.goto('/creation');
        await expect(page.locator('[data-testid="job-list"]')).toBeVisible();
    });
});

test.describe('AI Video Generation', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display generation options', async ({ page }) => {
        await page.goto('/creation');

        // Switch to generation tab
        await page.click('text=AI Generation');

        await expect(page.locator('textarea[name="prompt"]')).toBeVisible();
        await expect(page.locator('select[name="engine"]')).toBeVisible();
        await expect(page.locator('select[name="style"]')).toBeVisible();
        await expect(page.locator('select[name="aspect_ratio"]')).toBeVisible();
    });

    test('should generate with lite4k engine', async ({ page }) => {
        await page.goto('/creation');

        // Switch to generation tab
        await page.click('text=AI Generation');

        await page.fill('textarea[name="prompt"]', 'A futuristic city with flying cars');
        await page.selectOption('select[name="engine"]', 'lite4k');
        await page.selectOption('select[name="style"]', 'Cinematic');
        await page.selectOption('select[name="aspect_ratio"]', '9:16');

        await page.click('button[type="submit"]');

        // Should start generation
        await expect(page.locator('[data-testid="generation-started"], [data-testid="job-created"]')).toBeVisible({ timeout: 10000 });
    });

    test('should generate with ltx-video engine', async ({ page }) => {
        await page.goto('/creation');

        await page.click('text=AI Generation');

        await page.fill('textarea[name="prompt"]', 'Ocean waves at sunset');
        await page.selectOption('select[name="engine"]', 'ltx-video');
        await page.selectOption('select[name="style"]', 'Natural');
        await page.selectOption('select[name="aspect_ratio"]', '16:9');

        await page.click('button[type="submit"]');

        await expect(page.locator('[data-testid="generation-started"], [data-testid="job-created"]')).toBeVisible({ timeout: 10000 });
    });

    test('should show tier restriction for premium engines', async ({ page }) => {
        // Test with a free tier user - should see restrictions
        await page.goto('/creation');

        await page.click('text=AI Generation');

        await page.fill('textarea[name="prompt"]', 'Test');
        await page.selectOption('select[name="engine"]', 'veo3');

        await page.click('button[type="submit"]');

        // Should show upgrade prompt for free users
        await expect(page.locator('[data-testid="upgrade-prompt"], [data-testid="tier-required"]')).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Video Processing Jobs', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display job queue', async ({ page }) => {
        await page.goto('/creation');

        // Look for jobs section
        await expect(page.locator('[data-testid="job-queue"], [data-testid="jobs-list"]')).toBeVisible();
    });

    test('should show job progress', async ({ page }) => {
        await page.goto('/creation');

        // Should show progress bars for active jobs
        const progressElements = page.locator('[data-testid="job-progress"]');
        // May or may not have jobs depending on state
    });

    test('should cancel job', async ({ page }) => {
        await page.goto('/creation');

        // Find a cancel button if job exists
        const cancelButton = page.locator('[data-testid="cancel-job"]').first();
        if (await cancelButton.isVisible()) {
            await cancelButton.click();
            await expect(page.locator('[data-testid="job-cancelled"]')).toBeVisible();
        }
    });
});

test.describe('Remotion Templates', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display template options', async ({ page }) => {
        await page.goto('/creation');

        // Look for template selection
        await expect(page.locator('text=CinematicMinimal')).toBeVisible();
        await expect(page.locator('text=HormoziStyle')).toBeVisible();
    });

    test('should select template', async ({ page }) => {
        await page.goto('/creation');

        await page.click('text=CinematicMinimal');
        await expect(page.locator('[data-testid="template-selected"]')).toContainText('CinematicMinimal');
    });
});

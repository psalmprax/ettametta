import { test, expect } from '@playwright/test';

test.describe('Publishing - YouTube Upload', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display YouTube upload interface', async ({ page }) => {
        await page.goto('/publish/youtube');
        await expect(page.locator('[data-testid="youtube-upload"]')).toBeVisible();
    });

    test('should require YouTube OAuth connection', async ({ page }) => {
        await page.goto('/publish/youtube');
        await expect(page.locator('[data-testid="connect-youtube-prompt"]')).toBeVisible();
    });

    test('should upload video to YouTube', async ({ page }) => {
        await page.goto('/publish/youtube');
        // Assume OAuth is connected
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="title"]', 'My Test Video');
        await page.fill('textarea[name="description"]', 'Test description');
        await page.click('button:has-text("Upload to YouTube")');
        await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should set video privacy', async ({ page }) => {
        await page.goto('/publish/youtube');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.selectOption('select[name="privacy"]', 'private');
        await page.click('button:has-text("Upload to YouTube")');
        await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should add tags to video', async ({ page }) => {
        await page.goto('/publish/youtube');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="tags"]', 'viral,trending,ai');
        await page.click('button:has-text("Upload to YouTube")');
        await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should schedule video publication', async ({ page }) => {
        await page.goto('/publish/youtube');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="scheduled_time"]', '2026-04-15T10:00');
        await page.click('button:has-text("Schedule")');
        await expect(page.locator('[data-testid="scheduled"]')).toBeVisible();
    });
});

test.describe('Publishing - TikTok Upload', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display TikTok upload interface', async ({ page }) => {
        await page.goto('/publish/tiktok');
        await expect(page.locator('[data-testid="tiktok-upload"]')).toBeVisible();
    });

    test('should require TikTok OAuth connection', async ({ page }) => {
        await page.goto('/publish/tiktok');
        await expect(page.locator('[data-testid="connect-tiktok-prompt"]')).toBeVisible();
    });

    test('should upload video to TikTok', async ({ page }) => {
        await page.goto('/publish/tiktok');
        // Assume OAuth is connected
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="caption"]', 'Check this out! #viral #fyp');
        await page.click('button:has-text("Upload to TikTok")');
        await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should add hashtags', async ({ page }) => {
        await page.goto('/publish/tiktok');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="hashtags"]', '#viral #trending #fyp');
        await page.click('button:has-text("Upload to TikTok")');
        await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should set cover image', async ({ page }) => {
        await page.goto('/publish/tiktok');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="cover_url"]', 'https://example.com/cover.jpg');
        await page.click('button:has-text("Upload to TikTok")');
        await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
    });
});

test.describe('Publishing - Schedule Posts', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display scheduler interface', async ({ page }) => {
        await page.goto('/publish/schedule');
        await expect(page.locator('[data-testid="scheduler"]')).toBeVisible();
    });

    test('should schedule a post', async ({ page }) => {
        await page.goto('/publish/schedule');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.selectOption('select[name="platform"]', 'youtube');
        await page.fill('input[name="scheduled_date"]', '2026-04-15');
        await page.fill('input[name="scheduled_time"]', '10:00');
        await page.click('button:has-text("Schedule Post")');
        await expect(page.locator('[data-testid="post-scheduled"]')).toBeVisible();
    });

    test('should view scheduled posts', async ({ page }) => {
        await page.goto('/publish/schedule');
        await expect(page.locator('[data-testid="scheduled-list"]')).toBeVisible();
    });

    test('should edit scheduled post', async ({ page }) => {
        await page.goto('/publish/schedule');
        await page.click('[data-testid="scheduled-post"]:first-child');
        await page.click('button:has-text("Edit")');
        await page.fill('input[name="scheduled_time"]', '12:00');
        await page.click('button:has-text("Save")');
        await expect(page.locator('[data-testid="post-updated"]')).toBeVisible();
    });

    test('should cancel scheduled post', async ({ page }) => {
        await page.goto('/publish/schedule');
        await page.click('[data-testid="scheduled-post"]:first-child');
        await page.click('button:has-text("Cancel")');
        await expect(page.locator('[data-testid="post-cancelled"]')).toBeVisible();
    });
});

test.describe('Publishing - A/B Testing', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display A/B testing interface', async ({ page }) => {
        await page.goto('/publish/ab-testing');
        await expect(page.locator('[data-testid="ab-test-dashboard"]')).toBeVisible();
    });

    test('should create A/B test', async ({ page }) => {
        await page.goto('/publish/ab-testing');
        await page.click('button:has-text("Create Test")');
        await page.fill('input[name="video_url"]', 'https://example.com/video.mp4');
        await page.fill('input[name="title_a"]', 'Title A');
        await page.fill('input[name="title_b"]', 'Title B');
        await page.fill('input[name="traffic_split"]', '50');
        await page.click('button:has-text("Start Test")');
        await expect(page.locator('[data-testid="test-created"]')).toBeVisible();
    });

    test('should view test results', async ({ page }) => {
        await page.goto('/publish/ab-testing');
        await page.click('[data-testid="test-card"]:first-child');
        await expect(page.locator('[data-testid="test-results"]')).toBeVisible();
    });

    test('should declare winner', async ({ page }) => {
        await page.goto('/publish/ab-testing');
        await page.click('[data-testid="test-card"]:first-child');
        await page.click('button:has-text("Declare Winner")');
        await expect(page.locator('[data-testid="winner-declared"]')).toBeVisible();
    });
});
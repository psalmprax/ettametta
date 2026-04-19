import { test, expect } from '@playwright/test';

test.describe('Video Generation - Transform Existing Video', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display transformation form', async ({ page }) => {
        await page.goto('/creation');
        await expect(page.locator('input[name="source_url"]')).toBeVisible();
        await expect(page.locator('select[name="niche"]')).toBeVisible();
    });

    test('should transform video with face blur', async ({ page }) => {
        await page.goto('/creation');
        await page.fill('input[name="source_url"]', 'https://youtube.com/watch?v=test123');
        await page.selectOption('select[name="niche"]', 'Technology');
        await page.check('input[name="face_blur"]');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
    });

    test('should transform video with speed ramp', async ({ page }) => {
        await page.goto('/creation');
        await page.fill('input[name="source_url"]', 'https://youtube.com/watch?v=test456');
        await page.selectOption('select[name="niche"]', 'Motivation');
        await page.check('input[name="speed_ramp"]');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
    });

    test('should validate URL format', async ({ page }) => {
        await page.goto('/creation');
        await page.fill('input[name="source_url"]', 'invalid-url');
        await page.selectOption('select[name="niche"]', 'Technology');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="error-message"]')).toContainText(/valid url/i);
    });
});

test.describe('Video Generation - AI Generate from Text', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display AI generation interface', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await expect(page.locator('textarea[name="prompt"]')).toBeVisible();
        await expect(page.locator('select[name="engine"]')).toBeVisible();
    });

    test('should generate video with Lite4K engine', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await page.fill('textarea[name="prompt"]', 'A futuristic city with flying cars');
        await page.selectOption('select[name="engine"]', 'lite4k');
        await page.selectOption('select[name="style"]', 'Cinematic');
        await page.selectOption('select[name="aspect_ratio"]', '9:16');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="generation-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should generate video with LTX-Video engine', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await page.fill('textarea[name="prompt"]', 'Ocean waves at sunset');
        await page.selectOption('select[name="engine"]', 'ltx-video');
        await page.selectOption('select[name="style"]', 'Natural');
        await page.selectOption('select[name="aspect_ratio"]', '16:9');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="generation-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should generate video with HunyuanVideo engine', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await page.click('[data-testid="os-stack-card"]');
        await page.fill('textarea[name="prompt"]', 'Mountain landscape');
        await page.selectOption('select[name="engine"]', 'hunyuan');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="generation-started"]')).toBeVisible({ timeout: 30000 });
    });

    test('should show tier restriction for premium engines', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await page.fill('textarea[name="prompt"]', 'Test');
        await page.selectOption('select[name="engine"]', 'veo3');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="upgrade-prompt"]')).toBeVisible({ timeout: 10000 });
    });

    test('should validate prompt is not empty', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await page.fill('textarea[name="prompt"]', '');
        await page.click('button[type="submit"]');
        await expect(page.locator('[data-testid="error-message"]')).toContainText(/prompt/i);
    });
});

test.describe('Video Generation - Story Generate Narrative', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display storyboard interface', async ({ page }) => {
        await page.goto('/creation/storyboard');
        await expect(page.locator('textarea[name="story_prompt"]')).toBeVisible();
    });

    test('should generate storyboard from prompt', async ({ page }) => {
        await page.goto('/creation/storyboard');
        await page.fill('textarea[name="story_prompt"]', 'A hero journey through mystical lands');
        await page.click('button:has-text("Generate Storyboard")');
        await expect(page.locator('[data-testid="storyboard-frames"]')).toBeVisible({ timeout: 30000 });
    });

    test('should display storyboard frames', async ({ page }) => {
        await page.goto('/creation/storyboard');
        await page.fill('textarea[name="story_prompt"]', 'Adventure story');
        await page.click('button:has-text("Generate Storyboard")');
        await expect(page.locator('[data-testid="frame-1"]')).toBeVisible({ timeout: 30000 });
    });

    test('should edit individual frames', async ({ page }) => {
        await page.goto('/creation/storyboard');
        await page.fill('textarea[name="story_prompt"]', 'Test story');
        await page.click('button:has-text("Generate Storyboard")');
        await expect(page.locator('[data-testid="frame-1"]')).toBeVisible({ timeout: 30000 });
        await page.click('[data-testid="edit-frame-1"]');
        await expect(page.locator('[data-testid="frame-editor"]')).toBeVisible();
    });

    test('should generate video from storyboard', async ({ page }) => {
        await page.goto('/creation/storyboard');
        await page.fill('textarea[name="story_prompt"]', 'Simple story');
        await page.click('button:has-text("Generate Storyboard")');
        await expect(page.locator('[data-testid="storyboard-frames"]')).toBeVisible({ timeout: 30000 });
        await page.click('button:has-text("Generate Video")');
        await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
    });
});

test.describe('Video Generation - Test Drive Quick Preview', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display quick preview mode', async ({ page }) => {
        await page.goto('/creation/preview');
        await expect(page.locator('[data-testid="preview-mode"]')).toBeVisible();
    });

    test('should generate low-res preview', async ({ page }) => {
        await page.goto('/creation/preview');
        await page.fill('textarea[name="prompt"]', 'Quick test');
        await page.click('button:has-text("Generate Preview")');
        await expect(page.locator('[data-testid="preview-video"]')).toBeVisible({ timeout: 60000 });
    });

    test('should show preview immediately', async ({ page }) => {
        await page.goto('/creation/preview');
        await page.fill('textarea[name="prompt"]', 'Abstract shapes');
        await page.click('button:has-text("Generate Preview")');
        await expect(page.locator('video')).toBeVisible({ timeout: 60000 });
    });

    test('should upgrade to full quality', async ({ page }) => {
        await page.goto('/creation/preview');
        await page.fill('textarea[name="prompt"]', 'Test');
        await page.click('button:has-text("Generate Preview")');
        await expect(page.locator('[data-testid="preview-video"]')).toBeVisible({ timeout: 60000 });
        await page.click('button:has-text("Upgrade to Full Quality")');
        await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
    });
});
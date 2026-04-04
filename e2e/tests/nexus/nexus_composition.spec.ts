import { test, expect } from '@playwright/test';

test.describe('Nexus Composition - Assemble Video from Segments', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display video assembler interface', async ({ page }) => {
        await page.goto('/nexus/assemble');
        await expect(page.locator('[data-testid="segment-list"]')).toBeVisible();
    });

    test('should add video segments to timeline', async ({ page }) => {
        await page.goto('/nexus/assemble');
        await page.click('button:has-text("Add Segment")');
        await page.fill('input[name="segment_url"]', 'https://example.com/clip1.mp4');
        await page.click('button:has-text("Add to Timeline")');
        await expect(page.locator('[data-testid="timeline"]')).toContainText('clip1.mp4');
    });

    test('should reorder segments in timeline', async ({ page }) => {
        await page.goto('/nexus/assemble');
        await page.fill('input[name="segment_url"]', 'https://example.com/clip1.mp4');
        await page.click('button:has-text("Add to Timeline")');
        await page.fill('input[name="segment_url"]', 'https://example.com/clip2.mp4');
        await page.click('button:has-text("Add to Timeline")');
        await page.dragAndDrop('[data-testid="segment-2"]', '[data-testid="segment-1"]');
        await expect(page.locator('[data-testid="timeline"]')).toContainText(/clip2.*clip1/s);
    });

    test('should trim segment boundaries', async ({ page }) => {
        await page.goto('/nexus/assemble');
        await page.fill('input[name="segment_url"]', 'https://example.com/clip.mp4');
        await page.click('button:has-text("Add to Timeline")');
        await page.click('[data-testid="segment-1"]');
        await page.fill('input[name="start_time"]', '5');
        await page.fill('input[name="end_time"]', '30');
        await page.click('button:has-text("Trim")');
        await expect(page.locator('[data-testid="trimmed-segment"]')).toBeVisible();
    });

    test('should render final video', async ({ page }) => {
        await page.goto('/nexus/assemble');
        await page.fill('input[name="segment_url"]', 'https://example.com/clip.mp4');
        await page.click('button:has-text("Add to Timeline")');
        await page.click('button:has-text("Render Video")');
        await expect(page.locator('[data-testid="rendered-video"]')).toBeVisible({ timeout: 120000 });
    });
});

test.describe('Nexus Composition - Cinema Mode', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display cinema mode interface', async ({ page }) => {
        await page.goto('/nexus/cinema');
        await expect(page.locator('[data-testid="cinema-workspace"]')).toBeVisible();
    });

    test('should create autonomous project', async ({ page }) => {
        await page.goto('/nexus/cinema');
        await page.fill('textarea[name="description"]', 'Create an engaging tech tutorial');
        await page.click('button:has-text("Create Project")');
        await expect(page.locator('[data-testid="project-created"]')).toBeVisible({ timeout: 30000 });
    });

    test('should show AI-generated scenes', async ({ page }) => {
        await page.goto('/nexus/cinema');
        await page.fill('textarea[name="description"]', 'A day in the life of a developer');
        await page.click('button:has-text("Generate Scenes")');
        await expect(page.locator('[data-testid="scene-list"]')).toBeVisible({ timeout: 60000 });
    });

    test('should select scene for rendering', async ({ page }) => {
        await page.goto('/nexus/cinema');
        await page.fill('textarea[name="description"]', 'Test');
        await page.click('button:has-text("Generate Scenes")');
        await expect(page.locator('[data-testid="scene-1"]')).toBeVisible({ timeout: 60000 });
        await page.click('[data-testid="scene-1"]');
        await expect(page.locator('[data-testid="scene-detail"]')).toBeVisible();
    });
});

test.describe('Nexus Composition - Story Factory', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display story factory interface', async ({ page }) => {
        await page.goto('/nexus/story-factory');
        await expect(page.locator('[data-testid="story-workspace"]')).toBeVisible();
    });

    test('should create story from templates', async ({ page }) => {
        await page.goto('/nexus/story-factory');
        await page.click('[data-testid="template-card"]:first-child');
        await expect(page.locator('[data-testid="story-editor"]')).toBeVisible();
    });

    test('should generate AI story', async ({ page }) => {
        await page.goto('/nexus/story-factory');
        await page.fill('textarea[name="story_prompt"]', 'A hero saves the world');
        await page.click('button:has-text("Generate Story")');
        await expect(page.locator('[data-testid="generated-story"]')).toBeVisible({ timeout: 30000 });
    });

    test('should export story as video', async ({ page }) => {
        await page.goto('/nexus/story-factory');
        await page.fill('textarea[name="story_prompt"]', 'Test story');
        await page.click('button:has-text("Generate Story")');
        await expect(page.locator('[data-testid="generated-story"]')).toBeVisible({ timeout: 30000 });
        await page.click('button:has-text("Export as Video")');
        await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
    });
});

test.describe('Nexus Composition - Blueprint Templates', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should display template library', async ({ page }) => {
        await page.goto('/nexus/blueprints');
        await expect(page.locator('[data-testid="template-library"]')).toBeVisible();
    });

    test('should filter templates by category', async ({ page }) => {
        await page.goto('/nexus/blueprints');
        await page.click('text=Education');
        await expect(page.locator('[data-testid="template-grid"]')).toContainText(/education/i);
    });

    test('should apply template to project', async ({ page }) => {
        await page.goto('/nexus/blueprints');
        await page.click('[data-testid="template-card"]:first-child');
        await page.click('button:has-text("Apply Template")');
        await expect(page.locator('[data-testid="project-applied"]')).toBeVisible();
    });

    test('should customize template', async ({ page }) => {
        await page.goto('/nexus/blueprints');
        await page.click('[data-testid="template-card"]:first-child');
        await page.fill('input[name="title"]', 'My Custom Title');
        await page.click('button:has-text("Save")');
        await expect(page.locator('[data-testid="template-saved"]')).toBeVisible();
    });
});
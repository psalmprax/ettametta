import { test, expect } from '@playwright/test';

test.describe('Publishing Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should connect YouTube account', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="connect-youtube"]');
    
    await expect(page).toHaveURL(/youtube.*oauth/);
  });

  test('should connect TikTok account', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="connect-tiktok"]');
    
    await expect(page).toHaveURL(/tiktok.*oauth/);
  });

  test('should view connected accounts', async ({ page }) => {
    await page.goto('/publishing');
    
    await expect(page.locator('[data-testid="connected-accounts"]')).toBeVisible();
  });

  test('should upload video to YouTube', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="upload-button"]');
    
    await page.fill('input[name="title"]', 'Test Video Upload');
    await page.fill('textarea[name="description"]', 'Test description');
    await page.fill('input[name="tags"]', 'test, viral');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-video.mp4',
      mimeType: 'video/mp4',
      buffer: Buffer.from('fake-video-data')
    });
    
    await page.click('button:has-text("Publish")');
    
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();
  });

  test('should schedule a post', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="schedule-button"]');
    
    await page.fill('input[name="title"]', 'Scheduled Video');
    await page.selectOption('select[name="platform"]', 'YouTube');
    
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);
    await page.fill('input[name="scheduleDate"]', futureDate.toISOString().split('T')[0]);
    
    await page.click('button:has-text("Schedule")');
    
    await expect(page.locator('[data-testid="scheduled-post"]')).toBeVisible();
  });

  test('should view publishing history', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="history-tab"]');
    
    await expect(page.locator('[data-testid="publish-history"]')).toBeVisible();
  });

  test('should retry failed upload', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="failed-upload"]');
    await page.click('[data-testid="retry-button"]');
    
    await expect(page.locator('[data-testid="retry-progress"]')).toBeVisible();
  });
});

test.describe('Multi-Platform Publishing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should post to multiple platforms at once', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.click('[data-testid="multi-post-button"]');
    
    await page.fill('input[name="title"]', 'Multi-Platform Post');
    
    await page.check('input[name="platform-youtube"]');
    await page.check('input[name="platform-tiktok"]');
    await page.check('input[name="platform-instagram"]');
    
    await page.click('button:has-text("Publish All")');
    
    await expect(page.locator('[data-testid="multi-post-success"]')).toBeVisible();
  });
});
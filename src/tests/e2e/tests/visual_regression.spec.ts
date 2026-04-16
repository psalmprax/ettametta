import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('Dashboard page visual regression', async ({ page }) => {
    await page.goto('/');
    
    // Wait for content to load
    await page.waitForSelector('[data-testid="dashboard"]');
    
    // Take screenshot and compare
    await expect(page).toHaveScreenshot('dashboard.png', {
      maxDiffPixelRatio: 0.01,
    });
  });

  test('Discovery page visual regression', async ({ page }) => {
    await page.goto('/discovery');
    
    await page.waitForSelector('[data-testid="discovery-content"]');
    
    await expect(page).toHaveScreenshot('discovery.png', {
      maxDiffPixelRatio: 0.01,
    });
  });

  test('Analytics page visual regression', async ({ page }) => {
    await page.goto('/analytics');
    
    await page.waitForSelector('[data-testid="analytics-dashboard"]');
    
    await expect(page).toHaveScreenshot('analytics.png', {
      maxDiffPixelRatio: 0.01,
    });
  });

  test('Settings page visual regression', async ({ page }) => {
    await page.goto('/settings');
    
    await page.waitForSelector('[data-testid="settings-panel"]');
    
    await expect(page).toHaveScreenshot('settings.png', {
      maxDiffPixelRatio: 0.01,
    });
  });

  test('Publishing page visual regression', async ({ page }) => {
    await page.goto('/publishing');
    
    await page.waitForSelector('[data-testid="publishing-panel"]');
    
    await expect(page).toHaveScreenshot('publishing.png', {
      maxDiffPixelRatio: 0.01,
    });
  });

  test('Creation page visual regression', async ({ page }) => {
    await page.goto('/creation');
    
    await page.waitForSelector('[data-testid="creation-panel"]');
    
    await expect(page).toHaveScreenshot('creation.png', {
      maxDiffPixelRatio: 0.01,
    });
  });
});

test.describe('Mobile Visual Regression', () => {
  test('Mobile dashboard visual regression', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone X
    
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
    
    await page.waitForSelector('[data-testid="dashboard"]');
    
    await expect(page).toHaveScreenshot('mobile-dashboard.png', {
      maxDiffPixelRatio: 0.02,
    });
  });
});
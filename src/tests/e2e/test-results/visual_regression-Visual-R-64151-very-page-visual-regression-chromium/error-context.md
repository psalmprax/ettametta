# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: visual_regression.spec.ts >> Visual Regression Tests >> Discovery page visual regression
- Location: tests/visual_regression.spec.ts:25:7

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    4 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Visual Regression Tests', () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     // Login before each test
  6  |     await page.goto('/login');
> 7  |     await page.fill('input[name="email"]', 'test@example.com');
     |                ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  8  |     await page.fill('input[name="password"]', 'testpassword');
  9  |     await page.click('button[type="submit"]');
  10 |     await page.waitForURL('/');
  11 |   });
  12 | 
  13 |   test('Dashboard page visual regression', async ({ page }) => {
  14 |     await page.goto('/');
  15 |     
  16 |     // Wait for content to load
  17 |     await page.waitForSelector('[data-testid="dashboard"]');
  18 |     
  19 |     // Take screenshot and compare
  20 |     await expect(page).toHaveScreenshot('dashboard.png', {
  21 |       maxDiffPixelRatio: 0.01,
  22 |     });
  23 |   });
  24 | 
  25 |   test('Discovery page visual regression', async ({ page }) => {
  26 |     await page.goto('/discovery');
  27 |     
  28 |     await page.waitForSelector('[data-testid="discovery-content"]');
  29 |     
  30 |     await expect(page).toHaveScreenshot('discovery.png', {
  31 |       maxDiffPixelRatio: 0.01,
  32 |     });
  33 |   });
  34 | 
  35 |   test('Analytics page visual regression', async ({ page }) => {
  36 |     await page.goto('/analytics');
  37 |     
  38 |     await page.waitForSelector('[data-testid="analytics-dashboard"]');
  39 |     
  40 |     await expect(page).toHaveScreenshot('analytics.png', {
  41 |       maxDiffPixelRatio: 0.01,
  42 |     });
  43 |   });
  44 | 
  45 |   test('Settings page visual regression', async ({ page }) => {
  46 |     await page.goto('/settings');
  47 |     
  48 |     await page.waitForSelector('[data-testid="settings-panel"]');
  49 |     
  50 |     await expect(page).toHaveScreenshot('settings.png', {
  51 |       maxDiffPixelRatio: 0.01,
  52 |     });
  53 |   });
  54 | 
  55 |   test('Publishing page visual regression', async ({ page }) => {
  56 |     await page.goto('/publishing');
  57 |     
  58 |     await page.waitForSelector('[data-testid="publishing-panel"]');
  59 |     
  60 |     await expect(page).toHaveScreenshot('publishing.png', {
  61 |       maxDiffPixelRatio: 0.01,
  62 |     });
  63 |   });
  64 | 
  65 |   test('Creation page visual regression', async ({ page }) => {
  66 |     await page.goto('/creation');
  67 |     
  68 |     await page.waitForSelector('[data-testid="creation-panel"]');
  69 |     
  70 |     await expect(page).toHaveScreenshot('creation.png', {
  71 |       maxDiffPixelRatio: 0.01,
  72 |     });
  73 |   });
  74 | });
  75 | 
  76 | test.describe('Mobile Visual Regression', () => {
  77 |   test('Mobile dashboard visual regression', async ({ page }) => {
  78 |     await page.setViewportSize({ width: 375, height: 812 }); // iPhone X
  79 |     
  80 |     await page.goto('/login');
  81 |     await page.fill('input[name="email"]', 'test@example.com');
  82 |     await page.fill('input[name="password"]', 'testpassword');
  83 |     await page.click('button[type="submit"]');
  84 |     await page.waitForURL('/');
  85 |     
  86 |     await page.waitForSelector('[data-testid="dashboard"]');
  87 |     
  88 |     await expect(page).toHaveScreenshot('mobile-dashboard.png', {
  89 |       maxDiffPixelRatio: 0.02,
  90 |     });
  91 |   });
  92 | });
```
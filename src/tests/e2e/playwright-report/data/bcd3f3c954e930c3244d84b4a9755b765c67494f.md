# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creation/video_creation.spec.ts >> Video Transformation >> should navigate to creation page
- Location: tests/creation/video_creation.spec.ts:19:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    2 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"
    - waiting for" http://localhost:3000/login" navigation to finish...

```

# Test source

```ts
  1   | /**
  2   |  * Video Creation E2E Tests
  3   |  * ======================
  4   |  * End-to-end tests for video transformation and generation
  5   |  */
  6   | 
  7   | import { test, expect } from '@playwright/test';
  8   | 
  9   | test.describe('Video Transformation', () => {
  10  |     test.beforeEach(async ({ page }) => {
  11  |         // Login first
  12  |         await page.goto('/login');
> 13  |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  14  |         await page.fill('input[name="password"]', 'testpassword');
  15  |         await page.click('button[type="submit"]');
  16  |         await page.waitForURL('/');
  17  |     });
  18  | 
  19  |     test('should navigate to creation page', async ({ page }) => {
  20  |         await page.goto('/creation');
  21  |         await expect(page.locator('h1')).toContainText(/creation/i);
  22  |     });
  23  | 
  24  |     test('should display transformation form', async ({ page }) => {
  25  |         await page.goto('/creation');
  26  |         await expect(page.locator('input[name="source_uri"]')).toBeVisible();
  27  |         await expect(page.locator('select[name="niche"]')).toBeVisible();
  28  |         await expect(page.locator('select[name="platform"]')).toBeVisible();
  29  |         await expect(page.locator('button[type="submit"]')).toBeVisible();
  30  |     });
  31  | 
  32  |     test('should submit transformation request', async ({ page }) => {
  33  |         await page.goto('/creation');
  34  | 
  35  |         await page.fill('input[name="source_uri"]', 'https://youtube.com/watch?v=test');
  36  |         await page.selectOption('select[name="niche"]', 'Technology');
  37  |         await page.selectOption('select[name="platform"]', 'YouTube Shorts');
  38  |         await page.selectOption('select[name="quality_tier"]', 'standard');
  39  | 
  40  |         await page.click('button[type="submit"]');
  41  | 
  42  |         // Should show success or job created
  43  |         await expect(page.locator('[data-testid="success-message"], [data-testid="job-created"]')).toBeVisible({ timeout: 10000 });
  44  |     });
  45  | 
  46  |     test('should show job in progress', async ({ page }) => {
  47  |         await page.goto('/creation');
  48  | 
  49  |         // Submit a job
  50  |         await page.fill('input[name="source_uri"]', 'https://youtube.com/watch?v=test2');
  51  |         await page.selectOption('select[name="niche"]', 'Motivation');
  52  |         await page.click('button[type="submit"]');
  53  | 
  54  |         // Navigate to jobs
  55  |         await page.goto('/creation');
  56  |         await expect(page.locator('[data-testid="job-list"]')).toBeVisible();
  57  |     });
  58  | });
  59  | 
  60  | test.describe('AI Video Generation', () => {
  61  |     test.beforeEach(async ({ page }) => {
  62  |         await page.goto('/login');
  63  |         await page.fill('input[name="email"]', 'test@example.com');
  64  |         await page.fill('input[name="password"]', 'testpassword');
  65  |         await page.click('button[type="submit"]');
  66  |         await page.waitForURL('/');
  67  |     });
  68  | 
  69  |     test('should display generation options', async ({ page }) => {
  70  |         await page.goto('/creation');
  71  | 
  72  |         // Switch to generation tab
  73  |         await page.click('text=AI Generation');
  74  | 
  75  |         await expect(page.locator('textarea[name="prompt"]')).toBeVisible();
  76  |         await expect(page.locator('select[name="engine"]')).toBeVisible();
  77  |         await expect(page.locator('select[name="style"]')).toBeVisible();
  78  |         await expect(page.locator('select[name="aspect_ratio"]')).toBeVisible();
  79  |     });
  80  | 
  81  |     test('should generate with lite4k engine', async ({ page }) => {
  82  |         await page.goto('/creation');
  83  | 
  84  |         // Switch to generation tab
  85  |         await page.click('text=AI Generation');
  86  | 
  87  |         await page.fill('textarea[name="prompt"]', 'A futuristic city with flying cars');
  88  |         await page.selectOption('select[name="engine"]', 'lite4k');
  89  |         await page.selectOption('select[name="style"]', 'Cinematic');
  90  |         await page.selectOption('select[name="aspect_ratio"]', '9:16');
  91  | 
  92  |         await page.click('button[type="submit"]');
  93  | 
  94  |         // Should start generation
  95  |         await expect(page.locator('[data-testid="generation-started"], [data-testid="job-created"]')).toBeVisible({ timeout: 10000 });
  96  |     });
  97  | 
  98  |     test('should generate with ltx-video engine', async ({ page }) => {
  99  |         await page.goto('/creation');
  100 | 
  101 |         await page.click('text=AI Generation');
  102 | 
  103 |         await page.fill('textarea[name="prompt"]', 'Ocean waves at sunset');
  104 |         await page.selectOption('select[name="engine"]', 'ltx-video');
  105 |         await page.selectOption('select[name="style"]', 'Natural');
  106 |         await page.selectOption('select[name="aspect_ratio"]', '16:9');
  107 | 
  108 |         await page.click('button[type="submit"]');
  109 | 
  110 |         await expect(page.locator('[data-testid="generation-started"], [data-testid="job-created"]')).toBeVisible({ timeout: 10000 });
  111 |     });
  112 | 
  113 |     test('should show tier restriction for premium engines', async ({ page }) => {
```
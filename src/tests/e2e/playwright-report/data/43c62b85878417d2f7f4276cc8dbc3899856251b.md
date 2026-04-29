# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: discovery_flow.spec.ts >> Discovery to Video Pipeline >> should flow from discovery search to video creation
- Location: tests/discovery_flow.spec.ts:13:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Discovery to Video Pipeline', () => {
  4  |     test.beforeEach(async ({ page }) => {
  5  |         // Login
> 6  |         await page.goto('/login');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  7  |         await page.fill('input[name="email"]', 'test@example.com');
  8  |         await page.fill('input[name="password"]', 'testpassword');
  9  |         await page.click('button[type="submit"]');
  10 |         await page.waitForURL('/');
  11 |     });
  12 | 
  13 |     test('should flow from discovery search to video creation', async ({ page }) => {
  14 |         // 1. Go to Discovery
  15 |         await page.goto('/discovery');
  16 |         await expect(page.locator('h1')).toContainText(/discovery/i);
  17 | 
  18 |         // 2. Perform a search
  19 |         await page.fill('[data-testid="discovery-search-input"]', 'AI Automation');
  20 |         await page.keyboard.press('Enter');
  21 | 
  22 |         // 3. Wait for candidates and click "Deep Analysis" on the first one
  23 |         const firstCandidate = page.locator('[data-testid="candidate-card"]').first();
  24 |         await expect(firstCandidate).toBeVisible({ timeout: 15000 });
  25 |         
  26 |         await firstCandidate.locator('button:has-text("Deep Scan"), button:has-text("Analyze")').click();
  27 | 
  28 |         // 4. Verify AI Analysis modal/view opens
  29 |         await expect(page.locator('[data-testid="analysis-modal"]')).toBeVisible();
  30 |         await expect(page.locator('[data-testid="viral-score"]')).toBeVisible();
  31 | 
  32 |         // 5. Click "Transform to Video"
  33 |         await page.click('button:has-text("Transform to Video")');
  34 | 
  35 |         // 6. Should be redirected to /creation with the URL pre-filled
  36 |         await page.waitForURL(/\/creation/);
  37 |         const urlInput = page.locator('input[name="source_uri"]');
  38 |         await expect(urlInput).not.toHaveValue('');
  39 |         
  40 |         // 7. Verify we can select a platform and submit
  41 |         await page.selectOption('select[name="platform"]', 'TikTok');
  42 |         await page.click('button[type="submit"]');
  43 | 
  44 |         // 8. Confirm job is created
  45 |         await expect(page.locator('[data-testid="job-created"], [data-testid="success-message"]')).toBeVisible();
  46 |     });
  47 | });
  48 | 
```
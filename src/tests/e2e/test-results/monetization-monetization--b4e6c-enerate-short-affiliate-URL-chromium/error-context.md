# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: monetization/monetization.spec.ts >> Monetization - Affiliate Links >> should generate short affiliate URL
- Location: tests/monetization/monetization.spec.ts:26:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    5 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Monetization - Affiliate Links', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
> 6   |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  7   |         await page.fill('input[name="password"]', 'testpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display affiliate links interface', async ({ page }) => {
  13  |         await page.goto('/monetization/affiliate');
  14  |         await expect(page.locator('[data-testid="affiliate-dashboard"]')).toBeVisible();
  15  |     });
  16  | 
  17  |     test('should add affiliate link', async ({ page }) => {
  18  |         await page.goto('/monetization/affiliate');
  19  |         await page.click('button:has-text("Add Link")');
  20  |         await page.fill('input[name="product_url"]', 'https://amazon.com/product/123');
  21  |         await page.fill('input[name="product_name"]', 'Tech Gadget');
  22  |         await page.click('button:has-text("Save")');
  23  |         await expect(page.locator('[data-testid="link-created"]')).toBeVisible();
  24  |     });
  25  | 
  26  |     test('should generate short affiliate URL', async ({ page }) => {
  27  |         await page.goto('/monetization/affiliate');
  28  |         await page.click('button:has-text("Add Link")');
  29  |         await page.fill('input[name="product_url"]', 'https://amazon.com/product/123');
  30  |         await page.click('button:has-text("Generate Short URL")');
  31  |         await expect(page.locator('[data-testid="short-url"]')).toBeVisible();
  32  |     });
  33  | 
  34  |     test('should track link clicks', async ({ page }) => {
  35  |         await page.goto('/monetization/affiliate');
  36  |         await expect(page.locator('[data-testid="click-stats"]')).toBeVisible();
  37  |     });
  38  | });
  39  | 
  40  | test.describe('Monetization - Revenue Tracking', () => {
  41  |     test.beforeEach(async ({ page }) => {
  42  |         await page.goto('/login');
  43  |         await page.fill('input[name="email"]', 'test@example.com');
  44  |         await page.fill('input[name="password"]', 'testpassword');
  45  |         await page.click('button[type="submit"]');
  46  |         await page.waitForURL('/');
  47  |     });
  48  | 
  49  |     test('should display revenue dashboard', async ({ page }) => {
  50  |         await page.goto('/monetization/revenue');
  51  |         await expect(page.locator('[data-testid="revenue-dashboard"]')).toBeVisible();
  52  |     });
  53  | 
  54  |     test('should show total earnings', async ({ page }) => {
  55  |         await page.goto('/monetization/revenue');
  56  |         await expect(page.locator('[data-testid="total-earnings"]')).toBeVisible();
  57  |     });
  58  | 
  59  |     test('should display revenue by source', async ({ page }) => {
  60  |         await page.goto('/monetization/revenue');
  61  |         await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
  62  |     });
  63  | 
  64  |     test('should export revenue report', async ({ page }) => {
  65  |         await page.goto('/monetization/revenue');
  66  |         await page.click('button:has-text("Export Report")');
  67  |         await expect(page.locator('[data-testid="report-downloaded"]')).toBeVisible();
  68  |     });
  69  | });
  70  | 
  71  | test.describe('Monetization - Empire Building', () => {
  72  |     test.beforeEach(async ({ page }) => {
  73  |         await page.goto('/login');
  74  |         await page.fill('input[name="email"]', 'test@example.com');
  75  |         await page.fill('input[name="password"]', 'testpassword');
  76  |         await page.click('button[type="submit"]');
  77  |         await page.waitForURL('/');
  78  |     });
  79  | 
  80  |     test('should display empire dashboard', async ({ page }) => {
  81  |         await page.goto('/monetization/empire');
  82  |         await expect(page.locator('[data-testid="empire-dashboard"]')).toBeVisible();
  83  |     });
  84  | 
  85  |     test('should create new income stream', async ({ page }) => {
  86  |         await page.goto('/monetization/empire');
  87  |         await page.click('button:has-text("Add Income Stream")');
  88  |         await page.selectOption('select[name="stream_type"]', 'affiliate');
  89  |         await page.fill('input[name="name"]', 'Amazon Associates');
  90  |         await page.click('button:has-text("Create")');
  91  |         await expect(page.locator('[data-testid="stream-created"]')).toBeVisible();
  92  |     });
  93  | 
  94  |     test('should track empire health', async ({ page }) => {
  95  |         await page.goto('/monetization/empire');
  96  |         await expect(page.locator('[data-testid="empire-health"]')).toBeVisible();
  97  |     });
  98  | 
  99  |     test('should get diversification suggestions', async ({ page }) => {
  100 |         await page.goto('/monetization/empire');
  101 |         await page.click('button:has-text("Get Suggestions")');
  102 |         await expect(page.locator('[data-testid="suggestions"]')).toBeVisible({ timeout: 30000 });
  103 |     });
  104 | });
  105 | 
  106 | test.describe('Monetization - Auto Merch', () => {
```
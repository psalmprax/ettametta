# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creation/video_generation.spec.ts >> Video Generation - Transform Existing Video >> should transform video with speed ramp
- Location: tests/creation/video_generation.spec.ts:27:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - generic [ref=e6]:
      - generic [ref=e8]:
        - img [ref=e10]
        - generic [ref=e13]:
          - heading "Sign In" [level=1] [ref=e14]
          - paragraph [ref=e15]: Welcome back to Ettametta
      - generic [ref=e16]:
        - generic [ref=e17]:
          - generic [ref=e18]: Username
          - generic [ref=e19]:
            - textbox "Enter your username" [ref=e20]
            - img [ref=e22]
        - generic [ref=e25]:
          - generic [ref=e26]: Password
          - generic [ref=e27]:
            - textbox "Enter your password" [ref=e28]
            - img [ref=e30]
        - generic [ref=e34] [cursor=pointer]:
          - checkbox "Remember me" [ref=e35]
          - generic [ref=e36]: Remember me
        - button "Sign In" [ref=e37]:
          - generic [ref=e38]: Sign In
      - paragraph [ref=e40]:
        - text: Don't have an account?
        - link "Create account" [ref=e41] [cursor=pointer]:
          - /url: /register
    - region "Notifications alt+T"
  - button "Open Next.js Dev Tools" [ref=e47] [cursor=pointer]:
    - img [ref=e48]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Video Generation - Transform Existing Video', () => {
  4   |     test.beforeEach(async ({ page }) => {
> 5   |         await page.goto('/login');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  6   |         await page.fill('input[name="email"]', 'test@example.com');
  7   |         await page.fill('input[name="password"]', 'testpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display transformation form', async ({ page }) => {
  13  |         await page.goto('/creation');
  14  |         await expect(page.locator('input[name="source_uri"]')).toBeVisible();
  15  |         await expect(page.locator('select[name="niche"]')).toBeVisible();
  16  |     });
  17  | 
  18  |     test('should transform video with face blur', async ({ page }) => {
  19  |         await page.goto('/creation');
  20  |         await page.fill('input[name="source_uri"]', 'https://youtube.com/watch?v=test123');
  21  |         await page.selectOption('select[name="niche"]', 'Technology');
  22  |         await page.check('input[name="face_blur"]');
  23  |         await page.click('button[type="submit"]');
  24  |         await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
  25  |     });
  26  | 
  27  |     test('should transform video with speed ramp', async ({ page }) => {
  28  |         await page.goto('/creation');
  29  |         await page.fill('input[name="source_uri"]', 'https://youtube.com/watch?v=test456');
  30  |         await page.selectOption('select[name="niche"]', 'Motivation');
  31  |         await page.check('input[name="speed_ramp"]');
  32  |         await page.click('button[type="submit"]');
  33  |         await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
  34  |     });
  35  | 
  36  |     test('should validate URL format', async ({ page }) => {
  37  |         await page.goto('/creation');
  38  |         await page.fill('input[name="source_uri"]', 'invalid-url');
  39  |         await page.selectOption('select[name="niche"]', 'Technology');
  40  |         await page.click('button[type="submit"]');
  41  |         await expect(page.locator('[data-testid="error-message"]')).toContainText(/valid url/i);
  42  |     });
  43  | });
  44  | 
  45  | test.describe('Video Generation - AI Generate from Text', () => {
  46  |     test.beforeEach(async ({ page }) => {
  47  |         await page.goto('/login');
  48  |         await page.fill('input[name="email"]', 'test@example.com');
  49  |         await page.fill('input[name="password"]', 'testpassword');
  50  |         await page.click('button[type="submit"]');
  51  |         await page.waitForURL('/');
  52  |     });
  53  | 
  54  |     test('should display AI generation interface', async ({ page }) => {
  55  |         await page.goto('/creation');
  56  |         await page.click('text=AI Generation');
  57  |         await expect(page.locator('textarea[name="prompt"]')).toBeVisible();
  58  |         await expect(page.locator('select[name="engine"]')).toBeVisible();
  59  |     });
  60  | 
  61  |     test('should generate video with Lite4K engine', async ({ page }) => {
  62  |         await page.goto('/creation');
  63  |         await page.click('text=AI Generation');
  64  |         await page.fill('textarea[name="prompt"]', 'A futuristic city with flying cars');
  65  |         await page.selectOption('select[name="engine"]', 'lite4k');
  66  |         await page.selectOption('select[name="style"]', 'Cinematic');
  67  |         await page.selectOption('select[name="aspect_ratio"]', '9:16');
  68  |         await page.click('button[type="submit"]');
  69  |         await expect(page.locator('[data-testid="generation-started"]')).toBeVisible({ timeout: 30000 });
  70  |     });
  71  | 
  72  |     test('should generate video with LTX-Video engine', async ({ page }) => {
  73  |         await page.goto('/creation');
  74  |         await page.click('text=AI Generation');
  75  |         await page.fill('textarea[name="prompt"]', 'Ocean waves at sunset');
  76  |         await page.selectOption('select[name="engine"]', 'ltx-video');
  77  |         await page.selectOption('select[name="style"]', 'Natural');
  78  |         await page.selectOption('select[name="aspect_ratio"]', '16:9');
  79  |         await page.click('button[type="submit"]');
  80  |         await expect(page.locator('[data-testid="generation-started"]')).toBeVisible({ timeout: 30000 });
  81  |     });
  82  | 
  83  |     test('should generate video with HunyuanVideo engine', async ({ page }) => {
  84  |         await page.goto('/creation');
  85  |         await page.click('text=AI Generation');
  86  |         await page.click('[data-testid="os-stack-card"]');
  87  |         await page.fill('textarea[name="prompt"]', 'Mountain landscape');
  88  |         await page.selectOption('select[name="engine"]', 'hunyuan');
  89  |         await page.click('button[type="submit"]');
  90  |         await expect(page.locator('[data-testid="generation-started"]')).toBeVisible({ timeout: 30000 });
  91  |     });
  92  | 
  93  |     test('should show tier restriction for premium engines', async ({ page }) => {
  94  |         await page.goto('/creation');
  95  |         await page.click('text=AI Generation');
  96  |         await page.fill('textarea[name="prompt"]', 'Test');
  97  |         await page.selectOption('select[name="engine"]', 'veo3');
  98  |         await page.click('button[type="submit"]');
  99  |         await expect(page.locator('[data-testid="upgrade-prompt"]')).toBeVisible({ timeout: 10000 });
  100 |     });
  101 | 
  102 |     test('should validate prompt is not empty', async ({ page }) => {
  103 |         await page.goto('/creation');
  104 |         await page.click('text=AI Generation');
  105 |         await page.fill('textarea[name="prompt"]', '');
```
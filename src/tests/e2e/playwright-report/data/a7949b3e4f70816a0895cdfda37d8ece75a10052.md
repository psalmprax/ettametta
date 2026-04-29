# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: publishing/publishing.spec.ts >> Publishing - YouTube Upload >> should upload video to YouTube
- Location: tests/publishing/publishing.spec.ts:22:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    7 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Page snapshot

```yaml
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
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Publishing - YouTube Upload', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
> 6   |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  7   |         await page.fill('input[name="password"]', 'testpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display YouTube upload interface', async ({ page }) => {
  13  |         await page.goto('/publish/youtube');
  14  |         await expect(page.locator('[data-testid="youtube-upload"]')).toBeVisible();
  15  |     });
  16  | 
  17  |     test('should require YouTube OAuth connection', async ({ page }) => {
  18  |         await page.goto('/publish/youtube');
  19  |         await expect(page.locator('[data-testid="connect-youtube-prompt"]')).toBeVisible();
  20  |     });
  21  | 
  22  |     test('should upload video to YouTube', async ({ page }) => {
  23  |         await page.goto('/publish/youtube');
  24  |         // Assume OAuth is connected
  25  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  26  |         await page.fill('input[name="title"]', 'My Test Video');
  27  |         await page.fill('textarea[name="description"]', 'Test description');
  28  |         await page.click('button:has-text("Upload to YouTube")');
  29  |         await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
  30  |     });
  31  | 
  32  |     test('should set video privacy', async ({ page }) => {
  33  |         await page.goto('/publish/youtube');
  34  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  35  |         await page.selectOption('select[name="privacy"]', 'private');
  36  |         await page.click('button:has-text("Upload to YouTube")');
  37  |         await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
  38  |     });
  39  | 
  40  |     test('should add tags to video', async ({ page }) => {
  41  |         await page.goto('/publish/youtube');
  42  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  43  |         await page.fill('input[name="tags"]', 'viral,trending,ai');
  44  |         await page.click('button:has-text("Upload to YouTube")');
  45  |         await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
  46  |     });
  47  | 
  48  |     test('should schedule video publication', async ({ page }) => {
  49  |         await page.goto('/publish/youtube');
  50  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  51  |         await page.fill('input[name="scheduled_time"]', '2026-04-15T10:00');
  52  |         await page.click('button:has-text("Schedule")');
  53  |         await expect(page.locator('[data-testid="scheduled"]')).toBeVisible();
  54  |     });
  55  | });
  56  | 
  57  | test.describe('Publishing - TikTok Upload', () => {
  58  |     test.beforeEach(async ({ page }) => {
  59  |         await page.goto('/login');
  60  |         await page.fill('input[name="email"]', 'test@example.com');
  61  |         await page.fill('input[name="password"]', 'testpassword');
  62  |         await page.click('button[type="submit"]');
  63  |         await page.waitForURL('/');
  64  |     });
  65  | 
  66  |     test('should display TikTok upload interface', async ({ page }) => {
  67  |         await page.goto('/publish/tiktok');
  68  |         await expect(page.locator('[data-testid="tiktok-upload"]')).toBeVisible();
  69  |     });
  70  | 
  71  |     test('should require TikTok OAuth connection', async ({ page }) => {
  72  |         await page.goto('/publish/tiktok');
  73  |         await expect(page.locator('[data-testid="connect-tiktok-prompt"]')).toBeVisible();
  74  |     });
  75  | 
  76  |     test('should upload video to TikTok', async ({ page }) => {
  77  |         await page.goto('/publish/tiktok');
  78  |         // Assume OAuth is connected
  79  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  80  |         await page.fill('input[name="caption"]', 'Check this out! #viral #fyp');
  81  |         await page.click('button:has-text("Upload to TikTok")');
  82  |         await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
  83  |     });
  84  | 
  85  |     test('should add hashtags', async ({ page }) => {
  86  |         await page.goto('/publish/tiktok');
  87  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  88  |         await page.fill('input[name="hashtags"]', '#viral #trending #fyp');
  89  |         await page.click('button:has-text("Upload to TikTok")');
  90  |         await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
  91  |     });
  92  | 
  93  |     test('should set cover image', async ({ page }) => {
  94  |         await page.goto('/publish/tiktok');
  95  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  96  |         await page.fill('input[name="cover_url"]', 'https://example.com/cover.jpg');
  97  |         await page.click('button:has-text("Upload to TikTok")');
  98  |         await expect(page.locator('[data-testid="upload-started"]')).toBeVisible({ timeout: 30000 });
  99  |     });
  100 | });
  101 | 
  102 | test.describe('Publishing - Schedule Posts', () => {
  103 |     test.beforeEach(async ({ page }) => {
  104 |         await page.goto('/login');
  105 |         await page.fill('input[name="email"]', 'test@example.com');
  106 |         await page.fill('input[name="password"]', 'testpassword');
```
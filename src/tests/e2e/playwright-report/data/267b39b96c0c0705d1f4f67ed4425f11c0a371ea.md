# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: publishing_flow.spec.ts >> Publishing Flow >> should view connected accounts
- Location: tests/publishing_flow.spec.ts:28:7

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    6 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

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
  3   | test.describe('Publishing Flow', () => {
  4   |   test.beforeEach(async ({ page }) => {
  5   |     await page.goto('/login');
> 6   |     await page.fill('input[name="email"]', 'test@example.com');
      |                ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  7   |     await page.fill('input[name="password"]', 'testpassword');
  8   |     await page.click('button[type="submit"]');
  9   |     await page.waitForURL('/');
  10  |   });
  11  | 
  12  |   test('should connect YouTube account', async ({ page }) => {
  13  |     await page.goto('/publishing');
  14  |     
  15  |     await page.click('[data-testid="connect-youtube"]');
  16  |     
  17  |     await expect(page).toHaveURL(/youtube.*oauth/);
  18  |   });
  19  | 
  20  |   test('should connect TikTok account', async ({ page }) => {
  21  |     await page.goto('/publishing');
  22  |     
  23  |     await page.click('[data-testid="connect-tiktok"]');
  24  |     
  25  |     await expect(page).toHaveURL(/tiktok.*oauth/);
  26  |   });
  27  | 
  28  |   test('should view connected accounts', async ({ page }) => {
  29  |     await page.goto('/publishing');
  30  |     
  31  |     await expect(page.locator('[data-testid="connected-accounts"]')).toBeVisible();
  32  |   });
  33  | 
  34  |   test('should upload video to YouTube', async ({ page }) => {
  35  |     await page.goto('/publishing');
  36  |     
  37  |     await page.click('[data-testid="upload-button"]');
  38  |     
  39  |     await page.fill('input[name="title"]', 'Test Video Upload');
  40  |     await page.fill('textarea[name="description"]', 'Test description');
  41  |     await page.fill('input[name="tags"]', 'test, viral');
  42  |     
  43  |     const fileInput = page.locator('input[type="file"]');
  44  |     await fileInput.setInputFiles({
  45  |       name: 'test-video.mp4',
  46  |       mimeType: 'video/mp4',
  47  |       buffer: Buffer.from('fake-video-data')
  48  |     });
  49  |     
  50  |     await page.click('button:has-text("Publish")');
  51  |     
  52  |     await expect(page.locator('[data-testid="upload-success"]')).toBeVisible();
  53  |   });
  54  | 
  55  |   test('should schedule a post', async ({ page }) => {
  56  |     await page.goto('/publishing');
  57  |     
  58  |     await page.click('[data-testid="schedule-button"]');
  59  |     
  60  |     await page.fill('input[name="title"]', 'Scheduled Video');
  61  |     await page.selectOption('select[name="platform"]', 'YouTube');
  62  |     
  63  |     const futureDate = new Date();
  64  |     futureDate.setDate(futureDate.getDate() + 7);
  65  |     await page.fill('input[name="scheduleDate"]', futureDate.toISOString().split('T')[0]);
  66  |     
  67  |     await page.click('button:has-text("Schedule")');
  68  |     
  69  |     await expect(page.locator('[data-testid="scheduled-post"]')).toBeVisible();
  70  |   });
  71  | 
  72  |   test('should view publishing history', async ({ page }) => {
  73  |     await page.goto('/publishing');
  74  |     
  75  |     await page.click('[data-testid="history-tab"]');
  76  |     
  77  |     await expect(page.locator('[data-testid="publish-history"]')).toBeVisible();
  78  |   });
  79  | 
  80  |   test('should retry failed upload', async ({ page }) => {
  81  |     await page.goto('/publishing');
  82  |     
  83  |     await page.click('[data-testid="failed-upload"]');
  84  |     await page.click('[data-testid="retry-button"]');
  85  |     
  86  |     await expect(page.locator('[data-testid="retry-progress"]')).toBeVisible();
  87  |   });
  88  | });
  89  | 
  90  | test.describe('Multi-Platform Publishing', () => {
  91  |   test.beforeEach(async ({ page }) => {
  92  |     await page.goto('/login');
  93  |     await page.fill('input[name="email"]', 'test@example.com');
  94  |     await page.fill('input[name="password"]', 'testpassword');
  95  |     await page.click('button[type="submit"]');
  96  |     await page.waitForURL('/');
  97  |   });
  98  | 
  99  |   test('should post to multiple platforms at once', async ({ page }) => {
  100 |     await page.goto('/publishing');
  101 |     
  102 |     await page.click('[data-testid="multi-post-button"]');
  103 |     
  104 |     await page.fill('input[name="title"]', 'Multi-Platform Post');
  105 |     
  106 |     await page.check('input[name="platform-youtube"]');
```
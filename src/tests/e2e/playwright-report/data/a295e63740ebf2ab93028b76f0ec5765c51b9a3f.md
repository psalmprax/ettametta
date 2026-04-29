# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: publishing/publishing.spec.ts >> Publishing - A/B Testing >> should display A/B testing interface
- Location: tests/publishing/publishing.spec.ts:157:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

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
  107 |         await page.click('button[type="submit"]');
  108 |         await page.waitForURL('/');
  109 |     });
  110 | 
  111 |     test('should display scheduler interface', async ({ page }) => {
  112 |         await page.goto('/publish/schedule');
  113 |         await expect(page.locator('[data-testid="scheduler"]')).toBeVisible();
  114 |     });
  115 | 
  116 |     test('should schedule a post', async ({ page }) => {
  117 |         await page.goto('/publish/schedule');
  118 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  119 |         await page.selectOption('select[name="platform"]', 'youtube');
  120 |         await page.fill('input[name="scheduled_date"]', '2026-04-15');
  121 |         await page.fill('input[name="scheduled_time"]', '10:00');
  122 |         await page.click('button:has-text("Schedule Post")');
  123 |         await expect(page.locator('[data-testid="post-scheduled"]')).toBeVisible();
  124 |     });
  125 | 
  126 |     test('should view scheduled posts', async ({ page }) => {
  127 |         await page.goto('/publish/schedule');
  128 |         await expect(page.locator('[data-testid="scheduled-list"]')).toBeVisible();
  129 |     });
  130 | 
  131 |     test('should edit scheduled post', async ({ page }) => {
  132 |         await page.goto('/publish/schedule');
  133 |         await page.click('[data-testid="scheduled-post"]:first-child');
  134 |         await page.click('button:has-text("Edit")');
  135 |         await page.fill('input[name="scheduled_time"]', '12:00');
  136 |         await page.click('button:has-text("Save")');
  137 |         await expect(page.locator('[data-testid="post-updated"]')).toBeVisible();
  138 |     });
  139 | 
  140 |     test('should cancel scheduled post', async ({ page }) => {
  141 |         await page.goto('/publish/schedule');
  142 |         await page.click('[data-testid="scheduled-post"]:first-child');
  143 |         await page.click('button:has-text("Cancel")');
  144 |         await expect(page.locator('[data-testid="post-cancelled"]')).toBeVisible();
  145 |     });
  146 | });
  147 | 
  148 | test.describe('Publishing - A/B Testing', () => {
  149 |     test.beforeEach(async ({ page }) => {
> 150 |         await page.goto('/login');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  151 |         await page.fill('input[name="email"]', 'test@example.com');
  152 |         await page.fill('input[name="password"]', 'testpassword');
  153 |         await page.click('button[type="submit"]');
  154 |         await page.waitForURL('/');
  155 |     });
  156 | 
  157 |     test('should display A/B testing interface', async ({ page }) => {
  158 |         await page.goto('/publish/ab-testing');
  159 |         await expect(page.locator('[data-testid="ab-test-dashboard"]')).toBeVisible();
  160 |     });
  161 | 
  162 |     test('should create A/B test', async ({ page }) => {
  163 |         await page.goto('/publish/ab-testing');
  164 |         await page.click('button:has-text("Create Test")');
  165 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  166 |         await page.fill('input[name="title_a"]', 'Title A');
  167 |         await page.fill('input[name="title_b"]', 'Title B');
  168 |         await page.fill('input[name="traffic_split"]', '50');
  169 |         await page.click('button:has-text("Start Test")');
  170 |         await expect(page.locator('[data-testid="test-created"]')).toBeVisible();
  171 |     });
  172 | 
  173 |     test('should view test results', async ({ page }) => {
  174 |         await page.goto('/publish/ab-testing');
  175 |         await page.click('[data-testid="test-card"]:first-child');
  176 |         await expect(page.locator('[data-testid="test-results"]')).toBeVisible();
  177 |     });
  178 | 
  179 |     test('should declare winner', async ({ page }) => {
  180 |         await page.goto('/publish/ab-testing');
  181 |         await page.click('[data-testid="test-card"]:first-child');
  182 |         await page.click('button:has-text("Declare Winner")');
  183 |         await expect(page.locator('[data-testid="winner-declared"]')).toBeVisible();
  184 |     });
  185 | });
```
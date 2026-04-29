# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creation/video_creation.spec.ts >> Video Processing Jobs >> should show job progress
- Location: tests/creation/video_creation.spec.ts:145:9

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
  114 |         // Test with a free tier user - should see restrictions
  115 |         await page.goto('/creation');
  116 | 
  117 |         await page.click('text=AI Generation');
  118 | 
  119 |         await page.fill('textarea[name="prompt"]', 'Test');
  120 |         await page.selectOption('select[name="engine"]', 'veo3');
  121 | 
  122 |         await page.click('button[type="submit"]');
  123 | 
  124 |         // Should show upgrade prompt for free users
  125 |         await expect(page.locator('[data-testid="upgrade-prompt"], [data-testid="tier-required"]')).toBeVisible({ timeout: 10000 });
  126 |     });
  127 | });
  128 | 
  129 | test.describe('Video Processing Jobs', () => {
  130 |     test.beforeEach(async ({ page }) => {
  131 |         await page.goto('/login');
> 132 |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  133 |         await page.fill('input[name="password"]', 'testpassword');
  134 |         await page.click('button[type="submit"]');
  135 |         await page.waitForURL('/');
  136 |     });
  137 | 
  138 |     test('should display job queue', async ({ page }) => {
  139 |         await page.goto('/creation');
  140 | 
  141 |         // Look for jobs section
  142 |         await expect(page.locator('[data-testid="job-queue"], [data-testid="jobs-list"]')).toBeVisible();
  143 |     });
  144 | 
  145 |     test('should show job progress', async ({ page }) => {
  146 |         await page.goto('/creation');
  147 | 
  148 |         // Should show progress bars for active jobs
  149 |         const progressElements = page.locator('[data-testid="job-progress"]');
  150 |         // May or may not have jobs depending on state
  151 |     });
  152 | 
  153 |     test('should cancel job', async ({ page }) => {
  154 |         await page.goto('/creation');
  155 | 
  156 |         // Find a cancel button if job exists
  157 |         const cancelButton = page.locator('[data-testid="cancel-job"]').first();
  158 |         if (await cancelButton.isVisible()) {
  159 |             await cancelButton.click();
  160 |             await expect(page.locator('[data-testid="job-cancelled"]')).toBeVisible();
  161 |         }
  162 |     });
  163 | });
  164 | 
  165 | test.describe('Remotion Templates', () => {
  166 |     test.beforeEach(async ({ page }) => {
  167 |         await page.goto('/login');
  168 |         await page.fill('input[name="email"]', 'test@example.com');
  169 |         await page.fill('input[name="password"]', 'testpassword');
  170 |         await page.click('button[type="submit"]');
  171 |         await page.waitForURL('/');
  172 |     });
  173 | 
  174 |     test('should display template options', async ({ page }) => {
  175 |         await page.goto('/creation');
  176 | 
  177 |         // Look for template selection
  178 |         await expect(page.locator('text=CinematicMinimal')).toBeVisible();
  179 |         await expect(page.locator('text=HormoziStyle')).toBeVisible();
  180 |     });
  181 | 
  182 |     test('should select template', async ({ page }) => {
  183 |         await page.goto('/creation');
  184 | 
  185 |         await page.click('text=CinematicMinimal');
  186 |         await expect(page.locator('[data-testid="template-selected"]')).toContainText('CinematicMinimal');
  187 |     });
  188 | });
  189 | 
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creation/video_generation.spec.ts >> Video Generation - Story Generate Narrative >> should edit individual frames
- Location: tests/creation/video_generation.spec.ts:139:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    - waiting for" http://localhost:3000/login" navigation to finish...

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
  106 |         await page.click('button[type="submit"]');
  107 |         await expect(page.locator('[data-testid="error-message"]')).toContainText(/prompt/i);
  108 |     });
  109 | });
  110 | 
  111 | test.describe('Video Generation - Story Generate Narrative', () => {
  112 |     test.beforeEach(async ({ page }) => {
  113 |         await page.goto('/login');
> 114 |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  115 |         await page.fill('input[name="password"]', 'testpassword');
  116 |         await page.click('button[type="submit"]');
  117 |         await page.waitForURL('/');
  118 |     });
  119 | 
  120 |     test('should display storyboard interface', async ({ page }) => {
  121 |         await page.goto('/creation/storyboard');
  122 |         await expect(page.locator('textarea[name="story_prompt"]')).toBeVisible();
  123 |     });
  124 | 
  125 |     test('should generate storyboard from prompt', async ({ page }) => {
  126 |         await page.goto('/creation/storyboard');
  127 |         await page.fill('textarea[name="story_prompt"]', 'A hero journey through mystical lands');
  128 |         await page.click('button:has-text("Generate Storyboard")');
  129 |         await expect(page.locator('[data-testid="storyboard-frames"]')).toBeVisible({ timeout: 30000 });
  130 |     });
  131 | 
  132 |     test('should display storyboard frames', async ({ page }) => {
  133 |         await page.goto('/creation/storyboard');
  134 |         await page.fill('textarea[name="story_prompt"]', 'Adventure story');
  135 |         await page.click('button:has-text("Generate Storyboard")');
  136 |         await expect(page.locator('[data-testid="frame-1"]')).toBeVisible({ timeout: 30000 });
  137 |     });
  138 | 
  139 |     test('should edit individual frames', async ({ page }) => {
  140 |         await page.goto('/creation/storyboard');
  141 |         await page.fill('textarea[name="story_prompt"]', 'Test story');
  142 |         await page.click('button:has-text("Generate Storyboard")');
  143 |         await expect(page.locator('[data-testid="frame-1"]')).toBeVisible({ timeout: 30000 });
  144 |         await page.click('[data-testid="edit-frame-1"]');
  145 |         await expect(page.locator('[data-testid="frame-editor"]')).toBeVisible();
  146 |     });
  147 | 
  148 |     test('should generate video from storyboard', async ({ page }) => {
  149 |         await page.goto('/creation/storyboard');
  150 |         await page.fill('textarea[name="story_prompt"]', 'Simple story');
  151 |         await page.click('button:has-text("Generate Storyboard")');
  152 |         await expect(page.locator('[data-testid="storyboard-frames"]')).toBeVisible({ timeout: 30000 });
  153 |         await page.click('button:has-text("Generate Video")');
  154 |         await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
  155 |     });
  156 | });
  157 | 
  158 | test.describe('Video Generation - Test Drive Quick Preview', () => {
  159 |     test.beforeEach(async ({ page }) => {
  160 |         await page.goto('/login');
  161 |         await page.fill('input[name="email"]', 'test@example.com');
  162 |         await page.fill('input[name="password"]', 'testpassword');
  163 |         await page.click('button[type="submit"]');
  164 |         await page.waitForURL('/');
  165 |     });
  166 | 
  167 |     test('should display quick preview mode', async ({ page }) => {
  168 |         await page.goto('/creation/preview');
  169 |         await expect(page.locator('[data-testid="preview-mode"]')).toBeVisible();
  170 |     });
  171 | 
  172 |     test('should generate low-res preview', async ({ page }) => {
  173 |         await page.goto('/creation/preview');
  174 |         await page.fill('textarea[name="prompt"]', 'Quick test');
  175 |         await page.click('button:has-text("Generate Preview")');
  176 |         await expect(page.locator('[data-testid="preview-video"]')).toBeVisible({ timeout: 60000 });
  177 |     });
  178 | 
  179 |     test('should show preview immediately', async ({ page }) => {
  180 |         await page.goto('/creation/preview');
  181 |         await page.fill('textarea[name="prompt"]', 'Abstract shapes');
  182 |         await page.click('button:has-text("Generate Preview")');
  183 |         await expect(page.locator('video')).toBeVisible({ timeout: 60000 });
  184 |     });
  185 | 
  186 |     test('should upgrade to full quality', async ({ page }) => {
  187 |         await page.goto('/creation/preview');
  188 |         await page.fill('textarea[name="prompt"]', 'Test');
  189 |         await page.click('button:has-text("Generate Preview")');
  190 |         await expect(page.locator('[data-testid="preview-video"]')).toBeVisible({ timeout: 60000 });
  191 |         await page.click('button:has-text("Upgrade to Full Quality")');
  192 |         await expect(page.locator('[data-testid="job-created"]')).toBeVisible({ timeout: 15000 });
  193 |     });
  194 | });
```
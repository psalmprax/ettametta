# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: nexus/nexus_composition.spec.ts >> Nexus Composition - Assemble Video from Segments >> should render final video
- Location: tests/nexus/nexus_composition.spec.ts:46:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    8 × waiting for" http://localhost:3000/login" navigation to finish...
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
  3   | test.describe('Nexus Composition - Assemble Video from Segments', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
> 6   |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  7   |         await page.fill('input[name="password"]', 'testpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display video assembler interface', async ({ page }) => {
  13  |         await page.goto('/nexus/assemble');
  14  |         await expect(page.locator('[data-testid="segment-list"]')).toBeVisible();
  15  |     });
  16  | 
  17  |     test('should add video segments to timeline', async ({ page }) => {
  18  |         await page.goto('/nexus/assemble');
  19  |         await page.click('button:has-text("Add Segment")');
  20  |         await page.fill('input[name="segment_url"]', 'https://example.com/clip1.mp4');
  21  |         await page.click('button:has-text("Add to Timeline")');
  22  |         await expect(page.locator('[data-testid="timeline"]')).toContainText('clip1.mp4');
  23  |     });
  24  | 
  25  |     test('should reorder segments in timeline', async ({ page }) => {
  26  |         await page.goto('/nexus/assemble');
  27  |         await page.fill('input[name="segment_url"]', 'https://example.com/clip1.mp4');
  28  |         await page.click('button:has-text("Add to Timeline")');
  29  |         await page.fill('input[name="segment_url"]', 'https://example.com/clip2.mp4');
  30  |         await page.click('button:has-text("Add to Timeline")');
  31  |         await page.dragAndDrop('[data-testid="segment-2"]', '[data-testid="segment-1"]');
  32  |         await expect(page.locator('[data-testid="timeline"]')).toContainText(/clip2.*clip1/s);
  33  |     });
  34  | 
  35  |     test('should trim segment boundaries', async ({ page }) => {
  36  |         await page.goto('/nexus/assemble');
  37  |         await page.fill('input[name="segment_url"]', 'https://example.com/clip.mp4');
  38  |         await page.click('button:has-text("Add to Timeline")');
  39  |         await page.click('[data-testid="segment-1"]');
  40  |         await page.fill('input[name="start_time"]', '5');
  41  |         await page.fill('input[name="end_time"]', '30');
  42  |         await page.click('button:has-text("Trim")');
  43  |         await expect(page.locator('[data-testid="trimmed-segment"]')).toBeVisible();
  44  |     });
  45  | 
  46  |     test('should render final video', async ({ page }) => {
  47  |         await page.goto('/nexus/assemble');
  48  |         await page.fill('input[name="segment_url"]', 'https://example.com/clip.mp4');
  49  |         await page.click('button:has-text("Add to Timeline")');
  50  |         await page.click('button:has-text("Render Video")');
  51  |         await expect(page.locator('[data-testid="rendered-video"]')).toBeVisible({ timeout: 120000 });
  52  |     });
  53  | });
  54  | 
  55  | test.describe('Nexus Composition - Cinema Mode', () => {
  56  |     test.beforeEach(async ({ page }) => {
  57  |         await page.goto('/login');
  58  |         await page.fill('input[name="email"]', 'test@example.com');
  59  |         await page.fill('input[name="password"]', 'testpassword');
  60  |         await page.click('button[type="submit"]');
  61  |         await page.waitForURL('/');
  62  |     });
  63  | 
  64  |     test('should display cinema mode interface', async ({ page }) => {
  65  |         await page.goto('/nexus/cinema');
  66  |         await expect(page.locator('[data-testid="cinema-workspace"]')).toBeVisible();
  67  |     });
  68  | 
  69  |     test('should create autonomous project', async ({ page }) => {
  70  |         await page.goto('/nexus/cinema');
  71  |         await page.fill('textarea[name="description"]', 'Create an engaging tech tutorial');
  72  |         await page.click('button:has-text("Create Project")');
  73  |         await expect(page.locator('[data-testid="project-created"]')).toBeVisible({ timeout: 30000 });
  74  |     });
  75  | 
  76  |     test('should show AI-generated scenes', async ({ page }) => {
  77  |         await page.goto('/nexus/cinema');
  78  |         await page.fill('textarea[name="description"]', 'A day in the life of a developer');
  79  |         await page.click('button:has-text("Generate Scenes")');
  80  |         await expect(page.locator('[data-testid="scene-list"]')).toBeVisible({ timeout: 60000 });
  81  |     });
  82  | 
  83  |     test('should select scene for rendering', async ({ page }) => {
  84  |         await page.goto('/nexus/cinema');
  85  |         await page.fill('textarea[name="description"]', 'Test');
  86  |         await page.click('button:has-text("Generate Scenes")');
  87  |         await expect(page.locator('[data-testid="scene-1"]')).toBeVisible({ timeout: 60000 });
  88  |         await page.click('[data-testid="scene-1"]');
  89  |         await expect(page.locator('[data-testid="scene-detail"]')).toBeVisible();
  90  |     });
  91  | });
  92  | 
  93  | test.describe('Nexus Composition - Story Factory', () => {
  94  |     test.beforeEach(async ({ page }) => {
  95  |         await page.goto('/login');
  96  |         await page.fill('input[name="email"]', 'test@example.com');
  97  |         await page.fill('input[name="password"]', 'testpassword');
  98  |         await page.click('button[type="submit"]');
  99  |         await page.waitForURL('/');
  100 |     });
  101 | 
  102 |     test('should display story factory interface', async ({ page }) => {
  103 |         await page.goto('/nexus/story-factory');
  104 |         await expect(page.locator('[data-testid="story-workspace"]')).toBeVisible();
  105 |     });
  106 | 
```
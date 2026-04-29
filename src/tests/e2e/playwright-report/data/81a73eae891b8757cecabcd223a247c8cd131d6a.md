# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: enhancement/video_enhancement.spec.ts >> Video Enhancement - Thumbnail Generation >> should generate thumbnails from video frames
- Location: tests/enhancement/video_enhancement.spec.ts:245:9

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
  133 |     test('should add background music', async ({ page }) => {
  134 |         await page.goto('/enhancement/sound');
  135 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  136 |         await page.click('button:has-text("Add Music")');
  137 |         await page.selectOption('select[name="track"]', 'upbeat_1');
  138 |         await page.click('button:has-text("Apply")');
  139 |         await expect(page.locator('[data-testid="processed-audio"]')).toBeVisible({ timeout: 60000 });
  140 |     });
  141 | 
  142 |     test('should add sound effects', async ({ page }) => {
  143 |         await page.goto('/enhancement/sound');
  144 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  145 |         await page.click('button:has-text("Add SFX")');
  146 |         await page.selectOption('select[name="effect"]', 'whoosh');
  147 |         await page.click('button:has-text("Apply")');
  148 |         await expect(page.locator('[data-testid="processed-audio"]')).toBeVisible({ timeout: 60000 });
  149 |     });
  150 | 
  151 |     test('should mix audio tracks', async ({ page }) => {
  152 |         await page.goto('/enhancement/sound');
  153 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  154 |         await page.click('button:has-text("Audio Mixer")');
  155 |         await page.fill('input[name="music_volume"]', '50');
  156 |         await page.fill('input[name="sfx_volume"]', '30');
  157 |         await page.click('button:has-text("Mix")');
  158 |         await expect(page.locator('[data-testid="mixed-audio"]')).toBeVisible({ timeout: 60000 });
  159 |     });
  160 | });
  161 | 
  162 | test.describe('Video Enhancement - Music Addition', () => {
  163 |     test.beforeEach(async ({ page }) => {
  164 |         await page.goto('/login');
  165 |         await page.fill('input[name="email"]', 'test@example.com');
  166 |         await page.fill('input[name="password"]', 'testpassword');
  167 |         await page.click('button[type="submit"]');
  168 |         await page.waitForURL('/');
  169 |     });
  170 | 
  171 |     test('should display music library', async ({ page }) => {
  172 |         await page.goto('/enhancement/music');
  173 |         await expect(page.locator('[data-testid="music-library"]')).toBeVisible();
  174 |     });
  175 | 
  176 |     test('should preview music track', async ({ page }) => {
  177 |         await page.goto('/enhancement/music');
  178 |         await page.click('[data-testid="preview-track"]:first-child');
  179 |         await expect(page.locator('[data-testid="audio-player"]')).toBeVisible();
  180 |     });
  181 | 
  182 |     test('should add music to video', async ({ page }) => {
  183 |         await page.goto('/enhancement/music');
  184 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  185 |         await page.click('[data-testid="track-card"]:first-child');
  186 |         await page.click('button:has-text("Add to Video")');
  187 |         await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 60000 });
  188 |     });
  189 | });
  190 | 
  191 | test.describe('Video Enhancement - Subtitle Generation', () => {
  192 |     test.beforeEach(async ({ page }) => {
  193 |         await page.goto('/login');
  194 |         await page.fill('input[name="email"]', 'test@example.com');
  195 |         await page.fill('input[name="password"]', 'testpassword');
  196 |         await page.click('button[type="submit"]');
  197 |         await page.waitForURL('/');
  198 |     });
  199 | 
  200 |     test('should display subtitle generation interface', async ({ page }) => {
  201 |         await page.goto('/enhancement/subtitles');
  202 |         await expect(page.locator('input[name="video_uri"]')).toBeVisible();
  203 |     });
  204 | 
  205 |     test('should generate subtitles from audio', async ({ page }) => {
  206 |         await page.goto('/enhancement/subtitles');
  207 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  208 |         await page.click('button:has-text("Generate Subtitles")');
  209 |         await expect(page.locator('[data-testid="subtitle-preview"]')).toBeVisible({ timeout: 60000 });
  210 |     });
  211 | 
  212 |     test('should edit subtitle text', async ({ page }) => {
  213 |         await page.goto('/enhancement/subtitles');
  214 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  215 |         await page.click('button:has-text("Generate Subtitles")');
  216 |         await expect(page.locator('[data-testid="subtitle-editor"]')).toBeVisible({ timeout: 60000 });
  217 |         await page.click('[data-testid="subtitle-line"]:first-child');
  218 |         await page.fill('[data-testid="subtitle-input"]', 'Edited text');
  219 |     });
  220 | 
  221 |     test('should burn subtitles into video', async ({ page }) => {
  222 |         await page.goto('/enhancement/subtitles');
  223 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  224 |         await page.click('button:has-text("Generate Subtitles")');
  225 |         await expect(page.locator('[data-testid="subtitle-preview"]')).toBeVisible({ timeout: 60000 });
  226 |         await page.click('button:has-text("Burn to Video")');
  227 |         await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 60000 });
  228 |     });
  229 | });
  230 | 
  231 | test.describe('Video Enhancement - Thumbnail Generation', () => {
  232 |     test.beforeEach(async ({ page }) => {
> 233 |         await page.goto('/login');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  234 |         await page.fill('input[name="email"]', 'test@example.com');
  235 |         await page.fill('input[name="password"]', 'testpassword');
  236 |         await page.click('button[type="submit"]');
  237 |         await page.waitForURL('/');
  238 |     });
  239 | 
  240 |     test('should display thumbnail generation', async ({ page }) => {
  241 |         await page.goto('/enhancement/thumbnail');
  242 |         await expect(page.locator('input[name="video_uri"]')).toBeVisible();
  243 |     });
  244 | 
  245 |     test('should generate thumbnails from video frames', async ({ page }) => {
  246 |         await page.goto('/enhancement/thumbnail');
  247 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  248 |         await page.click('button:has-text("Generate Thumbnails")');
  249 |         await expect(page.locator('[data-testid="thumbnail-grid"]')).toBeVisible({ timeout: 60000 });
  250 |     });
  251 | 
  252 |     test('should select thumbnail', async ({ page }) => {
  253 |         await page.goto('/enhancement/thumbnail');
  254 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  255 |         await page.click('button:has-text("Generate Thumbnails")');
  256 |         await expect(page.locator('[data-testid="thumbnail-grid"]')).toBeVisible({ timeout: 60000 });
  257 |         await page.click('[data-testid="thumbnail-card"]:first-child');
  258 |         await expect(page.locator('[data-testid="selected-thumbnail"]')).toBeVisible();
  259 |     });
  260 | });
  261 | 
  262 | test.describe('Video Enhancement - Quality Upscaling', () => {
  263 |     test.beforeEach(async ({ page }) => {
  264 |         await page.goto('/login');
  265 |         await page.fill('input[name="email"]', 'test@example.com');
  266 |         await page.fill('input[name="password"]', 'testpassword');
  267 |         await page.click('button[type="submit"]');
  268 |         await page.waitForURL('/');
  269 |     });
  270 | 
  271 |     test('should display upscaling options', async ({ page }) => {
  272 |         await page.goto('/enhancement/upscale');
  273 |         await expect(page.locator('input[name="video_uri"]')).toBeVisible();
  274 |         await expect(page.locator('select[name="resolution"]')).toBeVisible();
  275 |     });
  276 | 
  277 |     test('should upscale video to 4K', async ({ page }) => {
  278 |         await page.goto('/enhancement/upscale');
  279 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  280 |         await page.selectOption('select[name="resolution"]', '4k');
  281 |         await page.click('button:has-text("Upscale Video")');
  282 |         await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 300000 });
  283 |     });
  284 | 
  285 |     test('should show progress during upscaling', async ({ page }) => {
  286 |         await page.goto('/enhancement/upscale');
  287 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  288 |         await page.selectOption('select[name="resolution"]', '1080p');
  289 |         await page.click('button:has-text("Upscale Video")');
  290 |         await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
  291 |     });
  292 | });
```
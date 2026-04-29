# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: enhancement/video_enhancement.spec.ts >> Video Enhancement - Voice Overdub (TTS) >> should generate voiceover with Gtts
- Location: tests/enhancement/video_enhancement.spec.ts:27:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Video Enhancement - Voice Overdub (TTS)', () => {
  4   |     test.beforeEach(async ({ page }) => {
> 5   |         await page.goto('/login');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  6   |         await page.fill('input[name="email"]', 'test@example.com');
  7   |         await page.fill('input[name="password"]', 'testpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display TTS options', async ({ page }) => {
  13  |         await page.goto('/enhancement/tts');
  14  |         await expect(page.locator('select[name="voice"]')).toBeVisible();
  15  |         await expect(page.locator('textarea[name="text"]')).toBeVisible();
  16  |     });
  17  | 
  18  |     test('should generate voiceover with ElevenLabs', async ({ page }) => {
  19  |         await page.goto('/enhancement/tts');
  20  |         await page.fill('textarea[name="text"]', 'Welcome to our channel');
  21  |         await page.selectOption('select[name="voice"]', 'Rachel');
  22  |         await page.selectOption('select[name="provider"]', 'elevenlabs');
  23  |         await page.click('button:has-text("Generate Voice")');
  24  |         await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible({ timeout: 30000 });
  25  |     });
  26  | 
  27  |     test('should generate voiceover with Gtts', async ({ page }) => {
  28  |         await page.goto('/enhancement/tts');
  29  |         await page.fill('textarea[name="text"]', 'Hello world');
  30  |         await page.selectOption('select[name="provider"]', 'gtts');
  31  |         await page.click('button:has-text("Generate Voice")');
  32  |         await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible({ timeout: 30000 });
  33  |     });
  34  | 
  35  |     test('should sync voiceover to video', async ({ page }) => {
  36  |         await page.goto('/enhancement/tts');
  37  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  38  |         await page.fill('textarea[name="text"]', 'This is the narration');
  39  |         await page.click('button:has-text("Sync to Video")');
  40  |         await expect(page.locator('[data-testid="synced-video"]')).toBeVisible({ timeout: 60000 });
  41  |     });
  42  | 
  43  |     test('should preview voice before applying', async ({ page }) => {
  44  |         await page.goto('/enhancement/tts');
  45  |         await page.fill('textarea[name="text"]', 'Test preview');
  46  |         await page.click('button:has-text("Preview")');
  47  |         await expect(page.locator('[data-testid="audio-player"]')).toBeVisible({ timeout: 15000 });
  48  |     });
  49  | });
  50  | 
  51  | test.describe('Video Enhancement - Face Animation (No-Face)', () => {
  52  |     test.beforeEach(async ({ page }) => {
  53  |         await page.goto('/login');
  54  |         await page.fill('input[name="email"]', 'test@example.com');
  55  |         await page.fill('input[name="password"]', 'testpassword');
  56  |         await page.click('button[type="submit"]');
  57  |         await page.waitForURL('/');
  58  |     });
  59  | 
  60  |     test('should display face animation interface', async ({ page }) => {
  61  |         await page.goto('/enhancement/face-animation');
  62  |         await expect(page.locator('input[name="video_uri"]')).toBeVisible();
  63  |         await expect(page.locator('select[name="avatar"]')).toBeVisible();
  64  |     });
  65  | 
  66  |     test('should animate face with avatar', async ({ page }) => {
  67  |         await page.goto('/enhancement/face-animation');
  68  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  69  |         await page.selectOption('select[name="avatar"]', 'avatar_1');
  70  |         await page.click('button:has-text("Animate Face")');
  71  |         await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 120000 });
  72  |     });
  73  | 
  74  |     test('should select different avatar styles', async ({ page }) => {
  75  |         await page.goto('/enhancement/face-animation');
  76  |         await expect(page.locator('[data-testid="avatar-options"]')).toBeVisible();
  77  |         await page.click('[data-testid="avatar-card"]:nth-child(2)');
  78  |         await expect(page.locator('select[name="avatar"]')).toHaveValue(/avatar_2/);
  79  |     });
  80  | 
  81  |     test('should show face detection preview', async ({ page }) => {
  82  |         await page.goto('/enhancement/face-animation');
  83  |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  84  |         await page.click('button:has-text("Detect Faces")');
  85  |         await expect(page.locator('[data-testid="face-preview"]')).toBeVisible({ timeout: 30000 });
  86  |     });
  87  | });
  88  | 
  89  | test.describe('Video Enhancement - Background Removal', () => {
  90  |     test.beforeEach(async ({ page }) => {
  91  |         await page.goto('/login');
  92  |         await page.fill('input[name="email"]', 'test@example.com');
  93  |         await page.fill('input[name="password"]', 'testpassword');
  94  |         await page.click('button[type="submit"]');
  95  |         await page.waitForURL('/');
  96  |     });
  97  | 
  98  |     test('should display background removal interface', async ({ page }) => {
  99  |         await page.goto('/enhancement/background');
  100 |         await expect(page.locator('input[name="video_uri"]')).toBeVisible();
  101 |     });
  102 | 
  103 |     test('should remove background from video', async ({ page }) => {
  104 |         await page.goto('/enhancement/background');
  105 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
```
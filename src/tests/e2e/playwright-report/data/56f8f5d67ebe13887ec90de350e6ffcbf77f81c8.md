# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: enhancement/video_enhancement.spec.ts >> Video Enhancement - Face Animation (No-Face) >> should select different avatar styles
- Location: tests/enhancement/video_enhancement.spec.ts:74:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    6 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Video Enhancement - Voice Overdub (TTS)', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
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
> 54  |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
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
  106 |         await page.click('button:has-text("Remove Background")');
  107 |         await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 120000 });
  108 |     });
  109 | 
  110 |     test('should replace background with image', async ({ page }) => {
  111 |         await page.goto('/enhancement/background');
  112 |         await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
  113 |         await page.fill('input[name="background_image"]', 'https://example.com/bg.jpg');
  114 |         await page.click('button:has-text("Replace Background")');
  115 |         await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 120000 });
  116 |     });
  117 | });
  118 | 
  119 | test.describe('Video Enhancement - Sound Design', () => {
  120 |     test.beforeEach(async ({ page }) => {
  121 |         await page.goto('/login');
  122 |         await page.fill('input[name="email"]', 'test@example.com');
  123 |         await page.fill('input[name="password"]', 'testpassword');
  124 |         await page.click('button[type="submit"]');
  125 |         await page.waitForURL('/');
  126 |     });
  127 | 
  128 |     test('should display sound design interface', async ({ page }) => {
  129 |         await page.goto('/enhancement/sound');
  130 |         await expect(page.locator('input[name="video_uri"]')).toBeVisible();
  131 |     });
  132 | 
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
```
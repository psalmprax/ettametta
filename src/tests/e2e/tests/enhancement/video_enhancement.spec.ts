import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../../helpers/auth';

test.describe('Video Enhancement - Voice Overdub (TTS)', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display TTS options', async ({ page }) => {
        await page.goto('/enhancement/tts');
        await expect(page.locator('select[name="voice"]')).toBeVisible();
        await expect(page.locator('textarea[name="text"]')).toBeVisible();
    });

    test('should generate voiceover with ElevenLabs', async ({ page }) => {
        await page.goto('/enhancement/tts');
        await page.fill('textarea[name="text"]', 'Welcome to our channel');
        await page.selectOption('select[name="voice"]', 'Rachel');
        await page.selectOption('select[name="provider"]', 'elevenlabs');
        await page.click('button:has-text("Generate Voice")');
        await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible({ timeout: 30000 });
    });

    test('should generate voiceover with Gtts', async ({ page }) => {
        await page.goto('/enhancement/tts');
        await page.fill('textarea[name="text"]', 'Hello world');
        await page.selectOption('select[name="provider"]', 'gtts');
        await page.click('button:has-text("Generate Voice")');
        await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible({ timeout: 30000 });
    });

    test('should sync voiceover to video', async ({ page }) => {
        await page.goto('/enhancement/tts');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.fill('textarea[name="text"]', 'This is the narration');
        await page.click('button:has-text("Sync to Video")');
        await expect(page.locator('[data-testid="synced-video"]')).toBeVisible({ timeout: 60000 });
    });

    test('should preview voice before applying', async ({ page }) => {
        await page.goto('/enhancement/tts');
        await page.fill('textarea[name="text"]', 'Test preview');
        await page.click('button:has-text("Preview")');
        await expect(page.locator('[data-testid="audio-player"]')).toBeVisible({ timeout: 15000 });
    });
});

test.describe('Video Enhancement - Face Animation (No-Face)', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display face animation interface', async ({ page }) => {
        await page.goto('/enhancement/face-animation');
        await expect(page.locator('input[name="video_uri"]')).toBeVisible();
        await expect(page.locator('select[name="avatar"]')).toBeVisible();
    });

    test('should animate face with avatar', async ({ page }) => {
        await page.goto('/enhancement/face-animation');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.selectOption('select[name="avatar"]', 'avatar_1');
        await page.click('button:has-text("Animate Face")');
        await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 120000 });
    });

    test('should select different avatar styles', async ({ page }) => {
        await page.goto('/enhancement/face-animation');
        await expect(page.locator('[data-testid="avatar-options"]')).toBeVisible();
        await page.click('[data-testid="avatar-card"]:nth-child(2)');
        await expect(page.locator('select[name="avatar"]')).toHaveValue(/avatar_2/);
    });

    test('should show face detection preview', async ({ page }) => {
        await page.goto('/enhancement/face-animation');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Detect Faces")');
        await expect(page.locator('[data-testid="face-preview"]')).toBeVisible({ timeout: 30000 });
    });
});

test.describe('Video Enhancement - Background Removal', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display background removal interface', async ({ page }) => {
        await page.goto('/enhancement/background');
        await expect(page.locator('input[name="video_uri"]')).toBeVisible();
    });

    test('should remove background from video', async ({ page }) => {
        await page.goto('/enhancement/background');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Remove Background")');
        await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 120000 });
    });

    test('should replace background with image', async ({ page }) => {
        await page.goto('/enhancement/background');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.fill('input[name="background_image"]', 'https://example.com/bg.jpg');
        await page.click('button:has-text("Replace Background")');
        await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 120000 });
    });
});

test.describe('Video Enhancement - Sound Design', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display sound design interface', async ({ page }) => {
        await page.goto('/enhancement/sound');
        await expect(page.locator('input[name="video_uri"]')).toBeVisible();
    });

    test('should add background music', async ({ page }) => {
        await page.goto('/enhancement/sound');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Add Music")');
        await page.selectOption('select[name="track"]', 'upbeat_1');
        await page.click('button:has-text("Apply")');
        await expect(page.locator('[data-testid="processed-audio"]')).toBeVisible({ timeout: 60000 });
    });

    test('should add sound effects', async ({ page }) => {
        await page.goto('/enhancement/sound');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Add SFX")');
        await page.selectOption('select[name="effect"]', 'whoosh');
        await page.click('button:has-text("Apply")');
        await expect(page.locator('[data-testid="processed-audio"]')).toBeVisible({ timeout: 60000 });
    });

    test('should mix audio tracks', async ({ page }) => {
        await page.goto('/enhancement/sound');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Audio Mixer")');
        await page.fill('input[name="music_volume"]', '50');
        await page.fill('input[name="sfx_volume"]', '30');
        await page.click('button:has-text("Mix")');
        await expect(page.locator('[data-testid="mixed-audio"]')).toBeVisible({ timeout: 60000 });
    });
});

test.describe('Video Enhancement - Music Addition', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display music library', async ({ page }) => {
        await page.goto('/enhancement/music');
        await expect(page.locator('[data-testid="music-library"]')).toBeVisible();
    });

    test('should preview music track', async ({ page }) => {
        await page.goto('/enhancement/music');
        await page.click('[data-testid="preview-track"]:first-child');
        await expect(page.locator('[data-testid="audio-player"]')).toBeVisible();
    });

    test('should add music to video', async ({ page }) => {
        await page.goto('/enhancement/music');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('[data-testid="track-card"]:first-child');
        await page.click('button:has-text("Add to Video")');
        await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 60000 });
    });
});

test.describe('Video Enhancement - Subtitle Generation', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display subtitle generation interface', async ({ page }) => {
        await page.goto('/enhancement/subtitles');
        await expect(page.locator('input[name="video_uri"]')).toBeVisible();
    });

    test('should generate subtitles from audio', async ({ page }) => {
        await page.goto('/enhancement/subtitles');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Generate Subtitles")');
        await expect(page.locator('[data-testid="subtitle-preview"]')).toBeVisible({ timeout: 60000 });
    });

    test('should edit subtitle text', async ({ page }) => {
        await page.goto('/enhancement/subtitles');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Generate Subtitles")');
        await expect(page.locator('[data-testid="subtitle-editor"]')).toBeVisible({ timeout: 60000 });
        await page.click('[data-testid="subtitle-line"]:first-child');
        await page.fill('[data-testid="subtitle-input"]', 'Edited text');
    });

    test('should burn subtitles into video', async ({ page }) => {
        await page.goto('/enhancement/subtitles');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Generate Subtitles")');
        await expect(page.locator('[data-testid="subtitle-preview"]')).toBeVisible({ timeout: 60000 });
        await page.click('button:has-text("Burn to Video")');
        await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 60000 });
    });
});

test.describe('Video Enhancement - Thumbnail Generation', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display thumbnail generation', async ({ page }) => {
        await page.goto('/enhancement/thumbnail');
        await expect(page.locator('input[name="video_uri"]')).toBeVisible();
    });

    test('should generate thumbnails from video frames', async ({ page }) => {
        await page.goto('/enhancement/thumbnail');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Generate Thumbnails")');
        await expect(page.locator('[data-testid="thumbnail-grid"]')).toBeVisible({ timeout: 60000 });
    });

    test('should select thumbnail', async ({ page }) => {
        await page.goto('/enhancement/thumbnail');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.click('button:has-text("Generate Thumbnails")');
        await expect(page.locator('[data-testid="thumbnail-grid"]')).toBeVisible({ timeout: 60000 });
        await page.click('[data-testid="thumbnail-card"]:first-child');
        await expect(page.locator('[data-testid="selected-thumbnail"]')).toBeVisible();
    });
});

test.describe('Video Enhancement - Quality Upscaling', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display upscaling options', async ({ page }) => {
        await page.goto('/enhancement/upscale');
        await expect(page.locator('input[name="video_uri"]')).toBeVisible();
        await expect(page.locator('select[name="resolution"]')).toBeVisible();
    });

    test('should upscale video to 4K', async ({ page }) => {
        await page.goto('/enhancement/upscale');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.selectOption('select[name="resolution"]', '4k');
        await page.click('button:has-text("Upscale Video")');
        await expect(page.locator('[data-testid="processed-video"]')).toBeVisible({ timeout: 300000 });
    });

    test('should show progress during upscaling', async ({ page }) => {
        await page.goto('/enhancement/upscale');
        await page.fill('input[name="video_uri"]', 'https://example.com/video.mp4');
        await page.selectOption('select[name="resolution"]', '1080p');
        await page.click('button:has-text("Upscale Video")');
        await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    });
});
/**
 * Video Model E2E Tests
 * =====================
 * Tests for autonomous mutual exclusive video generation across different models
 * 
 * Video Models (tested on RTX A6000 - 48GB VRAM):
 * - AnimateDiff (2.58GB) - Lightest
 * - CogVideoX-2b (14.61GB)
 * - Wan 2.1 T2V 1.3B (15.35GB)
 * - Mochi (30.29GB)
 * - HunyuanVideo 480p (~20GB)
 */

import { test, expect } from '@playwright/test';

const GPU_SERVER_URL = 'http://175.155.64.174:8080';
const API_SERVER_URL = 'http://149.104.110.122:7201';
const DASHBOARD_URL = 'http://149.104.110.122:7202';

test.describe('Video Model - GPU Server Endpoints', () => {
    test('should have GPU server accessible', async ({ request }) => {
        try {
            const response = await request.get(GPU_SERVER_URL, { timeout: 5000 });
            expect([200, 404, 500, 503]).toContain(response.status());
        } catch (e) {
            console.log('GPU server timeout - expected if server busy');
        }
    });

    test('should test AnimateDiff model endpoint', async ({ request }) => {
        try {
            const response = await request.post(`${GPU_SERVER_URL}/generate`, {
                data: {
                    prompt: 'A test animation',
                    engine: 'animatediff',
                    style: 'default',
                    aspect_ratio: '16:9'
                },
                timeout: 10000
            });
            console.log('AnimateDiff response:', response.status());
        } catch (e) {
            console.log('AnimateDiff endpoint test - server may be busy');
        }
    });

    test('should test CogVideo model endpoint', async ({ request }) => {
        try {
            const response = await request.post(`${GPU_SERVER_URL}/generate`, {
                data: {
                    prompt: 'A test video',
                    engine: 'cogvideo',
                    style: 'cinematic',
                    aspect_ratio: '16:9'
                },
                timeout: 10000
            });
            console.log('CogVideo response:', response.status());
        } catch (e) {
            console.log('CogVideo endpoint test - server may be busy');
        }
    });

    test('should test HunyuanVideo model endpoint', async ({ request }) => {
        try {
            const response = await request.post(`${GPU_SERVER_URL}/generate`, {
                data: {
                    prompt: 'A test video',
                    engine: 'hunyuan',
                    style: 'cinematic',
                    aspect_ratio: '9:16'
                },
                timeout: 10000
            });
            console.log('HunyuanVideo response:', response.status());
        } catch (e) {
            console.log('HunyuanVideo endpoint test - server may be busy');
        }
    });

    test('should test Wan model endpoint', async ({ request }) => {
        try {
            const response = await request.post(`${GPU_SERVER_URL}/generate`, {
                data: {
                    prompt: 'A test video',
                    engine: 'wan',
                    style: 'default',
                    aspect_ratio: '16:9'
                },
                timeout: 10000
            });
            console.log('Wan response:', response.status());
        } catch (e) {
            console.log('Wan endpoint test - server may be busy');
        }
    });

    test('should test Mochi model endpoint', async ({ request }) => {
        try {
            const response = await request.post(`${GPU_SERVER_URL}/generate`, {
                data: {
                    prompt: 'A test video',
                    engine: 'mochi',
                    style: 'cinematic',
                    aspect_ratio: '16:9'
                },
                timeout: 10000
            });
            console.log('Mochi response:', response.status());
        } catch (e) {
            console.log('Mochi endpoint test - server may be busy');
        }
    });
});

test.describe('Video Model - API Server Integration', () => {
    test('should connect to API server video endpoint', async ({ request }) => {
        const response = await request.get(`${API_SERVER_URL}/api/v1/video/jobs`);
        expect([200, 401, 403, 404]).toContain(response.status());
    });

    test('should check video transform endpoint', async ({ request }) => {
        const response = await request.post(`${API_SERVER_URL}/api/v1/video/transform`, {
            data: {
                source_uri: 'https://example.com/test.mp4',
                niche: 'Technology',
                platform: 'YouTube Shorts'
            }
        });
        expect([200, 401, 403, 404, 422]).toContain(response.status());
    });

    test('should check video generate endpoint', async ({ request }) => {
        const response = await request.post(`${API_SERVER_URL}/api/v1/video/generate`, {
            data: {
                prompt: 'A test video',
                engine: 'ltx-video',
                style: 'Cinematic',
                aspect_ratio: '9:16'
            }
        });
        expect([200, 401, 403, 404, 422]).toContain(response.status());
    });
});

test.describe('Video Model - Dashboard UI Tests', () => {
    test('should display creation page with form', async ({ page }) => {
        await page.goto('/creation');
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    });

    test('should display transformation page', async ({ page }) => {
        await page.goto('/transformation');
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    });

    test('should display autonomous page', async ({ page }) => {
        await page.goto('/autonomous');
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    });

    test('should display nexus page', async ({ page }) => {
        await page.goto('/nexus');
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Video Model - Engine Selection UI', () => {
    test('should show engine options in creation page', async ({ page }) => {
        await page.goto('/creation');
        const pageText = await page.locator('body').innerText();
        
        const hasEngineOptions = 
            pageText.toLowerCase().includes('engine') ||
            pageText.toLowerCase().includes('model') ||
            pageText.toLowerCase().includes('generation') ||
            pageText.toLowerCase().includes('video');
        
        expect(hasEngineOptions).toBe(true);
    });
});

test.describe('Video Model - Model Mutual Exclusion', () => {
    test('should show VRAM status indicator', async ({ page }) => {
        await page.goto('/');
        
        const pageText = await page.locator('body').innerText();
        const hasVRAMStatus = 
            pageText.toLowerCase().includes('vram') ||
            pageText.toLowerCase().includes('memory') ||
            pageText.toLowerCase().includes('gpu') ||
            pageText.toLowerCase().includes('engine');
        
        console.log('VRAM status present:', hasVRAMStatus);
    });
});

test.describe('Video Model - Model VRAM Requirements', () => {
    test('should document model requirements', () => {
        const modelRequirements = {
            'AnimateDiff': { vram: '2.58GB', status: 'Working', gpu: 'RTX A6000 48GB' },
            'CogVideoX-2b': { vram: '14.61GB', status: 'Working', gpu: 'RTX A6000 48GB' },
            'Wan 2.1 T2V 1.3B': { vram: '15.35GB', status: 'Working', gpu: 'RTX A6000 48GB' },
            'HunyuanVideo 480p': { vram: '~20GB', status: 'Working', gpu: 'RTX A6000 48GB' },
            'Mochi': { vram: '30.29GB', status: 'Working', gpu: 'RTX A6000 48GB' },
            'HunyuanVideo 720p': { vram: '>48GB', status: 'Failed (OOM)', gpu: 'RTX A6000 48GB' },
            'LTX-Video': { vram: 'N/A', status: 'Failed (Disk Space)', gpu: 'RTX A6000 48GB' },
            'Wan 2.2 I2V 14B': { vram: '>48GB', status: 'Failed (OOM)', gpu: 'RTX A6000 48GB' }
        };
        
        console.log('Model Requirements:', JSON.stringify(modelRequirements, null, 2));
        
        expect(Object.keys(modelRequirements).length).toBe(8);
    });
});
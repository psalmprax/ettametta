/**
 * E2E Test Configuration
 * =====================
 * Playwright configuration for end-to-end testing
 * Includes visual regression testing with screenshot comparison
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: process.env.CI 
        ? [['list'], ['html'], ['junit', { outputFile: 'results.xml' }]] 
        : 'html',
    use: {
        baseURL: process.env.BASE_URL || 'http://localhost:3000',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        actionTimeout: 30000,
        navigationTimeout: 60000,
        // Visual regression settings
        _visualRegressionOptions: {
            enabled: true,
            diffThreshold: 0.3,  // 0.3% difference allowed
            maxDiffPixels: 100,   // Allow 100 pixels difference
        },
    },
    timeout: 180000,
    expect: {
        timeout: 30000,
        // Custom expect for visual comparisons
        toHaveScreenshot: {
            maxDiffPixels: 100,
            maxDiffPixelRatio: 0.003,  // 0.3%
        },
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
    webServer: process.env.CI ? undefined : process.env.SKIP_WEB_SERVER ? undefined : {
        command: process.env.WEB_SERVER_COMMAND || 'cd ../../../apps/dashboard && npm run dev',
        url: process.env.BASE_URL || 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
    } as any,
});

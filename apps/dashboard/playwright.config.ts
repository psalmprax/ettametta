import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for the ettametta Dashboard.
 *
 * Usage:
 *   cd apps/dashboard
 *   npx playwright test                # headless (CI)
 *   npx playwright test --ui           # interactive UI mode
 *   npx playwright test --headed       # watch browser
 *
 * The dev server must be running:  npm run dev
 */
export default defineConfig({
    testDir: "./tests",
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: [["html", { outputFolder: "playwright-report" }], ["list"]],
    timeout: 30000,

    use: {
        baseURL: "http://localhost:3000",
        trace: "on-first-retry",
        screenshot: "only-on-failure",
    },

    projects: [
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] },
        },
    ],

    // Next.js dev server on port 3000
    webServer: {
        command: "npm run dev",
        port: 3000,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
    },
});

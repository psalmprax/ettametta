import { test, expect } from '@playwright/test';

test.describe('Agent Skills E2E - Universal Integration', () => {
    test.beforeEach(async ({ page }) => {
        // 1. Mock Authentication
        await page.route('**/api/auth/me', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 1,
                    email: 'test@example.com',
                    subscription: 'PRO'
                }),
            });
        });

        // 2. Mock Initial Data (Blueprints, Niches, Jobs)
        await page.route('**/api/nexus/blueprints', async (route) => {
            await route.fulfill({ status: 200, body: JSON.stringify([]) });
        });
        await page.route('**/api/discovery/niches', async (route) => {
            await route.fulfill({ status: 200, body: JSON.stringify(['AI Automation']) });
        });
        await page.route('**/api/nexus/jobs', async (route) => {
            await route.fulfill({ status: 200, body: JSON.stringify([]) });
        });
        await page.route('**/api/agent/capabilities', async (route) => {
            await route.fulfill({ 
                status: 200, 
                body: JSON.stringify({ 
                    capabilities: ['PAPERCLIP', 'SCIENTIFIC', 'REMOTION', 'CLAW4SCIENCE'] 
                }) 
            });
        });

        // Login flow
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/nexus');
    });

    test('should verify Scientific Hook conversion (Claw4Science)', async ({ page }) => {
        // Mock the chat response for Scientific Conversion
        await page.route('**/api/agent/chat', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    response: "🧪 [SCIENTIFIC] Signal Detected. Converting to Science-Pop...\n\nHook: 'Did you know GPU vRAM isn't just memory? It's the oxygen of AI.'\n\nScript generated successfully.",
                    status: "success"
                }),
            });
        });

        const input = page.getByTestId('agent-chat-input');
        await input.fill('Convert this technical paper on GPU architecture into a viral TikTok script.');
        await page.getByTestId('agent-chat-send').click();

        const messages = page.getByTestId('agent-chat-messages');
        await expect(messages).toContainText(/SCIENTIFIC/);
        await expect(messages).toContainText(/Science-Pop/);
        await expect(messages).toContainText(/GPU vRAM/);
    });

    test('should verify Paperclip KPI tracking performance', async ({ page }) => {
        // Mock the chat response for Paperclip KPI
        await page.route('**/api/agent/chat', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    response: "📈 [PAPERCLIP] KPI Synced for Job VF-102. Viral Signal Detected: 5,200 views. Recommendation: Triggering organic variation loop.",
                    status: "success"
                }),
            });
        });

        const input = page.getByTestId('agent-chat-input');
        await input.fill('Record performance for TikTok job VF-102: 5200 views.');
        await page.getByTestId('agent-chat-send').click();

        const messages = page.getByTestId('agent-chat-messages');
        await expect(messages).toContainText(/PAPERCLIP/);
        await expect(messages).toContainText(/Viral Signal Detected/);
        await expect(messages).toContainText(/VF-102/);
    });

    test('should verify Remotion Render dispatch', async ({ page }) => {
        // Mock the chat response for Remotion Render
        await page.route('**/api/agent/chat', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    response: "🎬 [REMOTION] Programmatic Overlay Dispatched. Composition: 'ScienceOverlay'. Job ID: REM-998.",
                    status: "success"
                }),
            });
        });

        const input = page.getByTestId('agent-chat-input');
        await input.fill('Trigger a Remotion render for the science video with high-fidelity overlays.');
        await page.getByTestId('agent-chat-send').click();

        const messages = page.getByTestId('agent-chat-messages');
        await expect(messages).toContainText(/REMOTION/);
        await expect(messages).toContainText(/REM-998/);
        await expect(messages).toContainText(/ScienceOverlay/);
    });
});

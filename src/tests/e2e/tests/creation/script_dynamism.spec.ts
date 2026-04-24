import { test, expect } from '@playwright/test';

test.describe('Creation Suite: Dynamism & Localization', () => {
    test.beforeEach(async ({ page }) => {
        // Updated for the branded Ettametta login UI
        await page.goto('/login');
        await page.fill('input[id="username"]', 'test');
        await page.fill('input[id="password"]', 'testpassword');
        await page.click('button:has-text("AUTHENTICATE")');
        
        // Wait for redirect to dashboard, then go to creation
        await page.waitForURL(/\/dashboard|\/$/);
        await page.goto('/creation');
    });

    test('should generate a dynamic script and perform retention analysis', async ({ page }) => {
        // 1. Trigger Script Generation
        const topicInput = page.locator('input[placeholder*="Topic"]');
        await topicInput.fill('The Future of Neural Networks in 2026');
        
        const generateBtn = page.locator('button:has-text("Generate Blueprint")');
        if (await generateBtn.isHidden()) {
            await page.locator('button:has-text("Generate Script")').click();
        } else {
            await generateBtn.click();
        }

        // 2. Wait for Script to load (Neural Blueprint header should be visible with a title)
        await expect(page.locator('h2')).toBeVisible({ timeout: 30000 });
        const initialTitle = await page.locator('h2').innerText();
        expect(initialTitle.length).toBeGreaterThan(0);

        // 3. Trigger Retention Analysis (The "Neural Kill-Switch" / Analyze Retention button)
        const analyzeBtn = page.locator('button:has-text("Analyze Retention")');
        await expect(analyzeBtn).toBeVisible();
        await analyzeBtn.click();

        // 4. Verify Analysis Result (Should NOT show 401 error anymore)
        const analysisCard = page.locator('span:has-text("Hook Validated"), span:has-text("Neural Kill-Switch Activated")');
        await expect(analysisCard).toBeVisible({ timeout: 15000 });
        
        const scoreText = page.locator('span.text-2xl.font-black');
        await expect(scoreText).not.toContainText('0%'); // It should have a score now
        
        const analysisBody = page.locator('p.text-zinc-400');
        await expect(analysisBody).not.toContainText('401');
        await expect(analysisBody).not.toContainText('Invalid API Key');
    });

    test('should translate script segments correctly', async ({ page }) => {
        // 1. Generate Script
        await page.locator('input[id="topic"]').fill('Stoic Wisdom for Modern Life');
        await page.locator('button:has-text("Generate Script")').click();
        await expect(page.locator('h2')).toBeVisible({ timeout: 30000 });

        // Capture initial English text of the first segment
        const firstSegment = page.locator('p.text-lg.font-bold').first();
        const englishText = await firstSegment.innerText();

        // 2. Click Language Button (ES - Spanish)
        const esBtn = page.locator('button:has-text("ES")');
        await esBtn.click();

        // 3. Verify Translation
        // Wait for the text to change from the initial English version
        await expect(async () => {
            const currentText = await firstSegment.innerText();
            expect(currentText).not.toEqual(englishText);
            // Simple check for Spanish keywords or just change detection
            expect(currentText.length).toBeGreaterThan(0);
        }).toPass({ timeout: 20000 });

        // 4. Verify Dynamism Metadata is preserved (e.g., Tone badge)
        const toneBadge = page.locator('span.text-primary:has-text("Tone")').first();
        // Wait, the badge might have the tone value itself
        const badgeText = page.locator('div[class*="bg-primary/5"] span').first();
        await expect(badgeText).toBeVisible();
    });
});

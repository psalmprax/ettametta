import { test, expect } from '@playwright/test';

test.describe('Video Stack Switching', () => {
    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/login');
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should switch between Cloud and Open-Source stacks', async ({ page }) => {
        await page.goto('/creation');
        await page.click('text=AI Generation');

        // 1. Initially should be on Cloud Stack
        const engineSelect = page.locator('select[name="engine"]');
        await expect(page.locator('text=Premium Cloud')).toBeVisible();
        
        // Check if a cloud-only engine is available
        const options = await engineSelect.innerText();
        expect(options).toContain('Lite4K');

        // 2. Click on Open-Source Stack toggle/card
        await page.click('[data-testid="os-stack-card"]');
        
        // 3. Verify stack switched
        await expect(page.locator('text=Open-Source Infrastructure')).toBeVisible();
        
        // 4. Verify engines updated to OS models
        const osOptions = await engineSelect.innerText();
        expect(osOptions).toContain('HunyuanVideo');
        expect(osOptions).toContain('Wan-2.2');
        
        // 5. Verify the "Transient" badge is visible for some models
        await expect(page.locator('text=Transient').first()).toBeVisible();
    });

    test('should show Sovereign tier requirement for OS stack', async ({ page }) => {
        // This test assumes the test user is "Free" or "Pro"
        await page.goto('/creation');
        await page.click('text=AI Generation');
        await page.click('[data-testid="os-stack-card"]');

        await page.fill('textarea[name="prompt"]', 'Test Prompt');
        await page.selectOption('select[name="engine"]', 'hunyuan');

        await page.click('button[type="submit"]');

        // Should show Sovereign requirement
        await expect(page.locator('text=Upgrade to Sovereign')).toBeVisible();
    });
});

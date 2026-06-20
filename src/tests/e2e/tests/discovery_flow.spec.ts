import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../helpers/auth';

test.describe('Discovery to Video Pipeline', () => {
    test.beforeEach(async ({ page }) => {

        await loginAsTestUser(page);

    });

    test('should flow from discovery search to video creation', async ({ page }) => {
        // 1. Go to Discovery
        await page.goto('/discovery');
        await expect(page.locator('h1')).toContainText(/discovery/i);

        // 2. Perform a search
        await page.fill('[data-testid="discovery-search-input"]', 'AI Automation');
        await page.keyboard.press('Enter');

        // 3. Wait for candidates and click "Deep Analysis" on the first one
        const firstCandidate = page.locator('[data-testid="candidate-card"]').first();
        await expect(firstCandidate).toBeVisible({ timeout: 15000 });
        
        await firstCandidate.locator('button:has-text("Deep Scan"), button:has-text("Analyze")').click();

        // 4. Verify AI Analysis modal/view opens
        await expect(page.locator('[data-testid="analysis-modal"]')).toBeVisible();
        await expect(page.locator('[data-testid="viral-score"]')).toBeVisible();

        // 5. Click "Transform to Video"
        await page.click('button:has-text("Transform to Video")');

        // 6. Should be redirected to /creation with the URL pre-filled
        await page.waitForURL(/\/creation/);
        const urlInput = page.locator('input[name="source_uri"]');
        await expect(urlInput).not.toHaveValue('');
        
        // 7. Verify we can select a platform and submit
        await page.selectOption('select[name="platform"]', 'TikTok');
        await page.click('button[type="submit"]');

        // 8. Confirm job is created
        await expect(page.locator('[data-testid="job-created"], [data-testid="success-message"]')).toBeVisible();
    });
});

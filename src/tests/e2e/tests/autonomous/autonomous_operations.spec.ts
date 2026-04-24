import { test, expect } from '@playwright/test';

/**
 * Comprehensive Autonomous Operations Test Suite
 * Covers Agent Zero (Autonomous Director) and Nexus Flow
 */

test.describe('Autonomous Operations - End-to-End', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="username"]', 'test');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('Agent Zero: Complete autonomous cycle with all phases', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Initial state verification
        await expect(page.locator('h1')).toContainText('Agent Zero');
        await expect(page.locator('button:has-text("Launch Director")')).toBeVisible();
        
        // Launch autonomous director
        await page.click('button:has-text("Launch Director")');
        
        // Verify transition to running state
        await expect(page.locator('button:has-text("Stop Director")')).toBeVisible({ timeout: 10000 });
        await expect(page.locator('text=Autonomous Active')).toBeVisible();
        
        // Verify all pipeline phases are visible
        const phases = ['Scout', 'Brain', 'Render', 'Post'];
        for (const phase of phases) {
            await expect(page.locator(`text=${phase}`)).toBeVisible();
        }
        
        // Verify status cards
        const statusCards = page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 .glass-card');
        await expect(statusCards).toHaveCount(4);
        
        // Engine state should show active step
        await expect(statusCards.nth(0)).toContainText(/Autonomous Active|Deactivated/);
        
        // Loop integrity should be nominal
        await expect(statusCards.nth(2)).toContainText(/Nominal/);
        
        // Verify insights oracle
        await expect(page.locator('.Autonomous Intelligence Oracle')).toBeVisible();
        
        // Stop autonomous director
        await page.click('button:has-text("Stop Director")');
        await expect(page.locator('button:has-text("Launch Director")')).toBeVisible({ timeout: 10000 });
    });

    test('Nexus Flow: Complete composition pipeline', async ({ page }) => {
        await page.goto('/nexus');
        
        // Verify page title
        await expect(page.locator('h1')).toContainText('Nexus Engine');
        
        // Configure niche
        const nicheSelect = page.locator('select').first();
        await nicheSelect.selectOption({ index: 1 });
        
        // Configure blueprint
        const blueprintSelect = page.locator('select').nth(1);
        await blueprintSelect.selectOption({ index: 0 });
        
        // Launch pipeline
        await page.click('button:has-text("Launch Pipeline")');
        
        // Verify dispatch confirmation
        await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
        
        // Verify job appears in activity stream
        await expect(page.locator('text=Activity Stream')).toBeVisible();
        
        // Wait for job completion
        const jobCard = page.locator('.flex.gap-4.p-4.rounded-2xl').first();
        await expect(jobCard.locator('text=COMPLETED')).toBeVisible({ timeout: 60000 });
    });

    test('Nexus Flow: Node visualization and interaction', async ({ page }) => {
        await page.goto('/nexus');
        
        // Launch a pipeline
        const nicheSelect = page.locator('select').first();
        await nicheSelect.selectOption({ index: 1 });
        
        const blueprintSelect = page.locator('select').nth(1);
        await blueprintSelect.selectOption({ index: 0 });
        
        await page.click('button:has-text("Launch Pipeline")');
        await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
        
        // Verify pipeline mesh
        await expect(page.locator('.aspect-21/9.rounded-6xl')).toBeVisible();
        
        // Verify node settings
        await expect(page.locator('text=Node Settings')).toBeVisible();
        await expect(page.locator('text=Execution Priority')).toBeVisible();
        await expect(page.locator('text=Ultra_High')).toBeVisible();
        
        // Verify cluster routing
        await expect(page.locator('text=Cluster Routing')).toBeVisible();
        
        // Verify live event stream
        await expect(page.locator('text=Live Event Stream')).toBeVisible();
        
        // Verify network health indicator
        await expect(page.locator('text=Network Health')).toBeVisible();
    });

    test('Autonomous Insights: Strategy generation and recommendations', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        
        // Wait for insights generation
        await page.waitForTimeout(10000);
        
        // Verify insights oracle
        const oracle = page.locator('.Autonomous Intelligence Oracle');
        await expect(oracle).toBeVisible();
        
        // Check for strategy components
        await expect(oracle.locator('text=Current Strategy')).toBeVisible();
        await expect(oracle.locator('text=Recommended Product')).toBeVisible();
        await expect(oracle.locator('text=Viral Hook')).toBeVisible();
        
        // Verify optimization card
        const optimizationCard = page.locator('.bg-emerald-500/5.border-emerald-500/10');
        await expect(optimizationCard).toBeVisible();
        await expect(optimizationCard.locator('text=Autonomous Insight')).toBeVisible();
    });

    test('Console Logging: Real-time system monitoring', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        
        // Verify console section
        await expect(page.locator('text=System Console')).toBeVisible();
        
        // Check for log entries
        const logEntries = page.locator('.font-mono.text-\[10px\]');
        await expect(logEntries.first()).toBeVisible({ timeout: 15000 });
        
        // Verify timestamp format
        const firstLog = await logEntries.first().textContent();
        expect(firstLog).toMatch(/\[\d{1,2}:\d{2}:\d{2}\]/);
        
        // Verify export button
        await expect(page.locator('button:has-text("Export")')).toBeVisible();
    });

    test('Workflow Integration: Autonomous to Nexus pipeline', async ({ page }) => {
        // Phase 1: Autonomous discovery
        await page.goto('/autonomous');
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        
        // Wait for insights
        await page.waitForTimeout(15000);
        
        // Verify insights generated
        await expect(page.locator('.Autonomous Intelligence Oracle')).toBeVisible();
        
        // Phase 2: Nexus composition
        await page.goto('/nexus');
        
        const nicheSelect = page.locator('select').first();
        await nicheSelect.selectOption({ index: 1 });
        
        const blueprintSelect = page.locator('select').nth(1);
        await blueprintSelect.selectOption({ index: 0 });
        
        await page.click('button:has-text("Launch Pipeline")');
        await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
        
        // Verify job tracking
        await expect(page.locator('text=Activity Stream')).toBeVisible();
        await expect(page.locator('.flex.gap-4.p-4.rounded-2xl').first()).toBeVisible({ timeout: 30000 });
    });

    test('Error Handling: Autonomous director force kill', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        
        // Force kill
        await page.click('button[title="Emergency Force Kill"]');
        
        // Verify termination
        await expect(page.locator('button:has-text("Launch Director")')).toBeVisible({ timeout: 10000 });
    });

    test('Performance: Multiple concurrent autonomous operations', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        
        // Navigate to Nexus while autonomous is running
        await page.goto('/nexus');
        
        // Launch multiple pipelines
        const nicheSelect = page.locator('select').first();
        const blueprintSelect = page.locator('select').nth(1);
        
        for (let i = 0; i < 3; i++) {
            await nicheSelect.selectOption({ index: (i % 3) + 1 });
            await blueprintSelect.selectOption({ index: i % 2 });
            await page.click('button:has-text("Launch Pipeline")');
            await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
            await page.waitForTimeout(500);
        }
        
        // Verify all jobs tracked
        await expect(page.locator('.flex.gap-4.p-4.rounded-2xl')).toHaveCount(3, { timeout: 30000 });
    });
});
import { test, expect } from '@playwright/test';

/**
 * Step 4: Autonomous Operations - Agent Zero & Nexus Flow
 * 
 * This test suite validates the autonomous content creation pipeline:
 * 1. Agent Zero (Autonomous Director) - Self-orchestrating trend-to-video pipeline
 * 2. Nexus Flow - Neural composition engine for high-fidelity video assembly
 * 
 * Test Flow:
 * - Login to dashboard
 * - Navigate to AUTONOMOUS section
 * - Launch Agent Zero
 * - Monitor autonomous execution states
 * - Navigate to NEXUS FLOW
 * - Trigger composition pipeline
 * - Verify node execution and job completion
 */

test.describe('Step 4: Autonomous Operations - Agent Zero & Nexus Flow', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[name="username"]', 'testuser');
        await page.fill('input[name="password"]', 'testpassword');
        await page.click('button[type="submit"]');
        await page.waitForURL('/');
    });

    test('should launch Agent Zero and verify autonomous execution states', async ({ page }) => {
        // Navigate to Autonomous section
        await page.goto('/autonomous');
        await expect(page).toHaveTitle(/Autonomous Director/);

        // Verify initial state
        await expect(page.locator('text=Agent Zero')).toBeVisible();
        await expect(page.locator('text=Launch Director')).toBeVisible();

        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        
        // Verify activation
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        await expect(page.locator('text=Autonomous Active')).toBeVisible();

        // Verify engine state card
        const engineStateCard = page.locator('.glass-card >> text=Engine State');
        await expect(engineStateCard).toBeVisible();
        
        // Verify status progression through autonomous loop
        // Should cycle through: SCOUTING -> SCREENING -> BRAINSTORMING -> RENDERING -> PUBLISHING
        await expect(page.locator('text=Scout')).toBeVisible();
        await expect(page.locator('text=Brain')).toBeVisible();
        await expect(page.locator('text=Render')).toBeVisible();
        await expect(page.locator('text=Post')).toBeVisible();

        // Verify insights oracle is populated
        await expect(page.locator('.Autonomous Intelligence Oracle')).toBeVisible();
        
        // Check for strategy insights
        const insights = page.locator('.glass-card >> text=Current Strategy');
        await expect(insights).toBeVisible({ timeout: 30000 });

        // Verify console is receiving logs
        await expect(page.locator('text=System Console')).toBeVisible();
        const consoleLogs = page.locator('.font-mono >> text=[SYSTEM]');
        await expect(consoleLogs.first()).toBeVisible({ timeout: 15000 });

        // Stop Agent Zero
        await page.click('button:has-text("Stop Director")');
        await expect(page.locator('text=Launch Director')).toBeVisible({ timeout: 10000 });
    });

    test('should trigger Nexus Flow composition and verify pipeline execution', async ({ page }) => {
        // Navigate to Nexus section
        await page.goto('/nexus');
        await expect(page).toHaveTitle(/Nexus Engine/);

        // Verify Nexus interface elements
        await expect(page.locator('text=Neural Orchestration')).toBeVisible();
        await expect(page.locator('text=Nexus Engine')).toBeVisible();

        // Select a niche for composition
        const nicheSelect = page.locator('select >> nth=0');
        await nicheSelect.waitFor({ state: 'visible' });
        
        // Get available niches
        const niches = await page.locator('select option').allTextContents();
        expect(niches.length).toBeGreaterThan(0);

        // Select first available niche
        await nicheSelect.selectOption({ index: 1 });

        // Select a pipeline recipe
        const recipeSelect = page.locator('select >> nth=1');
        await recipeSelect.waitFor({ state: 'visible' });
        await recipeSelect.selectOption({ index: 0 });

        // Launch the pipeline
        await page.click('button:has-text("Launch Pipeline")');

        // Verify pipeline dispatch
        await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });

        // Verify job appears in activity stream
        await page.goto('/nexus');
        await expect(page.locator('text=Activity Stream')).toBeVisible();
        
        // Check for active job in the list
        const jobCard = page.locator('.flex.gap-4.p-4.rounded-2xl').first();
        await expect(jobCard).toBeVisible({ timeout: 30000 });

        // Verify job status
        await expect(jobCard.locator('text=COMPLETED')).toBeVisible({ timeout: 60000 });
    });

    test('should verify autonomous node visualization and status indicators', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });

        // Verify node visualization
        const logicFlow = page.locator('.aspect-\[16\/10\].rounded-\[3rem\]');
        await expect(logicFlow).toBeVisible();

        // Verify all nodes are present
        await expect(page.locator('text=Scout')).toBeVisible();
        await expect(page.locator('text=Brain')).toBeVisible();
        await expect(page.locator('text=Render')).toBeVisible();
        await expect(page.locator('text=Post')).toBeVisible();

        // Verify status indicators
        const statusCards = page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 gap-6 .glass-card');
        await expect(statusCards).toHaveCount(4);

        // Check engine state
        await expect(statusCards.nth(0)).toContainText(/Engine State/);
        await expect(statusCards.nth(0)).toContainText(/Autonomous Active|Deactivated/);

        // Check loop integrity
        await expect(statusCards.nth(2)).toContainText(/Loop Integrity/);
        await expect(statusCards.nth(2)).toContainText(/Nominal|Degraded/);
    });

    test('should verify Nexus node pipeline visualization', async ({ page }) => {
        await page.goto('/nexus');

        // Launch a pipeline first
        const nicheSelect = page.locator('select >> nth=0');
        await nicheSelect.selectOption({ index: 1 });

        const recipeSelect = page.locator('select >> nth=1');
        await recipeSelect.selectOption({ index: 0 });

        await page.click('button:has-text("Launch Pipeline")');
        await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });

        // Verify pipeline mesh visualization
        const pipelineMesh = page.locator('.aspect-21/9.rounded-6xl.bg-zinc-950');
        await expect(pipelineMesh).toBeVisible();

        // Verify node connectors
        await expect(page.locator('text=Node Settings')).toBeVisible();
        
        // Verify execution priority
        await expect(page.locator('text=Execution Priority')).toBeVisible();
        await expect(page.locator('text=Ultra_High')).toBeVisible();

        // Verify cluster routing
        await expect(page.locator('text=Cluster Routing')).toBeVisible();
    });

    test('should verify autonomous insights and recommendations', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });

        // Wait for insights to populate
        await page.waitForTimeout(10000);

        // Verify insights oracle
        const oracle = page.locator('.Autonomous Intelligence Oracle');
        await expect(oracle).toBeVisible();

        // Check for strategy title
        const strategyTitle = oracle.locator('h4.text-2xl');
        await expect(strategyTitle).toBeVisible();

        // Verify recommended product
        await expect(oracle.locator('text=Recommended Product')).toBeVisible();
        
        // Verify viral hook
        await expect(oracle.locator('text=Viral Hook')).toBeVisible();

        // Check optimization card
        const optimizationCard = page.locator('.bg-emerald-500/5.border-emerald-500/10');
        await expect(optimizationCard).toBeVisible();
        await expect(optimizationCard.locator('text=Autonomous Insight')).toBeVisible();
    });

    test('should verify live console logging during autonomous operations', async ({ page }) => {
        await page.goto('/autonomous');
        
        // Launch Agent Zero
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });

        // Verify console section
        await expect(page.locator('text=System Console')).toBeVisible();

        // Check for live log entries
        const logEntries = page.locator('.font-mono.text-\[10px\]');
        await expect(logEntries.first()).toBeVisible({ timeout: 15000 });

        // Verify log format includes timestamps
        const firstLog = await logEntries.first().textContent();
        expect(firstLog).toMatch(/\[\d{1,2}:\d{2}:\d{2}\]/);

        // Verify export functionality
        await expect(page.locator('button:has-text("Export")')).toBeVisible();
    });

    test('should verify Nexus activity stream and job tracking', async ({ page }) => {
        await page.goto('/nexus');

        // Launch multiple pipelines
        const nicheSelect = page.locator('select >> nth=0');
        const recipeSelect = page.locator('select >> nth=1');

        for (let i = 0; i < 2; i++) {
            await nicheSelect.selectOption({ index: (i % 3) + 1 });
            await recipeSelect.selectOption({ index: i % 2 });
            await page.click('button:has-text("Launch Pipeline")');
            await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
            await page.waitForTimeout(1000);
        }

        // Navigate to activity stream
        await page.goto('/nexus');
        await expect(page.locator('text=Activity Stream')).toBeVisible();

        // Verify job cards
        const jobCards = page.locator('.flex.gap-4.p-4.rounded-2xl');
        const count = await jobCards.count();
        expect(count).toBeGreaterThan(0);

        // Check job details
        for (let i = 0; i < Math.min(count, 3); i++) {
            const card = jobCards.nth(i);
            await expect(card.locator('text=COMPLETED')).toBeVisible({ timeout: 60000 });
            await expect(card.locator('text=/[A-Z]+/')).toBeVisible(); // Niche name
        }
    });

    test('should verify autonomous to Nexus workflow integration', async ({ page }) => {
        // Step 1: Launch Agent Zero for autonomous discovery
        await page.goto('/autonomous');
        await page.click('button:has-text("Launch Director")');
        await expect(page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });

        // Wait for autonomous insights
        await page.waitForTimeout(15000);

        // Capture insights
        const insights = page.locator('.Autonomous Intelligence Oracle');
        await expect(insights.locator('text=Current Strategy')).toBeVisible();

        // Step 2: Navigate to Nexus and use insights
        await page.goto('/nexus');
        
        // Select niche based on autonomous insights
        const nicheSelect = page.locator('select >> nth=0');
        await nicheSelect.selectOption({ index: 1 });

        // Launch composition
        const recipeSelect = page.locator('select >> nth=1');
        await recipeSelect.selectOption({ index: 0 });
        await page.click('button:has-text("Launch Pipeline")');

        // Verify integration
        await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
        
        // Verify job tracking
        await expect(page.locator('text=Activity Stream')).toBeVisible();
        await expect(page.locator('.flex.gap-4.p-4.rounded-2xl').first()).toBeVisible({ timeout: 30000 });
    });
});
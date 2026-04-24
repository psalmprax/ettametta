import { Page, expect } from '@playwright/test';

/**
 * Test helpers for Autonomous Operations tests
 */

export class AutonomousTestHelper {
    constructor(private page: Page) {}

    async login(email: string = 'test@example.com', password: string = 'testpassword') {
        await this.page.goto('/login');
        await this.page.fill('input[name="email"]', email);
        await this.page.fill('input[name="password"]', password);
        await this.page.click('button[type="submit"]');
        await this.page.waitForURL('/');
    }

    async launchAgentZero() {
        await this.page.goto('/autonomous');
        await this.page.click('button:has-text("Launch Director")');
        await expect(this.page.locator('text=Stop Director')).toBeVisible({ timeout: 10000 });
        await expect(this.page.locator('text=Autonomous Active')).toBeVisible();
    }

    async stopAgentZero() {
        await this.page.click('button:has-text("Stop Director")');
        await expect(this.page.locator('button:has-text("Launch Director")')).toBeVisible({ timeout: 10000 });
    }

    async forceKillAgentZero() {
        await this.page.click('button[title="Emergency Force Kill"]');
        await expect(this.page.locator('button:has-text("Launch Director")')).toBeVisible({ timeout: 10000 });
    }

    async verifyAgentZeroPhases() {
        const phases = ['Scout', 'Brain', 'Render', 'Post'];
        for (const phase of phases) {
            await expect(this.page.locator(`text=${phase}`)).toBeVisible();
        }
    }

    async verifyStatusCards() {
        const statusCards = this.page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 .glass-card');
        await expect(statusCards).toHaveCount(4);
        
        // Engine state
        await expect(statusCards.nth(0)).toContainText(/Engine State/);
        
        // Next iteration
        await expect(statusCards.nth(1)).toContainText(/Next Iteration/);
        
        // Loop integrity
        await expect(statusCards.nth(2)).toContainText(/Loop Integrity/);
        
        // Policy
        await expect(statusCards.nth(3)).toContainText(/Policy/);
    }

    async verifyInsightsOracle() {
        const oracle = this.page.locator('.Autonomous Intelligence Oracle');
        await expect(oracle).toBeVisible();
        await expect(oracle.locator('text=Current Strategy')).toBeVisible();
        await expect(oracle.locator('text=Recommended Product')).toBeVisible();
        await expect(oracle.locator('text=Viral Hook')).toBeVisible();
    }

    async verifyConsoleLogging() {
        await expect(this.page.locator('text=System Console')).toBeVisible();
        const logEntries = this.page.locator('.font-mono.text-\[10px\]');
        await expect(logEntries.first()).toBeVisible({ timeout: 15000 });
        
        const firstLog = await logEntries.first().textContent();
        expect(firstLog).toMatch(/\[\d{1,2}:\d{2}:\d{2}\]/);
    }

    async launchNexusPipeline(nicheIndex: number = 1, blueprintIndex: number = 0) {
        await this.page.goto('/nexus');
        
        const nicheSelect = this.page.locator('select').first();
        await nicheSelect.selectOption({ index: nicheIndex });
        
        const blueprintSelect = this.page.locator('select').nth(1);
        await blueprintSelect.selectOption({ index: blueprintIndex });
        
        await this.page.click('button:has-text("Launch Pipeline")');
        await expect(this.page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
    }

    async verifyNexusPipeline() {
        await expect(this.page.locator('text=Activity Stream')).toBeVisible();
        const jobCard = this.page.locator('.flex.gap-4.p-4.rounded-2xl').first();
        await expect(jobCard.locator('text=COMPLETED')).toBeVisible({ timeout: 60000 });
    }

    async verifyNexusVisualization() {
        await expect(this.page.locator('.aspect-21/9.rounded-6xl')).toBeVisible();
        await expect(this.page.locator('text=Node Settings')).toBeVisible();
        await expect(this.page.locator('text=Execution Priority')).toBeVisible();
        await expect(this.page.locator('text=Ultra_High')).toBeVisible();
        await expect(this.page.locator('text=Cluster Routing')).toBeVisible();
        await expect(this.page.locator('text=Live Event Stream')).toBeVisible();
        await expect(this.page.locator('text=Network Health')).toBeVisible();
    }

    async getAutonomousLogs(): Promise<string[]> {
        const logs = await this.page.locator('.font-mono.text-\[10px\]').allTextContents();
        return logs;
    }

    async getNexusJobs(): Promise<any[]> {
        const jobCards = await this.page.locator('.flex.gap-4.p-4.rounded-2xl').all();
        const jobs = [];
        
        for (const card of jobCards) {
            const text = await card.textContent();
            jobs.push({ text });
        }
        
        return jobs;
    }
}

/**
 * Common test assertions
 */
export const assertions = {
    async verifyElementVisible(page: Page, selector: string, timeout: number = 5000) {
        await expect(page.locator(selector)).toBeVisible({ timeout });
    },

    async verifyElementContainsText(page: Page, selector: string, text: string, timeout: number = 5000) {
        await expect(page.locator(selector)).toContainText(text, { timeout });
    },

    async verifyElementCount(page: Page, selector: string, count: number, timeout: number = 5000) {
        await expect(page.locator(selector)).toHaveCount(count, { timeout });
    },

    async verifyUrl(page: Page, expectedUrl: string, timeout: number = 5000) {
        await expect(page).toHaveURL(expectedUrl, { timeout });
    }
};

/**
 * Test data for autonomous operations
 */
export const testData = {
    niches: [
        'AI Automation',
        'Tech Reviews',
        'Productivity',
        'Business Growth',
        'Digital Marketing'
    ],
    
    blueprints: [
        'Cinema Mode',
        'Story Factory',
        'Blueprint Templates',
        'Video Assembler'
    ],

    personas: [
        { name: 'Tech Expert', image: 'https://example.com/tech-expert.png' },
        { name: 'Business Coach', image: 'https://example.com/business-coach.png' },
        { name: 'Marketing Guru', image: 'https://example.com/marketing-guru.png' }
    ]
};

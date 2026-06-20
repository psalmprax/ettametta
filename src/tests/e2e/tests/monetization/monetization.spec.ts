import { test, expect } from '@playwright/test';
import { loginAsTestUser } from '../../helpers/auth';

test.describe('Monetization - Affiliate Links', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display affiliate links interface', async ({ page }) => {
        await page.goto('/monetization/affiliate');
        await expect(page.locator('[data-testid="affiliate-dashboard"]')).toBeVisible();
    });

    test('should add affiliate link', async ({ page }) => {
        await page.goto('/monetization/affiliate');
        await page.click('button:has-text("Add Link")');
        await page.fill('input[name="product_url"]', 'https://amazon.com/product/123');
        await page.fill('input[name="product_name"]', 'Tech Gadget');
        await page.click('button:has-text("Save")');
        await expect(page.locator('[data-testid="link-created"]')).toBeVisible();
    });

    test('should generate short affiliate URL', async ({ page }) => {
        await page.goto('/monetization/affiliate');
        await page.click('button:has-text("Add Link")');
        await page.fill('input[name="product_url"]', 'https://amazon.com/product/123');
        await page.click('button:has-text("Generate Short URL")');
        await expect(page.locator('[data-testid="short-url"]')).toBeVisible();
    });

    test('should track link clicks', async ({ page }) => {
        await page.goto('/monetization/affiliate');
        await expect(page.locator('[data-testid="click-stats"]')).toBeVisible();
    });
});

test.describe('Monetization - Revenue Tracking', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display revenue dashboard', async ({ page }) => {
        await page.goto('/monetization/revenue');
        await expect(page.locator('[data-testid="revenue-dashboard"]')).toBeVisible();
    });

    test('should show total earnings', async ({ page }) => {
        await page.goto('/monetization/revenue');
        await expect(page.locator('[data-testid="total-earnings"]')).toBeVisible();
    });

    test('should display revenue by source', async ({ page }) => {
        await page.goto('/monetization/revenue');
        await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible();
    });

    test('should export revenue report', async ({ page }) => {
        await page.goto('/monetization/revenue');
        await page.click('button:has-text("Export Report")');
        await expect(page.locator('[data-testid="report-downloaded"]')).toBeVisible();
    });
});

test.describe('Monetization - Empire Building', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display empire dashboard', async ({ page }) => {
        await page.goto('/monetization/empire');
        await expect(page.locator('[data-testid="empire-dashboard"]')).toBeVisible();
    });

    test('should create new income stream', async ({ page }) => {
        await page.goto('/monetization/empire');
        await page.click('button:has-text("Add Income Stream")');
        await page.selectOption('select[name="stream_type"]', 'affiliate');
        await page.fill('input[name="name"]', 'Amazon Associates');
        await page.click('button:has-text("Create")');
        await expect(page.locator('[data-testid="stream-created"]')).toBeVisible();
    });

    test('should track empire health', async ({ page }) => {
        await page.goto('/monetization/empire');
        await expect(page.locator('[data-testid="empire-health"]')).toBeVisible();
    });

    test('should get diversification suggestions', async ({ page }) => {
        await page.goto('/monetization/empire');
        await page.click('button:has-text("Get Suggestions")');
        await expect(page.locator('[data-testid="suggestions"]')).toBeVisible({ timeout: 30000 });
    });
});

test.describe('Monetization - Auto Merch', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display merch interface', async ({ page }) => {
        await page.goto('/monetization/merch');
        await expect(page.locator('[data-testid="merch-dashboard"]')).toBeVisible();
    });

    test('should create merchandise design', async ({ page }) => {
        await page.goto('/monetization/merch');
        await page.click('button:has-text("Create Design")');
        await page.fill('input[name="design_name"]', 'Viral Logo Tee');
        await page.fill('textarea[name="description"]', 'Cool t-shirt design');
        await page.click('button:has-text("Generate")');
        await expect(page.locator('[data-testid="design-created"]')).toBeVisible({ timeout: 30000 });
    });

    test('should add product to store', async ({ page }) => {
        await page.goto('/monetization/merch');
        await page.click('button:has-text("Add Product")');
        await page.fill('input[name="product_name"]', 'Viral T-Shirt');
        await page.fill('input[name="price"]', '29.99');
        await page.click('button:has-text("Add to Store")');
        await expect(page.locator('[data-testid="product-added"]')).toBeVisible();
    });

    test('should track merch sales', async ({ page }) => {
        await page.goto('/monetization/merch');
        await expect(page.locator('[data-testid="sales-stats"]')).toBeVisible();
    });
});

test.describe('Monetization - Product Recommendations', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display recommendations', async ({ page }) => {
        await page.goto('/monetization/recommendations');
        await expect(page.locator('[data-testid="recommendations-grid"]')).toBeVisible();
    });

    test('should get personalized product suggestions', async ({ page }) => {
        await page.goto('/monetization/recommendations');
        await page.click('button:has-text("Get Suggestions")');
        await expect(page.locator('[data-testid="suggestions-list"]')).toBeVisible({ timeout: 30000 });
    });

    test('should add recommendation to affiliate links', async ({ page }) => {
        await page.goto('/monetization/recommendations');
        await page.click('[data-testid="recommendation-card"]:first-child');
        await page.click('button:has-text("Add as Affiliate")');
        await expect(page.locator('[data-testid="link-created"]')).toBeVisible();
    });
});

test.describe('Monetization - Promo Script', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display promo script generator', async ({ page }) => {
        await page.goto('/monetization/promo');
        await expect(page.locator('[data-testid="promo-generator"]')).toBeVisible();
    });

    test('should generate promo script with AI', async ({ page }) => {
        await page.goto('/monetization/promo');
        await page.fill('textarea[name="product_info"]', 'A productivity app that saves time');
        await page.click('button:has-text("Generate Script")');
        await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({ timeout: 30000 });
    });

    test('should edit generated script', async ({ page }) => {
        await page.goto('/monetization/promo');
        await page.fill('textarea[name="product_info"]', 'Test product');
        await page.click('button:has-text("Generate Script")');
        await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({ timeout: 30000 });
        await page.click('button:has-text("Edit")');
        await expect(page.locator('[data-testid="script-editor"]')).toBeVisible();
    });

    test('should copy script to clipboard', async ({ page }) => {
        await page.goto('/monetization/promo');
        await page.fill('textarea[name="product_info"]', 'Test');
        await page.click('button:has-text("Generate Script")');
        await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({ timeout: 30000 });
        await page.click('button:has-text("Copy")');
        await expect(page.locator('[data-testid="copied-message"]')).toBeVisible();
    });
});

test.describe('Monetization - Commerce Sync', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display commerce sync interface', async ({ page }) => {
        await page.goto('/monetization/commerce-sync');
        await expect(page.locator('[data-testid="sync-dashboard"]')).toBeVisible();
    });

    test('should connect e-commerce platform', async ({ page }) => {
        await page.goto('/monetization/commerce-sync');
        await page.click('button:has-text("Connect Store")');
        await page.click('text=Shopify');
        await expect(page.locator('[data-testid="store-connected"]')).toBeVisible();
    });

    test('should sync products to video descriptions', async ({ page }) => {
        await page.goto('/monetization/commerce-sync');
        await page.click('button:has-text("Sync Products")');
        await expect(page.locator('[data-testid="sync-complete"]')).toBeVisible({ timeout: 60000 });
    });
});

test.describe('Monetization - Clone Strategy', () => {
    test.beforeEach(async ({ page }) => {
        await loginAsTestUser(page);
    });

    test('should display strategy cloning interface', async ({ page }) => {
        await page.goto('/monetization/clone');
        await expect(page.locator('[data-testid="clone-dashboard"]')).toBeVisible();
    });

    test('should analyze competitor strategy', async ({ page }) => {
        await page.goto('/monetization/clone');
        await page.fill('input[name="competitor_url"]', 'https://youtube.com/@competitor');
        await page.click('button:has-text("Analyze")');
        await expect(page.locator('[data-testid="analysis-results"]')).toBeVisible({ timeout: 60000 });
    });

    test('should generate clone recommendations', async ({ page }) => {
        await page.goto('/monetization/clone');
        await page.fill('input[name="competitor_url"]', 'https://youtube.com/@competitor');
        await page.click('button:has-text("Analyze")');
        await expect(page.locator('[data-testid="recommendations"]')).toBeVisible({ timeout: 60000 });
    });
});
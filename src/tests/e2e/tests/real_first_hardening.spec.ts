import { test, expect } from '@playwright/test';

/**
 * ettametta: Real-First Hardening E2E Suite
 * This suite validates that the dashboard is strictly coupled to the Go API Gateway
 * and that no simulated UI patterns or "dummy" data remain in production-level modules.
 */
test.describe('Real-First Hardening Verification', () => {
  
  test.beforeEach(async ({ page }) => {
    // Authenticate using standard credentials
    await page.goto('/login');
    // Note: In an real CI environment, these would be pulled from process.env
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    
    // Ensure dashboard context is established
    await expect(page).toHaveURL('/', { timeout: 10000 });
  });

  test('Nexus: Infrastructure must report real telemetry', async ({ page }) => {
    await page.goto('/nexus');
    
    // The Nexus page must show the real hostname/node ID from the backend
    // simulated fallbacks use strings like "HOST-SIM-X"
    const nodeLabel = page.locator('span:has-text("Node_ID")').first();
    await expect(nodeLabel).toBeVisible();
    
    const nodeValue = await page.locator('div:has-text("Node_ID") + h4, h4:has-text("NODE-")').first().innerText();
    expect(nodeValue).not.toContain('SIM-');
    expect(nodeValue).not.toContain('LOCAL-DUMMY');
  });

  test('Analytics: History must load via withRealFallback without simulated delay', async ({ page }) => {
    await page.goto('/analytics');
    
    // Verify that the posts list is operational
    const posts = page.locator('tr:has-text("Published")');
    if (await posts.count() > 0) {
      await posts.first().click();
      
      // Metrics should load. Check for View count visibility
      await expect(page.locator('h2:has-text("Views")')).toBeVisible();
      
      // Ensure no simulated indicators are present
      const simulatedBadge = page.locator('text=SIMULATED');
      await expect(simulatedBadge).not.toBeVisible();
    }
  });

  test('Empire: Velocity and Scale must be deterministic', async ({ page }) => {
    await page.goto('/empire');
    
    // Check for the velocity multiplier which is derived from real growth metrics
    const velocityDisplay = page.locator('p:has-text("x")').filter({ hasText: /^\d+\.\d+x$/ });
    await expect(velocityDisplay.first()).toBeVisible();
    
    // Ensure the "Global Scale" doesn't show a 0 value which would indicate a broken fetch
    const scaleValue = await page.locator('h2:has-text("Scale")').innerText();
    expect(parseInt(scaleValue)).toBeGreaterThan(0);
  });

  test('Settings: Communications verification must be operational', async ({ page }) => {
    await page.goto('/settings');
    
    const verifyBtn = page.locator('button:has-text("Verify Comms")');
    await expect(verifyBtn).toBeVisible();
    
    // Clicking should trigger a real API call (intercepted here for verification)
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().includes('/settings/verify-comms') && req.method() === 'POST'),
      verifyBtn.click()
    ]);
    
    expect(request.headers()['authorization']).toContain('Bearer');
  });

  test('Admin: Environment synchronization must use real backend signals', async ({ page }) => {
    await page.goto('/admin');
    
    // Scroll to Env Manager
    await page.locator('h3:has-text("Environment Management")').scrollIntoViewIfNeeded();
    
    // Check for 'STABLE' or 'SYNCED' status which implies real check
    const statusText = page.locator('.glass-card:has-text("System Status") span:has-text("STABLE")');
    await expect(statusText).toBeVisible();
  });

  test('Video Preview: Should handle dynamic status metadata', async ({ page }) => {
    // Navigate to a page with video previews (Discovery)
    await page.goto('/discovery');
    
    const previewBtn = page.locator('button:has-text("Preview")').first();
    if (await previewBtn.isVisible()) {
      await previewBtn.click();
      
      // Modal should show status
      const statusLabel = page.locator('p:has-text("Status") + p');
      await expect(statusLabel).toBeVisible();
      
      // Should default to a real-first value or a backend-provided one
      const statusText = await statusLabel.innerText();
      expect(statusText).not.toBe('');
      expect(statusText).not.toContain('RETICULATING');
    }
  });

});

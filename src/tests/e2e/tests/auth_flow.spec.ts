import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should register a new user', async ({ page }) => {
    await page.goto('/register');
    
    await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.fill('input[name="confirmPassword"]', 'TestPassword123!');
    await page.fill('input[name="username"]', 'testuser');
    
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/invalid|incorrect/i);
  });

  test('should logout successfully', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');
    
    await page.click('[data-testid="logout-button"]');
    await expect(page).toHaveURL('/login');
  });

  test('should handle password reset', async ({ page }) => {
    await page.goto('/login');
    await page.click('a:has-text("Forgot password?")');
    
    await expect(page).toHaveURL(/\/forgot-password/);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toContainText(/email|sent/i);
  });
});

test.describe('OAuth Authentication', () => {
  test('should show Google login option', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('button:has-text("Google")')).toBeVisible();
  });

  test('should show GitHub login option', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('button:has-text("GitHub")')).toBeVisible();
  });
});
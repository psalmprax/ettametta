import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should register a new user', async ({ page }) => {
    await page.goto('/register');
    
    const randomId = Date.now();
    await page.getByPlaceholder('you@example.com').fill(`test${randomId}@example.com`);
    await page.getByPlaceholder('Create a secure password').fill('TestPassword123!');
    
    await page.click('button[type="submit"]');
    
    // Registration redirects to login with ?registered=true
    await expect(page).toHaveURL(/\/login/);
    await expect(page).toHaveURL(/registered=true/);
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.getByPlaceholder('Enter your username').fill('samuelolle@yahoo.com');
    await page.getByPlaceholder('Enter your password').fill('Single123.');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('h1')).toContainText(/Intelligence OS/i);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.getByPlaceholder('Enter your username').fill('invalid@example.com');
    await page.getByPlaceholder('Enter your password').fill('wrongpassword');
    await page.click('button[type="submit"]');
    
    await expect(page.getByRole('alert').filter({ hasText: /incorrect|invalid/i })).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    const randomId = Date.now();
    const email = `logout${randomId}@example.com`;
    const password = 'TestPassword123!';

    // Register
    await page.goto('/register');
    await page.getByPlaceholder('you@example.com').fill(email);
    await page.getByPlaceholder('Create a secure password').fill(password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/login/);

    // Login
    await page.getByPlaceholder('Enter your username').fill(email);
    await page.getByPlaceholder('Enter your password').fill(password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Logout
    await page.getByRole('button', { name: /sign out/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
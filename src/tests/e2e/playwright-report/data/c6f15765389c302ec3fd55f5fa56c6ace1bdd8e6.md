# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin/admin_operations.spec.ts >> Admin Operations - User Management >> should search users
- Location: tests/admin/admin_operations.spec.ts:22:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    3 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Admin Operations - User Management', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
> 6   |         await page.fill('input[name="email"]', 'admin@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  7   |         await page.fill('input[name="password"]', 'adminpassword');
  8   |         await page.click('button[type="submit"]');
  9   |         await page.waitForURL('/');
  10  |     });
  11  | 
  12  |     test('should display admin panel', async ({ page }) => {
  13  |         await page.goto('/admin');
  14  |         await expect(page.locator('[data-testid="admin-dashboard"]')).toBeVisible();
  15  |     });
  16  | 
  17  |     test('should list all users', async ({ page }) => {
  18  |         await page.goto('/admin/users');
  19  |         await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
  20  |     });
  21  | 
  22  |     test('should search users', async ({ page }) => {
  23  |         await page.goto('/admin/users');
  24  |         await page.fill('[data-testid="search-input"]', 'test');
  25  |         await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
  26  |     });
  27  | 
  28  |     test('should edit user details', async ({ page }) => {
  29  |         await page.goto('/admin/users');
  30  |         await page.click('[data-testid="user-row"]:first-child');
  31  |         await page.click('button:has-text("Edit")');
  32  |         await page.fill('input[name="full_name"]', 'Updated Name');
  33  |         await page.click('button:has-text("Save")');
  34  |         await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  35  |     });
  36  | 
  37  |     test('should change user tier', async ({ page }) => {
  38  |         await page.goto('/admin/users');
  39  |         await page.click('[data-testid="user-row"]:first-child');
  40  |         await page.selectOption('select[name="tier"]', 'sovereign');
  41  |         await page.click('button:has-text("Update Tier")');
  42  |         await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  43  |     });
  44  | 
  45  |     test('should suspend user', async ({ page }) => {
  46  |         await page.goto('/admin/users');
  47  |         await page.click('[data-testid="user-row"]:first-child');
  48  |         await page.click('button:has-text("Suspend")');
  49  |         await expect(page.locator('[data-testid="user-suspended"]')).toBeVisible();
  50  |     });
  51  | });
  52  | 
  53  | test.describe('Admin Operations - System Monitoring', () => {
  54  |     test.beforeEach(async ({ page }) => {
  55  |         await page.goto('/login');
  56  |         await page.fill('input[name="email"]', 'admin@example.com');
  57  |         await page.fill('input[name="password"]', 'adminpassword');
  58  |         await page.click('button[type="submit"]');
  59  |         await page.waitForURL('/');
  60  |     });
  61  | 
  62  |     test('should display system metrics', async ({ page }) => {
  63  |         await page.goto('/admin/monitoring');
  64  |         await expect(page.locator('[data-testid="system-metrics"]')).toBeVisible();
  65  |     });
  66  | 
  67  |     test('should show API health status', async ({ page }) => {
  68  |         await page.goto('/admin/monitoring');
  69  |         await expect(page.locator('[data-testid="api-health"]')).toBeVisible();
  70  |     });
  71  | 
  72  |     test('should show database health', async ({ page }) => {
  73  |         await page.goto('/admin/monitoring');
  74  |         await expect(page.locator('[data-testid="db-health"]')).toBeVisible();
  75  |     });
  76  | 
  77  |     test('should display queue status', async ({ page }) => {
  78  |         await page.goto('/admin/monitoring');
  79  |         await expect(page.locator('[data-testid="queue-status"]')).toBeVisible();
  80  |     });
  81  | 
  82  |     test('should show storage usage', async ({ page }) => {
  83  |         await page.goto('/admin/monitoring');
  84  |         await expect(page.locator('[data-testid="storage-usage"]')).toBeVisible();
  85  |     });
  86  | });
  87  | 
  88  | test.describe('Admin Operations - Audit Logs', () => {
  89  |     test.beforeEach(async ({ page }) => {
  90  |         await page.goto('/login');
  91  |         await page.fill('input[name="email"]', 'admin@example.com');
  92  |         await page.fill('input[name="password"]', 'adminpassword');
  93  |         await page.click('button[type="submit"]');
  94  |         await page.waitForURL('/');
  95  |     });
  96  | 
  97  |     test('should display audit logs', async ({ page }) => {
  98  |         await page.goto('/admin/audit-logs');
  99  |         await expect(page.locator('[data-testid="audit-log-list"]')).toBeVisible();
  100 |     });
  101 | 
  102 |     test('should filter logs by date', async ({ page }) => {
  103 |         await page.goto('/admin/audit-logs');
  104 |         await page.fill('[data-testid="date-from"]', '2026-04-01');
  105 |         await page.fill('[data-testid="date-to"]', '2026-04-02');
  106 |         await page.click('button:has-text("Apply Filter")');
```
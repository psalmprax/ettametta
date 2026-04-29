# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin/admin_operations.spec.ts >> Admin Operations - Audit Logs >> should export audit logs
- Location: tests/admin/admin_operations.spec.ts:116:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e6]:
    - generic [ref=e8]:
      - img [ref=e10]
      - generic [ref=e13]:
        - heading "Sign In" [level=1] [ref=e14]
        - paragraph [ref=e15]: Welcome back to Ettametta
    - generic [ref=e16]:
      - generic [ref=e17]:
        - generic [ref=e18]: Username
        - generic [ref=e19]:
          - textbox "Enter your username" [ref=e20]
          - img [ref=e22]
      - generic [ref=e25]:
        - generic [ref=e26]: Password
        - generic [ref=e27]:
          - textbox "Enter your password" [ref=e28]
          - img [ref=e30]
      - generic [ref=e34] [cursor=pointer]:
        - checkbox "Remember me" [ref=e35]
        - generic [ref=e36]: Remember me
      - button "Sign In" [ref=e37]:
        - generic [ref=e38]: Sign In
    - paragraph [ref=e40]:
      - text: Don't have an account?
      - link "Create account" [ref=e41] [cursor=pointer]:
        - /url: /register
  - region "Notifications alt+T"
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Admin Operations - User Management', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         await page.goto('/login');
  6   |         await page.fill('input[name="email"]', 'admin@example.com');
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
> 90  |         await page.goto('/login');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
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
  107 |         await expect(page.locator('[data-testid="filtered-logs"]')).toBeVisible();
  108 |     });
  109 | 
  110 |     test('should filter logs by user', async ({ page }) => {
  111 |         await page.goto('/admin/audit-logs');
  112 |         await page.fill('[data-testid="user-filter"]', 'testuser');
  113 |         await expect(page.locator('[data-testid="filtered-logs"]')).toBeVisible();
  114 |     });
  115 | 
  116 |     test('should export audit logs', async ({ page }) => {
  117 |         await page.goto('/admin/audit-logs');
  118 |         await page.click('button:has-text("Export")');
  119 |         await expect(page.locator('[data-testid="export-downloaded"]')).toBeVisible();
  120 |     });
  121 | });
  122 | 
  123 | test.describe('Admin Operations - Content Moderation', () => {
  124 |     test.beforeEach(async ({ page }) => {
  125 |         await page.goto('/login');
  126 |         await page.fill('input[name="email"]', 'admin@example.com');
  127 |         await page.fill('input[name="password"]', 'adminpassword');
  128 |         await page.click('button[type="submit"]');
  129 |         await page.waitForURL('/');
  130 |     });
  131 | 
  132 |     test('should list pending content', async ({ page }) => {
  133 |         await page.goto('/admin/moderation');
  134 |         await expect(page.locator('[data-testid="pending-content"]')).toBeVisible();
  135 |     });
  136 | 
  137 |     test('should approve content', async ({ page }) => {
  138 |         await page.goto('/admin/moderation');
  139 |         await page.click('[data-testid="content-row"]:first-child');
  140 |         await page.click('button:has-text("Approve")');
  141 |         await expect(page.locator('[data-testid="content-approved"]')).toBeVisible();
  142 |     });
  143 | 
  144 |     test('should reject content', async ({ page }) => {
  145 |         await page.goto('/admin/moderation');
  146 |         await page.click('[data-testid="content-row"]:first-child');
  147 |         await page.click('button:has-text("Reject")');
  148 |         await expect(page.locator('[data-testid="content-rejected"]')).toBeVisible();
  149 |     });
  150 | 
  151 |     test('should flag content for review', async ({ page }) => {
  152 |         await page.goto('/admin/moderation');
  153 |         await page.click('[data-testid="content-row"]:first-child');
  154 |         await page.click('button:has-text("Flag")');
  155 |         await expect(page.locator('[data-testid="content-flagged"]')).toBeVisible();
  156 |     });
  157 | });
```
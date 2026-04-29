# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: accessibility.spec.ts >> Accessibility Tests >> Login page has proper ARIA labels
- Location: tests/accessibility.spec.ts:13:7

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
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
  - button "Open Next.js Dev Tools" [ref=e47] [cursor=pointer]:
    - img [ref=e48]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Accessibility Tests', () => {
  4   |   test.beforeEach(async ({ page }) => {
  5   |     // Enable accessibility diagnostics
  6   |     page.on('console', msg => {
  7   |       if (msg.type() === 'error') {
  8   |         console.log(`Console error: ${msg.text()}`);
  9   |       }
  10  |     });
  11  |   });
  12  | 
  13  |   test('Login page has proper ARIA labels', async ({ page }) => {
> 14  |     await page.goto('/login');
      |                ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  15  |     
  16  |     // Check for form labels
  17  |     const emailInput = page.locator('input[name="email"]');
  18  |     await expect(emailInput).toBeVisible();
  19  |     
  20  |     const passwordInput = page.locator('input[name="password"]');
  21  |     await expect(passwordInput).toBeVisible();
  22  |     
  23  |     const submitButton = page.locator('button[type="submit"]');
  24  |     await expect(submitButton).toBeVisible();
  25  |     
  26  |     // Check for accessibility violations
  27  |     const violations = await page.evaluate(() => {
  28  |       // Basic accessibility checks
  29  |       const issues = [];
  30  |       
  31  |       // Check for images without alt
  32  |       document.querySelectorAll('img').forEach(img => {
  33  |         if (!img.alt) issues.push('Image without alt text');
  34  |       });
  35  |       
  36  |       // Check for form inputs without labels
  37  |       document.querySelectorAll('input').forEach(input => {
  38  |         const id = input.getAttribute('id');
  39  |         const ariaLabel = input.getAttribute('aria-label');
  40  |         const ariaLabelledby = input.getAttribute('aria-labelledby');
  41  |         const label = document.querySelector(`label[for="${input.name}"]`);
  42  |         
  43  |         if (!id && !ariaLabel && !ariaLabelledby && !label) {
  44  |           issues.push(`Input ${input.name || input.type} without label`);
  45  |         }
  46  |       });
  47  |       
  48  |       return issues;
  49  |     });
  50  |     
  51  |     console.log('Accessibility issues:', violations);
  52  |     expect(violations.length).toBeLessThan(5);
  53  |   });
  54  | 
  55  |   test('Dashboard has keyboard navigation', async ({ page }) => {
  56  |     await page.goto('/login');
  57  |     await page.fill('input[name="email"]', 'test@example.com');
  58  |     await page.fill('input[name="password"]', 'testpassword');
  59  |     await page.click('button[type="submit"]');
  60  |     await page.waitForURL('/');
  61  |     
  62  |     // Test keyboard navigation
  63  |     await page.keyboard.press('Tab');
  64  |     await page.keyboard.press('Tab');
  65  |     
  66  |     // Should be able to navigate with keyboard
  67  |     const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
  68  |     expect(focusedElement).toBeDefined();
  69  |   });
  70  | 
  71  |   test('No focus traps in modal dialogs', async ({ page }) => {
  72  |     await page.goto('/login');
  73  |     await page.fill('input[name="email"]', 'test@example.com');
  74  |     await page.fill('input[name="password"]', 'testpassword');
  75  |     await page.click('button[type="submit"]');
  76  |     await page.waitForURL('/');
  77  |     
  78  |     // Go to discovery and open a modal if available
  79  |     await page.goto('/discovery');
  80  |     
  81  |     // Check if any modal has proper focus management
  82  |     const modalCheck = await page.evaluate(() => {
  83  |       const modals = document.querySelectorAll('[role="dialog"]');
  84  |       let hasProperFocus = true;
  85  |       
  86  |       modals.forEach(modal => {
  87  |         const focusable = modal.querySelectorAll('button, input, select, textarea, a[href]');
  88  |         if (focusable.length === 0) hasProperFocus = false;
  89  |         
  90  |         const hasClose = modal.querySelector('[aria-label="Close"], [role="close"]');
  91  |         if (!hasClose) hasProperFocus = false;
  92  |       });
  93  |       
  94  |       return { modalCount: modals.length, hasProperFocus };
  95  |     });
  96  |     
  97  |     console.log('Modal check:', modalCheck);
  98  |   });
  99  | 
  100 |   test('Color contrast meets WCAG AA', async ({ page }) => {
  101 |     await page.goto('/login');
  102 |     
  103 |     const contrastIssues = await page.evaluate(() => {
  104 |       const issues = [];
  105 |       
  106 |       // Check text contrast (simplified check)
  107 |       const elements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, a, button');
  108 |       
  109 |       elements.forEach(el => {
  110 |         const style = window.getComputedStyle(el);
  111 |         const color = style.color;
  112 |         const bgColor = style.backgroundColor;
  113 |         
  114 |         // Basic check - if color is light and bg is dark or vice versa
```
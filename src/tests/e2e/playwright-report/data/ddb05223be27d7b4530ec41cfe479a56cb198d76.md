# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: stack_switching.spec.ts >> Video Stack Switching >> should show Sovereign tier requirement for OS stack
- Location: tests/stack_switching.spec.ts:40:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    4 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"
    - waiting for navigation to finish...
    - navigated to "http://localhost:3000/login"
    - waiting for" http://localhost:3000/login" navigation to finish...
    - navigated to "http://localhost:3000/login"

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
    - generic [ref=e50]:
      - text: Compiling
      - generic [ref=e51]:
        - generic [ref=e52]: .
        - generic [ref=e53]: .
        - generic [ref=e54]: .
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Video Stack Switching', () => {
  4  |     test.beforeEach(async ({ page }) => {
  5  |         // Login
  6  |         await page.goto('/login');
> 7  |         await page.fill('input[name="email"]', 'test@example.com');
     |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  8  |         await page.fill('input[name="password"]', 'testpassword');
  9  |         await page.click('button[type="submit"]');
  10 |         await page.waitForURL('/');
  11 |     });
  12 | 
  13 |     test('should switch between Cloud and Open-Source stacks', async ({ page }) => {
  14 |         await page.goto('/creation');
  15 |         await page.click('text=AI Generation');
  16 | 
  17 |         // 1. Initially should be on Cloud Stack
  18 |         const engineSelect = page.locator('select[name="engine"]');
  19 |         await expect(page.locator('text=Premium Cloud')).toBeVisible();
  20 |         
  21 |         // Check if a cloud-only engine is available
  22 |         const options = await engineSelect.innerText();
  23 |         expect(options).toContain('Lite4K');
  24 | 
  25 |         // 2. Click on Open-Source Stack toggle/card
  26 |         await page.click('[data-testid="os-stack-card"]');
  27 |         
  28 |         // 3. Verify stack switched
  29 |         await expect(page.locator('text=Open-Source Infrastructure')).toBeVisible();
  30 |         
  31 |         // 4. Verify engines updated to OS models
  32 |         const osOptions = await engineSelect.innerText();
  33 |         expect(osOptions).toContain('HunyuanVideo');
  34 |         expect(osOptions).toContain('Wan-2.2');
  35 |         
  36 |         // 5. Verify the "Transient" badge is visible for some models
  37 |         await expect(page.locator('text=Transient').first()).toBeVisible();
  38 |     });
  39 | 
  40 |     test('should show Sovereign tier requirement for OS stack', async ({ page }) => {
  41 |         // This test assumes the test user is "Free" or "Pro"
  42 |         await page.goto('/creation');
  43 |         await page.click('text=AI Generation');
  44 |         await page.click('[data-testid="os-stack-card"]');
  45 | 
  46 |         await page.fill('textarea[name="prompt"]', 'Test Prompt');
  47 |         await page.selectOption('select[name="engine"]', 'hunyuan');
  48 | 
  49 |         await page.click('button[type="submit"]');
  50 | 
  51 |         // Should show Sovereign requirement
  52 |         await expect(page.locator('text=Upgrade to Sovereign')).toBeVisible();
  53 |     });
  54 | });
  55 | 
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: accessibility.spec.ts >> Screen Reader Compatibility >> Form inputs have associated labels
- Location: tests/accessibility.spec.ts:172:7

# Error details

```
Error: page.evaluate: Execution context was destroyed, most likely because of a navigation
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
  115 |         if (color === 'rgba(0, 0, 0, 0)' || bgColor === 'rgba(0, 0, 0, 0)') {
  116 |           return; // Skip transparent
  117 |         }
  118 |         
  119 |         // This is a simplified check - real implementation would calculate contrast ratio
  120 |         if (color && bgColor && color !== bgColor) {
  121 |           // Check for low contrast combinations
  122 |           if (color.includes('255, 255, 255') && bgColor.includes('255, 255, 255')) {
  123 |             // Both white - potential issue
  124 |           }
  125 |         }
  126 |       });
  127 |       
  128 |       return issues;
  129 |     });
  130 |     
  131 |     console.log('Contrast issues:', contrastIssues);
  132 |     // This is a placeholder - real implementation would use axe-core or similar
  133 |   });
  134 | 
  135 |   test('Page has proper language attribute', async ({ page }) => {
  136 |     await page.goto('/login');
  137 |     
  138 |     const html = await page.locator('html');
  139 |     const lang = await html.getAttribute('lang');
  140 |     
  141 |     expect(lang).toBeTruthy();
  142 |   });
  143 | 
  144 |   test('Headings follow proper hierarchy', async ({ page }) => {
  145 |     await page.goto('/login');
  146 |     await page.fill('input[name="email"]', 'test@example.com');
  147 |     await page.fill('input[name="password"]', 'testpassword');
  148 |     await page.click('button[type="submit"]');
  149 |     await page.waitForURL('/');
  150 |     
  151 |     const headingCheck = await page.evaluate(() => {
  152 |       const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
  153 |       const levels = headings.map(h => parseInt(h.tagName.replace('H', '')));
  154 |       
  155 |       let invalid = false;
  156 |       for (let i = 1; i < levels.length; i++) {
  157 |         if (levels[i] - levels[i-1] > 1) {
  158 |           invalid = true;
  159 |           break;
  160 |         }
  161 |       }
  162 |       
  163 |       return { count: headings.length, validHierarchy: !invalid };
  164 |     });
  165 |     
  166 |     console.log('Heading check:', headingCheck);
  167 |     // Allow some flexibility - just log the result
  168 |   });
  169 | });
  170 | 
  171 | test.describe('Screen Reader Compatibility', () => {
  172 |   test('Form inputs have associated labels', async ({ page }) => {
  173 |     await page.goto('/login');
  174 |     
> 175 |     const labelCheck = await page.evaluate(() => {
      |                                   ^ Error: page.evaluate: Execution context was destroyed, most likely because of a navigation
  176 |       const inputs = Array.from(document.querySelectorAll('input'));
  177 |       const results = inputs.map(input => {
  178 |         const id = input.getAttribute('id');
  179 |         const name = input.getAttribute('name');
  180 |         const ariaLabel = input.getAttribute('aria-label');
  181 |         const ariaLabelledby = input.getAttribute('aria-labelledby');
  182 |         const label = id ? document.querySelector(`label[for="${id}"]`) : null;
  183 |         
  184 |         const hasLabel = !!(ariaLabel || ariaLabelledby || label);
  185 |         return { name, hasLabel };
  186 |       });
  187 |       
  188 |       return results;
  189 |     });
  190 |     
  191 |     const labelsMissing = labelCheck.filter(r => !r.hasLabel);
  192 |     console.log('Inputs without labels:', labelsMissing);
  193 |     
  194 |     expect(labelsMissing.length).toBeLessThan(3);
  195 |   });
  196 | 
  197 |   test('Buttons have accessible names', async ({ page }) => {
  198 |     await page.goto('/login');
  199 |     
  200 |     const buttonCheck = await page.evaluate(() => {
  201 |       const buttons = Array.from(document.querySelectorAll('button'));
  202 |       return buttons.map(btn => ({
  203 |         text: btn.textContent?.trim().substring(0, 20),
  204 |         ariaLabel: btn.getAttribute('aria-label'),
  205 |         hasAccessibleName: !!(btn.textContent?.trim() || btn.getAttribute('aria-label'))
  206 |       }));
  207 |     });
  208 |     
  209 |     const buttonsWithoutNames = buttonCheck.filter(b => !b.hasAccessibleName);
  210 |     expect(buttonsWithoutNames.length).toBeLessThan(2);
  211 |   });
  212 | });
```
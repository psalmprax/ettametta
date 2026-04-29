# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: accessibility.spec.ts >> Screen Reader Compatibility >> Buttons have accessible names
- Location: tests/accessibility.spec.ts:197:7

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/login", waiting until "load"

```

# Test source

```ts
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
  175 |     const labelCheck = await page.evaluate(() => {
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
> 198 |     await page.goto('/login');
      |                ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
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
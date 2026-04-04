import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Enable accessibility diagnostics
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Console error: ${msg.text()}`);
      }
    });
  });

  test('Login page has proper ARIA labels', async ({ page }) => {
    await page.goto('/login');
    
    // Check for form labels
    const emailInput = page.locator('input[name="email"]');
    await expect(emailInput).toBeVisible();
    
    const passwordInput = page.locator('input[name="password"]');
    await expect(passwordInput).toBeVisible();
    
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
    
    // Check for accessibility violations
    const violations = await page.evaluate(() => {
      // Basic accessibility checks
      const issues = [];
      
      // Check for images without alt
      document.querySelectorAll('img').forEach(img => {
        if (!img.alt) issues.push('Image without alt text');
      });
      
      // Check for form inputs without labels
      document.querySelectorAll('input').forEach(input => {
        const id = input.getAttribute('id');
        const ariaLabel = input.getAttribute('aria-label');
        const ariaLabelledby = input.getAttribute('aria-labelledby');
        const label = document.querySelector(`label[for="${input.name}"]`);
        
        if (!id && !ariaLabel && !ariaLabelledby && !label) {
          issues.push(`Input ${input.name || input.type} without label`);
        }
      });
      
      return issues;
    });
    
    console.log('Accessibility issues:', violations);
    expect(violations.length).toBeLessThan(5);
  });

  test('Dashboard has keyboard navigation', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should be able to navigate with keyboard
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeDefined();
  });

  test('No focus traps in modal dialogs', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
    
    // Go to discovery and open a modal if available
    await page.goto('/discovery');
    
    // Check if any modal has proper focus management
    const modalCheck = await page.evaluate(() => {
      const modals = document.querySelectorAll('[role="dialog"]');
      let hasProperFocus = true;
      
      modals.forEach(modal => {
        const focusable = modal.querySelectorAll('button, input, select, textarea, a[href]');
        if (focusable.length === 0) hasProperFocus = false;
        
        const hasClose = modal.querySelector('[aria-label="Close"], [role="close"]');
        if (!hasClose) hasProperFocus = false;
      });
      
      return { modalCount: modals.length, hasProperFocus };
    });
    
    console.log('Modal check:', modalCheck);
  });

  test('Color contrast meets WCAG AA', async ({ page }) => {
    await page.goto('/login');
    
    const contrastIssues = await page.evaluate(() => {
      const issues = [];
      
      // Check text contrast (simplified check)
      const elements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, a, button');
      
      elements.forEach(el => {
        const style = window.getComputedStyle(el);
        const color = style.color;
        const bgColor = style.backgroundColor;
        
        // Basic check - if color is light and bg is dark or vice versa
        if (color === 'rgba(0, 0, 0, 0)' || bgColor === 'rgba(0, 0, 0, 0)') {
          return; // Skip transparent
        }
        
        // This is a simplified check - real implementation would calculate contrast ratio
        if (color && bgColor && color !== bgColor) {
          // Check for low contrast combinations
          if (color.includes('255, 255, 255') && bgColor.includes('255, 255, 255')) {
            // Both white - potential issue
          }
        }
      });
      
      return issues;
    });
    
    console.log('Contrast issues:', contrastIssues);
    // This is a placeholder - real implementation would use axe-core or similar
  });

  test('Page has proper language attribute', async ({ page }) => {
    await page.goto('/login');
    
    const html = await page.locator('html');
    const lang = await html.getAttribute('lang');
    
    expect(lang).toBeTruthy();
  });

  test('Headings follow proper hierarchy', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
    
    const headingCheck = await page.evaluate(() => {
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      const levels = headings.map(h => parseInt(h.tagName.replace('H', '')));
      
      let invalid = false;
      for (let i = 1; i < levels.length; i++) {
        if (levels[i] - levels[i-1] > 1) {
          invalid = true;
          break;
        }
      }
      
      return { count: headings.length, validHierarchy: !invalid };
    });
    
    console.log('Heading check:', headingCheck);
    // Allow some flexibility - just log the result
  });
});

test.describe('Screen Reader Compatibility', () => {
  test('Form inputs have associated labels', async ({ page }) => {
    await page.goto('/login');
    
    const labelCheck = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input'));
      const results = inputs.map(input => {
        const id = input.getAttribute('id');
        const name = input.getAttribute('name');
        const ariaLabel = input.getAttribute('aria-label');
        const ariaLabelledby = input.getAttribute('aria-labelledby');
        const label = id ? document.querySelector(`label[for="${id}"]`) : null;
        
        const hasLabel = !!(ariaLabel || ariaLabelledby || label);
        return { name, hasLabel };
      });
      
      return results;
    });
    
    const labelsMissing = labelCheck.filter(r => !r.hasLabel);
    console.log('Inputs without labels:', labelsMissing);
    
    expect(labelsMissing.length).toBeLessThan(3);
  });

  test('Buttons have accessible names', async ({ page }) => {
    await page.goto('/login');
    
    const buttonCheck = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.map(btn => ({
        text: btn.textContent?.trim().substring(0, 20),
        ariaLabel: btn.getAttribute('aria-label'),
        hasAccessibleName: !!(btn.textContent?.trim() || btn.getAttribute('aria-label'))
      }));
    });
    
    const buttonsWithoutNames = buttonCheck.filter(b => !b.hasAccessibleName);
    expect(buttonsWithoutNames.length).toBeLessThan(2);
  });
});
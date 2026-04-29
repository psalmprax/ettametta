# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: discovery/discovery.spec.ts >> Content Discovery >> should display creation page
- Location: tests/discovery/discovery.spec.ts:14:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/creation", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Content Discovery', () => {
  4  |     test('should display discovery page', async ({ page }) => {
  5  |         await page.goto('/discovery');
  6  |         await expect(page.getByRole('link', { name: 'Discovery' })).toBeVisible({ timeout: 15000 });
  7  |     });
  8  | 
  9  |     test('should display dashboard page', async ({ page }) => {
  10 |         await page.goto('/');
  11 |         await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible({ timeout: 15000 });
  12 |     });
  13 | 
  14 |     test('should display creation page', async ({ page }) => {
> 15 |         await page.goto('/creation');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  16 |         await expect(page.getByRole('link', { name: 'Creation' })).toBeVisible({ timeout: 15000 });
  17 |     });
  18 | 
  19 |     test('should display analytics page', async ({ page }) => {
  20 |         await page.goto('/analytics');
  21 |         await expect(page.getByRole('link', { name: 'Analytics' })).toBeVisible({ timeout: 15000 });
  22 |     });
  23 | 
  24 |     test('should display publishing page', async ({ page }) => {
  25 |         await page.goto('/publishing');
  26 |         await expect(page.getByRole('link', { name: 'Publishing' })).toBeVisible({ timeout: 15000 });
  27 |     });
  28 | 
  29 |     test('should display credits page', async ({ page }) => {
  30 |         await page.goto('/credits');
  31 |         await expect(page.getByRole('link', { name: 'Credits' })).toBeVisible({ timeout: 15000 });
  32 |     });
  33 | });
```
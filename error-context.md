# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: nexus/full_workflow.spec.ts >> Nexus Engine - Full System E2E Workflow >> should run E2E Nexus Pipeline from Dispatch to Scene Customization
- Location: tests/nexus/full_workflow.spec.ts:4:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Nexus Video Synthesizer')
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 15000ms
  - waiting for locator('text=Nexus Video Synthesizer')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - generic [ref=e7]:
      - generic [ref=e9]:
        - img [ref=e11]
        - generic [ref=e14]:
          - heading "Sign In" [level=1] [ref=e15]
          - paragraph [ref=e16]: Welcome back to Ettametta
      - generic [ref=e17]:
        - generic [ref=e18]:
          - generic [ref=e19]: Username
          - generic [ref=e20]:
            - textbox "Username" [ref=e21]:
              - /placeholder: Enter your username
            - img [ref=e23]
        - generic [ref=e26]:
          - generic [ref=e27]: Password
          - generic [ref=e28]:
            - textbox "Password" [ref=e29]:
              - /placeholder: Enter your password
            - img [ref=e31]
        - generic [ref=e35] [cursor=pointer]:
          - checkbox "Remember me" [ref=e36]
          - generic [ref=e37]: Remember me
        - button "Sign In" [ref=e38]:
          - generic [ref=e39]: Sign In
        - generic [ref=e44]: Or continue with
        - button "Continue with Google" [ref=e45]:
          - generic [ref=e46]:
            - img [ref=e47]
            - text: Continue with Google
      - paragraph [ref=e50]:
        - text: Don't have an account?
        - link "Create account" [ref=e51] [cursor=pointer]:
          - /url: /register
    - region "Notifications alt+T"
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('Nexus Engine - Full System E2E Workflow', () => {
  4   |     test('should run E2E Nexus Pipeline from Dispatch to Scene Customization', async ({ page }) => {
  5   |         // 1. Dynamic User Registration
  6   |         const timestamp = Date.now();
  7   |         const email = `nexus_user_${timestamp}@example.com`;
  8   |         const username = `nexus_user_${timestamp}`;
  9   |         const password = 'TestPassword123!';
  10  | 
  11  |         console.log(`[E2E] Navigating to registration page with username: ${username}`);
  12  |         await page.goto('/register');
  13  |         await expect(page.locator('h1')).toContainText(/create account/i);
  14  | 
  15  |         await page.getByPlaceholder('you@example.com').fill(email);
  16  |         await page.getByPlaceholder('Choose a display name').fill(username);
  17  |         await page.getByPlaceholder('Create a secure password').fill(password);
  18  |         await page.click('button[type="submit"]');
  19  | 
  20  |         console.log('[E2E] Awaiting redirection to login...');
  21  |         await expect(page).toHaveURL(/\/login/, { timeout: 15000 });
  22  | 
  23  |         // 2. Authentication / Login
  24  |         console.log('[E2E] Logging in with new credentials...');
  25  |         await page.fill('input[name="username"]', email);
  26  |         await page.fill('input[name="password"]', password);
  27  |         await page.click('button[type="submit"]');
  28  | 
  29  |         console.log('[E2E] Awaiting redirect to dashboard...');
  30  |         await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
  31  | 
  32  |         // 3. Navigation to Nexus
  33  |         console.log('[E2E] Navigating to /nexus?engine=orchestrator...');
  34  |         await page.goto('/nexus?engine=orchestrator');
  35  |         await expect(page.locator('text=Dispatch Pipeline')).toBeVisible({ timeout: 15000 });
  36  | 
  37  |         // 4. Select niche and blueprint
  38  |         console.log('[E2E] Selecting target niche and architecture blueprint...');
  39  |         const targetSelect = page.locator('select').first();
  40  |         const archSelect = page.locator('select').nth(1);
  41  | 
  42  |         await targetSelect.selectOption({ label: 'AI Technology' });
  43  |         await archSelect.selectOption({ label: 'Topic Narrative Fusion' });
  44  | 
  45  |         // 5. Dispatch the pipeline
  46  |         console.log('[E2E] Dispatching pipeline...');
  47  |         await page.click('button:has-text("Dispatch Pipeline")');
  48  | 
  49  |         // Check for success notification/toast
  50  |         await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
  51  |         console.log('[E2E] Pipeline dispatch confirmed.');
  52  | 
  53  |         // 6. Navigation to Pipeline History and poll for completion
  54  |         console.log('[E2E] Navigating to Pipeline History...');
  55  |         await page.click('button:has-text("Pipeline History")');
  56  |         await expect(page).toHaveURL(/engine=history/);
  57  | 
  58  |         // Wait for DesignCards to load
  59  |         const designCard = page.locator('div:has(h3:has-text("PIPELINE_"))').first();
  60  |         await expect(designCard).toBeVisible({ timeout: 15000 });
  61  | 
  62  |         console.log('[E2E] Polling for pipeline completion...');
  63  |         let isCompleted = false;
  64  |         for (let attempt = 0; attempt < 20; attempt++) {
  65  |             const statusSpan = designCard.locator('span.shrink-0');
  66  |             const statusText = await statusSpan.innerText();
  67  |             console.log(`[E2E] Current job status: ${statusText} (attempt ${attempt + 1}/20)`);
  68  |             if (statusText.includes('COMPLETED')) {
  69  |                 isCompleted = true;
  70  |                 break;
  71  |             }
  72  |             if (statusText.includes('FAILED')) {
  73  |                 throw new Error('Pipeline job failed on remote server');
  74  |             }
  75  |             // Wait 3 seconds
  76  |             await page.waitForTimeout(3000);
  77  |             // Reload page to fetch updates if websocket hasn't updated
  78  |             if (attempt % 3 === 2) {
  79  |                 console.log('[E2E] Reloading page to fetch latest job statuses...');
  80  |                 await page.reload();
  81  |                 await page.click('button:has-text("Pipeline History")');
  82  |                 await expect(page).toHaveURL(/engine=history/);
  83  |                 await expect(designCard).toBeVisible({ timeout: 15000 });
  84  |             }
  85  |         }
  86  | 
  87  |         if (!isCompleted) {
  88  |             throw new Error('Pipeline job did not complete within the timeout');
  89  |         }
  90  | 
  91  |         console.log('[E2E] Triggering Scene Preview Modal...');
  92  |         const previewButton = designCard.locator('button').first();
  93  |         await previewButton.click();
  94  | 
  95  |         // 7. Preview Modal Functional Verification
  96  |         console.log('[E2E] Verifying Preview Modal visibility...');
> 97  |         await expect(page.locator('text=Nexus Video Synthesizer')).toBeVisible({ timeout: 15000 });
      |                                                                    ^ Error: expect(locator).toBeVisible() failed
  98  |         
  99  |         // Assert that preview scenes are loaded successfully and not displaying empty placeholder
  100 |         await expect(page.locator('text=Visual Direction / Prompt').first()).toBeVisible({ timeout: 15000 });
  101 | 
  102 |         // 8. Swap Asset Flow inside Modal Drawer
  103 |         console.log('[E2E] Clicking Swap Asset...');
  104 |         const swapButton = page.locator('button:has-text("Swap Asset")').first();
  105 |         await swapButton.click();
  106 | 
  107 |         console.log('[E2E] Selecting candidate Digital Flow...');
  108 |         const candidateCard = page.locator('text=Digital Flow').first();
  109 |         await candidateCard.click();
  110 | 
  111 |         // Verify swap success toast
  112 |         await expect(page.locator('text=Asset replaced visually')).toBeVisible({ timeout: 10000 });
  113 |         console.log('[E2E] Asset swap verified successfully.');
  114 | 
  115 |         // 9. Style Modulator Preset Choice
  116 |         console.log('[E2E] Modifying style preset to Amber Warm...');
  117 |         const presetCard = page.locator('text=Amber Warm').first();
  118 |         await presetCard.click();
  119 | 
  120 |         // 10. Close Modal and complete
  121 |         console.log('[E2E] Closing Scene Preview Modal...');
  122 |         const closeModalButton = page.locator('button:has(svg, img)').first();
  123 |         await closeModalButton.click();
  124 |         
  125 |         await expect(page.locator('text=Nexus Video Synthesizer')).not.toBeVisible();
  126 |         console.log('[E2E] Full-system Nexus pipeline E2E test completed successfully.');
  127 |     });
  128 | });
  129 | 
```
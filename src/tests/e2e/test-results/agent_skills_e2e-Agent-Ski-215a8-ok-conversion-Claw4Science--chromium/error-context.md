# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: agent_skills_e2e.spec.ts >> Agent Skills E2E - Universal Integration >> should verify Scientific Hook conversion (Claw4Science)
- Location: tests/agent_skills_e2e.spec.ts:45:9

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
  3   | test.describe('Agent Skills E2E - Universal Integration', () => {
  4   |     test.beforeEach(async ({ page }) => {
  5   |         // 1. Mock Authentication
  6   |         await page.route('**/api/auth/me', async (route) => {
  7   |             await route.fulfill({
  8   |                 status: 200,
  9   |                 contentType: 'application/json',
  10  |                 body: JSON.stringify({
  11  |                     id: 1,
  12  |                     email: 'test@example.com',
  13  |                     subscription: 'PRO'
  14  |                 }),
  15  |             });
  16  |         });
  17  | 
  18  |         // 2. Mock Initial Data (Blueprints, Niches, Jobs)
  19  |         await page.route('**/api/nexus/blueprints', async (route) => {
  20  |             await route.fulfill({ status: 200, body: JSON.stringify([]) });
  21  |         });
  22  |         await page.route('**/api/discovery/niches', async (route) => {
  23  |             await route.fulfill({ status: 200, body: JSON.stringify(['AI Automation']) });
  24  |         });
  25  |         await page.route('**/api/nexus/jobs', async (route) => {
  26  |             await route.fulfill({ status: 200, body: JSON.stringify([]) });
  27  |         });
  28  |         await page.route('**/api/agent/capabilities', async (route) => {
  29  |             await route.fulfill({ 
  30  |                 status: 200, 
  31  |                 body: JSON.stringify({ 
  32  |                     capabilities: ['PAPERCLIP', 'SCIENTIFIC', 'REMOTION', 'CLAW4SCIENCE'] 
  33  |                 }) 
  34  |             });
  35  |         });
  36  | 
  37  |         // Login flow
> 38  |         await page.goto('/login');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  39  |         await page.fill('input[name="email"]', 'test@example.com');
  40  |         await page.fill('input[name="password"]', 'testpassword');
  41  |         await page.click('button[type="submit"]');
  42  |         await page.waitForURL('/nexus');
  43  |     });
  44  | 
  45  |     test('should verify Scientific Hook conversion (Claw4Science)', async ({ page }) => {
  46  |         // Mock the chat response for Scientific Conversion
  47  |         await page.route('**/api/agent/chat', async (route) => {
  48  |             await route.fulfill({
  49  |                 status: 200,
  50  |                 contentType: 'application/json',
  51  |                 body: JSON.stringify({
  52  |                     response: "🧪 [SCIENTIFIC] Signal Detected. Converting to Science-Pop...\n\nHook: 'Did you know GPU vRAM isn't just memory? It's the oxygen of AI.'\n\nScript generated successfully.",
  53  |                     status: "success"
  54  |                 }),
  55  |             });
  56  |         });
  57  | 
  58  |         const input = page.getByTestId('agent-chat-input');
  59  |         await input.fill('Convert this technical paper on GPU architecture into a viral TikTok script.');
  60  |         await page.getByTestId('agent-chat-send').click();
  61  | 
  62  |         const messages = page.getByTestId('agent-chat-messages');
  63  |         await expect(messages).toContainText(/SCIENTIFIC/);
  64  |         await expect(messages).toContainText(/Science-Pop/);
  65  |         await expect(messages).toContainText(/GPU vRAM/);
  66  |     });
  67  | 
  68  |     test('should verify Paperclip KPI tracking performance', async ({ page }) => {
  69  |         // Mock the chat response for Paperclip KPI
  70  |         await page.route('**/api/agent/chat', async (route) => {
  71  |             await route.fulfill({
  72  |                 status: 200,
  73  |                 contentType: 'application/json',
  74  |                 body: JSON.stringify({
  75  |                     response: "📈 [PAPERCLIP] KPI Synced for Job VF-102. Viral Signal Detected: 5,200 views. Recommendation: Triggering organic variation loop.",
  76  |                     status: "success"
  77  |                 }),
  78  |             });
  79  |         });
  80  | 
  81  |         const input = page.getByTestId('agent-chat-input');
  82  |         await input.fill('Record performance for TikTok job VF-102: 5200 views.');
  83  |         await page.getByTestId('agent-chat-send').click();
  84  | 
  85  |         const messages = page.getByTestId('agent-chat-messages');
  86  |         await expect(messages).toContainText(/PAPERCLIP/);
  87  |         await expect(messages).toContainText(/Viral Signal Detected/);
  88  |         await expect(messages).toContainText(/VF-102/);
  89  |     });
  90  | 
  91  |     test('should verify Remotion Render dispatch', async ({ page }) => {
  92  |         // Mock the chat response for Remotion Render
  93  |         await page.route('**/api/agent/chat', async (route) => {
  94  |             await route.fulfill({
  95  |                 status: 200,
  96  |                 contentType: 'application/json',
  97  |                 body: JSON.stringify({
  98  |                     response: "🎬 [REMOTION] Programmatic Overlay Dispatched. Composition: 'ScienceOverlay'. Job ID: REM-998.",
  99  |                     status: "success"
  100 |                 }),
  101 |             });
  102 |         });
  103 | 
  104 |         const input = page.getByTestId('agent-chat-input');
  105 |         await input.fill('Trigger a Remotion render for the science video with high-fidelity overlays.');
  106 |         await page.getByTestId('agent-chat-send').click();
  107 | 
  108 |         const messages = page.getByTestId('agent-chat-messages');
  109 |         await expect(messages).toContainText(/REMOTION/);
  110 |         await expect(messages).toContainText(/REM-998/);
  111 |         await expect(messages).toContainText(/ScienceOverlay/);
  112 |     });
  113 | });
  114 | 
```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: analytics/analytics.spec.ts >> Analytics >> should display empire page
- Location: tests/analytics/analytics.spec.ts:19:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/empire", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - link "Ettametta" [ref=e6] [cursor=pointer]:
        - /url: /
        - img [ref=e8]
        - generic [ref=e10]: Ettametta
      - button "Create with Agent" [ref=e12]:
        - img [ref=e13]
        - text: Create with Agent
      - navigation [ref=e15]:
        - link "Explore" [ref=e16] [cursor=pointer]:
          - /url: /dashboard
          - img [ref=e17]
          - generic [ref=e20]: Explore
        - link "Discovery" [ref=e21] [cursor=pointer]:
          - /url: /discovery
          - img [ref=e22]
          - generic [ref=e25]: Discovery
        - link "Experiments" [ref=e26] [cursor=pointer]:
          - /url: /dashboard/experiments
          - img [ref=e27]
          - generic [ref=e29]: Experiments
        - link "Intelligence" [ref=e30] [cursor=pointer]:
          - /url: /dashboard/intelligence
          - img [ref=e31]
          - generic [ref=e39]: Intelligence
        - link "My Assets" [ref=e40] [cursor=pointer]:
          - /url: /transformation
          - img [ref=e41]
          - generic [ref=e45]: My Assets
        - generic [ref=e46]: Creation Tools
        - link "AI Video Generator New" [ref=e47] [cursor=pointer]:
          - /url: /creation
          - img [ref=e48]
          - generic [ref=e51]:
            - generic [ref=e52]: AI Video Generator
            - generic [ref=e53]: New
        - link "AI Video Editor" [ref=e54] [cursor=pointer]:
          - /url: /dashboard/video-editor
          - img [ref=e55]
          - generic [ref=e59]: AI Video Editor
        - link "Image to Video" [ref=e60] [cursor=pointer]:
          - /url: /image-to-video
          - img [ref=e61]
          - generic [ref=e65]: Image to Video
        - link "Text to Video" [ref=e66] [cursor=pointer]:
          - /url: /text-to-video
          - img [ref=e67]
          - generic [ref=e70]: Text to Video
        - link "AI Image Nano Banana" [ref=e71] [cursor=pointer]:
          - /url: /ai-image
          - img [ref=e72]
          - generic [ref=e75]:
            - generic [ref=e76]: AI Image
            - generic [ref=e77]: Nano Banana
        - link "AI Image Editor" [ref=e78] [cursor=pointer]:
          - /url: /ai-image-editor
          - img [ref=e79]
          - generic [ref=e82]: AI Image Editor
        - link "AI Avatar" [ref=e83] [cursor=pointer]:
          - /url: /ai-avatar
          - img [ref=e84]
          - generic [ref=e88]: AI Avatar
        - link "AI Music" [ref=e89] [cursor=pointer]:
          - /url: /ai-music
          - img [ref=e90]
          - generic [ref=e95]: AI Music
        - link "Text To Speech" [ref=e96] [cursor=pointer]:
          - /url: /tts
          - img [ref=e97]
          - generic [ref=e102]: Text To Speech
      - generic [ref=e104]:
        - generic [ref=e105]:
          - img "User" [ref=e107]
          - generic [ref=e108]:
            - generic [ref=e109]: Guest User
            - generic [ref=e110]: Pro Plan
        - button "Sign Out" [ref=e111]:
          - img [ref=e112]
          - text: Sign Out
    - generic [ref=e115]:
      - banner [ref=e116]:
        - generic [ref=e117]:
          - button [ref=e118]:
            - img [ref=e119]
          - generic [ref=e122]:
            - img [ref=e123]
            - generic [ref=e128]: "20"
            - generic [ref=e130]: Free Trial
          - generic [ref=e132] [cursor=pointer]: S
      - main [ref=e133]:
        - generic [ref=e135]:
          - generic [ref=e136]:
            - generic [ref=e137]:
              - generic [ref=e140]: Empire Protocol
              - heading "Empire Registry" [level=1] [ref=e141]
              - paragraph [ref=e142]: Neural Synchronization Active
            - button "Refresh_Sync" [ref=e143]:
              - img [ref=e144]
              - generic [ref=e149]: Refresh_Sync
          - generic [ref=e150]:
            - generic [ref=e151]:
              - generic [ref=e152]:
                - generic [ref=e153]:
                  - generic [ref=e154]:
                    - heading "Algorithm Sentinel" [level=3] [ref=e155]
                    - paragraph [ref=e156]: Platform Drift Analyzer
                  - generic [ref=e157]: INITIALIZING...
                - generic [ref=e159]:
                  - img [ref=e160]
                  - generic [ref=e163]:
                    - generic [ref=e164]: "--%"
                    - generic [ref=e165]: Sync Score
                - paragraph [ref=e167]: "Strategic Pivots Required:"
              - generic [ref=e168]:
                - img [ref=e170]
                - generic [ref=e173]:
                  - heading "Regional Footprint" [level=4] [ref=e174]
                  - paragraph [ref=e175]: "Multi-Account: 0"
            - generic [ref=e176]:
              - generic [ref=e177]:
                - generic [ref=e178]:
                  - generic [ref=e179]:
                    - img [ref=e181]
                    - heading "Strategy Lab" [level=3] [ref=e185]
                    - paragraph [ref=e186]: Select a winning blueprint and clone it to related niches with one click.
                  - generic [ref=e187]:
                    - combobox [ref=e188] [cursor=pointer]:
                      - option "NO NICHES FOUND" [disabled]
                    - button "Launch Empire Protocol" [ref=e189]:
                      - img [ref=e190]
                      - text: Launch Empire Protocol
                - generic [ref=e193]:
                  - img [ref=e195]
                  - heading "Cross-Account Velocity" [level=3] [ref=e198]
                  - paragraph [ref=e200]: Establish accounts to see velocity metrics.
                - generic [ref=e201]:
                  - img [ref=e203]
                  - heading "Revenue Matrix" [level=3] [ref=e206]
                  - generic [ref=e207]:
                    - generic [ref=e208]:
                      - generic [ref=e209]: Total Revenue
                      - generic [ref=e210]: $0.00
                    - generic [ref=e211]:
                      - generic [ref=e212]: EPM
                      - generic [ref=e213]: $0.00
              - generic [ref=e214]:
                - generic [ref=e216]:
                  - img [ref=e218]
                  - generic [ref=e220]:
                    - heading "Monetization Engine" [level=3] [ref=e221]
                    - paragraph [ref=e222]: Digital Product Promo Generator
                - generic [ref=e223]:
                  - generic [ref=e224]:
                    - paragraph [ref=e225]: Enter product name to generate a high-conversion affiliate video script.
                    - textbox "e.g. Zen Stoic Journal" [ref=e226]
                    - button "Initialize Promo Synthesis" [disabled] [ref=e227]:
                      - img [ref=e228]
                      - text: Initialize Promo Synthesis
                  - generic [ref=e231]:
                    - img [ref=e232]
                    - paragraph [ref=e235]: Awaiting Product Intel
              - generic [ref=e236]:
                - generic [ref=e238]:
                  - img [ref=e240]
                  - generic [ref=e243]:
                    - heading "Affiliate Network" [level=3] [ref=e244]
                    - paragraph [ref=e245]: Link Management & Tracking
                - generic [ref=e246]:
                  - generic [ref=e247]:
                    - paragraph [ref=e248]: Add affiliate links to auto-inject into your content.
                    - textbox "Product Name" [ref=e249]
                    - textbox "Affiliate URL" [ref=e250]
                    - textbox "CTA Text (e.g. Get 20% Off)" [ref=e251]
                    - button "Add Affiliate Link" [disabled] [ref=e252]:
                      - img [ref=e253]
                      - text: Add Affiliate Link
                  - generic [ref=e257]:
                    - img [ref=e258]
                    - paragraph [ref=e261]: No Affiliate Links
              - generic [ref=e262]:
                - generic [ref=e264]:
                  - img [ref=e266]
                  - generic [ref=e269]:
                    - heading "Auto-Merch Engine" [level=3] [ref=e270]
                    - paragraph [ref=e271]: Trend-Driven Product Generation
                - generic [ref=e272]:
                  - paragraph [ref=e273]: Enter a trending topic to auto-generate merchandise.
                  - textbox "e.g. Stoic Quotes 2026" [ref=e274]
                  - button "Generate Auto-Merch" [disabled] [ref=e275]:
                    - img [ref=e276]
                    - text: Generate Auto-Merch
              - generic [ref=e279]:
                - generic [ref=e281]:
                  - img [ref=e283]
                  - generic [ref=e287]:
                    - heading "Commerce Sync" [level=3] [ref=e288]
                    - paragraph [ref=e289]: Shopify Integration
                - button "Sync Shopify" [ref=e290]:
                  - img [ref=e291]
                  - text: Sync Shopify
              - generic [ref=e296]:
                - generic [ref=e298]:
                  - img [ref=e300]
                  - generic [ref=e303]:
                    - heading "AI Link Recommender" [level=3] [ref=e304]
                    - paragraph [ref=e305]: Smart Affiliate Suggestions
                - generic [ref=e306]:
                  - generic [ref=e307]:
                    - textbox "Niche (e.g. Stoic Wisdom)" [ref=e308]
                    - textbox "Paste your script text here..." [ref=e309]
                    - button "Get Recommendations" [disabled] [ref=e310]:
                      - img [ref=e311]
                      - text: Get Recommendations
                  - generic [ref=e315]:
                    - img [ref=e316]
                    - paragraph [ref=e319]: Awaiting Script Analysis
              - generic [ref=e320]:
                - generic [ref=e321]:
                  - img [ref=e323]
                  - generic [ref=e327]:
                    - heading "Neural Repositories" [level=3] [ref=e328]
                    - paragraph [ref=e329]: Winning Blueprint History
                - generic [ref=e331]: Waiting for Initial Conquests...
            - generic [ref=e332]:
              - generic [ref=e333]: INITIALIZING NEURAL LINK...
              - generic [ref=e334]:
                - generic [ref=e336]:
                  - heading "Strategic Timeline" [level=3] [ref=e337]
                  - paragraph [ref=e338]: Sentinel Drift Events
                - generic [ref=e340]:
                  - img [ref=e343]
                  - heading "0% Autonomy" [level=4] [ref=e347]
                  - paragraph [ref=e348]: System is operating in CONNECTING mode. Review sentinel recommendations.
        - button [ref=e349]:
          - img [ref=e350]
  - region "Notifications alt+T"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Analytics', () => {
  4  |     test('should display analytics page', async ({ page }) => {
  5  |         await page.goto('/analytics');
  6  |         await expect(page.getByRole('link', { name: 'Analytics' })).toBeVisible({ timeout: 15000 });
  7  |     });
  8  | 
  9  |     test('should display dashboard', async ({ page }) => {
  10 |         await page.goto('/');
  11 |         await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
  12 |     });
  13 | 
  14 |     test('should display credits page', async ({ page }) => {
  15 |         await page.goto('/credits');
  16 |         await expect(page.getByRole('link', { name: 'Credits' })).toBeVisible({ timeout: 15000 });
  17 |     });
  18 | 
  19 |     test('should display empire page', async ({ page }) => {
> 20 |         await page.goto('/empire');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  21 |         await expect(page.getByRole('link', { name: 'Empire' })).toBeVisible({ timeout: 15000 });
  22 |     });
  23 | });
```
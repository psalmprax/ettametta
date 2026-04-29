# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: analytics/analytics.spec.ts >> Analytics >> should display credits page
- Location: tests/analytics/analytics.spec.ts:14:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/credits", waiting until "load"

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
              - generic [ref=e140]: Credits System
              - heading "Credit Vault" [level=1] [ref=e141]
              - paragraph [ref=e142]: Manage your credit balance, purchase packages, and track usage.
            - button "Refresh" [ref=e143]:
              - img [ref=e144]
              - generic [ref=e149]: Refresh
          - generic [ref=e152]:
            - generic [ref=e153]:
              - generic [ref=e156]: Current Balance
              - generic [ref=e157]:
                - heading "--" [level=2] [ref=e158]
                - generic [ref=e159]: Credits
              - generic [ref=e161]: "Tier: Free"
            - img [ref=e163]
          - generic [ref=e168]:
            - generic [ref=e169]:
              - img [ref=e170]
              - heading "Credit Packages" [level=3] [ref=e172]
            - paragraph [ref=e175]: Loading packages...
          - generic [ref=e176]:
            - generic [ref=e177]:
              - generic [ref=e178]:
                - img [ref=e180]
                - generic [ref=e182]:
                  - heading "Credit Costs" [level=3] [ref=e183]
                  - paragraph [ref=e184]: Action Cost Matrix
              - paragraph [ref=e187]: Loading cost matrix...
            - generic [ref=e188]:
              - generic [ref=e189]:
                - img [ref=e191]
                - generic [ref=e194]:
                  - heading "Transaction History" [level=3] [ref=e195]
                  - paragraph [ref=e196]: Recent Credit Activity
              - generic [ref=e198]:
                - img [ref=e199]
                - paragraph [ref=e202]: No transactions yet
          - generic [ref=e203]:
            - generic [ref=e204]:
              - img [ref=e205]
              - heading "Referral Program" [level=3] [ref=e209]
            - generic [ref=e210]:
              - generic [ref=e211]:
                - generic [ref=e212]:
                  - heading "Your Referral Code" [level=3] [ref=e213]
                  - paragraph [ref=e214]: Share and earn credits
                - generic [ref=e215]:
                  - generic [ref=e216]:
                    - generic [ref=e217]: LOADING...
                    - button [ref=e218]:
                      - img [ref=e219]
                  - generic [ref=e222]:
                    - img [ref=e223]
                    - paragraph [ref=e229]: Generating link...
              - generic [ref=e230]:
                - generic [ref=e231]:
                  - heading "Referral Stats" [level=3] [ref=e232]
                  - paragraph [ref=e233]: Network growth metrics
                - generic [ref=e234]:
                  - generic [ref=e235]:
                    - img [ref=e236]
                    - paragraph [ref=e241]: "0"
                    - paragraph [ref=e242]: Referrals
                  - generic [ref=e243]:
                    - img [ref=e244]
                    - paragraph [ref=e249]: "0"
                    - paragraph [ref=e250]: Earned
              - generic [ref=e251]:
                - generic [ref=e252]:
                  - heading "Apply Code" [level=3] [ref=e253]
                  - paragraph [ref=e254]: Have a referral code?
                - generic [ref=e255]:
                  - textbox "Enter referral code" [ref=e256]
                  - button "Apply Code" [disabled] [ref=e257]:
                    - img [ref=e258]
                    - text: Apply Code
            - generic [ref=e262]:
              - generic [ref=e263]:
                - heading "Referral Statistics" [level=3] [ref=e264]
                - paragraph [ref=e265]: Overall referral performance
              - generic [ref=e266]:
                - generic [ref=e267]:
                  - img [ref=e269]
                  - generic [ref=e274]:
                    - paragraph [ref=e275]: "0"
                    - paragraph [ref=e276]: Total Referrals
                - generic [ref=e277]:
                  - img [ref=e279]
                  - generic [ref=e284]:
                    - paragraph [ref=e285]: "0"
                    - paragraph [ref=e286]: Total Credits Earned from Referrals
        - button [ref=e287]:
          - img [ref=e288]
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
> 15 |         await page.goto('/credits');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  16 |         await expect(page.getByRole('link', { name: 'Credits' })).toBeVisible({ timeout: 15000 });
  17 |     });
  18 | 
  19 |     test('should display empire page', async ({ page }) => {
  20 |         await page.goto('/empire');
  21 |         await expect(page.getByRole('link', { name: 'Empire' })).toBeVisible({ timeout: 15000 });
  22 |     });
  23 | });
```
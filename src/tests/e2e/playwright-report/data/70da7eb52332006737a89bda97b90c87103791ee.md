# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: analytics/analytics.spec.ts >> Analytics >> should display analytics page
- Location: tests/analytics/analytics.spec.ts:4:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/analytics", waiting until "load"

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
        - generic [ref=e139]:
          - generic [ref=e140]:
            - generic [ref=e142]:
              - heading "Intel Core" [level=1] [ref=e143]
              - paragraph [ref=e144]:
                - img [ref=e145]
                - text: "SIGNAL_STRENGTH: 98.4%"
                - text: "ENCRYPTION: AES_256_NEURAL"
            - generic [ref=e152]:
              - generic [ref=e153]:
                - generic [ref=e154]: SYSTEM_TIME
                - generic [ref=e155]: 2:42:35 AM
              - button "EXPORT_DATA_PACK" [ref=e156]
          - generic [ref=e157]:
            - generic [ref=e158]:
              - generic [ref=e159]:
                - img [ref=e160]
                - generic [ref=e163]: NET_REACH
              - generic [ref=e164]:
                - heading "0" [level=4] [ref=e165]
                - generic [ref=e166]:
                  - img [ref=e167]
                  - generic [ref=e170]: +14.2%
            - generic [ref=e171]:
              - generic [ref=e174]: ATTENTION_DECAY
              - generic [ref=e175]:
                - heading "0%" [level=4] [ref=e176]
                - generic [ref=e177]:
                  - img [ref=e178]
                  - generic [ref=e181]: +14.2%
            - generic [ref=e182]:
              - generic [ref=e185]: VIRAL_VELOCITY
              - generic [ref=e186]:
                - heading "Nominal" [level=4] [ref=e187]
                - generic [ref=e188]:
                  - img [ref=e189]
                  - generic [ref=e192]: +14.2%
            - generic [ref=e193]:
              - generic [ref=e197]: NEURAL_CONVERSION
              - generic [ref=e198]:
                - heading "0.0%" [level=4] [ref=e199]
                - generic [ref=e200]:
                  - img [ref=e201]
                  - generic [ref=e204]: +14.2%
          - generic [ref=e205]:
            - generic [ref=e209]:
              - heading "Retention Spectrum" [level=3] [ref=e210]
              - paragraph [ref=e211]: DEEP_BEHAVIORAL_MAPPING // T+0_INITIAL_HOOK
            - generic [ref=e218]:
              - generic [ref=e219]:
                - heading "AI_OPTIMIZATION" [level=3] [ref=e221]:
                  - img [ref=e222]
                  - text: AI_OPTIMIZATION
                - generic [ref=e226]:
                  - generic [ref=e227]:
                    - paragraph [ref=e228]: "\"The signal drops by 14% at the 5s mark. Recommend injecting a high-velocity visual hook at this node.\""
                    - paragraph [ref=e229]: "CONFIDENCE: 99.2%"
                  - button "RE-OPTIMIZE_SEGMENT" [ref=e230]
              - generic [ref=e231]:
                - heading "NETWORK_RELIABILITY" [level=3] [ref=e232]: NETWORK_RELIABILITY
                - generic [ref=e234]:
                  - generic [ref=e235]:
                    - generic [ref=e236]: "ORACLE_MAE:"
                    - generic [ref=e237]: "0.024"
                  - paragraph [ref=e239]: SYSTEM_OPTIMIZED
          - generic [ref=e240]:
            - generic [ref=e241]:
              - generic [ref=e243]:
                - heading "Global Propagation" [level=3] [ref=e244]
                - paragraph [ref=e245]: LIVE_GEOSPATIAL_STREAM
              - generic [ref=e248]: ACTIVE_PULSE
            - generic [ref=e249]:
              - generic [ref=e250]:
                - heading "Viral Matrix" [level=3] [ref=e251]
                - img [ref=e252]
              - generic [ref=e256]:
                - generic [ref=e257]:
                  - generic [ref=e258]: Retention Hook
                  - generic [ref=e260]: PEAK
                - generic [ref=e261]:
                  - generic [ref=e262]: Share Velocity
                  - generic [ref=e264]: STABLE
                - generic [ref=e265]:
                  - generic [ref=e266]: Comment Sentiment
                  - generic [ref=e268]: RECOVERING
                - generic [ref=e269]:
                  - generic [ref=e270]: Thumbnail CTR
                  - generic [ref=e272]: PEAK
        - button [ref=e273]:
          - img [ref=e274]
  - region "Notifications alt+T"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Analytics', () => {
  4  |     test('should display analytics page', async ({ page }) => {
> 5  |         await page.goto('/analytics');
     |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
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
  20 |         await page.goto('/empire');
  21 |         await expect(page.getByRole('link', { name: 'Empire' })).toBeVisible({ timeout: 15000 });
  22 |     });
  23 | });
```
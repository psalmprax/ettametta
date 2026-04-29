# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creation/video_models.spec.ts >> Video Model - Engine Selection UI >> should show engine options in creation page
- Location: tests/creation/video_models.spec.ts:169:9

# Error details

```
TimeoutError: page.goto: Timeout 60000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/creation", waiting until "load"

```

# Test source

```ts
  70  |                     style: 'cinematic',
  71  |                     aspect_ratio: '9:16'
  72  |                 },
  73  |                 timeout: 10000
  74  |             });
  75  |             console.log('HunyuanVideo response:', response.status());
  76  |         } catch (e) {
  77  |             console.log('HunyuanVideo endpoint test - server may be busy');
  78  |         }
  79  |     });
  80  | 
  81  |     test('should test Wan model endpoint', async ({ request }) => {
  82  |         try {
  83  |             const response = await request.post(`${GPU_SERVER_URL}/generate`, {
  84  |                 data: {
  85  |                     prompt: 'A test video',
  86  |                     engine: 'wan',
  87  |                     style: 'default',
  88  |                     aspect_ratio: '16:9'
  89  |                 },
  90  |                 timeout: 10000
  91  |             });
  92  |             console.log('Wan response:', response.status());
  93  |         } catch (e) {
  94  |             console.log('Wan endpoint test - server may be busy');
  95  |         }
  96  |     });
  97  | 
  98  |     test('should test Mochi model endpoint', async ({ request }) => {
  99  |         try {
  100 |             const response = await request.post(`${GPU_SERVER_URL}/generate`, {
  101 |                 data: {
  102 |                     prompt: 'A test video',
  103 |                     engine: 'mochi',
  104 |                     style: 'cinematic',
  105 |                     aspect_ratio: '16:9'
  106 |                 },
  107 |                 timeout: 10000
  108 |             });
  109 |             console.log('Mochi response:', response.status());
  110 |         } catch (e) {
  111 |             console.log('Mochi endpoint test - server may be busy');
  112 |         }
  113 |     });
  114 | });
  115 | 
  116 | test.describe('Video Model - API Server Integration', () => {
  117 |     test('should connect to API server video endpoint', async ({ request }) => {
  118 |         const response = await request.get(`${API_SERVER_URL}/api/v1/video/jobs`);
  119 |         expect([200, 401, 403, 404]).toContain(response.status());
  120 |     });
  121 | 
  122 |     test('should check video transform endpoint', async ({ request }) => {
  123 |         const response = await request.post(`${API_SERVER_URL}/api/v1/video/transform`, {
  124 |             data: {
  125 |                 source_uri: 'https://example.com/test.mp4',
  126 |                 niche: 'Technology',
  127 |                 platform: 'YouTube Shorts'
  128 |             }
  129 |         });
  130 |         expect([200, 401, 403, 404, 422]).toContain(response.status());
  131 |     });
  132 | 
  133 |     test('should check video generate endpoint', async ({ request }) => {
  134 |         const response = await request.post(`${API_SERVER_URL}/api/v1/video/generate`, {
  135 |             data: {
  136 |                 prompt: 'A test video',
  137 |                 engine: 'ltx-video',
  138 |                 style: 'Cinematic',
  139 |                 aspect_ratio: '9:16'
  140 |             }
  141 |         });
  142 |         expect([200, 401, 403, 404, 422]).toContain(response.status());
  143 |     });
  144 | });
  145 | 
  146 | test.describe('Video Model - Dashboard UI Tests', () => {
  147 |     test('should display creation page with form', async ({ page }) => {
  148 |         await page.goto('/creation');
  149 |         await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  150 |     });
  151 | 
  152 |     test('should display transformation page', async ({ page }) => {
  153 |         await page.goto('/transformation');
  154 |         await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  155 |     });
  156 | 
  157 |     test('should display autonomous page', async ({ page }) => {
  158 |         await page.goto('/autonomous');
  159 |         await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  160 |     });
  161 | 
  162 |     test('should display nexus page', async ({ page }) => {
  163 |         await page.goto('/nexus');
  164 |         await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  165 |     });
  166 | });
  167 | 
  168 | test.describe('Video Model - Engine Selection UI', () => {
  169 |     test('should show engine options in creation page', async ({ page }) => {
> 170 |         await page.goto('/creation');
      |                    ^ TimeoutError: page.goto: Timeout 60000ms exceeded.
  171 |         const pageText = await page.locator('body').innerText();
  172 |         
  173 |         const hasEngineOptions = 
  174 |             pageText.toLowerCase().includes('engine') ||
  175 |             pageText.toLowerCase().includes('model') ||
  176 |             pageText.toLowerCase().includes('generation') ||
  177 |             pageText.toLowerCase().includes('video');
  178 |         
  179 |         expect(hasEngineOptions).toBe(true);
  180 |     });
  181 | });
  182 | 
  183 | test.describe('Video Model - Model Mutual Exclusion', () => {
  184 |     test('should show VRAM status indicator', async ({ page }) => {
  185 |         await page.goto('/');
  186 |         
  187 |         const pageText = await page.locator('body').innerText();
  188 |         const hasVRAMStatus = 
  189 |             pageText.toLowerCase().includes('vram') ||
  190 |             pageText.toLowerCase().includes('memory') ||
  191 |             pageText.toLowerCase().includes('gpu') ||
  192 |             pageText.toLowerCase().includes('engine');
  193 |         
  194 |         console.log('VRAM status present:', hasVRAMStatus);
  195 |     });
  196 | });
  197 | 
  198 | test.describe('Video Model - Model VRAM Requirements', () => {
  199 |     test('should document model requirements', () => {
  200 |         const modelRequirements = {
  201 |             'AnimateDiff': { vram: '2.58GB', status: 'Working', gpu: 'RTX A6000 48GB' },
  202 |             'CogVideoX-2b': { vram: '14.61GB', status: 'Working', gpu: 'RTX A6000 48GB' },
  203 |             'Wan 2.1 T2V 1.3B': { vram: '15.35GB', status: 'Working', gpu: 'RTX A6000 48GB' },
  204 |             'HunyuanVideo 480p': { vram: '~20GB', status: 'Working', gpu: 'RTX A6000 48GB' },
  205 |             'Mochi': { vram: '30.29GB', status: 'Working', gpu: 'RTX A6000 48GB' },
  206 |             'HunyuanVideo 720p': { vram: '>48GB', status: 'Failed (OOM)', gpu: 'RTX A6000 48GB' },
  207 |             'LTX-Video': { vram: 'N/A', status: 'Failed (Disk Space)', gpu: 'RTX A6000 48GB' },
  208 |             'Wan 2.2 I2V 14B': { vram: '>48GB', status: 'Failed (OOM)', gpu: 'RTX A6000 48GB' }
  209 |         };
  210 |         
  211 |         console.log('Model Requirements:', JSON.stringify(modelRequirements, null, 2));
  212 |         
  213 |         expect(Object.keys(modelRequirements).length).toBe(8);
  214 |     });
  215 | });
```
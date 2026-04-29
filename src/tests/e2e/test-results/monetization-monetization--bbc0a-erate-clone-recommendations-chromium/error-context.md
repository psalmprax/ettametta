# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: monetization/monetization.spec.ts >> Monetization - Clone Strategy >> should generate clone recommendations
- Location: tests/monetization/monetization.spec.ts:261:9

# Error details

```
TimeoutError: page.fill: Timeout 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"]')
    4 × waiting for" http://localhost:3000/login" navigation to finish...
      - navigated to "http://localhost:3000/login"

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
  143 | 
  144 | test.describe('Monetization - Product Recommendations', () => {
  145 |     test.beforeEach(async ({ page }) => {
  146 |         await page.goto('/login');
  147 |         await page.fill('input[name="email"]', 'test@example.com');
  148 |         await page.fill('input[name="password"]', 'testpassword');
  149 |         await page.click('button[type="submit"]');
  150 |         await page.waitForURL('/');
  151 |     });
  152 | 
  153 |     test('should display recommendations', async ({ page }) => {
  154 |         await page.goto('/monetization/recommendations');
  155 |         await expect(page.locator('[data-testid="recommendations-grid"]')).toBeVisible();
  156 |     });
  157 | 
  158 |     test('should get personalized product suggestions', async ({ page }) => {
  159 |         await page.goto('/monetization/recommendations');
  160 |         await page.click('button:has-text("Get Suggestions")');
  161 |         await expect(page.locator('[data-testid="suggestions-list"]')).toBeVisible({ timeout: 30000 });
  162 |     });
  163 | 
  164 |     test('should add recommendation to affiliate links', async ({ page }) => {
  165 |         await page.goto('/monetization/recommendations');
  166 |         await page.click('[data-testid="recommendation-card"]:first-child');
  167 |         await page.click('button:has-text("Add as Affiliate")');
  168 |         await expect(page.locator('[data-testid="link-created"]')).toBeVisible();
  169 |     });
  170 | });
  171 | 
  172 | test.describe('Monetization - Promo Script', () => {
  173 |     test.beforeEach(async ({ page }) => {
  174 |         await page.goto('/login');
  175 |         await page.fill('input[name="email"]', 'test@example.com');
  176 |         await page.fill('input[name="password"]', 'testpassword');
  177 |         await page.click('button[type="submit"]');
  178 |         await page.waitForURL('/');
  179 |     });
  180 | 
  181 |     test('should display promo script generator', async ({ page }) => {
  182 |         await page.goto('/monetization/promo');
  183 |         await expect(page.locator('[data-testid="promo-generator"]')).toBeVisible();
  184 |     });
  185 | 
  186 |     test('should generate promo script with AI', async ({ page }) => {
  187 |         await page.goto('/monetization/promo');
  188 |         await page.fill('textarea[name="product_info"]', 'A productivity app that saves time');
  189 |         await page.click('button:has-text("Generate Script")');
  190 |         await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({ timeout: 30000 });
  191 |     });
  192 | 
  193 |     test('should edit generated script', async ({ page }) => {
  194 |         await page.goto('/monetization/promo');
  195 |         await page.fill('textarea[name="product_info"]', 'Test product');
  196 |         await page.click('button:has-text("Generate Script")');
  197 |         await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({ timeout: 30000 });
  198 |         await page.click('button:has-text("Edit")');
  199 |         await expect(page.locator('[data-testid="script-editor"]')).toBeVisible();
  200 |     });
  201 | 
  202 |     test('should copy script to clipboard', async ({ page }) => {
  203 |         await page.goto('/monetization/promo');
  204 |         await page.fill('textarea[name="product_info"]', 'Test');
  205 |         await page.click('button:has-text("Generate Script")');
  206 |         await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({ timeout: 30000 });
  207 |         await page.click('button:has-text("Copy")');
  208 |         await expect(page.locator('[data-testid="copied-message"]')).toBeVisible();
  209 |     });
  210 | });
  211 | 
  212 | test.describe('Monetization - Commerce Sync', () => {
  213 |     test.beforeEach(async ({ page }) => {
  214 |         await page.goto('/login');
  215 |         await page.fill('input[name="email"]', 'test@example.com');
  216 |         await page.fill('input[name="password"]', 'testpassword');
  217 |         await page.click('button[type="submit"]');
  218 |         await page.waitForURL('/');
  219 |     });
  220 | 
  221 |     test('should display commerce sync interface', async ({ page }) => {
  222 |         await page.goto('/monetization/commerce-sync');
  223 |         await expect(page.locator('[data-testid="sync-dashboard"]')).toBeVisible();
  224 |     });
  225 | 
  226 |     test('should connect e-commerce platform', async ({ page }) => {
  227 |         await page.goto('/monetization/commerce-sync');
  228 |         await page.click('button:has-text("Connect Store")');
  229 |         await page.click('text=Shopify');
  230 |         await expect(page.locator('[data-testid="store-connected"]')).toBeVisible();
  231 |     });
  232 | 
  233 |     test('should sync products to video descriptions', async ({ page }) => {
  234 |         await page.goto('/monetization/commerce-sync');
  235 |         await page.click('button:has-text("Sync Products")');
  236 |         await expect(page.locator('[data-testid="sync-complete"]')).toBeVisible({ timeout: 60000 });
  237 |     });
  238 | });
  239 | 
  240 | test.describe('Monetization - Clone Strategy', () => {
  241 |     test.beforeEach(async ({ page }) => {
  242 |         await page.goto('/login');
> 243 |         await page.fill('input[name="email"]', 'test@example.com');
      |                    ^ TimeoutError: page.fill: Timeout 30000ms exceeded.
  244 |         await page.fill('input[name="password"]', 'testpassword');
  245 |         await page.click('button[type="submit"]');
  246 |         await page.waitForURL('/');
  247 |     });
  248 | 
  249 |     test('should display strategy cloning interface', async ({ page }) => {
  250 |         await page.goto('/monetization/clone');
  251 |         await expect(page.locator('[data-testid="clone-dashboard"]')).toBeVisible();
  252 |     });
  253 | 
  254 |     test('should analyze competitor strategy', async ({ page }) => {
  255 |         await page.goto('/monetization/clone');
  256 |         await page.fill('input[name="competitor_url"]', 'https://youtube.com/@competitor');
  257 |         await page.click('button:has-text("Analyze")');
  258 |         await expect(page.locator('[data-testid="analysis-results"]')).toBeVisible({ timeout: 60000 });
  259 |     });
  260 | 
  261 |     test('should generate clone recommendations', async ({ page }) => {
  262 |         await page.goto('/monetization/clone');
  263 |         await page.fill('input[name="competitor_url"]', 'https://youtube.com/@competitor');
  264 |         await page.click('button:has-text("Analyze")');
  265 |         await expect(page.locator('[data-testid="recommendations"]')).toBeVisible({ timeout: 60000 });
  266 |     });
  267 | });
```
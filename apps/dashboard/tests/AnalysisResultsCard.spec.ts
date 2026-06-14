import { test, expect } from "@playwright/test";

/**
 * Playwright tests for the AnalysisResultsCard component.
 *
 * These tests navigate to the test fixture page at /dev/analysis-card
 * and verify rendering, interactions, and visual states of the component
 * in isolation from the backend.
 *
 * Run:  cd apps/dashboard && npx playwright test tests/AnalysisResultsCard.spec.ts
 */

// ── Helpers ────────────────────────────────────────────────────────────────

/** Navigate to the high-score section (first card on the page). */
const highScoreSection = (page: any) =>
    page.locator('[data-testid="section-high-score"]');

/** Navigate to the section with the Create Video button. */
const withButtonSection = (page: any) =>
    page.locator('[data-testid="section-with-button"]');

/** Navigate to the low-score section. */
const lowScoreSection = (page: any) =>
    page.locator('[data-testid="section-low-score"]');

/** Navigate to the loading state section. */
const loadingSection = (page: any) =>
    page.locator('[data-testid="section-loading"]');

/** Navigate to the section with onClose callback. */
const onCloseSection = (page: any) =>
    page.locator('[data-testid="section-on-close"]');

test.describe("AnalysisResultsCard", () => {
    test.beforeEach(async ({ page }) => {
        // Inject fake auth credentials before the page loads so AuthContext
        // sees a valid session and doesn't redirect to /login.
        await page.addInitScript(() => {
            const fakeToken = "test-playwright-token-00000000";
            const fakeUser = {
                id: "test-user-001",
                username: "playwright",
                email: "test@playwright.dev",
                role: "admin",
                subscription: "premium",
            };
            localStorage.setItem("et_token", fakeToken);
            sessionStorage.setItem("et_token", fakeToken);
            localStorage.setItem("et_user", JSON.stringify(fakeUser));
        });

        await page.goto("/dev/analysis-card");
        // Wait for the fixture page text to appear…
        await page.waitForSelector(
            'text=AnalysisResultsCard — Test Fixtures',
            { timeout: 15000 },
        );
        // …then for React to fully hydrate (set by useEffect after mount).
        // This is deterministic — no fixed waits, no race conditions.
        await page.waitForSelector('[data-hydrated="true"]', { timeout: 15000 });
    });

    // ── Rendering ──────────────────────────────────────────────────────

    test("renders high viral score card with all sections", async ({ page }) => {
        const section = highScoreSection(page);

        // Header
        await expect(section.getByText("AI Analysis Report")).toBeVisible();
        // candidate_id is sliced to 16 chars with "..." appended
        await expect(section.getByText(/cand_test_e2e_00\.\.\./)).toBeVisible();

        // Viral score badge shows "VIRAL" for score >= 80
        await expect(section.getByText("VIRAL", { exact: true })).toBeVisible();

        // Score ring shows 85
        await expect(section.getByText("85").first()).toBeVisible();

        // Confidence ring shows 89
        await expect(section.getByText("89").first()).toBeVisible();

        // BPM display
        await expect(section.getByText("132").first()).toBeVisible();

        // Hook section
        await expect(
            section.getByText(/What if I told you/)
        ).toBeVisible();
        await expect(section.getByText("curiosity").first()).toBeVisible();
        await expect(section.getByText("YES ✓")).toBeVisible();

        // Pacing: cuts_per_minute = 11.0 → displayed as "11" in monospace
        await expect(section.locator(".font-mono").filter({ hasText: "11" }).first()).toBeVisible();

        // Structure arcs
        await expect(section.getByText("hook").first()).toBeVisible();
        await expect(section.getByText("build").first()).toBeVisible();
        await expect(section.getByText("payoff").first()).toBeVisible();

        // Style
        await expect(section.getByText("cinematic-dark", { exact: true })).toBeVisible();

        // Sentiment
        await expect(section.getByText("positive")).toBeVisible();
        await expect(
            section.getByText("creators aged 18-34")
        ).toBeVisible();

        // Summary (first few words)
        await expect(
            section.getByText(/punchy, high-retention/).first()
        ).toBeVisible();
    });

    test("renders low viral score card with correct labels", async ({ page }) => {
        const section = lowScoreSection(page);

        // Score 35 → "TRENDING" badge
        await expect(section.getByText("TRENDING")).toBeVisible();

        // Scroll stopper is NO
        await expect(section.getByText("NO").first()).toBeVisible();

        // Sentiment is neutral
        await expect(section.getByText("neutral")).toBeVisible();

        // Style is minimal
        await expect(section.getByText("minimal")).toBeVisible();

        // BPM is 60
        await expect(section.getByText("60").first()).toBeVisible();

        // No motion graphics tags
        await expect(section.getByText("zoom-pulse")).toHaveCount(0);
    });

    // ── Loading State ──────────────────────────────────────────────────

    test("shows skeleton loader when isLoading is true", async ({ page }) => {
        const section = loadingSection(page);

        // Skeleton should have animate-pulse class
        await expect(section.locator(".animate-pulse")).toBeVisible();

        // The loading card should NOT contain actual report data
        await expect(section.getByText("VIRAL")).toHaveCount(0);
        await expect(section.getByText("AI Analysis Report")).toHaveCount(0);
    });

    // ── Create Video Button ────────────────────────────────────────────

    test("shows Create Video button when onCreateVideo callback is provided", async ({
        page,
    }) => {
        const section = withButtonSection(page);

        const createBtn = section.getByRole("button", { name: /Create Video/i });
        await expect(createBtn).toBeVisible();
        await expect(createBtn).toBeEnabled();
    });

    test("does NOT show Create Video button when callback is absent", async ({
        page,
    }) => {
        // High-score section has no onCreateVideo callback
        const section = highScoreSection(page);
        await expect(
            section.getByRole("button", { name: /Create Video/i })
        ).toHaveCount(0);

        // Low-score section also has no callback
        const section2 = lowScoreSection(page);
        await expect(
            section2.getByRole("button", { name: /Create Video/i })
        ).toHaveCount(0);
    });

    // ── Expand/Collapse ────────────────────────────────────────────────

    test("toggles expandable details section", async ({ page }) => {
        const section = highScoreSection(page);

        // Initially collapsed — "Show all details" should be visible
        const toggleBtn = section.getByText("Show all details");
        await expect(toggleBtn).toBeVisible();

        // Act Breaks and Color Palette should NOT be visible when collapsed
        await expect(section.getByText("Act Breaks")).toHaveCount(0);
        await expect(section.getByText("Color Palette")).toHaveCount(0);

        // Click to expand
        await toggleBtn.click();

        // The "Hide details" text changes immediately (sync React state).
        await expect(section.getByText("Hide details")).toBeVisible({ timeout: 5000 });

        // Then wait for AnimatePresence content to finish entering.
        await expect(section.getByText("Color Palette")).toBeVisible({ timeout: 5000 });

        // Then wait for AnimatePresence content to finish entering.
        await expect(section.getByText("Color Palette")).toBeVisible({ timeout: 5000 });

        // Typography should be visible
        await expect(section.getByText("Typography")).toBeVisible();
        await expect(section.getByText("Inter Bold")).toBeVisible();

        // Act Breaks should be visible
        await expect(section.getByText("Act Breaks")).toBeVisible();

        // Click to collapse again
        await section.getByText("Hide details").click();
        await expect(section.getByText("Show all details")).toBeVisible();
    });

    test("summary section is visible", async ({ page }) => {
        const section = highScoreSection(page);

        // Summary header should be visible
        await expect(section.getByText("AI Summary")).toBeVisible();

        // The summary text should be visible
        await expect(
            section.getByText(/punchy, high-retention/).first()
        ).toBeVisible();
    });

    // ── Viral Score Badge Variants ─────────────────────────────────────

    test("shows VIRAL badge with score >= 80", async ({ page }) => {
        const section = highScoreSection(page);
        // Use exact match — "VIRAL" substring also matches "Viral Score" label
        await expect(section.getByText("VIRAL", { exact: true })).toBeVisible();
    });

    test("shows TRENDING badge for score < 60", async ({ page }) => {
        const section = lowScoreSection(page);
        await expect(section.getByText("TRENDING")).toBeVisible();
    });

    // ── Score Rings ────────────────────────────────────────────────────

    test("renders SVG score rings for viral score and confidence", async ({
        page,
    }) => {
        const section = highScoreSection(page);

        // SVG circles should exist (score ring component uses SVG)
        const circles = section.locator("svg circle");
        const count = await circles.count();
        expect(count).toBeGreaterThanOrEqual(2); // two rings: viral + confidence
    });

    test("confidence ring shows percentage value", async ({ page }) => {
        const section = highScoreSection(page);

        // Confidence is 0.89 → displayed as "89" in the ring
        await expect(section.getByText("89").first()).toBeVisible();
        await expect(section.getByText("Confidence")).toBeVisible();
    });

    // ── Emotional Triggers ─────────────────────────────────────────────

    test("renders emotional trigger tags", async ({ page }) => {
        const section = highScoreSection(page);

        // All three emotional triggers should be visible as tags
        await expect(section.getByText("curiosity").first()).toBeVisible();
        await expect(section.getByText("validation").first()).toBeVisible();
        await expect(section.getByText("urgency").first()).toBeVisible();
    });

    // ── Retention Curve ────────────────────────────────────────────────

    test("renders retention curve bars in structure section", async ({
        page,
    }) => {
        const section = highScoreSection(page);

        // The retention curve renders bar divs with inline height styles.
        // Each bar has a title attribute with the percentage tooltip.
        const bars = section.locator("[title]");
        const barCount = await bars.count();
        expect(barCount).toBeGreaterThanOrEqual(5);
    });

    // ── Accessibility ──────────────────────────────────────────────────

    test("buttons have accessible names", async ({ page }) => {
        const section = withButtonSection(page);

        // Create Video button
        const btn = section.getByRole("button", { name: /Create Video/i });
        await expect(btn).toBeVisible();

        // Show all details toggle
        const toggle = section.getByText("Show all details");
        await expect(toggle).toBeVisible();
    });

    // ── onClose callback ────────────────────────────────────────────

    test("shows ✕ close button and fires onClose callback when clicked", async ({
        page,
    }) => {
        const section = onCloseSection(page);

        // The ✕ button should be visible in the header
        const closeBtn = section.getByRole("button", { name: "✕" });
        await expect(closeBtn).toBeVisible();

        // Click the close button
        await closeBtn.click();

        // Verify the onClose callback set window.__onCloseCalled to true
        const wasCalled = await page.evaluate(
            () => (window as any).__onCloseCalled === true,
        );
        expect(wasCalled).toBe(true);
    });

    test("✕ button is absent when onClose is not provided", async ({
        page,
    }) => {
        // High-score section has no onClose callback
        const section = highScoreSection(page);
        await expect(
            section.getByRole("button", { name: "✕" }),
        ).toHaveCount(0);
    });
});

import { test, expect } from "@playwright/test";

/**
 * Playwright tests for the WebSocketStatusIndicator component.
 *
 * These tests navigate to the test fixture page at /dev/websocket-status
 * and verify rendering, status colors, reconnect attempt counts,
 * aggregate icon behavior, mixed states, and accessibility.
 *
 * Run:  cd apps/dashboard && npx playwright test tests/WebSocketStatusIndicator.spec.ts
 */

// ── Section helpers ─────────────────────────────────────────────────────

/** Get the indicator container inside a section via data-testid. */
const indicatorIn = (section: any) =>
    section.locator('[data-testid="ws-indicator"]').first();

const allOpenSection = (page: any) =>
    page.locator('[data-testid="section-all-open"]');

const allConnectingSection = (page: any) =>
    page.locator('[data-testid="section-all-connecting"]');

const allClosedSection = (page: any) =>
    page.locator('[data-testid="section-all-closed"]');

const mixedSection = (page: any) =>
    page.locator('[data-testid="section-mixed"]');

const emptySection = (page: any) =>
    page.locator('[data-testid="section-empty"]');

test.describe("WebSocketStatusIndicator", () => {
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

        await page.goto("/dev/websocket-status");
        await page.waitForSelector(
            "text=WebSocketStatusIndicator — Test Fixtures",
            { timeout: 15000 },
        );
    });

    // ── Aggregate icon states ──────────────────────────────────────────

    test("shows green Zap icon when all connections are open", async ({
        page,
    }) => {
        const section = allOpenSection(page);

        // The Zap icon (lucide-react) renders as an SVG
        const zapIcon = section.locator("svg.lucide-zap");
        await expect(zapIcon).toBeVisible();

        // Zap should have text-emerald-400 (green) color class
        await expect(zapIcon).toHaveClass(/text-emerald-400/);
    });

    test("shows aggregate amber Loader2 icon when all connecting", async ({
        page,
    }) => {
        const section = allConnectingSection(page);

        // When all connections are "connecting", overallStatus is now
        // "connecting" (not "mixed"), so the aggregate Loader2 icon renders.
        // Each pill also has its own Loader2 spinner — scope to the first
        // Loader2 in DOM order (the aggregate one).
        const aggregateLoader = section
            .locator("svg.lucide-loader-2, svg.lucide-loader-circle")
            .first();
        await expect(aggregateLoader).toBeVisible();
        await expect(aggregateLoader).toHaveClass(/animate-spin/);
        await expect(aggregateLoader).toHaveClass(/text-amber-400/);
    });

    test("shows red WifiOff icon when all connections are closed", async ({
        page,
    }) => {
        const section = allClosedSection(page);

        const wifiOffIcon = section.locator("svg.lucide-wifi-off");
        await expect(wifiOffIcon).toBeVisible();
        await expect(wifiOffIcon).toHaveClass(/text-rose-400/);
    });

    test("hides aggregate icon when connections are in mixed states", async ({
        page,
    }) => {
        const section = mixedSection(page);

        // NO Zap, Loader2, or WifiOff should be visible as aggregate icon
        // (per-connection pills do have icons, but the aggregate one is absent)
        // The AnimatePresence wrapper won't render children when overallStatus === "mixed"
        await expect(
            section.locator("svg.lucide-zap.text-emerald-400"),
        ).toHaveCount(0);
        await expect(
            section.locator("svg.lucide-loader-2").first(),
        ).toHaveCount(0);
        await expect(
            section.locator("svg.lucide-wifi-off"),
        ).toHaveCount(0);
    });

    // ── Per-connection pills ───────────────────────────────────────────

    test("renders a pill for each connection with correct name", async ({
        page,
    }) => {
        const indicator = indicatorIn(allOpenSection(page));

        // Two connection pills should be visible inside the indicator
        await expect(indicator.getByText("Telemetry")).toBeVisible();
        await expect(indicator.getByText("Discovery")).toBeVisible();
    });

    test("open connection pills have green pulsing dot", async ({ page }) => {
        const section = allOpenSection(page);

        // Each open pill has a motion.div with bg-emerald-400 rounded-full
        // The dot is inside the pill's span for each connection
        const telemetryPill = section.locator("div", { hasText: "Telemetry" }).last();
        // The dot animates opacity; verify the emerald dot div exists
        const dots = telemetryPill.locator(".rounded-full.bg-emerald-400");
        await expect(dots).toHaveCount(1);
    });

    test("connecting pills show reconnect attempt counts when > 0", async ({
        page,
    }) => {
        const indicator = indicatorIn(allConnectingSection(page));

        // Telemetry pill shows "(3)" reconnect attempts
        await expect(indicator.getByText("(3)")).toBeVisible();
        // Discovery pill shows "(7)" reconnect attempts
        await expect(indicator.getByText("(7)")).toBeVisible();
        // No "(0)" pills (count only shown when attempts > 0)
        await expect(indicator.getByText("(0)")).toHaveCount(0);
    });

    test("closed connection pills have red indicators", async ({ page }) => {
        const section = allClosedSection(page);

        // The pill should contain text-rose-400 class
        const telemetryPill = section.getByText("Telemetry");
        await expect(telemetryPill).toBeVisible();

        // The static red dot (not animated) uses bg-rose-400
        const redDots = section.locator(".rounded-full.bg-rose-400");
        await expect(redDots).toHaveCount(1);
    });

    // ── Border/container color per overallStatus ────────────────────────

    test("container border is green when all open", async ({ page }) => {
        const section = allOpenSection(page);

        // Use attribute substring matcher to avoid Tailwind slash escaping
        const container = section.locator('[class*="border-emerald-500"]').first();
        await expect(container).toBeVisible();

        // Background should be emerald-tinted
        const bg = section.locator('[class*="bg-emerald-500"]').first();
        await expect(bg).toBeVisible();
    });

    test("container border is amber when all connections are connecting", async ({
        page,
    }) => {
        // When all connections are "connecting", overallStatus is now
        // "connecting" (not "mixed") — the amber branch is no longer dead.
        const section = allConnectingSection(page);
        const container = section.locator('[class*="border-amber-500"]').first();
        await expect(container).toBeVisible();
    });

    test("container border is rose when all closed", async ({ page }) => {
        const section = allClosedSection(page);

        const container = section.locator('[class*="border-rose-500"]').first();
        await expect(container).toBeVisible();
    });

    test("container border is rose in mixed state (degraded)", async ({
        page,
    }) => {
        const section = mixedSection(page);

        // Mixed → neither allOpen nor allClosed → falls through to rose
        const container = section.locator('[class*="border-rose-500"]').first();
        await expect(container).toBeVisible();
    });

    // ── Component presence ─────────────────────────────────────────────

    test("renders nothing when connections array is empty", async ({
        page,
    }) => {
        const wrapper = emptySection(page).locator(
            '[data-testid="empty-wrapper"]',
        );
        // The wrapper div should be in the DOM (use toBeAttached since a 0×0
        // div with no content won't pass Playwright's visibility check).
        await expect(wrapper).toBeAttached();
        // …but it should contain NO children (the component returns null)
        const children = wrapper.locator("> *");
        const count = await children.count();
        expect(count).toBe(0);
    });

    test("handles a single closed connection without errors", async ({ page }) => {
        // The all-closed section uses a single connection — verifies the
        // component doesn't crash when given just one entry.
        const indicator = indicatorIn(allClosedSection(page));

        // Should render the pill
        await expect(indicator.getByText("Telemetry")).toBeVisible();
        // Aggregate icon should still render (single conn trivially "all closed")
        await expect(indicator.locator("svg.lucide-wifi-off")).toBeVisible();
    });

    // ── Accessibility ───────────────────────────────────────────────────

    test("connection names are readable text in each indicator", async ({
        page,
    }) => {
        // All-open indicator has both Telemetry + Discovery pills.
        const openIndicator = indicatorIn(allOpenSection(page));
        await expect(openIndicator.getByText("Telemetry")).toBeVisible();
        await expect(openIndicator.getByText("Discovery")).toBeVisible();

        // All-closed indicator has a single Telemetry pill.
        const closedIndicator = indicatorIn(allClosedSection(page));
        await expect(closedIndicator.getByText("Telemetry")).toBeVisible();

        // Mixed indicator has both.
        const mixedIndicator = indicatorIn(mixedSection(page));
        await expect(mixedIndicator.getByText("Telemetry")).toBeVisible();
        await expect(mixedIndicator.getByText("Discovery")).toBeVisible();
    });

    test("reconnect counts are distinguishable from connection names", async ({
        page,
    }) => {
        const indicator = indicatorIn(allConnectingSection(page));

        // The count "(3)" is in a smaller span (text-[8px]) and should not
        // be confused with the connection name text
        const pill = indicator.locator("div.uppercase").filter({ hasText: "Telemetry" }).last();

        // The name "Telemetry" should be in a <span> child
        await expect(pill.locator("span").filter({ hasText: "Telemetry" })).toBeVisible();

        // The count "(3)" should also be in a span with opacity-70
        await expect(
            pill.locator("span.opacity-70").filter({ hasText: "(3)" }),
        ).toBeVisible();
    });
});

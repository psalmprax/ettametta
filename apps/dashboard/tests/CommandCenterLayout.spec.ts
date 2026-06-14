import { test, expect } from "@playwright/test";

/**
 * Playwright tests for the CommandCenterLayout header with
 * integrated WebSocketStatusIndicator.
 *
 * These tests navigate to /dev/command-center and verify that:
 * - The telemetry WS status flows through to the indicator
 * - additionalWsConnections adds Discovery pills
 * - Uptime, latency, footer status bar reflect telemetry pulse
 *
 * Run:  cd apps/dashboard && npx playwright test tests/CommandCenterLayout.spec.ts
 */

// ── Section + header helpers ────────────────────────────────────────────

const telemetryOnlySection = (page: any) =>
    page.locator('[data-testid="section-telemetry-only"]');

const withDiscoveryOpenSection = (page: any) =>
    page.locator('[data-testid="section-with-discovery-open"]');

const bothConnectingSection = (page: any) =>
    page.locator('[data-testid="section-both-connecting"]');

/** The header element inside a section. */
const headerIn = (section: any) => section.locator("header").first();

/** The footer element inside a section. */
const footerIn = (section: any) => section.locator("footer").first();

test.describe("CommandCenterLayout header", () => {
    test.beforeEach(async ({ page }) => {
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

        await page.goto("/dev/command-center");
        await page.waitForSelector(
            "text=CommandCenterLayout — Test Fixtures",
            { timeout: 15000 },
        );
        await page.waitForSelector('[data-hydrated="true"]', {
            timeout: 15000,
        });
    });

    // ── Telemetry → Indicator piping ────────────────────────────────

    test("renders telemetry pill in WS indicator when telemetry is open", async ({
        page,
    }) => {
        const header = headerIn(telemetryOnlySection(page));

        // The indicator should show "Telemetry" pill (from telemetry context)
        await expect(header.getByText("Telemetry")).toBeVisible();

        // No "Discovery" pill since additionalWsConnections is empty
        await expect(header.getByText("Discovery")).toHaveCount(0);
    });

    test("renders Discovery pill when additionalWsConnections is provided", async ({
        page,
    }) => {
        const header = headerIn(withDiscoveryOpenSection(page));

        // Both Telemetry (from context) and Discovery (from prop) should appear
        await expect(header.getByText("Telemetry")).toBeVisible();
        await expect(header.getByText("Discovery")).toBeVisible();
    });

    test("WS indicator shows green Zap when both connections are open", async ({
        page,
    }) => {
        const header = headerIn(withDiscoveryOpenSection(page));

        // Aggregate Zap icon should be visible (all open → green)
        const zapIcon = header.locator("svg.lucide-zap");
        await expect(zapIcon).toBeVisible();
        await expect(zapIcon).toHaveClass(/text-emerald-400/);
    });

    test("Discovery reconnect count appears when connecting", async ({
        page,
    }) => {
        const header = headerIn(bothConnectingSection(page));

        // Discovery pill should show "(2)" reconnect attempts
        await expect(header.getByText("Discovery")).toBeVisible();
        await expect(header.getByText("(2)")).toBeVisible();
    });

    test("Telemetry + Discovery both visible when both connecting", async ({
        page,
    }) => {
        const header = headerIn(bothConnectingSection(page));

        await expect(header.getByText("Telemetry")).toBeVisible();
        await expect(header.getByText("Discovery")).toBeVisible();
    });

    // ── Header title / subtitle ──────────────────────────────────────

    test("renders title and subtitle from props", async ({ page }) => {
        const header = headerIn(telemetryOnlySection(page));

        await expect(header.getByText("TEST CC")).toBeVisible();
        await expect(header.getByText("T-001")).toBeVisible();
    });

    // ── Footer status bar ────────────────────────────────────────────

    test("footer shows SYSTEM_STABLE when telemetry is open", async ({
        page,
    }) => {
        const footer = footerIn(telemetryOnlySection(page));

        await expect(footer.getByText("SYSTEM_STABLE")).toBeVisible();
    });

    test("footer shows uptime from telemetry pulse", async ({ page }) => {
        // Uptime is in the header, not the footer ("System Uptime" label).
        const header = headerIn(telemetryOnlySection(page));

        // MOCK_PULSE.uptime = "12:34:56"
        await expect(header.getByText("12:34:56")).toBeVisible();
    });

    test("footer shows latency from telemetry pulse", async ({ page }) => {
        const footer = footerIn(telemetryOnlySection(page));

        // MOCK_PULSE.latency_ms = 42
        await expect(footer.getByText("42")).toBeVisible();
        await expect(footer.getByText("MS")).toBeVisible();
    });

    test("footer shows hostname from telemetry pulse", async ({ page }) => {
        const footer = footerIn(telemetryOnlySection(page));

        await expect(footer.getByText("TEST_NODE")).toBeVisible();
    });

    // ── Connects to children ─────────────────────────────────────────

    test("renders children content inside the layout", async ({ page }) => {
        const section = telemetryOnlySection(page);

        await expect(
            section.locator('[data-testid="page-content-telemetry-only"]'),
        ).toBeVisible();
        await expect(
            section.getByText("Content — Telemetry open only"),
        ).toBeVisible();
    });

    // ── No crash with defaults ───────────────────────────────────────

    // ── Footer status bar states ─────────────────────────────────────

    test("footer shows CONNECTION_LOST when telemetry is connecting", async ({
        page,
    }) => {
        const footer = footerIn(bothConnectingSection(page));

        // Telemetry status is "connecting" → not "open" → CONNECTION_LOST
        await expect(footer.getByText("CONNECTION_LOST")).toBeVisible();
    });

    // ── Aggregate Zap icon when telemetry alone is open ───────────────

    test("shows green Zap aggregate icon when only Telemetry is open", async ({
        page,
    }) => {
        const header = headerIn(telemetryOnlySection(page));

        // Single open connection → aggregate Zap icon should be visible
        const zapIcon = header.locator("svg.lucide-zap");
        await expect(zapIcon).toBeVisible();
        await expect(zapIcon).toHaveClass(/text-emerald-400/);
    });
});

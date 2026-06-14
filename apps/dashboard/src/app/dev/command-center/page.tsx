"use client";

import React, { useEffect, useState } from "react";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import {
    TelemetryContext,
    TelemetryPulse,
    LogEntry,
} from "@/context/TelemetryContext";
import { WsConnectionState } from "@/components/WebSocketStatusIndicator";

/**
 * Test fixture page for the CommandCenterLayout header with
 * integrated WebSocketStatusIndicator.
 *
 * Renders the layout with mock TelemetryContext values so Playwright
 * tests can verify header rendering, WS indicator integration,
 * telemetry → indicator piping, and additionalWsConnections
 * without needing a running backend or real WebSocket.
 *
 * Route: /dev/command-center
 */

// ── Mock telemetry pulse ─────────────────────────────────────────────

const MOCK_PULSE: TelemetryPulse = {
    status: "HEALTHY",
    cluster_node: "X-TEST-01",
    hostname: "TEST_NODE",
    active_jobs: 3,
    nexus_active: 1,
    video_active: 2,
    latency_ms: 42,
    timestamp: Date.now(),
    load_avg: 0.35,
    uptime: "12:34:56",
    signals: [],
};

// ── Mock provider ────────────────────────────────────────────────────

function MockTelemetryProvider({
    status,
    children,
}: {
    readonly status: "connecting" | "open" | "closed";
    readonly children: React.ReactNode;
}) {
    const logs: LogEntry[] = [];
    return (
        <TelemetryContext.Provider
            value={{
                pulse: MOCK_PULSE,
                logs,
                lastJobUpdate: null,
                status,
                agents: [],
            }}
        >
            {children}
        </TelemetryContext.Provider>
    );
}

// ── Fixture states ───────────────────────────────────────────────────

/** Discovery WS is also open (two green pills in the indicator). */
const DISCOVERY_OPEN: WsConnectionState[] = [
    { name: "Discovery", status: "open" },
];

/** Discovery WS is reconnecting (amber pill with attempt count). */
const DISCOVERY_CONNECTING: WsConnectionState[] = [
    { name: "Discovery", status: "connecting", reconnectAttempts: 2 },
];

// ── Page ─────────────────────────────────────────────────────────────

export default function CommandCenterTestPage() {
    const [hydrated, setHydrated] = useState(false);
    useEffect(() => {
        setHydrated(true);
    }, []);

    return (
        <div
            data-hydrated={hydrated ? "true" : "false"}
            style={{ background: "#050507", minHeight: "100vh" }}
        >
            <h1
                style={{
                    fontSize: 20,
                    fontWeight: 700,
                    padding: "2rem 2rem 0",
                    color: "#fff",
                }}
            >
                CommandCenterLayout — Test Fixtures
            </h1>

            {/* 1. Telemetry open, no additional connections */}
            <section
                data-testid="section-telemetry-only"
                style={{ marginBottom: 4 }}
            >
                <MockTelemetryProvider status="open">
                    <CommandCenterLayout title="TEST CC" subtitle="T-001">
                        <div
                            style={{ padding: 24, color: "#666" }}
                            data-testid="page-content-telemetry-only"
                        >
                            Content — Telemetry open only
                        </div>
                    </CommandCenterLayout>
                </MockTelemetryProvider>
            </section>

            {/* 2. Telemetry open + Discovery open */}
            <section
                data-testid="section-with-discovery-open"
                style={{ marginBottom: 4 }}
            >
                <MockTelemetryProvider status="open">
                    <CommandCenterLayout
                        title="TEST CC"
                        subtitle="T-002"
                        additionalWsConnections={DISCOVERY_OPEN}
                    >
                        <div
                            style={{ padding: 24, color: "#666" }}
                            data-testid="page-content-with-discovery"
                        >
                            Content — Telemetry + Discovery open
                        </div>
                    </CommandCenterLayout>
                </MockTelemetryProvider>
            </section>

            {/* 3. Telemetry connecting + Discovery connecting */}
            <section
                data-testid="section-both-connecting"
                style={{ marginBottom: 4 }}
            >
                <MockTelemetryProvider status="connecting">
                    <CommandCenterLayout
                        title="TEST CC"
                        subtitle="T-003"
                        additionalWsConnections={DISCOVERY_CONNECTING}
                    >
                        <div
                            style={{ padding: 24, color: "#666" }}
                            data-testid="page-content-both-connecting"
                        >
                            Content — Both connecting
                        </div>
                    </CommandCenterLayout>
                </MockTelemetryProvider>
            </section>
        </div>
    );
}

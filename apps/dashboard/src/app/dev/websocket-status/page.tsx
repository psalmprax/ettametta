"use client";

import React from "react";
import {
    WebSocketStatusIndicator,
    WsConnectionState,
} from "@/components/WebSocketStatusIndicator";

/**
 * Test fixture page for the WebSocketStatusIndicator component.
 *
 * Renders the indicator in isolation with hardcoded connection states so
 * Playwright tests can verify rendering, status colors, reconnect counts,
 * aggregate icons, and mixed-state behavior without needing a real WS.
 *
 * Route: /dev/websocket-status
 */

// ── Connection state fixtures ────────────────────────────────────────────

const ALL_OPEN: WsConnectionState[] = [
    { name: "Telemetry", status: "open" },
    { name: "Discovery", status: "open" },
];

const ALL_CONNECTING: WsConnectionState[] = [
    { name: "Telemetry", status: "connecting", reconnectAttempts: 3 },
    { name: "Discovery", status: "connecting", reconnectAttempts: 7 },
];

const ALL_CLOSED: WsConnectionState[] = [
    { name: "Telemetry", status: "closed" },
];

const MIXED: WsConnectionState[] = [
    { name: "Telemetry", status: "open" },
    { name: "Discovery", status: "connecting", reconnectAttempts: 2 },
];

const EMPTY: WsConnectionState[] = [];

export default function WebSocketStatusTestPage() {
    return (
        <div
            style={{
                padding: "2rem",
                maxWidth: 800,
                margin: "0 auto",
                background: "#050507",
            }}
        >
            <h1
                style={{
                    fontSize: 20,
                    fontWeight: 700,
                    marginBottom: 24,
                    color: "#fff",
                }}
            >
                WebSocketStatusIndicator — Test Fixtures
            </h1>

            {/* All Open */}
            <section
                data-testid="section-all-open"
                style={{ marginBottom: 48 }}
            >
                <h2 style={{ fontSize: 14, marginBottom: 12, color: "#999" }}>
                    All Open — Both Telemetry + Discovery connected
                </h2>
                <div data-testid="ws-indicator">
                    <WebSocketStatusIndicator connections={ALL_OPEN} />
                </div>
            </section>

            {/* All Connecting */}
            <section
                data-testid="section-all-connecting"
                style={{ marginBottom: 48 }}
            >
                <h2 style={{ fontSize: 14, marginBottom: 12, color: "#999" }}>
                    All Connecting — Both reconnecting with attempt counts
                </h2>
                <div data-testid="ws-indicator">
                    <WebSocketStatusIndicator connections={ALL_CONNECTING} />
                </div>
            </section>

            {/* All Closed */}
            <section
                data-testid="section-all-closed"
                style={{ marginBottom: 48 }}
            >
                <h2 style={{ fontSize: 14, marginBottom: 12, color: "#999" }}>
                    All Closed — Connection lost
                </h2>
                <div data-testid="ws-indicator">
                    <WebSocketStatusIndicator connections={ALL_CLOSED} />
                </div>
            </section>

            {/* Mixed */}
            <section
                data-testid="section-mixed"
                style={{ marginBottom: 48 }}
            >
                <h2 style={{ fontSize: 14, marginBottom: 12, color: "#999" }}>
                    Mixed — Telemetry open, Discovery reconnecting (no aggregate icon)
                </h2>
                <div data-testid="ws-indicator">
                    <WebSocketStatusIndicator connections={MIXED} />
                </div>
            </section>

            {/* Empty */}
            <section
                data-testid="section-empty"
                style={{ marginBottom: 48 }}
            >
                <h2 style={{ fontSize: 14, marginBottom: 12, color: "#999" }}>
                    Empty — Zero connections (renders nothing)
                </h2>
                <div data-testid="empty-wrapper">
                    <WebSocketStatusIndicator connections={EMPTY} />
                </div>
            </section>
        </div>
    );
}

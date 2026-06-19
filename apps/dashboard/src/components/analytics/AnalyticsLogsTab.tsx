"use client";

import React from "react";
import { ConsoleLogPanel } from "@/components/ui/ConsoleLogPanel";

/** Module-internal — do not consume from outside. */
interface Props {
    logs: { timestamp: number; message: string }[];
    status: string;
}

/**
 * Telemetry-Logs tab — wrapper around `ConsoleLogPanel` with the
 * analytics-themed violet accent and "Observer_Sync" badge.
 */
export default function AnalyticsLogsTab({ logs, status }: Props) {
    return (
        <ConsoleLogPanel
            title="Telemetry Stream"
            accent="text-violet-500"
            badge="Observer_Sync"
            logs={logs}
            liveStatus={status}
        />
    );
}

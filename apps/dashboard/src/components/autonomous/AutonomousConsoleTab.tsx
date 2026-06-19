"use client";

import React from "react";
import { ConsoleLogPanel } from "@/components/ui/ConsoleLogPanel";

/** Module-internal — do not consume from outside. */
interface Props {
    logs: any[];
    status: string;
}

/**
 * System-Console tab — full-spectrum log panel (focused view of the
 * agent-zero stream). When active, the `CompactConsole` sibling below
 * the AnimatePresence is hidden to avoid double render.
 */
export default function AutonomousConsoleTab({ logs, status }: Props) {
    return (
        <ConsoleLogPanel
            title="Full Spectrum System Console"
            accent="text-emerald-500"
            badge="Observer_Active"
            logs={logs}
            liveStatus={status}
        />
    );
}

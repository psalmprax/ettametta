"use client";

import React from "react";
import { ConsoleLogPanel } from "@/components/ui/ConsoleLogPanel";

interface Props {
    logs: { timestamp: number; message: string; level?: string }[];
    liveStatus?: string;
}

/**
 * Logs tab — Strategic Event Horizon (amber-accented ConsoleLogPanel wrapper).
 */
export default function EmpireLogsTab({ logs, liveStatus }: Props) {
    return (
        <ConsoleLogPanel
            title="Strategic Event Horizon"
            accent="text-amber-500"
            badge="Observer_Active"
            logs={logs}
            liveStatus={liveStatus}
        />
    );
}

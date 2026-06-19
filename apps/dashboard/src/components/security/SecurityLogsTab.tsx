"use client";

import React from "react";
import { ConsoleLogPanel } from "@/components/ui/ConsoleLogPanel";

/** Module-internal — do not consume from outside. */
interface Props {
    logs: { timestamp: number; message: string }[];
    isScanning: boolean;
}

/**
 * Engine-Logs tab — wraps `ConsoleLogPanel` with security-themed accents
 * and infers a `level` from message prefix ([SUCCESS], [ERROR], [SCAN]).
 */
export default function SecurityLogsTab({ logs, isScanning }: Props) {
    return (
        <ConsoleLogPanel
            title="Security Engine Logs"
            accent="text-emerald-500"
            badge={isScanning ? "Scan_In_Progress" : "Sentinel_Active"}
            logs={logs.map((l) => ({
                timestamp: l.timestamp,
                level: l.message?.startsWith("[SUCCESS]") ? "SUCCESS" :
                       l.message?.startsWith("[ERROR]") ? "ERROR" :
                       l.message?.startsWith("[SCAN]") ? "ACTION" : "INFO",
                message: l.message,
            }))}
        />
    );
}

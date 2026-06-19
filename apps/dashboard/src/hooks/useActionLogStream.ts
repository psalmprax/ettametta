"use client";

import { useCallback, useMemo, useState } from "react";
import { useTelemetry } from "@/context/TelemetryContext";

/** Module-internal — do not consume from outside. */
interface MergedLogEntry {
    type: string;
    level: string;
    module: string;
    message: string;
    timestamp: number;
}

/**
 * Action-log stream with merged telemetry entries.
 *
 * Each dashboard page has its own private "ACTION" log (e.g. click observability
 * for the user-driven actions) and also wants to surface relevant entries from
 * the cross-page telemetry stream. This hook centralises that merge so the page
 * component can stay declarative.
 *
 * @param moduleName     The module tag attached to local action log entries
 *                       (used both for stamping and as an implicit default for
 *                       telemetry filtering when `includeSystemModules` is true).
 * @param seed           Optional initial log lines (e.g. analyzer banner).
 * @param includeSystemModules
 *                       When true, telemetry entries whose module equals
 *                       `moduleName`, `AGENT_ZERO`, or `SYSTEM` are merged into
 *                       the displayed stream. When false (default), all
 *                       telemetry entries are merged — the original behaviour
 *                       used by the security / empire / analytics pages.
 */
export function useActionLogStream(
    moduleName: string,
    seed: string[] = [],
    includeSystemModules = false
) {
    const { logs: systemLogs } = useTelemetry();
    const [actionLogs, setActionLogs] = useState<string[]>(seed);

    const addLog = useCallback((msg: string) => {
        setActionLogs((prev) => [msg, ...prev]);
    }, []);

    const displayLogs = useMemo<MergedLogEntry[]>(() => {
        const filteredSystemLogs = includeSystemModules
            ? (Array.isArray(systemLogs) ? systemLogs : []).filter(
                  (l: any) => l?.module === moduleName || l?.module === "SYSTEM"
              )
            : Array.isArray(systemLogs)
            ? systemLogs
            : [];

        const merged: MergedLogEntry[] = [
            ...actionLogs.map((message) => ({
                type: "log",
                level: "ACTION",
                module: moduleName,
                message,
                timestamp: Date.now() / 1000,
            })),
            ...filteredSystemLogs,
        ];
        return merged.sort((a, b) => b.timestamp - a.timestamp);
    }, [actionLogs, systemLogs, moduleName, includeSystemModules]);

    return { actionLogs, addLog, displayLogs };
}

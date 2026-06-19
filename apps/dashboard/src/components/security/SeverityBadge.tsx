"use client";

import React from "react";
import {
    AlertOctagon,
    AlertTriangle,
    AlertCircle,
    Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { SecurityEvent } from "@/hooks/useSecurityData";

// Reuse the typed severity union from the data hook — avoids drift if a new
// tier is added to SecurityEvent.
type Severity = SecurityEvent["severity"];

/**
 * Severity icon for a security event — chosen by severity tier.
 *
 * Used by both `SecurityStatusView` (recent-threats list) and
 * `SecurityEventsView` (event log). Pure presentational; no data hook
 * coupling.
 */
export function SeverityIcon({
    severity,
    className,
}: {
    severity: Severity;
    className?: string;
}) {
    const cnCls = cn("h-5 w-5", className);
    switch (severity) {
        case "critical":
            return <AlertOctagon className={cnCls} />;
        case "high":
            return <AlertTriangle className={cnCls} />;
        case "medium":
            return <AlertCircle className={cnCls} />;
        default:
            return <Activity className={cnCls} />;
    }
}

/**
 * Severity pill — compact severity tag with consistent colour tiers.
 */
export function SeverityPill({ severity }: { severity: Severity }) {
    const cnCls = cn(
        "px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest",
        severity === "critical" && "bg-rose-500/20 text-rose-400",
        severity === "high" && "bg-orange-500/20 text-orange-400",
        severity === "medium" && "bg-amber-500/20 text-amber-400",
        (!severity || severity === "info") && "bg-zinc-500/20 text-zinc-400"
    );
    return <span className={cnCls}>{severity || "info"}</span>;
}

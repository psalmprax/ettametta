"use client";

import React from "react";
import { Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

export type ConsoleLogLevel = "ACTION" | "DATA" | "SUCCESS" | "ERROR" | string;

export interface ConsoleLogEntry {
    timestamp: number;
    level?: ConsoleLogLevel;
    module?: string;
    message: string;
}

export interface ConsoleLogPanelProps {
    title: string;
    /** Tailwind class applied to the active-status pill text colour. */
    accent?: string;
    /** Optional trailing badge text (e.g. "Sentinel_Active"). */
    badge?: string;
    /** Optional delete button on the right side of the header. */
    onClear?: () => void;
    /** The merged log entries (typically from useActionLogStream). */
    logs: ConsoleLogEntry[];
    /** Determines if a small footer (LINK_ESTABLISHED / LINK_OFFLINE) shows. */
    liveStatus?: "open" | "closed" | string;
}

/**
 * Shared log-viewer panel used by the security, empire, autonomous, and
 * analytics pages. Each page previously inlined a near-identical block:
 * header with `Terminal` icon + status badge, scrollable monospace log rows,
 * level-based colour coding.
 *
 * Page-specific styling is preserved via the `accent` prop, which controls
 * the active-status pill colour. The component itself stays unstyled otherwise.
 */
export function ConsoleLogPanel({
    title,
    accent = "text-amber-500",
    badge = "Observer_Active",
    logs,
    liveStatus,
}: ConsoleLogPanelProps) {
    const live = liveStatus === "open";

    return (
        <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                <div className="flex items-center gap-4">
                    <Terminal className="h-4 w-4 text-zinc-500" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-widest">
                        {title}
                    </h3>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className={`text-[9px] font-bold uppercase ${accent}`}>
                        {badge}
                    </span>
                </div>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                {logs.map((log, i) => (
                    <div
                        key={i}
                        className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all"
                    >
                        <span className="text-zinc-700 shrink-0 select-none">
                            {new Date(log.timestamp * 1000).toLocaleTimeString()}
                        </span>
                        <span className="text-zinc-800 shrink-0 select-none">|</span>
                        <span
                            className={cn(
                                "leading-relaxed",
                                log.level === "ACTION"
                                    ? "text-cyan-400"
                                    : log.level === "ERROR"
                                    ? "text-rose-500"
                                    : log.level === "SUCCESS"
                                    ? "text-emerald-500"
                                    : log.message?.includes("[SUCCESS]")
                                    ? "text-emerald-500"
                                    : log.message?.includes("[ERROR]")
                                    ? "text-rose-500"
                                    : log.message?.includes("[DATA]")
                                    ? "text-cyan-400"
                                    : "text-zinc-400"
                            )}
                        >
                            {log.message}
                        </span>
                    </div>
                ))}
                <div className="h-4" />
            </div>
            {liveStatus !== undefined && (
                <div className="px-6 py-2 border-t border-white/5 flex items-center gap-2 text-[8px] font-mono text-zinc-600">
                    <div
                        className={cn(
                            "h-1.5 w-1.5 rounded-full",
                            live ? "bg-emerald-500 animate-pulse" : "bg-zinc-800"
                        )}
                    />
                    <span>{live ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                </div>
            )}
        </div>
    );
}

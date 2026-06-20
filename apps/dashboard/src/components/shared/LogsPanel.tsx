"use client";

import React from "react";
import { cn } from "@/lib/utils";

/** Module-internal — do not consume from outside. */
interface LogsPanelProps {
    readonly logs: readonly string[];
    readonly label?: string;
    readonly badge?: string;
    readonly badgeClass?: string;
    readonly colorMap?: Record<string, string>;
}

/** Module-internal — do not consume from outside. */
const DEFAULT_COLOR_MAP: Record<string, string> = {
    "[PROTOCOL]": "text-cyan-400",
    "[SUCCESS]": "text-emerald-500",
    "[FAILURE]": "text-rose-500",
    "[ANALYSIS]": "text-cyan-400",
    "[WINNER]": "text-amber-500",
    "[EVOLUTION]": "text-violet-500",
    "[AGENT]": "text-violet-400",
    "[USER]": "text-cyan-400",
    "[ERROR]": "text-rose-500",
    "[CREATE]": "text-cyan-400",
    "[DELETE]": "text-orange-500",
    "[GENERATE]": "text-violet-400",
    "[INFO]": "text-zinc-400",
};

/**
 * Shared logs panel for CommandCenterLayout-based pages.
 * Replaces the identical log rendering pattern in 6+ dashboard pages.
 */
export function LogsPanel({
    logs,
    label = "Session Logs",
    badge = "LOG_ACTIVE",
    badgeClass = "text-cyan-500/50",
    colorMap = DEFAULT_COLOR_MAP,
}: LogsPanelProps) {
    const resolveColor = (log: string): string => {
        for (const [prefix, color] of Object.entries(colorMap)) {
            if (log.includes(prefix)) return color;
        }
        return "text-zinc-600";
    };

    return (
        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{label}</span>
                <span className={cn("text-[8px] font-mono uppercase", badgeClass)}>{badge}</span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                {logs.map((log, i) => (
                    <div key={i} className="flex gap-4">
                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                        <span className={resolveColor(log)}>{log}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

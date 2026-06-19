"use client";

import React from "react";
import { Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
    logs: any[];
    status: string;
}

/**
 * Compact-console panel — sibling of the AnimatePresence tab view.
 *
 * Always rendered below the active tab except when `activeEngine === "console"`,
 * where the full-spectrum `AutonomousConsoleTab` already renders. Page
 * owns the visibility decision; this component is purely presentational.
 */
export default function CompactConsole({ logs, status }: Props) {
    return (
        <div className="mt-8 h-64 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Terminal className="h-3 w-3 text-emerald-500" />
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">System Console</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[8px] font-mono text-emerald-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                    <div className={cn("h-1.5 w-1.5 rounded-full", status === "open" ? "bg-emerald-500 animate-pulse" : "bg-zinc-800")} />
                </div>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                {logs.map((log, i) => (
                    <div key={i} className="flex gap-4">
                        <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                        <span className={cn(
                            log.level === "ACTION" ? "text-cyan-400" :
                            log.level === "ERROR" ? "text-red-500" :
                            log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-600"
                        )}>
                            {log.module ? `[${log.module}] ` : ""}{log.message}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

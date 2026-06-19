"use client";

import React, { useMemo } from "react";
import { cn } from "@/lib/utils";

interface LogEntry {
    type?: string;
    level?: string;
    module?: string;
    message: string;
    timestamp: number;
}

interface Props {
    actionLogs: string[];
    systemLogs: any[] | undefined;
    status: "open" | "closed" | string;
}

export default function LogsTab({ actionLogs, systemLogs, status }: Props) {
    const displayLogs = useMemo(() => {
        const logs = Array.isArray(systemLogs) ? systemLogs : [];
        return [
            ...(actionLogs || []).map((msg) => ({
                type: "log",
                level: "ACTION",
                module: "NEXUS",
                message: msg,
                timestamp: Date.now() / 1000,
            })),
            ...logs,
        ].sort((a, b) => b.timestamp - a.timestamp);
    }, [actionLogs, systemLogs]);

    return (
        <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-[32px] border border-white/5 overflow-hidden">
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">
                    Log Stream
                </h3>
                <span className="text-[8px] font-mono text-cyan-400">
                    {status === "open" ? "NEXUS_CORE_ACTIVE" : "OFFLINE"}
                </span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                {displayLogs?.map((log, i) => (
                    <div key={i} className="flex gap-4">
                        <span className="text-zinc-700">
                            [{new Date(log.timestamp * 1000).toLocaleTimeString()}]
                        </span>
                        <span
                            className={cn(
                                log.level === "ACTION"
                                    ? "text-cyan-400"
                                    : log.level === "ERROR"
                                    ? "text-rose-500"
                                    : log.level === "SUCCESS"
                                    ? "text-emerald-500"
                                    : "text-zinc-500"
                            )}
                        >
                            {log.module ? `[${log.module}] ` : ""}
                            {log.message}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

"use client";

import React from "react";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { SeverityIcon, SeverityPill } from "./SeverityBadge";
import type { SecurityEvent } from "@/hooks/useSecurityData";

interface Props {
    events: SecurityEvent[];
}

/**
 * Event-Log tab — full event stream with severity icons + pills.
 * Reuses `SeverityBadge` from `SecurityStatusView` for visual parity.
 */
export default function SecurityEventsView({ events }: Props) {
    if (events.length === 0) {
        return (
            <div className="overflow-y-auto custom-scrollbar flex-1 p-1">
                <div className="flex flex-col items-center justify-center py-32 opacity-20">
                    <Activity className="h-16 w-16 mb-4" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.5em]">No security events recorded</span>
                </div>
            </div>
        );
    }

    return (
        <div className="overflow-y-auto custom-scrollbar flex-1 p-1">
            <div className="space-y-2">
                {events.map((event, i) => (
                    <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/5 flex items-start gap-4 group hover:border-emerald-500/20 transition-all">
                        <div className={cn(
                            "h-10 w-10 rounded-xl flex items-center justify-center shrink-0",
                            event.severity === "critical" ? "bg-rose-500/10" :
                            event.severity === "high" ? "bg-orange-500/10" : "bg-zinc-500/10"
                        )}>
                            <SeverityIcon severity={event.severity} className={cn(
                                event.severity === "critical" && "text-rose-500",
                                event.severity === "high" && "text-orange-500",
                                "text-zinc-500"
                            )} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-1">
                                <span className="text-xs font-bold text-white uppercase tracking-tight">{event.type || "Unknown"}</span>
                                <span className="text-[8px] font-mono text-zinc-600">{event.timestamp ? new Date(event.timestamp).toLocaleString() : ""}</span>
                            </div>
                            <p className="text-[10px] text-zinc-500 leading-relaxed">
                                {event.details ? JSON.stringify(event.details).slice(0, 200) : event.message || ""}
                            </p>
                        </div>
                        <SeverityPill severity={event.severity} />
                    </div>
                ))}
            </div>
        </div>
    );
}

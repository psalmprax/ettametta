"use client";

import React from "react";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { cn } from "@/lib/utils";

interface Props {
    agents: any[];
    /** Already-derived health score (defaults to 0). */
    healthScore: number;
    /** Already-derived threat level (defaults to "NOMINAL"). */
    threatLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "NOMINAL";
    /** Already-derived threat counts with safe defaults. */
    threatBreakdown: { low: number; medium: number; high: number; critical: number };
}

/**
 * Right-side context panel for the Security page.
 *
 * Receives pre-derived view-models so `SecurityContent` owns all the
 * `securityStatus?.data?.X` chain logic in one place. This panel is purely
 * presentational — no data hooks, no derivation, no nullable types.
 */
export default function SecurityRightPanel({
    agents,
    healthScore,
    threatLevel,
    threatBreakdown,
}: Props) {
    const threatColor =
        threatLevel === "CRITICAL" ? "text-rose-500" :
        threatLevel === "HIGH" ? "text-orange-500" :
        threatLevel === "MEDIUM" ? "text-amber-500" :
        "text-emerald-500";

    return (
        <>
            <AgentMatrix agents={agents} />
            <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Health Overview</h4>
                <div className="flex flex-col">
                    <span className="text-3xl font-bold text-white">{healthScore}%</span>
                    <span className={cn("text-[8px] font-bold uppercase tracking-widest", threatColor)}>
                        Threat: {threatLevel}
                    </span>
                </div>
                <div className="space-y-2 pt-2 border-t border-white/5">
                    <div className="flex justify-between text-[8px] font-bold"><span className="text-zinc-600">Critical</span><span className="text-rose-500">{threatBreakdown.critical || 0}</span></div>
                    <div className="flex justify-between text-[8px] font-bold"><span className="text-zinc-600">High</span><span className="text-orange-500">{threatBreakdown.high || 0}</span></div>
                    <div className="flex justify-between text-[8px] font-bold"><span className="text-zinc-600">Medium</span><span className="text-amber-500">{threatBreakdown.medium || 0}</span></div>
                    <div className="flex justify-between text-[8px] font-bold"><span className="text-zinc-600">Low</span><span className="text-zinc-400">{threatBreakdown.low || 0}</span></div>
                </div>
            </div>
        </>
    );
}

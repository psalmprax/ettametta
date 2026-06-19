"use client";

import React from "react";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";

/** Module-internal — do not consume from outside. */
interface Props {
    agents: any[];
    /** Total views (defaulted to 0 in page if missing). */
    views: number;
    /** Growth percentage label, e.g. "+14.2". */
    growthPct: string;
}

/**
 * Right-side context panel for the Analytics page.
 */
export default function AnalyticsRightPanel({ agents, views, growthPct }: Props) {
    return (
        <>
            <AgentMatrix agents={agents} />
            <div className="p-3 rounded-2xl border border-white/5 bg-white/5 space-y-3">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Reach</h4>
                <div className="flex flex-col">
                    <span className="text-xl font-bold text-white">{(views / 1000).toFixed(1)}K</span>
                    <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-widest">+{growthPct}% Growth</span>
                </div>
                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full w-[72%] bg-violet-500" />
                </div>
            </div>
        </>
    );
}

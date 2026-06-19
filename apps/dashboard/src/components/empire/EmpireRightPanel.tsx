"use client";

import React from "react";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";

/** Module-internal — do not consume from outside. */
interface Props {
    agents: any[];
    /** Total revenue in USD, already formatted-or-zeroed by the page. */
    totalRevenueFormatted: string;
    /** Pre-formatted label for the daily-avg line: "Daily Avg" when revenue
     *  exists; "Velocity" fallback ("+8.4% Velocity") when revenue is absent.
     *  Always starts with "+" — panel renders as-is. */
    dailyAvgLabel: string;
    /** Pre-derived platform rows (already defaulted to [] by page). */
    platforms: { platform: string; revenue: number; views?: number; clicks?: number }[];
    /** Velocity multiplier (already falled back to 1.5 by page). */
    velocity: number;
    /** Total published count (already falled back to 12 by page). */
    totalPublished: number;
}

/**
 * Right-side context panel for the Empire page.
 *
 * Receives pre-derived view-models so the page-level derivation (and any
 * chain defaults that bend around `?.' optional access) lives in one place
 * — `EmpireContent`. This keeps the panel purely presentational.
 */
export default function EmpireRightPanel({
    agents,
    totalRevenueFormatted,
    dailyAvgLabel,
    platforms,
    velocity,
    totalPublished,
}: Props) {
    return (
        <>
            <AgentMatrix agents={agents} />
            <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Revenue Pulse</h4>
                <div className="flex flex-col">
                    <span className="text-2xl font-bold text-white">${totalRevenueFormatted}</span>
                    <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-widest">
                        {dailyAvgLabel}
                    </span>
                </div>
                {platforms.length > 0 && (
                    <div className="mt-4 space-y-2">
                        {platforms.map((platform, i) => (
                            <div key={i} className="flex items-center justify-between text-[9px]">
                                <span className="text-zinc-400 font-bold uppercase">{platform.platform}</span>
                                <div className="flex items-center gap-3">
                                    <span className="text-white">${platform.revenue.toFixed(2)}</span>
                                    <span className="text-zinc-600">({(platform.views || platform.clicks || 0).toLocaleString()})</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Scale & Velocity</h4>
                <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col">
                        <span className="text-[8px] text-zinc-500 font-bold uppercase tracking-widest">Velocity Multiplier</span>
                        <p className="text-2xl font-bold text-white mt-1">{velocity.toFixed(1)}x</p>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[8px] text-zinc-500 font-bold uppercase tracking-widest">Global Scale</span>
                        <h2 className="text-2xl font-bold text-amber-500 mt-1">{totalPublished} Scale</h2>
                    </div>
                </div>
            </div>
        </>
    );
}

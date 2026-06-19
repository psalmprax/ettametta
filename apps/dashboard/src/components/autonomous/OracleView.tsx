"use client";

import React from "react";
import { Sparkles } from "lucide-react";

/** Module-internal — do not consume from outside. */
interface Props {
    insights: any;
}

/**
 * Insight-Oracle tab — hypothesis title + market-alignment bar + hook quote.
 */
export default function OracleView({ insights }: Props) {
    return (
        <div className="h-full min-h-[400px] p-12 border border-white/5 bg-[#0F0F11]/60 rounded-[40px] space-y-8">
            <div className="flex items-center gap-4">
                <Sparkles className="h-8 w-8 text-emerald-500" />
                <h3 className="text-2xl font-black text-white uppercase tracking-tighter">Strategic Insight Oracle</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="p-8 rounded-3xl bg-white/2 border border-white/5 space-y-4">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Hypothesis</label>
                    <p className="text-white text-lg font-bold leading-tight">{insights?.title || "HYPOTHESIS_PENDING"}</p>
                </div>
                <div className="p-8 rounded-3xl bg-white/2 border border-white/5 space-y-4">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Market Alignment</label>
                    <div className="flex items-center gap-4">
                        <div className="h-2 flex-1 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 w-[78%]" />
                        </div>
                        <span className="text-emerald-500 font-bold">78%</span>
                    </div>
                </div>
            </div>
            <div className="p-8 rounded-3xl bg-emerald-500/5 border border-emerald-500/10">
                <p className="text-zinc-400 leading-relaxed italic">"{insights?.hook || "Waiting for autonomous agents to report high-confidence signals..."}"</p>
            </div>
        </div>
    );
}

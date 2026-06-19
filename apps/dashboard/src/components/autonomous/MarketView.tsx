"use client";

import React from "react";
import { Radar } from "lucide-react";

/**
 * Market-Pulse tab placeholder — animated radar awaiting trend-signal feed.
 */
export default function MarketView() {
    return (
        <div className="h-full min-h-[400px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px]">
            <div className="flex flex-col items-center gap-6">
                <Radar className="h-16 w-16 text-emerald-500 animate-spin-slow" />
                <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Market Pulse Radar</h3>
                <span className="text-[10px] text-zinc-500 font-mono italic">SCANNING_GLOBAL_TREND_SIGNAL_VECTORS</span>
            </div>
        </div>
    );
}

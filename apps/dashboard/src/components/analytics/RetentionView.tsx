"use client";

import React from "react";
import { Activity } from "lucide-react";
import { AreaChartCustom } from "@/components/ui/ChartComponents";

/** Module-internal — do not consume from outside. */
interface Props {
    retentionData: { time: number; value: number }[];
}

/**
 * Attention-Decay tab — Area chart with overlay banner showing avg-stability
 * and live-stream indicator.
 */
export default function RetentionView({ retentionData }: Props) {
    return (
        <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-8 flex flex-col relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[100px] -mr-32 -mt-32" />
            <div className="flex items-center justify-between mb-8 relative z-10">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                        <Activity className="h-5 w-5 text-emerald-400" />
                        Attention Decay Analysis
                    </h3>
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mt-1">Neural Retention Mapping • Active Stream</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] font-bold text-emerald-500 uppercase">Avg Stability</span>
                        <span className="text-lg font-black text-white">82.4%</span>
                    </div>
                    <div className="h-10 w-px bg-white/5 mx-2" />
                    <div className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]" />
                </div>
            </div>
            <div className="flex-1 min-h-[350px] relative z-10">
                <AreaChartCustom data={retentionData} dataKey="value" color="#10b981" height="100%" gradientId="retentionGradient" />
            </div>
            <div className="mt-6 flex items-center justify-between relative z-10 pt-6 border-t border-white/5">
                <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Control Group</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-500/30" />
                        <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Projected Drift</span>
                    </div>
                </div>
                <span className="text-[9px] font-mono text-zinc-600">SAMPLE_SIZE: 14.2K_NODES</span>
            </div>
        </div>
    );
}

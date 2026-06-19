"use client";

import React from "react";
import nextDynamic from "next/dynamic";

const GlobalPulseGlobe = nextDynamic(() => import("@/components/ui/GlobalPulseGlobe"), { ssr: false });

interface Props {
    /** Already-derived velocity (defaults to 1.2 in page). */
    velocity: number;
    /** Already-derived signal integrity (defaults to 98.4 in page). */
    signal: number;
    /** Already-derived active-node count (defaults to 142 in page). */
    activeNodes: number;
    pulseIntensityMultiplier: number;
    setPulseIntensityMultiplier: (n: number) => void;
    /** Raw pulse object — only used to pass to GlobalPulseGlobe for telemetry. */
    pulse: any;
}

const REGIONAL_HUBS = [
    { name: "Americas", load: "74%", latency: "24ms", color: "border-cyan-500/20 text-cyan-400" },
    { name: "Europe", load: "89%", latency: "18ms", color: "border-violet-500/20 text-violet-400" },
    { name: "Asia-Pacific", load: "62%", latency: "42ms", color: "border-emerald-500/20 text-emerald-400" },
    { name: "Africa", load: "45%", latency: "58ms", color: "border-amber-500/20 text-amber-500" },
];

/**
 * Global-Pulse tab — globe visualisation + orbital-metrics slider + regional
 * hub list.
 */
export default function PropagationView({
    velocity,
    signal,
    activeNodes,
    pulseIntensityMultiplier,
    setPulseIntensityMultiplier,
    pulse,
}: Props) {
    return (
        <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-0">
            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative min-h-[450px] flex items-center justify-center">
                <GlobalPulseGlobe pulseIntensity={pulseIntensityMultiplier * velocity} telemetry={pulse} />
                <div className="absolute top-6 left-6 p-4 bg-black/60 backdrop-blur-xl border border-white/5 rounded-2xl space-y-1 select-none pointer-events-none">
                    <span className="text-[8px] font-black text-zinc-500 uppercase tracking-widest">Network Orbit</span>
                    <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                        <span className="text-xs font-bold text-white font-mono">SYNCED_TO_MAIN_ORBIT</span>
                    </div>
                </div>
                <div className="absolute bottom-6 left-6 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-xs space-y-3">
                    <h4 className="text-white font-black uppercase tracking-widest text-xs">Propagation Vector</h4>
                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">
                        Analyzing real-time content dispersion velocity across decentralized client clusters.
                    </p>
                </div>
            </div>

            <div className="w-full lg:w-80 flex flex-col gap-4">
                <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest">Orbit Metrics</h3>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-[10px]">
                                <span className="text-zinc-500 font-bold uppercase">Dispersion Rate</span>
                                <span className="text-cyan-400 font-mono">{velocity.toFixed(2)}x</span>
                            </div>
                            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-cyan-500" style={{ width: `${Math.min(100, velocity * 50)}%` }} />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-[10px]">
                                <span className="text-zinc-500 font-bold uppercase">Signal Integrity</span>
                                <span className="text-violet-400 font-mono">{signal.toFixed(1)}%</span>
                            </div>
                            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-violet-500" style={{ width: `${signal}%` }} />
                            </div>
                        </div>
                        <div className="space-y-2 pt-2">
                            <div className="flex justify-between text-[10px]">
                                <span className="text-zinc-500 font-bold uppercase">Pulse Multiplier</span>
                                <span className="text-amber-400 font-mono">{pulseIntensityMultiplier.toFixed(1)}x</span>
                            </div>
                            <input
                                type="range"
                                min="0.2"
                                max="3.0"
                                step="0.1"
                                value={pulseIntensityMultiplier}
                                onChange={(e) => setPulseIntensityMultiplier(parseFloat(e.target.value))}
                                className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-violet-500 outline-none"
                            />
                        </div>
                        <div className="flex justify-between text-xs pt-4 border-t border-white/5">
                            <span className="text-zinc-500 font-bold uppercase tracking-widest text-[9px]">Active Transmitters</span>
                            <span className="text-white font-bold font-mono">{activeNodes} Nodes</span>
                        </div>
                    </div>
                </div>

                <div className="flex-1 p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 flex flex-col min-h-0 space-y-4">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest">Regional Hubs</h3>
                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1">
                        {REGIONAL_HUBS.map((hub, idx) => (
                            <div key={idx} className={`p-3 bg-white/2 border rounded-xl flex items-center justify-between transition-all hover:bg-white/5 ${hub.color}`}>
                                <div>
                                    <p className="text-xs font-bold text-white">{hub.name}</p>
                                    <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider mt-0.5">Latency: {hub.latency}</p>
                                </div>
                                <div className="text-right">
                                    <span className="text-xs font-bold font-mono">{hub.load}</span>
                                    <p className="text-[8px] text-zinc-500 font-black uppercase tracking-widest mt-0.5">Load</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

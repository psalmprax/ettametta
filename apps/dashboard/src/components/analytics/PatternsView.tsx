"use client";

import React from "react";
import { motion } from "framer-motion";
import { Cpu, LineChart, Radar } from "lucide-react";
import { Button } from "@/components/ui/Button";

/**
 * Static content for the Patterns tab. Will move server-side once a real
 * ML-driven pattern-correlator ships.
 */
const PATTERNS_DATA = [
    { label: "Narrative Hook Resonance", score: 92, status: "DOMINANT" },
    { label: "High-Contrast Visual Flow", score: 84, status: "OPTIMIZED" },
    { label: "Cognitive Ease Index", score: 78, status: "STABLE" },
    { label: "Emotional Amplitude", score: 65, status: "GROWING" },
];

/**
 * Neural-Patterns tab — Success Correlation panel (animated probability
 * bars) + Prediction Matrix placeholder CTA.
 */
export default function PatternsView() {
    return (
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
            <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-6 flex flex-col min-h-0">
                <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                        <Cpu className="h-5 w-5 text-violet-400" />
                        Success Correlation
                    </h3>
                    <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest">Active Patterns</span>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
                    {PATTERNS_DATA.map((pattern, i) => (
                        <div key={i} className="p-6 bg-white/5 border border-white/5 rounded-[24px] group hover:border-violet-500/30 transition-all space-y-4">
                            <div className="flex items-center justify-between">
                                <h4 className="text-sm font-bold text-white">{pattern.label}</h4>
                                <span className="text-[9px] font-bold text-emerald-500 uppercase tracking-widest">{pattern.status}</span>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-[10px]">
                                    <span className="text-zinc-500 font-bold uppercase">Probability Shift</span>
                                    <span className="text-white font-mono">+{pattern.score}%</span>
                                </div>
                                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                    <motion.div initial={{ width: 0 }} animate={{ width: `${pattern.score}%` }} className="h-full bg-violet-500" />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-6 flex flex-col min-h-0">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                    <LineChart className="h-5 w-5 text-cyan-400" />
                    Prediction Matrix
                </h3>
                <div className="flex-1 flex flex-col items-center justify-center space-y-6 opacity-20">
                    <Radar className="h-16 w-16 text-zinc-500 animate-pulse" />
                    <div className="text-center space-y-2">
                        <p className="text-sm font-black uppercase tracking-[0.4em] text-white">Aggregating Global Drift</p>
                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest italic">Simulation running at 14.2 GFLOPS</p>
                    </div>
                </div>
                <Button className="w-full h-14 bg-violet-600 hover:bg-violet-500 text-white font-bold rounded-2xl uppercase tracking-widest text-xs transition-all">Launch Strategic Forecast</Button>
            </div>
        </div>
    );
}

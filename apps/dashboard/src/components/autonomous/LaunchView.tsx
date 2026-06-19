"use client";

import React from "react";
import { Layers, Share2, Cpu, Search, Radar, Sparkles, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

/** Module-internal — do not consume from outside. */
interface Props {
    isRunning: boolean;
    currentStep: string;
    insights: any;
}

/**
 * Launch-Control tab — orbital logic-flow visualization (Scout → Brain →
 * Render → Post) + Insight Oracle + Self-Correction banner.
 */
export default function LaunchView({ isRunning, currentStep, insights }: Props) {
    return (
        <>
            <div className="glass-card aspect-21/9 rounded-[40px] flex items-center justify-center relative overflow-hidden bg-[#0F0F11]/60 border border-white/5">
                <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                <div className="flex items-center gap-12 relative z-10">
                    <LogicNode icon={Search} label="Scout" active={isRunning && currentStep === "SCOUTING"} pulse={currentStep === "SCOUTING"} />
                    <Connector active={isRunning && ["SCREENING", "BRAINSTORMING", "RENDERING", "PUBLISHING", "WAITING"].includes(currentStep)} />
                    <LogicNode icon={Cpu} label="Brain" active={isRunning && ["SCREENING", "BRAINSTORMING"].includes(currentStep)} pulse={currentStep === "BRAINSTORMING"} />
                    <Connector active={isRunning && ["RENDERING", "PUBLISHING", "WAITING"].includes(currentStep)} />
                    <LogicNode icon={Layers} label="Render" active={isRunning && currentStep === "RENDERING"} pulse={currentStep === "RENDERING"} />
                    <Connector active={isRunning && ["PUBLISHING", "WAITING"].includes(currentStep)} />
                    <LogicNode icon={Share2} label="Post" active={isRunning && currentStep === "PUBLISHING"} pulse={currentStep === "PUBLISHING"} />
                </div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                    <div className="flex items-center gap-3">
                        <Sparkles className="h-4 w-4 text-emerald-500" />
                        <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Autonomous Insight Oracle</h3>
                    </div>
                    {insights ? (
                        <div className="space-y-4">
                            <h4 className="text-3xl font-bold text-white uppercase tracking-tighter">{insights.title}</h4>
                            <p className="text-zinc-500 text-sm leading-relaxed">{insights.hook}</p>
                        </div>
                    ) : (
                        <div className="h-32 flex flex-col items-center justify-center opacity-20">
                            <Radar className="h-10 w-10 animate-pulse" />
                            <span className="text-[8px] font-bold mt-2">LISTENING_FOR_PULSES</span>
                        </div>
                    )}
                </div>
                <div className="p-10 rounded-[32px] bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-8">
                    <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                        <Activity className="h-8 w-8" />
                    </div>
                    <div className="space-y-1">
                        <span className="text-[10px] font-bold text-emerald-500/60 uppercase tracking-widest">Self-Correction Mode</span>
                        <p className="text-white font-bold uppercase">Dynamic Optimization Active</p>
                    </div>
                </div>
            </div>
        </>
    );
}

/**
 * Logic-node chevron — used only by `LaunchView`. Module-private: the
 * step list is owned by the Launch tab, and we don't need a separate file.
 */
function LogicNode({
    icon: Icon,
    label,
    active,
    pulse,
}: {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    active: boolean;
    pulse: boolean;
}) {
    return (
        <div className="flex flex-col items-center gap-4">
            <div className={cn(
                "h-20 w-20 rounded-[32px] flex items-center justify-center transition-all duration-700 relative",
                active ? "bg-emerald-500 text-black shadow-[0_0_40px_rgba(16,185,129,0.4)]" : "bg-black/40 text-zinc-800 border border-white/5"
            )}>
                <Icon className="h-8 w-8" />
                {active && pulse && (
                    <div className="absolute inset-0 rounded-[32px] border-2 border-emerald-500 animate-ping opacity-20" />
                )}
            </div>
            <span className={cn(
                "text-[10px] font-bold uppercase tracking-widest transition-colors duration-500",
                active ? "text-emerald-500" : "text-zinc-800"
            )}>{label}</span>
        </div>
    );
}

/**
 * Connector line — links sequential logic-nodes. Module-private to
 * LaunchView's data model.
 */
function Connector({ active }: { active: boolean }) {
    return (
        <div className="h-px w-12 bg-white/5 relative">
            {active && <div className="absolute inset-0 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />}
        </div>
    );
}

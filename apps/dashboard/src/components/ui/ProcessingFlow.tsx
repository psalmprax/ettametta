"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from "@/lib/utils";
import { Info, Cpu, Sparkles, Database } from "lucide-react";

interface FlowStep {
    id: string;
    label: string;
    status: 'pending' | 'active' | 'complete' | 'error';
}

const STAGE_DETAILS: Record<string, { desc: string; icon: any; default_metric: string }> = {
    ingest: { desc: "Byte-stream verification and multi-threaded source retrieval.", icon: Database, default_metric: "Verifying Integrity" },
    analyze: { desc: "Deep semantic deconstruction and hook identification.", icon: Cpu, default_metric: "Semantic Extraction" },
    remix: { desc: "Neural pattern injection and social compliance wrapping.", icon: Sparkles, default_metric: "Neural Optimization" },
    render: { desc: "High-velocity parallel synthesis and encoding.", icon: Info, default_metric: "GPU Synthesis" }
};

export default React.memo(function ProcessingFlow({ steps, telemetry }: { readonly steps: FlowStep[], readonly telemetry?: any }) {
    const [selectedDetail, setSelectedDetail] = useState<string | null>(null);
    const completedSteps = steps.filter(s => s.status === 'complete').length;

    // Extract real-time metrics for active stages
    const activeMetrics = telemetry?.metrics || {};
    const bitrate = activeMetrics.bitrate ? `${activeMetrics.bitrate} kbps` : null;
    const latency = activeMetrics.latency ? `${activeMetrics.latency.toFixed(1)}ms` : null;

    return (
        <div
            className="w-full p-12 bg-zinc-950/20 border border-white/5 rounded-[3rem] relative overflow-hidden"
            role="region"
            aria-label="Processing flow visualization"
        >
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

            <div
                className="flex flex-col md:flex-row items-center justify-between relative gap-8"
                role="list"
                aria-label={`Processing steps: ${completedSteps} of ${steps.length} completed`}
            >
                {steps.map((step, idx) => {
                    const DetailIcon = STAGE_DETAILS[step.id]?.icon || Info;
                    return (
                        <React.Fragment key={step.id}>
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => setSelectedDetail(selectedDetail === step.id ? null : step.id)}
                                className={cn(
                                    "relative z-10 p-6 rounded-3xl border transition-all duration-700 w-full md:w-64 cursor-pointer",
                                    step.status === 'active' ? "bg-primary shadow-[0_0_40px_rgba(var(--primary-rgb),0.2)] border-white/20" :
                                        step.status === 'complete' ? "bg-zinc-900 border-emerald-500/30" : 
                                        step.status === 'error' ? "bg-red-500/10 border-red-500/50" : "bg-zinc-950/50 border-white/5",
                                    selectedDetail === step.id && "ring-2 ring-white/20 border-white/40"
                                )}
                            >
                                <div className="flex items-center justify-between mb-4">
                                    <span className={cn(
                                        "text-[8px] font-bold uppercase tracking-widest",
                                        step.status === 'active' ? "text-black" : 
                                        step.status === 'complete' ? "text-emerald-500" : 
                                        step.status === 'error' ? "text-red-500" : "text-zinc-600"
                                    )}>
                                        Stage_{idx + 1}
                                    </span>
                                    {step.status === 'active' && <div className="h-1.5 w-1.5 rounded-full bg-black animate-ping" />}
                                    {step.status === 'complete' && <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
                                    {step.status === 'error' && <div className="h-1.5 w-1.5 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />}
                                </div>
                                <h4 className={cn(
                                    "text-lg font-bold uppercase tracking-tighter",
                                    step.status === 'active' ? "text-black" : "text-white"
                                )}>
                                    {step.label}
                                </h4>

                                <AnimatePresence>
                                    {selectedDetail === step.id && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            className="mt-4 pt-4 border-t border-white/10 space-y-3"
                                        >
                                            <p className={cn(
                                                "text-[9px] font-medium leading-relaxed",
                                                step.status === 'active' ? "text-black/70" : "text-zinc-400"
                                            )}>
                                                {STAGE_DETAILS[step.id]?.desc}
                                            </p>
                                            <div className={cn(
                                                "flex items-center gap-2 text-[8px] font-bold uppercase tracking-widest",
                                                step.status === 'active' ? "text-black" : "text-primary"
                                            )}>
                                                <DetailIcon className="h-3 w-3" />
                                                {step.status === 'active' && bitrate ? (
                                                    <span className="flex items-center gap-3">
                                                        <span>{bitrate}</span>
                                                        {latency && <span className="opacity-40">| {latency}</span>}
                                                    </span>
                                                ) : (
                                                    STAGE_DETAILS[step.id]?.default_metric
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                <div className={cn(
                                    "mt-4 h-1 rounded-full overflow-hidden",
                                    step.status === 'active' ? "bg-black/20" : "bg-white/5"
                                )}>
                                    {step.status === 'active' && (
                                        <motion.div
                                            animate={{ x: ["-100%", "100%"] }}
                                            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                                            className="h-full w-1/2 bg-black"
                                            aria-hidden="true"
                                        />
                                    )}
                                    {step.status === 'complete' && <div className="h-full w-full bg-emerald-500" aria-hidden="true" />}
                                    {step.status === 'error' && <div className="h-full w-full bg-red-500" aria-hidden="true" />}
                                </div>
                            </motion.div>

                            {idx < steps.length - 1 && (
                                <div className="flex-1 h-px bg-white/5 relative min-w-[20px] hidden md:block">
                                    {step.status === 'complete' && (
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: "100%" }}
                                            className="absolute inset-0 h-full bg-primary/40 shadow-[0_0_10px_#00f2ff]"
                                        />
                                    )}
                                </div>
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        </div>
    );
});

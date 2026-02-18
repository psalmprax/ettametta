"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from "@/lib/utils";

interface FlowStep {
    id: string;
    label: string;
    status: 'pending' | 'active' | 'complete';
}

export default React.memo(function ProcessingFlow({ steps }: { steps: FlowStep[] }) {
    const completedSteps = steps.filter(s => s.status === 'complete').length;
    const activeStep = steps.find(s => s.status === 'active');

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
                {steps.map((step, idx) => (
                    <React.Fragment key={step.id}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: idx * 0.1 }}
                            role="listitem"
                            aria-label={`${step.label}: ${step.status}`}
                            aria-current={step.status === 'active' ? 'step' : undefined}
                            className={cn(
                                "relative z-10 p-6 rounded-3xl border transition-all duration-700 w-full md:w-64",
                                step.status === 'active' ? "bg-primary shadow-[0_0_40px_rgba(var(--primary-rgb),0.2)] border-white/20" :
                                    step.status === 'complete' ? "bg-zinc-900 border-emerald-500/30" : "bg-zinc-950/50 border-white/5"
                            )}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <span className={cn(
                                    "text-[8px] font-black uppercase tracking-widest",
                                    step.status === 'active' ? "text-black" : step.status === 'complete' ? "text-emerald-500" : "text-zinc-600"
                                )}>
                                    Stage_{idx + 1}
                                </span>
                                {step.status === 'active' && <div className="h-1.5 w-1.5 rounded-full bg-black animate-ping" />}
                                {step.status === 'complete' && <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
                            </div>
                            <h4 className={cn(
                                "text-lg font-black uppercase tracking-tighter italic",
                                step.status === 'active' ? "text-black" : "text-white"
                            )}>
                                {step.label}
                            </h4>
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
                ))}
            </div>
        </div>
    );
});

"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Activity, ShieldCheck, Zap, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

interface CommandPodProps {
    readonly name: string;
    readonly status: "nominal" | "degraded" | "critical" | "offline";
    readonly load: number; // 0-100
    readonly circuitBreaker: "closed" | "open" | "half-open";
    readonly description?: string;
}

export function CommandPod({ name, status, load, circuitBreaker, description }: CommandPodProps) {
    const getStatusColor = () => {
        switch (status) {
            case "nominal": return "text-emerald-500 border-emerald-500/20 shadow-emerald-500/20";
            case "degraded": return "text-amber-500 border-amber-500/20 shadow-amber-500/20";
            case "critical": return "text-rose-500 border-rose-500/20 shadow-rose-500/20";
            default: return "text-zinc-600 border-zinc-800 shadow-transparent";
        }
    };

    const getBreakerIcon = () => {
        if (circuitBreaker === "open") return <AlertTriangle className="h-4 w-4 text-rose-500 animate-pulse" />;
        if (circuitBreaker === "half-open") return <Zap className="h-4 w-4 text-amber-500" />;
        return <ShieldCheck className="h-4 w-4 text-emerald-500" />;
    };

    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn(
                "glass-card p-6 border bg-white/[0.01] transition-all hover:bg-white/[0.03] relative overflow-hidden group",
                getStatusColor()
            )}
        >
            {/* Glow Effect */}
            <div className={cn(
                "absolute -inset-1 opacity-0 group-hover:opacity-10 blur-xl transition-opacity duration-500",
                status === "nominal" ? "bg-emerald-500" : status === "degraded" ? "bg-amber-500" : "bg-rose-500"
            )} />

            <div className="flex items-center justify-between mb-6 relative">
                <div className="space-y-1">
                    <p className="text-[10px] font-bold uppercase tracking-[0.3em] opacity-50">Service Cluster</p>
                    <h4 className="text-sm font-bold text-white uppercase tracking-tight">{name}</h4>
                </div>
                <div className="h-10 w-10 rounded-xl bg-black/40 border border-white/5 flex items-center justify-center">
                    {status === "nominal" ? <Activity className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
                </div>
            </div>

            <div className="space-y-4 relative">
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <span className="text-[9px] font-bold uppercase tracking-widest opacity-40">Load Intensity</span>
                        <span className="text-[10px] font-mono font-bold text-white">{load}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden border border-white/5">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${load}%` }}
                            className={cn(
                                "h-full rounded-full transition-all duration-1000",
                                load > 80 ? "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]" : 
                                load > 50 ? "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]" : 
                                "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                            )}
                        />
                    </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                    <div className="flex items-center gap-2">
                        {getBreakerIcon()}
                        <span className="text-[8px] font-bold uppercase tracking-widest text-zinc-500">Breaker: {circuitBreaker}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <div className={cn(
                            "h-1 w-1 rounded-full",
                            status === "nominal" ? "bg-emerald-500 shadow-[0_0_5px_#10b981]" : "bg-rose-500"
                        )} />
                        <span className="text-[8px] font-bold uppercase tracking-widest opacity-60">{status}</span>
                    </div>
                </div>

                {description && (
                    <p className="text-[9px] text-zinc-500 leading-relaxed font-medium pt-2 border-t border-white/5 opacity-0 group-hover:opacity-100 transition-opacity">
                        {description}
                    </p>
                )}
            </div>
        </motion.div>
    );
}

"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from "@/lib/utils";
import {
    Search,
    Cpu,
    Sparkles,
    Share2,
    Database,
    Zap,
    AlertCircle,
    CheckCircle2,
    Clock
} from "lucide-react";

export type NodeType = 'ingress' | 'cognition' | 'synthesis' | 'egress';

interface NexusNodeProps {
    type: NodeType;
    label: string;
    description: string;
    status: 'pending' | 'processing' | 'complete' | 'error';
    active?: boolean;
    progress?: number;
    metrics?: { label: string; value: string }[];
    onClick?: () => void;
}

const NODE_CONFIG: Record<NodeType, { icon: any; color: string; bg: string }> = {
    ingress: { icon: Database, color: "text-blue-400", bg: "bg-blue-400/10" },
    cognition: { icon: Cpu, color: "text-purple-400", bg: "bg-purple-400/10" },
    synthesis: { icon: Sparkles, color: "text-primary", bg: "bg-primary/10" },
    egress: { icon: Share2, color: "text-emerald-400", bg: "bg-emerald-400/10" }
};

export function NexusNode({ type, label, description, status, active, progress, metrics, onClick }: NexusNodeProps) {
    const config = NODE_CONFIG[type];
    const Icon = config.icon;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.02, y: -5 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClick}
            className={cn(
                "w-72 p-6 rounded-[2rem] border transition-all duration-300 relative overflow-hidden group mb-4",
                active
                    ? "bg-zinc-900 border-primary/40 shadow-[0_0_50px_rgba(var(--primary-rgb),0.15)]"
                    : "bg-zinc-950/40 border-white/5 hover:border-primary/20",
                onClick && "cursor-pointer",
                status === 'complete' && "border-emerald-500/30 bg-emerald-500/[0.02]"
            )}
        >
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

            <div className="flex items-start justify-between mb-6">
                <div className={cn("p-4 rounded-2xl", config.bg)}>
                    <Icon className={cn("h-6 w-6", config.color)} />
                </div>
                <div className="flex flex-col items-end">
                    {status === 'processing' && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/20 border border-primary/20">
                            <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                            <span className="text-[8px] font-black text-primary uppercase tracking-widest">Active</span>
                        </div>
                    )}
                    {status === 'complete' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                    {status === 'pending' && <Clock className="h-4 w-4 text-zinc-600" />}
                    {status === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
                </div>
            </div>

            <div className="space-y-1 mb-4">
                <h4 className="text-sm font-black text-white uppercase tracking-tight italic group-hover:text-primary transition-colors">
                    {label}
                </h4>
                <p className="text-[10px] font-medium text-zinc-500 leading-relaxed line-clamp-2">
                    {description}
                </p>
            </div>

            {active && progress !== undefined && (
                <div className="space-y-2 mb-6">
                    <div className="flex items-center justify-between text-[8px] font-black uppercase tracking-widest text-zinc-500">
                        <span>Progress</span>
                        <span className="text-primary">{progress}%</span>
                    </div>
                    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            className="h-full bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]"
                        />
                    </div>
                </div>
            )}

            {metrics && metrics.length > 0 && (
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                    {metrics.map((m, i) => (
                        <div key={i} className="space-y-1">
                            <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest">{m.label}</p>
                            <p className="text-[10px] font-black text-white">{m.value}</p>
                        </div>
                    ))}
                </div>
            )}
        </motion.div>
    );
}

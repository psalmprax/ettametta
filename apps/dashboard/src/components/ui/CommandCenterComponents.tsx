"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
    Eye,
    Sparkles,
    Clapperboard,
    Mic2,
    FileText,
    Download
} from "lucide-react";
import { motion } from "framer-motion";

// --- AgentMatrix Component ---

interface AgentStatus {
    id: string;
    name: string;
    icon: any;
    status: "ACTIVE" | "IDLE" | "DEGRADED" | "QUEUED";
    latency: number;
    load: number;
    details?: string;
}

export function AgentMatrix({ agents }: { readonly agents: AgentStatus[] }) {
    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Agent Matrix</h3>
                <div className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded text-[8px] font-bold text-emerald-500 uppercase">
                    Monitoring_Active
                </div>
            </div>
            <div className="space-y-2">
                {agents?.map((agent) => (
                    <motion.div
                        key={agent.id}
                        whileHover={{ scale: 1.01, backgroundColor: "rgba(255, 255, 255, 0.03)" }}
                        className="p-3 rounded-xl border border-white/5 bg-white/5 space-y-2 transition-all group"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className={cn(
                                    "h-8 w-8 rounded-lg flex items-center justify-center border border-white/10",
                                    agent.status === "ACTIVE" ? "bg-violet-500/20 text-violet-400" : "bg-white/5 text-zinc-500"
                                )}>
                                    <agent.icon className="h-4 w-4" />
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xs font-bold text-white uppercase">{agent.name}</span>
                                    <span className="text-[10px] text-zinc-600 font-mono tracking-tighter">ID: {agent.id}</span>
                                </div>
                            </div>
                            <div className="flex flex-col items-end">
                                <div className="flex items-center gap-1.5">
                                    <div className={cn(
                                        "h-1.5 w-1.5 rounded-full",
                                        agent.status === "ACTIVE" ? "bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" : 
                                        agent.status === "IDLE" ? "bg-zinc-700" : "bg-rose-500"
                                    )} />
                                    <span className={cn(
                                        "text-[10px] font-bold uppercase",
                                        agent.status === "ACTIVE" ? "text-emerald-500" : "text-zinc-600"
                                    )}>{agent.status}</span>
                                </div>
                                <span className="text-[10px] text-zinc-500 font-mono mt-1">{agent.latency}ms</span>
                            </div>
                        </div>

                        {agent.status === "ACTIVE" && (
                            <div className="space-y-2">
                                <div className="flex justify-between items-center text-[8px] font-bold text-zinc-500 uppercase">
                                    <span>Neural Load</span>
                                    <span>{agent.load}%</span>
                                </div>
                                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                    <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${agent.load}%` }}
                                        className="h-full bg-violet-500"
                                    />
                                </div>
                                {agent.details && (
                                    <p className="text-[9px] text-zinc-500 font-medium truncate italic">
                                        &gt; {agent.details}
                                    </p>
                                )}
                            </div>
                        )}
                    </motion.div>
                ))}
            </div>
        </div>
    );
}

// --- AssetQuickview Component ---

interface Asset {
    id: string;
    title: string;
    type: "VIDEO" | "IMAGE" | "VOICE" | "SCRIPT";
    thumbnail?: string;
    timestamp: string;
    tags: string[];
    size?: string;
}

export function AssetQuickview({ assets }: { readonly assets: Asset[] }) {
    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-[10px] font-bold text-cyan-400 tracking-[0.2em] uppercase">Asset Quickview</h3>
                <button className="text-[10px] font-bold text-zinc-500 hover:text-white uppercase transition-colors">
                    View_All
                </button>
            </div>
            <div className="space-y-3">
                {assets?.map((asset) => (
                    <motion.div
                        key={asset.id}
                        whileHover={{ scale: 1.01 }}
                        className="group relative rounded-xl border border-white/5 bg-white/5 overflow-hidden transition-all"
                    >
                        {/* Thumbnail or Icon Placeholder */}
                        <div className="aspect-video w-full bg-zinc-900 relative overflow-hidden">
                            {asset.thumbnail ? (
                                <img src={asset.thumbnail} alt={asset.title} className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                    {asset.type === "VIDEO" && <Clapperboard className="h-10 w-10 text-zinc-800" />}
                                    {asset.type === "IMAGE" && <Sparkles className="h-10 w-10 text-zinc-800" />}
                                    {asset.type === "VOICE" && <Mic2 className="h-10 w-10 text-zinc-800" />}
                                    {asset.type === "SCRIPT" && <FileText className="h-10 w-10 text-zinc-800" />}
                                </div>
                            )}
                            
                            {/* Scanning Overlay Effect */}
                            <div className="absolute inset-0 bg-linear-to-b from-cyan-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-cyan-500/50" />
                            <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-500/50" />
                            <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-500/50" />
                            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-cyan-500/50" />

                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-sm">
                                <div className="flex gap-2">
                                    <button className="h-8 w-8 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-center text-white">
                                        <Eye className="h-4 w-4" />
                                    </button>
                                    <button className="h-8 w-8 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-center text-white">
                                        <Download className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>

                            {/* Tags */}
                            <div className="absolute top-2 right-2 flex gap-1">
                                {asset.tags?.map((tag, i) => (
                                    <span key={i} className="px-1.5 py-0.5 bg-black/60 backdrop-blur-md border border-white/10 rounded text-[7px] font-bold text-cyan-400 uppercase tracking-tighter">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Metadata */}
                        <div className="p-3 space-y-1.5">
                            <div className="flex items-center justify-between">
                                <h4 className="text-[10px] font-bold text-white uppercase truncate flex-1">{asset.title}</h4>
                                <span className="text-[9px] text-zinc-600 font-mono ml-2">{asset.size}</span>
                            </div>
                            <div className="flex items-center justify-between text-[8px] font-bold text-zinc-500 uppercase tracking-wider">
                                <span>{asset.timestamp}</span>
                                <span className="text-zinc-700">ID: {asset.id.slice(0, 8)}</span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
            <button className="w-full h-10 border border-white/5 bg-white/20 hover:bg-white/30 text-[10px] font-bold text-white uppercase tracking-widest transition-all rounded-xl">
                View Full Repository
            </button>
        </div>
    );
}

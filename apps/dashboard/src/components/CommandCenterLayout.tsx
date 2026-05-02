"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { 
    Cpu, 
    Terminal, 
    Activity, 
    Layers, 
    Zap, 
    Database, 
    Globe, 
    Settings,
    Layout,
    ChevronLeft,
    ChevronRight,
    Search,
    User,
    ShieldCheck
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar } from "./sidebar";

interface CommandCenterLayoutProps {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
    leftPanel?: React.ReactNode;
    rightPanel?: React.ReactNode;
}

import { useTelemetry } from "@/context/TelemetryContext";

export default function CommandCenterLayout({ 
    children, 
    title = "COMMAND CENTER", 
    subtitle = "INTEL_OS_V4.2",
    leftPanel,
    rightPanel 
}: CommandCenterLayoutProps) {
    const { pulse, status } = useTelemetry();
    const [isLeftExpanded, setIsLeftExpanded] = useState(true);
    const [isRightExpanded, setIsRightExpanded] = useState(true);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    return (
        <div className="flex h-screen bg-[#050507] text-white font-space-grotesk overflow-hidden relative">
            {/* Subtle Grid Background */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03]" 
                 style={{ backgroundImage: 'linear-gradient(rgba(45, 112, 255, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(45, 112, 255, 0.2) 1px, transparent 1px)', backgroundSize: '24px 24px' }} 
            />

            {/* Main Side Nav (The global one) */}
            <div className="hidden lg:block">
                <Sidebar />
            </div>

            {/* Left Engine Navigation (260px) */}
            <AnimatePresence>
                {isLeftExpanded && (
                    <motion.aside
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 260, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="h-full border-r border-white/5 bg-black/40 backdrop-blur-xl z-10 flex flex-col relative"
                    >
                        <div className="p-6 border-b border-white/5 flex items-center justify-between">
                            <span className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase">Specialized Engines</span>
                            <button onClick={() => setIsLeftExpanded(false)} className="text-zinc-500 hover:text-white transition-colors">
                                <ChevronLeft className="h-4 w-4" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
                            {leftPanel || (
                                <div className="space-y-2 opacity-50 text-center py-20 italic text-zinc-600 text-xs">
                                    ENGINE_SLOT_EMPTY
                                </div>
                            )}
                        </div>
                    </motion.aside>
                )}
            </AnimatePresence>

            {!isLeftExpanded && (
                <button 
                    onClick={() => setIsLeftExpanded(true)}
                    className="absolute left-[70px] top-1/2 -translate-y-1/2 bg-white/5 border border-white/10 p-1 rounded-r-lg z-20"
                >
                    <ChevronRight className="h-4 w-4" />
                </button>
            )}

            {/* Center Creative Workspace (Flexible) */}
            <main className="flex-1 flex flex-col h-full overflow-hidden relative z-10">
                {/* Header */}
                <header className="h-20 border-b border-white/5 bg-black/20 backdrop-blur-md px-10 flex items-center justify-between shrink-0">
                    <div className="flex flex-col">
                        <div className="flex items-center gap-3">
                            <h1 className="text-2xl font-bold tracking-tight text-white uppercase">{title}</h1>
                            <div className="px-2 py-0.5 bg-violet-500/10 border border-violet-500/20 rounded text-[10px] font-bold text-violet-400">
                                {subtitle}
                            </div>
                        </div>
                        <span className="text-[10px] font-bold text-zinc-600 tracking-[0.4em] mt-1 uppercase">Synchronizing Neural Channels...</span>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] font-bold text-zinc-500 uppercase">System Uptime</span>
                            <span className="text-xs font-mono text-emerald-500">{pulse?.uptime || "00:00:00"}</span>
                        </div>
                        <div className="h-10 w-px bg-white/5" />
                        <div className="flex items-center gap-4">
                            <div 
                                onClick={() => setIsSearchOpen(true)}
                                className="h-10 w-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer hover:bg-white/10 group"
                            >
                                <Search className="h-5 w-5 group-hover:scale-110 transition-transform" />
                            </div>
                            <div 
                                onClick={() => setIsSettingsOpen(true)}
                                className="h-10 w-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer hover:bg-white/10 group"
                            >
                                <Settings className="h-5 w-5 group-hover:rotate-90 transition-transform duration-500" />
                            </div>
                        </div>
                    </div>
                </header>

                {/* Main Content Area */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {children}
                </div>

                {/* Footer / Status Bar */}
                <footer className="h-10 border-t border-white/5 bg-black px-10 flex items-center justify-between shrink-0 text-[10px] font-bold text-zinc-600 tracking-widest">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <div className={cn("h-1.5 w-1.5 rounded-full animate-pulse", status === "open" ? "bg-emerald-500" : "bg-rose-500")} />
                            <span className={cn(status === "open" ? "text-emerald-500/80" : "text-rose-500/80")}>
                                {status === "open" ? "SYSTEM_STABLE" : "CONNECTION_LOST"}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>LATENCY:</span>
                            <span className="text-zinc-400">{pulse?.latency_ms || "---"} MS</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <span>NODE: {pulse?.hostname || "LOCAL_COMMAND"}</span>
                        <span className="text-violet-500/80 uppercase">V-ID: {(pulse?.cluster_node || "X-0").slice(0, 8)}</span>
                    </div>
                </footer>
            </main>

            {/* Right Contextual Utilities (320px) */}
            <AnimatePresence>
                {isRightExpanded && (
                    <motion.aside
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 320, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="h-full border-l border-white/5 bg-black/40 backdrop-blur-xl z-10 flex flex-col relative"
                    >
                        <div className="p-6 border-b border-white/5 flex items-center justify-between">
                            <button onClick={() => setIsRightExpanded(false)} className="text-zinc-500 hover:text-white transition-colors">
                                <ChevronRight className="h-4 w-4" />
                            </button>
                            <span className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase">Contextual Intelligence</span>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
                            {rightPanel || (
                                <div className="space-y-4 opacity-50 text-center py-20 italic text-zinc-600 text-xs">
                                    CONTEXT_UNIT_IDLE
                                </div>
                            )}
                        </div>
                    </motion.aside>
                )}
            </AnimatePresence>

            {!isRightExpanded && (
                <button 
                    onClick={() => setIsRightExpanded(true)}
                    className="absolute right-0 top-1/2 -translate-y-1/2 bg-white/5 border border-white/10 p-1 rounded-l-lg z-20"
                >
                    <ChevronLeft className="h-4 w-4" />
                </button>
            )}
            {/* Global Overlays */}
            <AnimatePresence>
                {isSearchOpen && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-2xl flex items-center justify-center p-6"
                        onClick={() => setIsSearchOpen(false)}
                    >
                        <motion.div 
                            initial={{ scale: 0.9, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            className="w-full max-w-2xl bg-[#0F0F11] border border-white/10 rounded-[32px] p-8 shadow-2xl"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="flex items-center gap-4 mb-8">
                                <Search className="h-6 w-6 text-cyan-400" />
                                <input 
                                    autoFocus
                                    placeholder="SEARCH_NEURAL_ASSETS..."
                                    className="bg-transparent border-none outline-none text-2xl font-bold text-white placeholder:text-zinc-800 w-full uppercase"
                                />
                            </div>
                            <div className="space-y-4">
                                <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Recent Queries</span>
                                <div className="grid grid-cols-1 gap-2">
                                    {["TREND_CLUSTER_ALPHA", "EGRESS_GATE_STATS", "AGENT_PERSONA_SYNC"].map(q => (
                                        <div key={q} className="p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-all flex items-center justify-between group">
                                            <span className="text-xs font-bold text-zinc-400 group-hover:text-white">{q}</span>
                                            <ChevronRight className="h-4 w-4 text-zinc-700" />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}

                {isSettingsOpen && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-2xl flex items-center justify-center p-6"
                        onClick={() => setIsSettingsOpen(false)}
                    >
                        <motion.div 
                            initial={{ scale: 0.9, x: 20 }}
                            animate={{ scale: 1, x: 0 }}
                            className="w-full max-w-xl bg-[#0F0F11] border border-white/10 rounded-[32px] p-10 shadow-2xl"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-10">
                                <h2 className="text-2xl font-bold text-white uppercase tracking-tighter flex items-center gap-3">
                                    <Settings className="h-6 w-6 text-violet-400" />
                                    System Settings
                                </h2>
                                <button onClick={() => setIsSettingsOpen(false)} className="text-zinc-500 hover:text-white transition-colors uppercase text-[10px] font-bold tracking-widest">Close</button>
                            </div>
                            
                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Neural Sync Mode</label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <button className="p-4 bg-violet-500/10 border border-violet-500/20 rounded-2xl text-xs font-bold text-violet-400">High Velocity</button>
                                        <button className="p-4 bg-white/5 border border-white/5 rounded-2xl text-xs font-bold text-zinc-500 hover:text-white transition-all">Deep Analysis</button>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Global Egress</label>
                                    <div className="flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-2xl">
                                        <span className="text-xs font-bold text-zinc-400">Auto-Publish to TikTok</span>
                                        <div className="h-6 w-12 bg-emerald-500/20 border border-emerald-500/40 rounded-full relative p-1">
                                            <div className="h-full aspect-square bg-emerald-500 rounded-full ml-auto" />
                                        </div>
                                    </div>
                                </div>
                                <div className="pt-4 border-t border-white/5 flex gap-4">
                                    <button className="flex-1 h-12 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-bold uppercase tracking-widest text-zinc-400">Export Config</button>
                                    <button className="flex-1 h-12 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl text-[10px] font-bold uppercase tracking-widest text-rose-500">Purge Local Cache</button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

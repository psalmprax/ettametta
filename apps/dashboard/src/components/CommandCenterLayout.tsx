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
import { Sidebar } from "../sidebar";

interface CommandCenterLayoutProps {
    children: React.ReactNode;
    title?: string;
    subtitle?: string;
    leftPanel?: React.ReactNode;
    rightPanel?: React.ReactNode;
}

export default function CommandCenterLayout({ 
    children, 
    title = "COMMAND CENTER", 
    subtitle = "INTEL_OS_V4.2",
    leftPanel,
    rightPanel 
}: CommandCenterLayoutProps) {
    const [isLeftExpanded, setIsLeftExpanded] = useState(true);
    const [isRightExpanded, setIsRightExpanded] = useState(true);

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
                            <span className="text-xs font-mono text-emerald-500">142:12:08</span>
                        </div>
                        <div className="h-10 w-px bg-white/5" />
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer">
                                <Search className="h-5 w-5" />
                            </div>
                            <div className="h-10 w-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer">
                                <Settings className="h-5 w-5" />
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
                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-emerald-500/80">SYSTEM_STABLE</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>THROUGHPUT:</span>
                            <span className="text-zinc-400">1.2 GB/S</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <span>NODE: US-EAST-COMMAND</span>
                        <span className="text-violet-500/80">ENCRYPTION: AES-256-LIVE</span>
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
        </div>
    );
}

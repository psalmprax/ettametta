"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    Search,
    Video,
    Share2,
    BarChart3,
    Settings,
    Zap,
    LogOut,
    Sparkles,
    Cpu,
    Lock,
    TrendingUp
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

import { motion, AnimatePresence } from "framer-motion";

import { Crown, Coins } from "lucide-react";

const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Discovery", href: "/discovery", icon: Search },
    { name: "Creation", href: "/creation", icon: Sparkles },
    { name: "Nexus Flow", href: "/nexus", icon: Zap },
    { name: "Autonomous", href: "/autonomous", icon: Cpu },
    { name: "Transformation", href: "/transformation", icon: Video },
    { name: "Publishing", href: "/publishing", icon: Share2 },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
    { name: "Empire", href: "/empire", icon: Crown },
    { name: "Credits", href: "/credits", icon: Coins },
    { name: "Trading", href: "/trading", icon: TrendingUp },
];

export function Sidebar() {
    const pathname = usePathname();
    const { logout, user } = useAuth();

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col h-full w-72 glass-sidebar text-zinc-400 relative overflow-hidden z-40"
        >
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            <div className="absolute top-0 left-0 w-full h-[2px] bg-linear-to-r from-transparent via-cyan-400/30 to-transparent shadow-[0_0_15px_rgba(34,211,238,0.5)]" />

            <Link href="/" className="flex items-center gap-4 px-8 py-10 hover:opacity-90 transition-all relative group">
                <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="h-11 w-11 rounded-xl bg-linear-to-br from-violet-600 to-cyan-500 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.3)] relative overflow-hidden"
                >
                    <div className="absolute inset-0 shimmer opacity-20" />
                    <Zap className="h-6 w-6 text-white fill-white neon-glow-violet" />
                </motion.div>
                <div className="flex flex-col">
                    <span className="text-xl font-black text-white tracking-tighter uppercase leading-none group-hover:text-cyan-400 transition-colors">ettametta</span>
                    <span className="text-[9px] font-black text-cyan-400 tracking-[0.4em] uppercase mt-1.5 opacity-80 flex items-center gap-1.5">
                        <div className="h-1 w-1 rounded-full bg-cyan-400 animate-pulse" />
                        OS // V3.0
                    </span>
                </div>
            </Link>

            <nav className="flex-1 px-4 space-y-1 relative z-10">
                {navItems.map((item, index) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-300 group relative cyber-border",
                                isActive
                                    ? "text-cyan-400 bg-white/2"
                                    : "hover:text-white"
                            )}
                        >
                            <AnimatePresence>
                                {isActive && (
                                    <motion.div
                                        layoutId="nav-active"
                                        className="absolute inset-0 bg-cyan-400/5 rounded-xl"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                    >
                                        <div className="absolute -left-px top-1/4 w-[2px] h-1/2 bg-cyan-400 neon-glow-cyan" />
                                    </motion.div>
                                )}
                            </AnimatePresence>
                            <motion.div
                                whileHover={{ scale: 1.1 }}
                                className="z-10"
                            >
                                <item.icon className={cn(
                                    "h-4.5 w-4.5 transition-all duration-300",
                                    isActive ? "text-cyan-400 neon-glow-cyan" : "text-zinc-500 group-hover:text-zinc-200"
                                )} />
                            </motion.div>
                            <span className={cn(
                                "font-black text-[10px] uppercase tracking-[0.2em] z-10",
                                isActive ? "text-cyan-400" : "text-zinc-500 group-hover:text-zinc-200"
                            )}>{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="px-6 py-8 space-y-6 relative z-10 border-t border-white/5 bg-zinc-950/20">
                <div className="p-5 rounded-2xl bg-zinc-900/50 border border-white/5 space-y-4 relative overflow-hidden group shadow-inner">
                    <div className="flex items-center justify-between">
                        <span className="text-[8px] font-black uppercase tracking-[0.2em] text-zinc-600">Engine Core</span>
                        <div className="h-1 w-8 rounded-full bg-cyan-400/20 relative overflow-hidden">
                            <motion.div 
                                className="absolute inset-0 bg-cyan-400"
                                animate={{ x: ["-100%", "100%"] }}
                                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                            />
                        </div>
                    </div>
                    <div className="space-y-2.5">
                        <StatusLine label="Neural Network" pulse color="bg-cyan-400" />
                        <StatusLine label="Distribution" color="bg-violet-500" />
                    </div>
                </div>

                <div className="space-y-1">
                    <Link
                        href="/settings"
                        className={cn(
                            "flex items-center gap-4 px-5 py-3 rounded-xl transition-all duration-300 hover:text-white group border border-transparent hover:border-white/5",
                            pathname === "/settings" ? "text-white" : ""
                        )}
                    >
                        <Settings className="h-4 w-4 text-zinc-600 group-hover:text-cyan-400 transition-colors" />
                        <span className="font-black text-[9px] uppercase tracking-[0.25em]">Config</span>
                    </Link>

                    <button
                        onClick={logout}
                        className="w-full flex items-center gap-4 px-5 py-3 rounded-xl transition-all duration-300 hover:bg-violet-500/10 hover:text-violet-400 group border border-transparent hover:border-violet-500/10"
                    >
                        <LogOut className="h-4 w-4 text-zinc-600 group-hover:text-violet-400" />
                        <span className="font-black text-[9px] uppercase tracking-[0.25em]">Exit</span>
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

function StatusLine({ label, color, pulse = false }: { label: string, color: string, pulse?: boolean }) {
    return (
        <div className="flex items-center justify-between group/line">
            <span className="text-[9px] font-black text-zinc-500 tracking-widest uppercase transition-colors group-hover/line:text-zinc-300">{label}</span>
            <div className="flex items-center gap-3">
                <span className="text-[8px] font-black font-mono text-zinc-700 uppercase tracking-tighter group-hover/line:text-zinc-500 transition-colors">Nominal</span>
                <div className={cn(
                    "h-2 w-2 rounded-full relative shadow-lg",
                    color
                )}>
                    {pulse && <div className={cn("absolute inset-0 rounded-full animate-ping opacity-40", color)} />}
                    <div className="absolute inset-0 rounded-full bg-white/20" />
                </div>
            </div>
        </div>
    );
}

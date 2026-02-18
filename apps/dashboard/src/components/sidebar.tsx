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
    Sparkles
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

import { motion, AnimatePresence } from "framer-motion";

const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Discovery", href: "/discovery", icon: Search },
    { name: "Creation", href: "/creation", icon: Sparkles },
    { name: "Transformation", href: "/transformation", icon: Video },
    { name: "Publishing", href: "/publishing", icon: Share2 },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
];

export function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuth();

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col h-full w-72 glass-sidebar text-zinc-400 relative overflow-hidden z-40"
        >
            <div className="absolute inset-0 scanline opacity-10 pointer-events-none" />
            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]" />

            <Link href="/" className="flex items-center gap-4 px-8 py-12 hover:opacity-90 transition-all relative group">
                <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="h-12 w-12 rounded-2xl bg-primary flex items-center justify-center shadow-[0_0_30px_rgba(var(--primary-rgb),0.4)] relative overflow-hidden"
                >
                    <div className="absolute inset-0 shimmer opacity-20" />
                    <Zap className="h-7 w-7 text-white fill-white neon-glow" />
                </motion.div>
                <div className="flex flex-col">
                    <span className="text-2xl font-black text-white tracking-tighter uppercase italic leading-none group-hover:text-primary transition-colors">ViralForge</span>
                    <span className="text-[10px] font-black text-primary tracking-[0.3em] uppercase mt-1.5 opacity-80 flex items-center gap-1.5">
                        <div className="h-1 w-1 rounded-full bg-primary animate-pulse" />
                        Neural Cluster v2.4
                    </span>
                </div>
            </Link>

            <nav className="flex-1 px-5 space-y-2 pt-2 relative z-10">
                {navItems.map((item, index) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 group relative overflow-hidden",
                                isActive
                                    ? "text-primary shadow-[0_0_30px_rgba(var(--primary-rgb),0.1)] border border-white/10"
                                    : "hover:bg-white/[0.04] hover:text-white"
                            )}
                        >
                            <AnimatePresence>
                                {isActive && (
                                    <motion.div
                                        layoutId="nav-active"
                                        className="absolute inset-0 bg-primary/5"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.4 }}
                                    >
                                        <div className="absolute left-0 top-0 w-[3px] h-full bg-gradient-to-b from-primary via-primary/50 to-primary neon-glow" />
                                    </motion.div>
                                )}
                            </AnimatePresence>
                            <motion.div
                                whileHover={{ scale: 1.15, rotate: -2 }}
                                whileTap={{ scale: 0.95 }}
                                transition={{ type: "spring", stiffness: 400, damping: 17 }}
                                className="z-10"
                            >
                                <item.icon className={cn(
                                    "h-5 w-5 transition-all duration-300",
                                    isActive ? "text-primary neon-glow" : "text-zinc-600 group-hover:text-zinc-200"
                                )} />
                            </motion.div>
                            <span className={cn(
                                "font-black text-xs uppercase tracking-[0.15em] z-10 transition-colors duration-300 italic",
                                isActive ? "text-primary" : "text-zinc-500 group-hover:text-zinc-200"
                            )}>{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="px-6 py-8 space-y-6 relative z-10 border-t border-white/5 bg-black/20">
                {/* System Status Display (Investor durability feature) */}
                <div className="p-6 rounded-3xl bg-zinc-950/50 border border-white/5 space-y-4 shadow-inner relative overflow-hidden group">
                    <div className="absolute inset-0 scanline opacity-5" />
                    <div className="flex items-center justify-between relative">
                        <span className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-600 italic">Engine Status Matrix</span>
                        <div className="flex gap-1.5">
                            <div className="h-1 w-4 rounded-full bg-primary shadow-[0_0_5px_rgba(var(--primary-rgb),0.5)]" />
                            <div className="h-1 w-4 rounded-full bg-zinc-800" />
                        </div>
                    </div>
                    <div className="space-y-3 relative">
                        <StatusLine label="Intelligence Cluster" pulse color="bg-emerald-500" />
                        <StatusLine label="High-Velocity Nodes" pulse color="bg-primary" />
                        <StatusLine label="Neural Syncing" color="bg-zinc-700" />
                    </div>
                </div>

                <div className="space-y-2">
                    <Link
                        href="/settings"
                        className={cn(
                            "flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-500 hover:bg-white/[0.03] hover:text-white group border border-transparent hover:border-white/5",
                            pathname === "/settings" ? "bg-white/5 text-white border-white/5" : ""
                        )}
                    >
                        <Settings className="h-5 w-5 text-zinc-600 group-hover:text-primary transition-colors" />
                        <span className="font-black text-[10px] uppercase tracking-[0.2em] italic">Infrastructure Settings</span>
                    </Link>

                    <button
                        onClick={logout}
                        className="w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-500 hover:bg-primary/10 hover:text-primary group text-left border border-transparent hover:border-primary/20"
                    >
                        <LogOut className="h-5 w-5 text-zinc-600 group-hover:text-primary transition-colors" />
                        <span className="font-black text-[10px] uppercase tracking-[0.2em] italic">Terminate Connection</span>
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

function StatusLine({ label, color, pulse = false }: { label: string, color: string, pulse?: boolean }) {
    return (
        <div className="flex items-center justify-between group/line">
            <span className="text-[9px] font-black text-zinc-500 tracking-widest uppercase transition-colors group-hover/line:text-zinc-300 italic">{label}</span>
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

"use client";

import React, { useState, useMemo, memo } from "react";
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
    TrendingUp,
    Menu,
    X,
    Crown,
    Coins
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

import { motion, AnimatePresence } from "framer-motion";

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

interface SidebarProps {
    collapsed?: boolean;
    onToggle?: () => void;
}

export const Sidebar = memo<SidebarProps>(function Sidebar({ collapsed = false, onToggle }) {
    const pathname = usePathname();
    const { logout, user } = useAuth();

    // Memoize nav items to avoid recreation on every render
    const memoizedNavItems = useMemo(() => navItems, []);

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
                "flex flex-col h-full glass-sidebar text-zinc-400 relative overflow-hidden z-40 transition-all duration-300",
                collapsed ? "w-20" : "w-72"
            )}
        >
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            <div className="absolute top-0 left-0 w-full h-[2px] bg-linear-to-r from-transparent via-cyan-400/30 to-transparent shadow-[0_0_15px_rgba(34,211,238,0.5)]" />

            {/* Toggle Button */}
            <button
                onClick={onToggle}
                className="absolute top-4 right-4 z-50 p-2 rounded-lg hover:bg-white/5 transition-colors"
            >
                {collapsed ? <Menu className="h-5 w-5 text-zinc-400" /> : <X className="h-5 w-5 text-zinc-400" />}
            </button>

            <Link href="/" className={cn(
                "flex items-center gap-4 py-10 hover:opacity-90 transition-all relative group",
                collapsed ? "px-4 justify-center" : "px-8"
            )}>
                <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="h-11 w-11 rounded-xl bg-linear-to-br from-violet-600 to-cyan-500 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.3)] relative overflow-hidden flex-shrink-0"
                >
                    <div className="absolute inset-0 shimmer opacity-20" />
                    <Zap className="h-6 w-6 text-white fill-white neon-glow-violet" />
                </motion.div>
                <AnimatePresence>
                    {!collapsed && (
                        <motion.div
                            initial={{ opacity: 0, width: 0 }}
                            animate={{ opacity: 1, width: "auto" }}
                            exit={{ opacity: 0, width: 0 }}
                            className="flex flex-col overflow-hidden"
                        >
                            <span className="text-xl font-black text-white tracking-tighter uppercase leading-none group-hover:text-cyan-400 transition-colors whitespace-nowrap">ettametta</span>
                            <span className="text-[9px] font-black text-cyan-400 tracking-[0.4em] uppercase mt-1.5 opacity-80 flex items-center gap-1.5">
                                <div className="h-1 w-1 rounded-full bg-cyan-400 animate-pulse" />
                                OS // V3.0
                            </span>
                        </motion.div>
                    )}
                </AnimatePresence>
            </Link>

            <nav className={cn("flex-1 px-4 space-y-1 relative z-10", collapsed ? "px-2" : "")}>
                {navItems.map((item, index) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-300 group relative cyber-border",
                                collapsed && "justify-center px-3",
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
                                className="z-10 flex-shrink-0"
                            >
                                <item.icon className={cn(
                                    "h-4.5 w-4.5 transition-all duration-300",
                                    isActive ? "text-cyan-400 neon-glow-cyan" : "text-zinc-500 group-hover:text-zinc-200"
                                )} />
                            </motion.div>
                            <AnimatePresence>
                                {!collapsed && (
                                    <motion.span
                                        initial={{ opacity: 0, width: 0 }}
                                        animate={{ opacity: 1, width: "auto" }}
                                        exit={{ opacity: 0, width: 0 }}
                                        className={cn(
                                            "font-black text-[10px] uppercase tracking-[0.2em] z-10 whitespace-nowrap overflow-hidden",
                                            isActive ? "text-cyan-400" : "text-zinc-500 group-hover:text-zinc-200"
                                        )}
                                    >
                                        {item.name}
                                    </motion.span>
                                )}
                            </AnimatePresence>
                        </Link>
                    );
                })}
            </nav>

            <AnimatePresence>
                {!collapsed && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="px-6 py-8 space-y-6 relative z-10 border-t border-white/5 bg-zinc-950/20 overflow-hidden"
                    >
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
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
});

export function MobileNav() {
    const pathname = usePathname();
    
    const mobileNavItems = [
        { name: "Home", href: "/", icon: LayoutDashboard },
        { name: "Discovery", href: "/discovery", icon: Search },
        { name: "Create", href: "/creation", icon: Sparkles },
        { name: "Nexus", href: "/nexus", icon: Zap },
        { name: "Profile", href: "/settings", icon: Settings },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 h-16 bg-zinc-950 border-t border-white/5 z-50 md:hidden">
            <nav className="flex items-center justify-around h-full px-2">
                {mobileNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex flex-col items-center justify-center w-16 h-12 rounded-xl transition-all",
                                isActive ? "text-cyan-400" : "text-zinc-500"
                            )}
                        >
                            <item.icon className={cn("h-6 w-6", isActive && "neon-glow-cyan")} />
                            <span className="text-[10px] font-black uppercase tracking-wider mt-1">{item.name}</span>
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}

export function MobileHeader({ onMenuClick }: { onMenuClick?: () => void }) {
    return (
        <div className="fixed top-0 left-0 right-0 h-14 bg-zinc-950 border-b border-white/5 z-50 md:hidden flex items-center justify-between px-4">
            <button onClick={onMenuClick} className="p-2 -ml-2">
                <Menu className="h-6 w-6 text-zinc-400" />
            </button>
            <span className="text-lg font-bold text-violet-500">VF</span>
            <div className="h-8 w-8 rounded-full bg-violet-600 flex items-center justify-center">
                <span className="text-xs font-bold text-white">U</span>
            </div>
        </div>
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

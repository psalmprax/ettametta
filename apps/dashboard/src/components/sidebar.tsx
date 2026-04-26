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
    Coins,
    CheckCircle2,
    Layers,
    PlusSquare,
    Activity,
    Bell,
    User,
    ChevronRight,
    Terminal,
    Fingerprint,
    Lock
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Discovery", href: "/discovery", icon: Search },
    { name: "Creation", href: "/creation", icon: Sparkles },
    { name: "Nexus Flow", href: "/nexus", icon: Zap },
    { name: "Autonomous", href: "/autonomous", icon: Cpu },
    { name: "Transformation", href: "/transformation", icon: Video },
    { name: "Studio", href: "http://149.104.110.122.sslip.io:7203", icon: Layers },
    { name: "Audits", href: "/admin/audits", icon: CheckCircle2 },
    { name: "Publishing", href: "/publishing", icon: Share2 },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
    { name: "Empire", href: "/empire", icon: Crown },
    { name: "Credits", href: "/credits", icon: Coins },
];

interface SidebarProps {
    collapsed?: boolean;
    onToggle?: () => void;
}

export const Sidebar = memo<SidebarProps>(function Sidebar({ collapsed = false, onToggle }) {
    const pathname = usePathname();
    const { logout, user } = useAuth();

    const memoizedNavItems = useMemo(() => navItems, []);

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
                "flex flex-col h-full surface-glass text-zinc-400 relative overflow-hidden z-40 transition-all duration-300 border-r border-white/5",
                collapsed ? "w-20" : "w-72"
            )}
        >
            <div className="noise-overlay" />
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            <div className="absolute inset-0 opacity-[0.02] pointer-events-none" 
                 style={{ backgroundImage: "radial-gradient(#fff 1px, transparent 0)", backgroundSize: "40px 40px" }} />
            
            {/* Logo Section */}
            <div className={cn(
                "flex items-center py-12 transition-all",
                collapsed ? "px-4 justify-center" : "px-10"
            )}>
                <Link href="/" className="flex items-center gap-5 group">
                    <motion.div 
                        whileHover={{ scale: 1.1, rotateY: 20, rotateX: -20 }}
                        transition={{ type: "spring", stiffness: 400, damping: 10 }}
                        className="h-14 w-14 bg-cyan-400 flex items-center justify-center shadow-[0_0_40px_rgba(0,251,251,0.5)] relative cyber-border"
                    >
                        <Zap className="h-7 w-7 text-black fill-black" />
                        <div className="absolute inset-0 border-2 border-cyan-400 animate-ping opacity-20" />
                    </motion.div>
                    {!collapsed && (
                        <div className="flex flex-col">
                            <span className="text-2xl font-black text-white tracking-tighter uppercase leading-none neon-text-cyan italic">Ettametta</span>
                            <div className="flex items-center gap-2 mt-1">
                                <div className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_10px_#00fbfb]" />
                                <span className="font-data-mono text-[8px] text-zinc-500 tracking-[0.3em]">INTELLIGENCE OS_CORE</span>
                            </div>
                        </div>
                    )}
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 space-y-2 overflow-y-auto custom-scrollbar pt-6">
                {memoizedNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-4 px-6 py-5 group transition-all relative overflow-hidden cyber-border",
                                isActive 
                                    ? "bg-cyan-400/5 text-cyan-400 rim-glow-cyan shadow-[0_0_20px_rgba(0,251,251,0.05)]" 
                                    : "text-zinc-600 hover:text-zinc-200 hover:bg-white/5"
                            )}
                        >
                            <item.icon className={cn("h-5 w-5 shrink-0 transition-all duration-500", isActive ? "text-cyan-400 scale-110" : "group-hover:text-cyan-400/50 group-hover:scale-110")} />
                            {!collapsed && (
                                <span className={cn(
                                    "font-label-caps text-[10px] whitespace-nowrap transition-all",
                                    isActive ? "tracking-[0.4em] font-black" : "tracking-widest"
                                )}>
                                    {item.name}
                                </span>
                            )}
                            {isActive && !collapsed && (
                                <motion.div 
                                    layoutId="active-pill"
                                    className="absolute right-0 w-1 h-6 bg-cyan-400 shadow-[0_0_20px_#00fbfb]"
                                />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer / User Profile */}
            <div className="p-6 mt-auto border-t border-white/5">
                {!collapsed ? (
                    <motion.div 
                        initial={false}
                        whileHover={{ y: -5 }}
                        className="p-5 bg-black/60 rim-light space-y-5 relative group/profile cursor-pointer overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-cyan-400/0 group-hover/profile:bg-cyan-400/[0.02] transition-colors" />
                        <div className="flex items-center gap-4 relative z-10">
                            <div className="h-12 w-12 bg-zinc-900 border border-white/10 overflow-hidden relative group-hover/profile:border-cyan-400/50 transition-colors">
                                <img src={"https://api.dicebear.com/7.x/avataaars/svg?seed=" + (user?.username || "Felix")} alt="User" className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-cyan-400/10 opacity-0 group-hover/profile:opacity-100 transition-opacity" />
                            </div>
                            <div className="flex flex-col min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-black text-white truncate group-hover/profile:text-cyan-400 transition-colors">{user?.username || "Agent Null"}</span>
                                    <Fingerprint className="h-3 w-3 text-cyan-400/40" />
                                </div>
                                <span className="font-data-mono text-[7px] text-zinc-600 truncate mt-1">ACCESS_LEVEL: ALPHA_X</span>
                            </div>
                        </div>
                        <div className="pt-2 relative z-10">
                            <button 
                                onClick={(e) => { e.preventDefault(); logout(); }}
                                className="w-full py-3 flex items-center justify-center gap-3 font-label-caps text-[8px] text-zinc-600 hover:text-red-400 transition-all border border-white/5 hover:border-red-400/30 hover:bg-red-400/5 group/logout"
                            >
                                <Lock className="h-3 w-3 group-hover/logout:rotate-12 transition-transform" />
                                TERMINATE_UPLINK
                            </button>
                        </div>
                    </motion.div>
                ) : (
                    <button 
                        onClick={() => logout()}
                        className="w-12 h-12 flex items-center justify-center text-zinc-700 hover:text-red-400 transition-all hover:bg-red-400/5 border border-transparent hover:border-red-400/20"
                    >
                        <LogOut className="h-5 w-5" />
                    </button>
                )}
            </div>
        </motion.div>
    );
});

export function MobileNav() {
    const pathname = usePathname();
    
    const mobileNavItems = [
        { name: "Explore", href: "/discovery", Icon: Search },
        { name: "Creation", href: "/creation", Icon: PlusSquare },
        { name: "Nexus", href: "/nexus", Icon: Activity },
        { name: "Analysis", href: "/analytics", Icon: BarChart3 },
    ];

    return (
        <nav className="bg-[#050507]/95 backdrop-blur-3xl border-t border-white/5 fixed bottom-0 w-full z-50 h-24 shadow-[0_-10px_40px_rgba(0,0,0,0.8)] flex justify-around items-center px-8 pb-safe md:hidden">
            <div className="noise-overlay" />
            {mobileNavItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "flex flex-col items-center justify-center transition-all relative px-2",
                            isActive ? "text-cyan-400 scale-110" : "text-zinc-700"
                        )}
                    >
                        <item.Icon className={cn(
                            "h-7 w-7 mb-2 transition-all", 
                            isActive && "drop-shadow-[0_0_10px_rgba(0,251,251,0.5)]"
                        )} />
                        <span className="font-label-caps text-[7px] tracking-widest">{item.name}</span>
                        {isActive && (
                            <motion.div 
                                layoutId="mobile-active"
                                className="absolute -bottom-3 h-1 w-10 bg-cyan-400 shadow-[0_0_15px_#00fbfb]"
                            />
                        )}
                    </Link>
                );
            })}
        </nav>
    );
}

export function MobileHeader({ onMenuClick }: { onMenuClick?: () => void }) {
    return (
        <header className="bg-[#050507]/90 backdrop-blur-2xl border-b border-white/5 shadow-[0_10px_30px_rgba(0,0,0,0.5)] fixed top-0 z-50 flex justify-between items-center w-full px-6 h-20 md:hidden">
            <div className="noise-overlay" />
            <div className="flex items-center gap-5">
                <button 
                    onClick={onMenuClick} 
                    className="h-12 w-12 flex items-center justify-center bg-white/5 border border-white/10 hover:border-cyan-400/50 transition-all"
                >
                    <Menu className="h-6 w-6 text-cyan-400" />
                </button>
                <div className="flex flex-col">
                    <span className="text-lg font-black text-white tracking-tighter uppercase leading-none italic">Ettametta</span>
                    <span className="font-data-mono text-[7px] text-cyan-400/40 mt-1">NEURAL_OS_CORE</span>
                </div>
            </div>
            <div className="flex items-center gap-4">
                <div className="h-10 w-10 bg-white/5 border border-white/10 flex items-center justify-center hover:bg-cyan-400/5 transition-all">
                    <Bell className="h-5 w-5 text-zinc-500" />
                </div>
                <div className="h-10 w-10 border border-cyan-400/20 p-1 bg-black">
                    <img alt="User" className="w-full h-full object-cover" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"/>
                </div>
            </div>
        </header>
    );
}

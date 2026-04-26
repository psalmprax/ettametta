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
    Terminal
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
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            
            {/* Logo Section */}
            <div className={cn(
                "flex items-center py-10 transition-all",
                collapsed ? "px-4 justify-center" : "px-8"
            )}>
                <Link href="/" className="flex items-center gap-4 group">
                    <div className="h-10 w-10 bg-cyan-400 flex items-center justify-center shadow-[0_0_20px_rgba(0,251,251,0.3)] relative group-hover:scale-110 transition-transform">
                        <Zap className="h-5 w-5 text-black fill-black" />
                    </div>
                    {!collapsed && (
                        <div className="flex flex-col">
                            <span className="text-xl font-black text-white tracking-tighter uppercase leading-none neon-text-cyan">Ettametta</span>
                            <span className="font-data-mono text-[8px] text-zinc-500 mt-1">Intelligence OS v3</span>
                        </div>
                    )}
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 space-y-1 overflow-y-auto custom-scrollbar pt-4">
                {memoizedNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-4 px-4 py-3 group transition-all relative overflow-hidden",
                                isActive 
                                    ? "bg-cyan-400/5 text-cyan-400 border border-cyan-400/20" 
                                    : "text-zinc-500 hover:text-zinc-200 hover:bg-white/5 border border-transparent"
                            )}
                        >
                            <item.icon className={cn("h-5 w-5 shrink-0 transition-colors", isActive ? "text-cyan-400" : "group-hover:text-cyan-400/50")} />
                            {!collapsed && (
                                <span className="font-label-caps text-[10px] whitespace-nowrap">{item.name}</span>
                            )}
                            {isActive && !collapsed && (
                                <motion.div 
                                    layoutId="active-pill"
                                    className="absolute right-0 w-1 h-4 bg-cyan-400 shadow-[0_0_10px_#00fbfb]"
                                />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer / User Profile */}
            <div className="p-4 mt-auto border-t border-white/5">
                {!collapsed ? (
                    <div className="p-4 bg-white/5 rim-light space-y-4">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-zinc-800 border border-white/10 overflow-hidden">
                                <img src={"https://api.dicebear.com/7.x/avataaars/svg?seed=" + (user?.username || "Felix")} alt="User" className="w-full h-full object-cover" />
                            </div>
                            <div className="flex flex-col min-w-0">
                                <span className="text-xs font-bold text-white truncate">{user?.username || "Agent Null"}</span>
                                <span className="font-data-mono text-[8px] text-zinc-500 truncate">Core Access: Level 4</span>
                            </div>
                        </div>
                        <button 
                            onClick={() => logout()}
                            className="w-full py-2 flex items-center justify-center gap-2 font-label-caps text-[8px] text-zinc-500 hover:text-red-400 transition-colors border border-white/5 hover:border-red-400/20"
                        >
                            <LogOut className="h-3 w-3" />
                            Terminate Session
                        </button>
                    </div>
                ) : (
                    <button 
                        onClick={() => logout()}
                        className="w-12 h-12 flex items-center justify-center text-zinc-600 hover:text-red-400 transition-colors"
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
        { name: "Live", href: "/nexus", Icon: Activity },
        { name: "Insights", href: "/analytics", Icon: BarChart3 },
    ];

    return (
        <nav className="bg-black/90 backdrop-blur-2xl border-t border-cyan-400/20 fixed bottom-0 w-full z-50 h-20 shadow-[0_-4px_30px_rgba(0,251,251,0.1)] flex justify-around items-center px-6 pb-safe md:hidden">
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            {mobileNavItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "flex flex-col items-center justify-center transition-all relative px-4",
                            isActive ? "text-cyan-400" : "text-zinc-600"
                        )}
                    >
                        <item.Icon className={cn("h-6 w-6 mb-1 transition-all", isActive && "scale-110 shadow-[0_0_15px_rgba(0,251,251,0.5)]")} />
                        <span className="font-label-caps text-[8px]">{item.name}</span>
                        {isActive && (
                            <motion.div 
                                layoutId="mobile-active"
                                className="absolute -bottom-2 h-1 w-8 bg-cyan-400 shadow-[0_0_10px_#00fbfb]"
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
        <header className="bg-black/80 backdrop-blur-xl border-b border-white/5 shadow-[0_0_20px_rgba(0,0,0,0.5)] fixed top-0 z-50 flex justify-between items-center w-full px-5 h-16 md:hidden">
            <div className="flex items-center gap-4">
                <button 
                    onClick={onMenuClick} 
                    className="h-10 w-10 flex items-center justify-center bg-white/5 border border-white/10"
                >
                    <Menu className="h-5 w-5 text-cyan-400" />
                </button>
                <div className="flex flex-col">
                    <span className="text-sm font-black text-white tracking-tighter uppercase leading-none">Ettametta</span>
                    <span className="font-data-mono text-[8px] text-cyan-400/50 mt-0.5">Neural Core</span>
                </div>
            </div>
            <div className="flex items-center gap-3">
                <div className="h-8 w-8 bg-white/5 border border-white/10 flex items-center justify-center">
                    <Bell className="h-4 w-4 text-zinc-500" />
                </div>
                <div className="h-8 w-8 border border-cyan-400/30">
                    <img alt="User" className="w-full h-full object-cover" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"/>
                </div>
            </div>
        </header>
    );
}

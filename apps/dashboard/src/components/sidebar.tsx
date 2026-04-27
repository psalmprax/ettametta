"use client";

import React, { useState, useEffect, useMemo } from "react";
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

export const Sidebar = React.memo<SidebarProps>(function Sidebar({ collapsed = false, onToggle }) {
    const pathname = usePathname();
    const { logout, user } = useAuth();

    const memoizedNavItems = useMemo(() => navItems, []);

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
                "flex flex-col h-full bg-white border-r border-slate-200 relative z-40 transition-all duration-300",
                collapsed ? "w-20" : "w-72"
            )}
        >
            {/* Logo Section */}
            <div className={cn(
                "flex items-center py-6 transition-all",
                collapsed ? "px-4 justify-center" : "px-8"
            )}>
                <Link href="/" className="flex items-center gap-3 group">
                    <div className="h-10 w-10 bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
                        <Zap className="h-5 w-5 text-white" />
                    </div>
                    {!collapsed && (
                        <div className="flex flex-col">
                            <span className="text-lg font-bold text-slate-900 tracking-tight">Ettametta</span>
                            <span className="text-[9px] text-slate-500 font-medium uppercase tracking-wider mt-0.5">Intelligence Platform</span>
                        </div>
                    )}
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 space-y-1 overflow-y-auto pt-2">
                {memoizedNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 text-sm font-medium",
                                isActive 
                                    ? "bg-indigo-50 text-indigo-700" 
                                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                            )}
                        >
                            <item.icon className={cn("h-5 w-5 shrink-0", isActive ? "text-indigo-600" : "text-slate-400")} />
                            {!collapsed && (
                                <span className="truncate">
                                    {item.name}
                                </span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* User Profile Section */}
            <div className="p-3 mt-auto border-t border-slate-100">
                {!collapsed ? (
                    <div className="p-3 bg-slate-50 rounded-xl space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-9 w-9 rounded-full bg-white border border-slate-200 overflow-hidden flex-shrink-0">
                                <img src={"https://api.dicebear.com/7.x/avataaars/svg?seed=" + (user?.username || "Felix")} alt="User" className="w-full h-full object-cover" />
                            </div>
                            <div className="flex flex-col min-w-0">
                                <span className="text-sm font-bold text-slate-900 truncate">{user?.username || "Guest User"}</span>
                                <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Pro Plan</span>
                            </div>
                        </div>
                        <button 
                            onClick={(e) => { e.preventDefault(); logout(); }}
                            className="w-full py-2 px-3 flex items-center justify-center gap-2 text-[11px] font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg border border-slate-200 transition-all"
                        >
                            <LogOut className="h-3.5 w-3.5" />
                            Sign Out
                        </button>
                    </div>
                ) : (
                    <button 
                        onClick={() => logout()}
                        className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
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
        <nav className="bg-white/95 backdrop-blur-xl border-t border-slate-200 fixed bottom-0 w-full z-50 h-16 flex justify-around items-center px-4 md:hidden">
            {mobileNavItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "flex flex-col items-center justify-center transition-all relative px-2",
                            isActive ? "text-indigo-600 scale-110" : "text-slate-500 hover:text-slate-700"
                        )}
                    >
                        <item.Icon className={cn(
                            "h-6 w-6 mb-1 transition-all"
                        )} />
                        <span className="text-[10px] font-medium tracking-wide">{item.name}</span>
                        {isActive && (
                            <motion.div 
                                layoutId="mobile-active"
                                className="absolute -bottom-2 h-0.5 w-8 bg-indigo-600 rounded-full"
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
        <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200 fixed top-0 z-50 flex justify-between items-center w-full px-4 h-16 md:hidden">
            <div className="flex items-center gap-3">
                <button 
                    onClick={onMenuClick} 
                    className="h-10 w-10 flex items-center justify-center bg-slate-50 border border-slate-200 hover:border-slate-300 transition-all rounded-xl"
                >
                    <Menu className="h-5 w-5 text-slate-600" />
                </button>
                <div className="flex flex-col">
                    <span className="text-base font-bold text-slate-900">Ettametta</span>
                    <span className="text-[9px] text-slate-400 font-medium uppercase tracking-wider">Intelligence Platform</span>
                </div>
            </div>
            <div className="flex items-center gap-2">
                <div className="h-9 w-9 bg-slate-50 border border-slate-200 flex items-center justify-center hover:bg-slate-100 transition-all rounded-lg">
                    <Bell className="h-4 w-4 text-slate-500" />
                </div>
                <div className="h-9 w-9 border border-slate-200 p-0.5 bg-white rounded-lg overflow-hidden">
                    <img alt="User" className="w-full h-full object-cover" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"/>
                </div>
            </div>
        </header>
    );
}



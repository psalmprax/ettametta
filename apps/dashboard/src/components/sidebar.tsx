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
    Lock,
    PlaySquare,
    Music,
    Volume2,
    Brain,
    FileVideo
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
    { name: "Explore", href: "/dashboard", icon: Search },
    { name: "Discovery", href: "/discovery", icon: TrendingUp },
    { name: "Experiments", href: "/dashboard/experiments", icon: Activity },
    { name: "Intelligence", href: "/dashboard/intelligence", icon: Brain },
    { name: "My Assets", href: "/transformation", icon: Layers },
];

const creationTools = [
    { name: "AI Video Generator", href: "/creation", icon: PlaySquare, badge: "New" },
    { name: "AI Video Editor", href: "/dashboard/video-editor", icon: Video },
    { name: "Image to Video", href: "/image-to-video", icon: Video },
    { name: "Text to Video", href: "/text-to-video", icon: PlusSquare },
    { name: "AI Image", href: "/ai-image", icon: Sparkles, badge: "Nano Banana" },
    { name: "AI Image Editor", href: "/ai-image-editor", icon: Activity },
    { name: "AI Avatar", href: "/ai-avatar", icon: User },
    { name: "AI Music", href: "/ai-music", icon: Music },
    { name: "Text To Speech", href: "/tts", icon: Volume2 },
];

interface SidebarProps {
    collapsed?: boolean;
    onToggle?: () => void;
}

export const Sidebar = React.memo<SidebarProps>(function Sidebar({ collapsed = false, onToggle }) {
    const pathname = usePathname();
    const { logout, user } = useAuth();

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
                "flex flex-col h-full bg-black border-r border-white/5 relative z-40 transition-all duration-300",
                collapsed ? "w-20" : "w-64"
            )}
        >
            {/* Logo Section */}
            <div className={cn(
                "flex items-center py-6 transition-all",
                collapsed ? "px-4 justify-center" : "px-6"
            )}>
                <Link href="/" className="flex items-center gap-2 group">
                    <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20">
                        <Zap className="h-4 w-4 text-white fill-current" />
                    </div>
                    {!collapsed && (
                        <span className="text-xl font-bold text-white tracking-tight">Ettametta</span>
                    )}
                </Link>
            </div>

            {/* Create with Agent Button */}
            {!collapsed && (
                <div className="px-4 mb-6">
                    <button className="w-full py-2.5 px-4 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-600/30 text-blue-500 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all">
                        <PlusSquare className="h-4 w-4" />
                        Create with Agent
                    </button>
                </div>
            )}

            {/* Navigation */}
            <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 text-[13px] font-medium",
                                isActive 
                                    ? "bg-white/5 text-white" 
                                    : "text-slate-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <item.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-blue-500" : "text-slate-500")} />
                            {!collapsed && <span className="truncate">{item.name}</span>}
                        </Link>
                    );
                })}

                <div className="pt-6 pb-2 px-3">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Creation Tools</span>
                </div>

                {creationTools.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 text-[13px] font-medium group",
                                isActive 
                                    ? "bg-white/10 text-white" 
                                    : "text-slate-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            <item.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-blue-500" : "text-slate-500 group-hover:text-slate-300")} />
                            {!collapsed && (
                                <div className="flex items-center justify-between flex-1 min-w-0">
                                    <span className="truncate">{item.name}</span>
                                    {item.badge && (
                                        <span className={cn(
                                            "ml-2 px-1.5 py-0.5 rounded text-[9px] font-bold",
                                            item.badge === "New" ? "bg-blue-600/20 text-blue-500" : "bg-slate-800 text-slate-400"
                                        )}>
                                            {item.badge}
                                        </span>
                                    )}
                                </div>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* User Profile Section */}
            <div className="p-3 mt-auto border-t border-white/5">
                {!collapsed ? (
                    <div className="p-3 bg-white/5 rounded-xl space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-9 w-9 rounded-full bg-slate-800 border border-white/10 overflow-hidden flex-shrink-0">
                                <img src={"https://api.dicebear.com/7.x/avataaars/svg?seed=" + (user?.username || "Felix")} alt="User" className="w-full h-full object-cover" />
                            </div>
                            <div className="flex flex-col min-w-0">
                                <span className="text-sm font-bold text-white truncate">{user?.username || "Guest User"}</span>
                                <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Pro Plan</span>
                            </div>
                        </div>
                        <button 
                            onClick={(e) => { e.preventDefault(); logout(); }}
                            className="w-full py-2 px-3 flex items-center justify-center gap-2 text-[11px] font-semibold text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg border border-white/10 transition-all"
                        >
                            <LogOut className="h-3.5 w-3.5" />
                            Sign Out
                        </button>
                    </div>
                ) : (
                    <button 
                        onClick={() => logout()}
                        className="w-10 h-10 flex items-center justify-center text-slate-500 hover:text-white hover:bg-white/5 rounded-lg transition-all"
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
        { name: "Explore", href: "/dashboard", Icon: Search },
        { name: "Creation", href: "/dashboard/video-editor", Icon: PlusSquare },
        { name: "Assets", href: "/assets", Icon: Activity },
        { name: "Profile", href: "/profile", Icon: User },
    ];

    return (
        <nav className="bg-black/95 backdrop-blur-xl border-t border-white/5 fixed bottom-0 w-full z-50 h-16 flex justify-around items-center px-4 md:hidden">
            {mobileNavItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "flex flex-col items-center justify-center transition-all relative px-2",
                            isActive ? "text-blue-500 scale-110" : "text-slate-500 hover:text-slate-300"
                        )}
                    >
                        <item.Icon className={cn(
                            "h-6 w-6 mb-1 transition-all"
                        )} />
                        <span className="text-[10px] font-medium tracking-wide">{item.name}</span>
                        {isActive && (
                            <motion.div 
                                layoutId="mobile-active"
                                className="absolute -bottom-2 h-0.5 w-8 bg-blue-500 rounded-full"
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
        <header className="bg-black/80 backdrop-blur-xl border-b border-white/5 fixed top-0 z-50 flex justify-between items-center w-full px-4 h-16 md:hidden">
            <div className="flex items-center gap-3">
                <button 
                    onClick={onMenuClick} 
                    className="h-10 w-10 flex items-center justify-center bg-white/5 border border-white/10 hover:border-white/20 transition-all rounded-xl"
                >
                    <Menu className="h-5 w-5 text-slate-300" />
                </button>
                <div className="flex flex-col">
                    <span className="text-base font-bold text-white">Ettametta</span>
                    <span className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">Video Workspace</span>
                </div>
            </div>
            <div className="flex items-center gap-2">
                <div className="h-9 w-9 bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all rounded-lg">
                    <Bell className="h-4 w-4 text-slate-400" />
                </div>
                <div className="h-9 w-9 border border-white/10 p-0.5 bg-slate-900 rounded-lg overflow-hidden">
                    <img alt="User" className="w-full h-full object-cover" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"/>
                </div>
            </div>
        </header>
    );
}



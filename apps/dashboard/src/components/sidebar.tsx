"use client";

import React, {  } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    Share2,
    BarChart3,
    Zap,
    LogOut,
    Cpu,
    Menu,
    Crown,
    Layers,
    Activity,
    User,
    ShieldCheck,
    Lock,
    PlaySquare,
    Brain,
    Radar,
    Bell
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { motion } from "framer-motion";
import { useNotificationCount } from "@/hooks/useNotificationCount";

const navItems = [
    { name: "Command Center", href: "/dashboard", icon: LayoutDashboard },
    { 
        name: "Empire Registry", 
        href: "/empire", 
        icon: Crown,
        subItems: [
            { name: "Registry", href: "/empire?engine=registry" },
            { name: "Algo Sentinel", href: "/empire?engine=sentinel" },
            { name: "Promo Hub", href: "/empire?engine=monetization" },
            { name: "Commerce Matrix", href: "/empire?engine=commerce" },
            { name: "Registry Logs", href: "/empire?engine=logs" }
        ]
    },
    { 
        name: "Trend Discovery", 
        href: "/discovery", 
        icon: Radar,
        subItems: [
            { name: "Viral Trends", href: "/discovery?engine=trends" },
            { name: "Niche Intel", href: "/discovery?engine=intel" },
            { name: "Neural Alerts", href: "/discovery?engine=alerts" },
            { name: "Global Hotspots", href: "/discovery?engine=hotspots" },
            { name: "Scanner Logs", href: "/discovery?engine=logs" }
        ]
    },
    { name: "Global Publish", href: "/publishing", icon: Share2 },
    { 
        name: "Autonomous OS", 
        href: "/autonomous", 
        icon: Activity,
        subItems: [
            { name: "Launch Control", href: "/autonomous?engine=launch" },
            { name: "Logic Flow", href: "/autonomous?engine=logic" },
            { name: "Insight Oracle", href: "/autonomous?engine=oracle" },
            { name: "Market Pulse", href: "/autonomous?engine=market" },
            { name: "System Console", href: "/autonomous?engine=console" }
        ]
    },
];

const intelligenceItems = [
    { 
        name: "Nexus Engine", 
        href: "/nexus", 
        icon: Cpu,
        subItems: [
            { name: "Orchestrator", href: "/nexus?engine=orchestrator" },
            { name: "Neural IDs", href: "/nexus?engine=identities" },
            { name: "Code Sandbox", href: "/nexus?engine=sandbox" },
            { name: "Pipeline History", href: "/nexus?engine=history" },
            { name: "Command Pod", href: "/nexus?engine=command" }
        ]
    },
    { name: "Knowledge Base", href: "/knowledge", icon: Brain },
    { 
        name: "Intel Core", 
        href: "/analytics", 
        icon: BarChart3,
        subItems: [
            { name: "Intel Overview", href: "/analytics?engine=overview" },
            { name: "Attention Decay", href: "/analytics?engine=retention" },
            { name: "Neural Patterns", href: "/analytics?engine=patterns" },
            { name: "Global Pulse", href: "/analytics?engine=propagation" },
            { name: "Telemetry Logs", href: "/analytics?engine=logs" }
        ]
    },
    { name: "Security Audit", href: "/admin/audits", icon: ShieldCheck },
    { name: "Security Sentinel", href: "/security", icon: Lock },
    { name: "Agent Interface", href: "/agent", icon: Brain },
    { name: "Persona Lab", href: "/persona", icon: User },
    { name: "Notifications", href: "/settings", icon: Bell },
];

const studioItems = [
    { 
        name: "Creation Hub", 
        href: "/creation", 
        icon: PlaySquare,
        subItems: [
            { name: "Voice Forge", href: "/creation?engine=voice" },
            { name: "Script Engine", href: "/creation?engine=script" },
            { name: "Visual Core", href: "/creation?engine=visual" },
            { name: "System Logs", href: "/creation?engine=logs" }
        ]
    },
    { 
        name: "Transformation", 
        href: "/transformation", 
        icon: Layers,
        subItems: [
            { name: "Studio Control", href: "/transformation?engine=studio" },
            { name: "Mass Deployment", href: "/transformation?engine=mass" },
            { name: "Render Queue", href: "/transformation?engine=queue" },
            { name: "Neural Nodes", href: "/transformation?engine=nodes" },
            { name: "System Logs", href: "/transformation?engine=logs" }
        ]
    },
];

/** Module-internal — do not consume from outside. */
interface SidebarProps {
    collapsed?: boolean;
    onToggle?: () => void;
}

export const Sidebar = React.memo<SidebarProps>(function Sidebar({ collapsed = false, onToggle }) {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const currentEngine = searchParams?.get("engine");
    const { logout, user } = useAuth();

    const isSubActive = (subHref: string) => {
        if (subHref.includes("?")) {
            const [path, query] = subHref.split("?");
            const params = new URLSearchParams(query);
            const engineVal = params.get("engine");
            return pathname === path && currentEngine === engineVal;
        }
        return pathname === subHref;
    };

    return (
        <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
                "flex flex-col h-full bg-[#09090B] border-r border-white/5 relative z-40 transition-all duration-300",
                collapsed ? "w-20" : "w-[220px]"
            )}
        >
            {/* System Header */}
            <div className={cn(
                "flex items-center py-6 transition-all",
                collapsed ? "px-4 justify-center" : "px-6"
            )}>
                <Link href="/" className="flex items-center gap-3 group">
                    <div className="h-9 w-9 bg-cyan-500 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all group-hover:scale-105">
                        <Zap className="h-5 w-5 text-black fill-current" />
                    </div>
                    {!collapsed && (
                        <div className="flex flex-col">
                            <span className="text-sm font-black text-white tracking-widest uppercase italic">Ettametta</span>
                            <span className="text-[8px] font-bold text-cyan-500/50 tracking-[0.3em] uppercase">Intelligence OS</span>
                        </div>
                    )}
                </Link>
            </div>

            {/* Navigation Groups */}
            <nav className="flex-1 px-4 space-y-8 overflow-y-auto custom-scrollbar pt-4">
                <div className="space-y-1">
                    {!collapsed && <label className="px-4 mb-2 block text-[9px] font-black text-zinc-600 uppercase tracking-[0.3em]">Operational</label>}
                    {navItems.map((item) => {
                        const isActive = pathname.startsWith(item.href);
                        return (
                            <div key={item.href} className="space-y-1">
                                <Link
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 group relative",
                                        isActive ? "bg-white/5 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/2"
                                    )}
                                >
                                    <item.icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-cyan-400" : "text-zinc-600 group-hover:text-zinc-400")} />
                                    {!collapsed && <span className="text-xs font-bold uppercase tracking-tight">{item.name}</span>}
                                    {isActive && !item.subItems && (
                                        <motion.div layoutId="nav-active" className="absolute left-0 w-1 h-4 bg-cyan-400 rounded-full" />
                                    )}
                                </Link>
                                {!collapsed && isActive && item.subItems && (
                                    <div className="ml-9 border-l border-white/5 pl-4 py-1 space-y-1">
                                        {item.subItems.map(sub => (
                                            <Link 
                                                key={sub.href} 
                                                href={sub.href}
                                                className={cn(
                                                    "block text-[10px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                    isSubActive(sub.href) ? "text-cyan-400" : "text-zinc-600 hover:text-zinc-400"
                                                )}
                                            >
                                                {sub.name}
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="space-y-1">
                    {!collapsed && <label className="px-4 mb-2 block text-[9px] font-black text-zinc-600 uppercase tracking-[0.3em]">Intelligence</label>}
                    {intelligenceItems.map((item) => {
                        const isActive = pathname.startsWith(item.href);
                        const isNotifications = item.name === "Notifications";
                        return (
                            <div key={item.href} className="space-y-1">
                                <Link
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 group relative",
                                        isActive ? "bg-white/5 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/2"
                                    )}
                                >
                                    <item.icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-violet-400" : "text-zinc-600 group-hover:text-zinc-400")} />
                                    {!collapsed && <span className="text-xs font-bold uppercase tracking-tight">{item.name}</span>}
                                    {!collapsed && isNotifications && (
                                        <UnreadBadge />
                                    )}
                                </Link>
                                {!collapsed && isActive && item.subItems && (
                                    <div className="ml-9 border-l border-white/5 pl-4 py-1 space-y-1">
                                        {item.subItems.map(sub => (
                                            <Link 
                                                key={sub.href} 
                                                href={sub.href}
                                                className={cn(
                                                    "block text-[10px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                    isSubActive(sub.href) ? "text-violet-400" : "text-zinc-600 hover:text-zinc-400"
                                                )}
                                            >
                                                {sub.name}
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="space-y-1">
                    {!collapsed && <label className="px-4 mb-2 block text-[9px] font-black text-zinc-600 uppercase tracking-[0.3em]">Studio</label>}
                    {studioItems.map((item) => {
                        const isActive = pathname.startsWith(item.href);
                        return (
                            <div key={item.href} className="space-y-1">
                                <Link
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 group relative",
                                        isActive ? "bg-white/5 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/2"
                                    )}
                                >
                                    <item.icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-rose-500" : "text-zinc-600 group-hover:text-zinc-400")} />
                                    {!collapsed && <span className="text-xs font-bold uppercase tracking-tight">{item.name}</span>}
                                </Link>
                                {!collapsed && isActive && item.subItems && (
                                    <div className="ml-9 border-l border-white/5 pl-4 py-1 space-y-1">
                                        {item.subItems.map(sub => (
                                            <Link 
                                                key={sub.href} 
                                                href={sub.href}
                                                className={cn(
                                                    "block text-[10px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                    isSubActive(sub.href) ? "text-rose-400" : "text-zinc-600 hover:text-zinc-400"
                                                )}
                                            >
                                                {sub.name}
                                            </Link>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </nav>

            {/* Bottom Telemetry & User */}
            <div className="p-3 mt-auto border-t border-white/5 bg-black/20 space-y-3">
                {!collapsed && (
                    <div className="px-3 py-2 rounded-2xl bg-white/2 border border-white/5 space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-[8px] font-black text-zinc-600 uppercase tracking-widest">System Pulse</span>
                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]" />
                        </div>
                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div 
                                animate={{ x: [-100, 100] }}
                                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                className="h-full w-20 bg-linear-to-r from-transparent via-cyan-500 to-transparent" 
                            />
                        </div>
                    </div>
                )}
                
                <div className={cn(
                    "flex items-center gap-3 transition-all",
                    collapsed ? "justify-center" : "px-3 py-1"
                )}>
                    <div className="h-9 w-9 rounded-xl bg-zinc-900 border border-white/10 overflow-hidden shrink-0">
                        <img src={"https://api.dicebear.com/7.x/avataaars/svg?seed=" + (user?.username || "Felix")} alt="User" className="w-full h-full object-cover" />
                    </div>
                    {!collapsed && (
                        <div className="flex flex-col min-w-0 flex-1">
                            <span className="text-xs font-bold text-white truncate uppercase tracking-tighter">{user?.username || "OPERATIVE_01"}</span>
                            <span className="text-[8px] text-zinc-500 font-black uppercase tracking-[0.2em]">Tier: Elite</span>
                        </div>
                    )}
                    {!collapsed && (
                        <button onClick={logout} className="text-zinc-600 hover:text-rose-500 transition-colors">
                            <LogOut className="h-4 w-4" />
                        </button>
                    )}
                </div>
            </div>
        </motion.div>
    );
});

function UnreadBadge() {
    const unreadCount = useNotificationCount();
    if (unreadCount === 0) return null;
    return (
        <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-amber-500/20 px-1.5 text-[9px] font-black text-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.3)]">
            {unreadCount > 99 ? "99+" : unreadCount}
        </span>
    );
}

export function MobileNav() {
    const pathname = usePathname();
    const mobileNavItems = [
        { name: "Explore", href: "/discovery", Icon: Radar },
        { name: "Creation", href: "/creation", Icon: PlaySquare },
        { name: "Nexus", href: "/nexus", Icon: Cpu },
        { name: "Stats", href: "/analytics", Icon: BarChart3 },
    ];

    return (
        <nav className="bg-black/95 backdrop-blur-3xl border-t border-white/5 fixed bottom-0 w-full z-50 h-20 flex justify-around items-center px-4 md:hidden">
            {mobileNavItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                            "flex flex-col items-center justify-center transition-all relative px-2",
                            isActive ? "text-cyan-400 scale-110" : "text-zinc-600 hover:text-zinc-400"
                        )}
                    >
                        <item.Icon className="h-6 w-6 mb-1" />
                        <span className="text-[8px] font-black uppercase tracking-widest">{item.name}</span>
                        {isActive && (
                            <motion.div layoutId="mobile-active" className="absolute -bottom-2 h-0.5 w-8 bg-cyan-400 rounded-full" />
                        )}
                    </Link>
                );
            })}
        </nav>
    );
}

export function MobileHeader({ onMenuClick }: { readonly onMenuClick?: () => void }) {
    return (
        <header className="bg-black/80 backdrop-blur-2xl border-b border-white/5 fixed top-0 z-50 flex justify-between items-center w-full px-4 h-20 md:hidden">
            <div className="flex items-center gap-4">
                <button 
                    onClick={onMenuClick} 
                    className="h-12 w-12 flex items-center justify-center bg-white/2 border border-white/10 rounded-2xl"
                >
                    <Menu className="h-6 w-6 text-zinc-300" />
                </button>
                <div className="flex flex-col">
                    <span className="text-sm font-black text-white uppercase tracking-widest italic">Ettametta</span>
                    <span className="text-[8px] font-bold text-cyan-500/50 uppercase tracking-[0.3em]">Intelligence OS</span>
                </div>
            </div>
            <div className="h-10 w-10 bg-zinc-900 border border-white/10 rounded-xl overflow-hidden p-0.5">
                <img alt="User" className="w-full h-full object-cover" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"/>
            </div>
        </header>
    );
}

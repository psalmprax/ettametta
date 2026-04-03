"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, MobileNav, MobileHeader } from "@/components/sidebar";
import { SearchBar } from "@/components/search-bar";
import { useUITheme } from "@/context/UIThemeContext";

import { motion, AnimatePresence } from "framer-motion";
import { Coins, Sun, Moon, HelpCircle, Bell } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

function LegacyLayout({ children }: { children: React.ReactNode }) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [credits] = useState(250);

    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    if (isMobile) {
        return (
            <div className="flex h-screen bg-black text-white relative overflow-hidden elite-mesh">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(var(--primary-rgb),0.08),transparent_50%)] pointer-events-none" />
                <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                <div className="absolute inset-0 elite-grain-overlay z-50 pointer-events-none" />

                <MobileHeader onMenuClick={() => setMobileMenuOpen(true)} />

                <main className="flex-1 overflow-y-auto bg-transparent pt-14 pb-20 px-4 relative z-10 custom-scrollbar">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], opacity: { duration: 0.8 } }}
                        className="max-w-7xl mx-auto w-full"
                    >
                        {children}
                    </motion.div>
                </main>

                <MobileNav />

                <AnimatePresence>
                    {mobileMenuOpen && (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="fixed inset-0 bg-black/80 z-40 md:hidden"
                                onClick={() => setMobileMenuOpen(false)}
                            />
                            <motion.div
                                initial={{ x: "-100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "-100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                className="fixed top-0 left-0 bottom-0 w-72 bg-zinc-950 z-50 md:hidden"
                            >
                                <Sidebar collapsed={false} onToggle={() => setMobileMenuOpen(false)} />
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-black text-white relative overflow-hidden elite-mesh">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(var(--primary-rgb),0.08),transparent_50%)] pointer-events-none" />
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            <div className="absolute inset-0 elite-grain-overlay z-50 pointer-events-none" />

            <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

            <div className="hidden md:flex flex-col flex-1">
                <header className="h-16 border-b border-white/5 bg-zinc-950/50 flex items-center justify-between px-6">
                    <SearchBar />
                    <div className="flex items-center gap-4">
                        <Link href="/credits" className="flex items-center gap-2 px-3 py-1.5 bg-violet-500/10 border border-violet-500/20 rounded-lg hover:bg-violet-500/20 transition-colors">
                            <Coins className="h-4 w-4 text-violet-400" />
                            <span className="text-sm font-medium text-violet-300">{credits} credits</span>
                        </Link>
                        <div className="h-8 w-8 rounded-full bg-violet-600 flex items-center justify-center">
                            <span className="text-xs font-bold text-white">U</span>
                        </div>
                    </div>
                </header>

                <main className={cn(
                    "flex-1 overflow-y-auto bg-transparent py-8 px-14 relative z-10 custom-scrollbar",
                    sidebarCollapsed && "px-8 transition-all duration-300"
                )}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], opacity: { duration: 0.8 } }}
                        className="max-w-7xl mx-auto w-full"
                    >
                        {children}
                    </motion.div>
                </main>
            </div>
        </div>
    );
}

function ModernLayout({ children }: { children: React.ReactNode }) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [credits] = useState(250);
    const { toggleTheme } = useUITheme();

    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    const navItems = [
        { icon: "📊", active: true },
        { icon: "🔍", active: false },
        { icon: "✨", active: false },
        { icon: "⚡", active: false },
        { icon: "🤖", active: false },
        { icon: "🎬", active: false },
        { icon: "📤", active: false },
        { icon: "📈", active: false },
        { icon: "👑", active: false },
        { icon: "💰", active: false },
    ];

    if (isMobile) {
        return (
            <div className="flex h-screen bg-zinc-950 text-white">
                <MobileHeader onMenuClick={() => setMobileMenuOpen(true)} />
                <main className="flex-1 overflow-y-auto pt-14 pb-20 px-4">
                    {children}
                </main>
                <MobileNav />
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-zinc-950 text-white">
            {/* Sidebar */}
            <aside className={cn(
                "flex flex-col bg-zinc-950 border-r border-zinc-800 transition-all duration-300",
                sidebarCollapsed ? "w-16" : "w-64"
            )}>
                {/* Toggle */}
                <button
                    onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                    className="h-12 flex items-center justify-center hover:bg-zinc-900 transition-colors"
                >
                    <span className="text-zinc-500">{sidebarCollapsed ? "→" : "←"}</span>
                </button>

                {/* Nav Icons */}
                <nav className="flex-1 py-2">
                    {navItems.map((item, idx) => (
                        <button
                            key={idx}
                            className={cn(
                                "w-full h-12 flex items-center justify-center transition-colors",
                                item.active ? "bg-violet-600" : "hover:bg-zinc-900"
                            )}
                        >
                            <span className="text-lg">{item.icon}</span>
                        </button>
                    ))}
                </nav>

                {/* Settings */}
                <button className="h-12 flex items-center justify-center hover:bg-zinc-900 transition-colors">
                    <span className="text-lg">⚙️</span>
                </button>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <header className="h-14 border-b border-zinc-800 bg-zinc-950 flex items-center justify-between px-6">
                    {/* Search */}
                    <div className="w-96 h-9 bg-zinc-900 rounded-lg flex items-center px-3 gap-2">
                        <span className="text-zinc-500">🔍</span>
                        <span className="text-zinc-500 text-sm">Search (⌘K)</span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3">
                        <button className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center">
                            <HelpCircle className="w-4 h-4 text-zinc-400" />
                        </button>

                        <button
                            onClick={toggleTheme}
                            className="w-16 h-7 bg-zinc-900 rounded-lg flex items-center justify-center gap-2"
                        >
                            <Sun className="w-3 h-3 text-zinc-500" />
                            <Moon className="w-3 h-3 text-zinc-400" />
                        </button>

                        <button className="h-7 px-3 bg-indigo-950 border border-indigo-500/30 rounded-lg flex items-center gap-2">
                            <Coins className="w-3 h-3 text-indigo-400" />
                            <span className="text-xs font-semibold text-indigo-400">{credits} cr</span>
                        </button>

                        <button className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center relative">
                            <Bell className="w-4 h-4 text-zinc-400" />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                        </button>

                        <div className="w-8 h-8 rounded-full bg-violet-600 flex items-center justify-center">
                            <span className="text-xs font-bold">U</span>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { theme } = useUITheme();

    return theme === "modern" ? (
        <ModernLayout>{children}</ModernLayout>
    ) : (
        <LegacyLayout>{children}</LegacyLayout>
    );
}

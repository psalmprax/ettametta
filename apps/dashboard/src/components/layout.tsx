"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, MobileNav, MobileHeader } from "@/components/sidebar";
import { SearchBar } from "@/components/search-bar";
import { NotificationCenter } from "@/components/NotificationCenter";
import { useAuth } from "@/context/AuthContext";

import { motion, AnimatePresence } from "framer-motion";
import { Coins, User } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

function LegacyLayout({ children }: { children: React.ReactNode }) {
    const { user, credits } = useAuth();
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);

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
                        <NotificationCenter />
                        <Link href="/credits" className="flex items-center gap-2 px-3 py-1.5 bg-violet-500/10 border border-violet-500/20 rounded-lg hover:bg-violet-500/20 transition-colors">
                            <Coins className="h-4 w-4 text-violet-400" />
                            <span className="text-sm font-black text-violet-300 tabular-nums">{credits?.toLocaleString()} credits</span>
                        </Link>
                        <Link href="/settings" className="flex items-center gap-3 group">
                            <div className="text-right hidden sm:block">
                                <p className="text-[10px] font-black text-white uppercase tracking-tighter leading-none">{user?.role || "USER"}</p>
                                <p className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest">{user?.subscription || "Free"}</p>
                            </div>
                            <div className="h-9 w-9 rounded-xl bg-linear-to-br from-violet-600 to-indigo-600 flex items-center justify-center border border-white/10 shadow-lg group-hover:scale-105 transition-transform">
                                <span className="text-sm font-black text-white">{user?.telegram_chat_id ? "A" : "U"}</span>
                            </div>
                        </Link>
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

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    // Modern layout is incomplete; forcing legacy for stability.
    return <LegacyLayout>{children}</LegacyLayout>;
}

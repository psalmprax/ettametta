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
import { Activity, Shield } from "lucide-react";
import { Card } from "@/components/ui/Card";

function IntelligenceHUD() {
    return (
        <div className="hidden xl:flex items-center gap-8 py-4 border-b border-slate-200">
            <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-medium text-slate-500">System Status</span>
                <span className="text-emerald-600 font-semibold text-sm">Operational</span>
            </div>
            <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-slate-400" />
                <span className="text-xs font-medium text-slate-500">Encryption</span>
                <span className="text-slate-600 text-sm">AES-256</span>
            </div>
            <div className="flex items-center gap-3">
                <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: "65%" }}
                        transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
                        className="h-full bg-indigo-500 rounded-full"
                    />
                </div>
                <span className="text-xs font-medium text-slate-500">Load</span>
            </div>
        </div>
    );
}

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
            <div className="flex h-screen bg-slate-50 text-slate-900 relative overflow-hidden">
                <MobileHeader onMenuClick={() => setMobileMenuOpen(true)} />

                <main className="flex-1 overflow-y-auto pt-16 pb-20 px-4 relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                        className="max-w-7xl mx-auto w-full"
                    >
                        <IntelligenceHUD />
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
                                className="fixed inset-0 bg-slate-900/60 z-40 md:hidden"
                                onClick={() => setMobileMenuOpen(false)}
                            />
                            <motion.div
                                initial={{ x: "-100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "-100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                className="fixed top-0 left-0 bottom-0 w-72 bg-white z-50 md:hidden border-r border-slate-200 shadow-xl"
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
        <div className="flex h-screen bg-slate-50 text-slate-900">
            <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

            <div className="hidden md:flex flex-col flex-1">
                <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur-sm flex items-center justify-between px-6">
                    <SearchBar />
                    <div className="flex items-center gap-3">
                        <NotificationCenter />
                        <Link href="/credits" className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 border border-indigo-100 rounded-xl hover:bg-indigo-100 hover:border-indigo-200 transition-colors">
                            <Coins className="h-4 w-4 text-indigo-600" />
                            <span className="text-sm font-semibold text-indigo-700">{credits?.toLocaleString() || 0} credits</span>
                        </Link>
                        <Link href="/settings" className="flex items-center gap-3 group">
                            <div className="hidden sm:block text-right">
                                <p className="text-xs font-bold text-slate-900">{user?.role || "User"}</p>
                                <p className="text-[10px] text-slate-500">{user?.subscription || "Free"}</p>
                            </div>
                            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center border border-indigo-500/30 shadow-lg group-hover:scale-105 transition-transform">
                                <span className="text-sm font-bold text-white">{user?.telegram_chat_id ? user.username?.[0]?.toUpperCase() : "U"}</span>
                            </div>
                        </Link>
                    </div>
                </header>

                <main className={cn(
                    "flex-1 overflow-y-auto bg-transparent py-10 px-14 relative z-10",
                    sidebarCollapsed && "px-10 transition-all duration-300"
                )}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                        className="max-w-7xl mx-auto w-full"
                    >
                        <IntelligenceHUD />
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
    return <LegacyLayout>{children}</LegacyLayout>;
}

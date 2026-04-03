"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, MobileNav, MobileHeader } from "@/components/sidebar";
import { SearchBar } from "@/components/search-bar";

import { motion, AnimatePresence } from "framer-motion";
import { Coins } from "lucide-react";
import Link from "next/link";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const [credits] = useState(250); // TODO: Fetch from API

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768);
        };
        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    const toggleSidebar = () => setSidebarCollapsed(!sidebarCollapsed);

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
                        transition={{
                            duration: 1.2,
                            ease: [0.16, 1, 0.3, 1],
                            opacity: { duration: 0.8 }
                        }}
                        className="max-w-7xl mx-auto w-full"
                    >
                        {children}
                    </motion.div>
                </main>

                <MobileNav />

                {/* Mobile Menu Overlay */}
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
                                <Sidebar 
                                    collapsed={false} 
                                    onToggle={() => setMobileMenuOpen(false)} 
                                />
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-black text-white relative overflow-hidden elite-mesh">
            {/* Elite Background Atmosphere */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(var(--primary-rgb),0.08),transparent_50%)] pointer-events-none" />
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

            {/* Persistent Texture Overlay (Elite Grain) */}
            <div className="absolute inset-0 elite-grain-overlay z-50 pointer-events-none" />

            <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />

            {/* Desktop Header Bar */}
            <div className="hidden md:flex flex-col flex-1">
                <header className="h-16 border-b border-white/5 bg-zinc-950/50 flex items-center justify-between px-6">
                    <SearchBar />
                    
                    <div className="flex items-center gap-4">
                        <Link 
                            href="/credits" 
                            className="flex items-center gap-2 px-3 py-1.5 bg-violet-500/10 border border-violet-500/20 rounded-lg hover:bg-violet-500/20 transition-colors"
                        >
                            <Coins className="h-4 w-4 text-violet-400" />
                            <span className="text-sm font-medium text-violet-300">{credits} credits</span>
                        </Link>
                        
                        <div className="h-8 w-8 rounded-full bg-violet-600 flex items-center justify-center">
                            <span className="text-xs font-bold text-white">U</span>
                        </div>
                    </div>
                </header>

                <main className={sidebarCollapsed ? "flex-1 overflow-y-auto bg-transparent py-8 px-8 relative z-10 custom-scrollbar transition-all duration-300" : "flex-1 overflow-y-auto bg-transparent py-8 px-14 relative z-10 custom-scrollbar"}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{
                            duration: 1.2,
                            ease: [0.16, 1, 0.3, 1],
                            opacity: { duration: 0.8 }
                        }}
                        className="max-w-7xl mx-auto w-full"
                    >
                        {children}
                    </motion.div>
                </main>
            </div>
        </div>
    );
}

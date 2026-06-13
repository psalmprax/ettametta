"use client";

import React, { useState, useEffect, Suspense } from "react";
import { Sidebar, MobileNav, MobileHeader } from "@/components/sidebar";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { 
    Globe, 
    Coins, 
    MessageSquare
} from "lucide-react";

function LegacyLayout({ children }: { readonly children: React.ReactNode }) {
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
            <div className="flex h-screen bg-black text-white relative overflow-hidden">
                <MobileHeader onMenuClick={() => setMobileMenuOpen(true)} />

                <main className="flex-1 overflow-y-auto pt-16 pb-20 px-4 relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4 }}
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
                                className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 md:hidden"
                                onClick={() => setMobileMenuOpen(false)}
                            />
                            <motion.div
                                initial={{ x: "-100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "-100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                className="fixed top-0 left-0 bottom-0 w-64 bg-black z-50 md:hidden border-r border-white/5 shadow-2xl"
                            >
                                <Suspense fallback={null}>
                                    <Sidebar collapsed={false} onToggle={() => setMobileMenuOpen(false)} />
                                </Suspense>
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-black text-white font-sans">
            <Suspense fallback={null}>
                <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
            </Suspense>

            <div className="flex flex-col flex-1 relative">
                <header className="h-16 border-b border-white/5 bg-black/50 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-30">
                    <div className="flex-1" />
                    
                    <div className="flex items-center gap-6">
                        <button className="text-slate-400 hover:text-white transition-colors">
                            <Globe className="h-5 w-5" />
                        </button>

                        <div className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-white/10 rounded-full">
                            <Coins className="h-4 w-4 text-blue-500 fill-current" />
                            <span className="text-xs font-bold text-blue-500">{credits || 20}</span>
                            <div className="w-px h-3 bg-white/10 mx-1" />
                            <span className="text-[10px] font-bold text-white uppercase tracking-wider">Free Trial</span>
                        </div>

                        <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center border border-white/20 shadow-lg shadow-blue-900/20 cursor-pointer">
                            <span className="text-xs font-bold text-white">{user?.username?.[0]?.toUpperCase() || "S"}</span>
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto bg-black p-8 relative">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.5 }}
                        className="max-w-[1600px] mx-auto w-full h-full"
                    >
                        {children}
                    </motion.div>
                    
                    {/* Chat Bubble */}
                    <button className="fixed bottom-6 right-6 h-12 w-12 bg-blue-500 rounded-full flex items-center justify-center shadow-lg shadow-blue-500/20 hover:scale-110 transition-all z-40">
                        <MessageSquare className="h-6 w-6 text-white" />
                    </button>
                </main>
            </div>
        </div>
    );
}

export default function DashboardLayout({
    children,
}: {
    readonly children: React.ReactNode;
}) {
    return <LegacyLayout>{children}</LegacyLayout>;
}

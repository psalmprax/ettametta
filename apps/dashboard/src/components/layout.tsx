import React from "react";
import { Sidebar } from "@/components/sidebar";

import { motion, AnimatePresence } from "framer-motion";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen bg-black text-white relative overflow-hidden elite-mesh">
            {/* Elite Background Atmosphere */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(var(--primary-rgb),0.08),transparent_50%)] pointer-events-none" />
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

            {/* Persistent Texture Overlay (Elite Grain) */}
            <div className="absolute inset-0 elite-grain-overlay z-50" />

            <Sidebar />

            <main className="flex-1 overflow-y-auto bg-transparent py-12 px-14 relative z-10 custom-scrollbar">
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
    );
}

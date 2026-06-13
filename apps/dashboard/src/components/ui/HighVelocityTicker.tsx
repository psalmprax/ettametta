"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Globe, Activity } from "lucide-react";

interface TickerEvent {
    id: string;
    text: string;
    type: "info" | "success" | "warning" | "alert";
    timestamp: string;
}

export function HighVelocityTicker() {
    const [events, setEvents] = useState<TickerEvent[]>([
        { id: "1", text: "NEURAL_CORE_INITIALIZED", type: "success", timestamp: "0.001s" },
        { id: "2", text: "TRAFFIC_BURST_DETECTED: US-EAST-1", type: "info", timestamp: "0.042s" },
        { id: "3", text: "VIRAL_PATTERN_INJECTED: 0x4F92", type: "alert", timestamp: "0.120s" },
    ]);

    useEffect(() => {
        const timer = setInterval(() => {
            const types: ("info" | "success" | "warning" | "alert")[] = ["info", "success", "warning", "alert"];
            const msgs = [
                "SYST_CALL: RENDER_CLUSTER_ACTIVE",
                "EGRESS_OPTIMIZED: TIKTOK_ALGO_V4",
                "INGESTION_STABILIZED: [REDACTED]",
                "THREAT_NEUTRALIZED: DUPLICATE_SIG",
                "CACHE_FLUSH: PERSISTENT_MEMORY",
                "NODE_UPGRADE: [ELITE_LEVEL_3]"
            ];
            
            const newEvent: TickerEvent = {
                id: Math.random().toString(36).substr(2, 9),
                text: msgs[Math.floor(Math.random() * msgs.length)],
                type: types[Math.floor(Math.random() * types.length)],
                timestamp: `${(Math.random() * 0.5).toFixed(3)}s`
            };

            setEvents(prev => [newEvent, ...prev.slice(0, 10)]);
        }, 3000);

        return () => clearInterval(timer);
    }, []);

    return (
        <div className="h-10 bg-zinc-950 border-y border-white/5 flex items-center overflow-hidden relative z-50">
            <div className="flex items-center gap-4 px-6 bg-primary text-black font-bold text-[9px] uppercase tracking-widest h-full shrink-0 relative z-10">
                <Activity className="h-3 w-3" />
                Live Velocity
            </div>
            
            <div className="flex-1 flex items-center gap-10 whitespace-nowrap overflow-hidden relative">
                <AnimatePresence initial={false}>
                    {events.map((event, idx) => (
                        <motion.div
                            key={event.id}
                            initial={{ x: 100, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: -100, opacity: 0 }}
                            className="flex items-center gap-3"
                        >
                            <span className={cn(
                                "h-1 w-1 rounded-full",
                                event.type === "success" ? "bg-emerald-500 shadow-[0_0_5px_#10b981]" :
                                event.type === "alert" ? "bg-rose-500 shadow-[0_0_5px_#f43f5e]" :
                                event.type === "warning" ? "bg-amber-500 shadow-[0_0_5px_#f59e0b]" :
                                "bg-cyan-500 shadow-[0_0_5px_#06b6d4]"
                            )} />
                            <span className="text-[9px] font-bold text-zinc-500 uppercase font-mono">[{event.timestamp}]</span>
                            <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-tighter">{event.text}</span>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            <div className="px-6 border-l border-white/5 flex items-center gap-4 text-[9px] font-bold text-zinc-600 uppercase tracking-widest bg-zinc-950 h-full relative z-10">
                <Globe className="h-3 w-3" />
                Edge_Global
            </div>
        </div>
    );
}

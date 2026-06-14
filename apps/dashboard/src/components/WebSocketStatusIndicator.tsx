"use client";

import React, { useMemo } from "react";
import { cn } from "@/lib/utils";
import { WifiOff, Loader2, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export type WsConnectionStatus = "connecting" | "open" | "closed";

export interface WsConnectionState {
    /** Display name shown in the indicator (e.g. "Telemetry", "Discovery") */
    name: string;
    /** Current connection status */
    status: WsConnectionStatus;
    /** How many reconnection attempts have been made (0 when connected) */
    reconnectAttempts?: number;
}

interface WebSocketStatusIndicatorProps {
    /** List of WebSocket connections to monitor */
    readonly connections: WsConnectionState[];
    /** Optional className for positioning/sizing */
    readonly className?: string;
}

/**
 * Compact visual indicator showing the health of one or more WebSocket
 * connections. Each connection renders as a small pill with:
 * - Green pulsing dot + "LIVE" when open
 * - Amber spinning loader + attempt count when reconnecting
 * - Red broken icon + "DEAD" when closed
 *
 * Used in the CommandCenterLayout header to give users instant visibility
 * into both the telemetry and discovery WebSocket connections.
 */
export function WebSocketStatusIndicator({
    connections,
    className,
}: WebSocketStatusIndicatorProps) {
    const overallStatus = useMemo<WsConnectionStatus | "mixed">(() => {
        if (connections.length === 0) return "closed";
        const allOpen = connections.every((c) => c.status === "open");
        const allConnecting = connections.every((c) => c.status === "connecting");
        const allClosed = connections.every((c) => c.status === "closed");
        if (allOpen) return "open";
        if (allConnecting) return "connecting";
        if (allClosed) return "closed";
        return "mixed";
    }, [connections]);

    if (connections.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-colors",
                overallStatus === "open"
                    ? "bg-emerald-500/5 border-emerald-500/20"
                    : overallStatus === "connecting"
                      ? "bg-amber-500/5 border-amber-500/20"
                      : "bg-rose-500/5 border-rose-500/20",
                className,
            )}
        >
            {/* Aggregate status icon — hidden in mixed states; per-connection pills speak for themselves */}
            {overallStatus !== "mixed" && (
            <AnimatePresence mode="wait">
                {overallStatus === "open" ? (
                    <motion.div
                        key="open"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="flex items-center gap-1"
                    >
                        <div className="relative">
                            <Zap className="h-3 w-3 text-emerald-400" />
                            <motion.div
                                className="absolute inset-0 rounded-full bg-emerald-400/30"
                                animate={{ scale: [1, 1.8, 1], opacity: [0.6, 0, 0.6] }}
                                transition={{ duration: 2, repeat: Infinity }}
                            />
                        </div>
                    </motion.div>
                ) : overallStatus === "connecting" ? (
                    <motion.div
                        key="connecting"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                    >
                        <Loader2 className="h-3 w-3 text-amber-400 animate-spin" />
                    </motion.div>
                ) : (
                    <motion.div
                        key="closed"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                    >
                        <WifiOff className="h-3 w-3 text-rose-400" />
                    </motion.div>
                )}
            </AnimatePresence>
            )}

            {/* Per-connection pills */}
            {connections.map((conn) => (
                <div
                    key={conn.name}
                    className={cn(
                        "flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider transition-all",
                        conn.status === "open"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : conn.status === "connecting"
                              ? "bg-amber-500/10 text-amber-400"
                              : "bg-rose-500/10 text-rose-400",
                    )}
                >
                    {conn.status === "open" ? (
                        <motion.div
                            className="h-1.5 w-1.5 rounded-full bg-emerald-400"
                            animate={{ opacity: [1, 0.4, 1] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                        />
                    ) : conn.status === "connecting" ? (
                        <Loader2 className="h-2 w-2 animate-spin" />
                    ) : (
                        <div className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                    )}
                    <span>{conn.name}</span>
                    {conn.status === "connecting" &&
                        conn.reconnectAttempts !== undefined &&
                        conn.reconnectAttempts > 0 && (
                            <span className="text-[8px] opacity-70">
                                ({conn.reconnectAttempts})
                            </span>
                        )}
                </div>
            ))}
        </motion.div>
    );
}

"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";

interface ErrorNodeProps {
    message?: string;
    onRetry?: () => void;
}

export function ErrorNode({ message = "Neural Link Interrupted", onRetry }: ErrorNodeProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center p-12 glass-card border-red-500/20 text-center space-y-6"
        >
            <div className="relative">
                <AlertTriangle className="h-16 w-16 text-red-500/50" />
                <div className="absolute -inset-4 bg-red-500/10 blur-2xl rounded-full" />
            </div>
            <div className="space-y-2">
                <h3 className="text-xl font-black text-white uppercase tracking-tighter">Signal Failure</h3>
                <p className="text-zinc-400 text-sm max-w-xs">{message}</p>
            </div>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-black uppercase tracking-widest text-zinc-300 transition-all border border-white/5"
                >
                    <RefreshCw className="h-4 w-4" />
                    Re-establish Link
                </button>
            )}
        </motion.div>
    );
}

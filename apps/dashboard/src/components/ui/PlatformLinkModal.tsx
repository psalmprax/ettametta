"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Youtube, Video, Instagram, Twitter, Linkedin, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";

interface PlatformLinkModalProps {
    readonly isOpen: boolean;
    readonly onClose: () => void;
}

const PLATFORMS = [
    { id: "youtube", name: "YouTube", icon: Youtube, color: "hover:bg-red-500/20 hover:border-red-500/40 text-red-500" },
    { id: "tiktok", name: "TikTok", icon: Video, color: "hover:bg-cyan-500/20 hover:border-cyan-500/40 text-cyan-500" },
    { id: "instagram", name: "Instagram", icon: Instagram, color: "hover:bg-pink-500/20 hover:border-pink-500/40 text-pink-500" },
    { id: "x", name: "X (Twitter)", icon: Twitter, color: "hover:bg-blue-500/20 hover:border-blue-500/40 text-blue-500" },
    { id: "linkedin", name: "LinkedIn", icon: Linkedin, color: "hover:bg-blue-700/20 hover:border-blue-700/40 text-blue-700" }
];

export const PlatformLinkModal: React.FC<PlatformLinkModalProps> = ({ isOpen, onClose }) => {
    const handleLink = async (platformId: string) => {
        const token = getAuthToken();
        if (!token) return;

        await withRealFallback<{ url: string }>((signal) => fetch(`${API_BASE}/publish/auth/${platformId}`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: { url: "" },
                onSuccess: (data) => {
                    if (data && data.url) {
                        window.location.href = data.url;
                    } else {
                        toast.error("Auth Error", { description: "Platform auth URL not returned." });
                    }
                },
                onFallback: (err: any) => {
                    toast.error("Handshake Failed", { description: err.message });
                }
            }
        );
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center p-6"
                >
                    <div className="absolute inset-0 bg-black/80 backdrop-blur-xl" onClick={onClose} />

                    <motion.div
                        initial={{ scale: 0.95, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.95, opacity: 0, y: 20 }}
                        className="relative w-full max-w-2xl glass-card p-10 space-y-10 overflow-hidden"
                    >
                        <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="h-1 w-8 bg-primary rounded-full" />
                                <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary">Node Expansion</span>
                            </div>
                            <h3 className="text-3xl font-bold uppercase tracking-tighter text-white">Link New Egress Node</h3>
                            <p className="text-zinc-500 font-medium leading-relaxed">Connect your social accounts to enable <span className="text-primary font-bold">Autonomous Multi-Platform Distribution</span>.</p>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                            {PLATFORMS.map((platform) => (
                                <button
                                    key={platform.id}
                                    onClick={() => handleLink(platform.id)}
                                    className={cn(
                                        "group flex flex-col items-center justify-center p-8 rounded-3xl border border-white/5 bg-zinc-900/50 transition-all space-y-4 hover:scale-[1.05] active:scale-[0.95]",
                                        platform.color
                                    )}
                                >
                                    <platform.icon className="h-10 w-10 transition-transform group-hover:scale-110" />
                                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 group-hover:text-white transition-colors">
                                        {platform.name}
                                    </span>
                                </button>
                            ))}
                            <button className="flex flex-col items-center justify-center p-8 rounded-3xl border border-dashed border-white/10 bg-transparent text-zinc-600 space-y-4 opacity-50 cursor-not-allowed">
                                <Share2 className="h-10 w-10" />
                                <span className="text-[10px] font-bold uppercase tracking-widest">More Soon</span>
                            </button>
                        </div>

                        <button
                            onClick={onClose}
                            className="absolute top-8 right-8 p-3 rounded-2xl bg-white/5 border border-white/10 text-zinc-500 hover:text-white transition-all"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

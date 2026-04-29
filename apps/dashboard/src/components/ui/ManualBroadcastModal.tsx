"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Video, Tag, Globe, Shield, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";

interface ManualBroadcastModalProps {
    isOpen: boolean;
    onClose: () => void;
    accounts: any[];
    onSuccess: () => void;
}

export const ManualBroadcastModal: React.FC<ManualBroadcastModalProps> = ({ 
    isOpen, 
    onClose, 
    accounts,
    onSuccess 
}) => {
    const [videoPath, setVideoPath] = useState("");
    const [selectedAccount, setSelectedAccount] = useState("");
    const [niche, setNiche] = useState("Motivation");
    const [injectMonetization, setInjectMonetization] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleDeploy = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!videoPath || !selectedAccount) {
            toast.error("Validation Error", { description: "Please provide video path and select an account." });
            return;
        }

        const account = accounts.find(a => a.id === selectedAccount);
        if (!account) return;

        const token = getAuthToken();
        if (!token) return;

        setIsSubmitting(true);
        await withRealFallback(
            () => fetch(`${API_BASE}/publish/post`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    video_path: videoPath,
                    platform: account.platform,
                    niche: niche,
                    account_id: selectedAccount,
                    inject_monetization: injectMonetization
                })
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Broadcast Dispatched", { description: "Video is being uploaded to the node." });
                    onSuccess();
                    onClose();
                },
                onFallback: (err: any) => {
                    toast.error("Deployment Failed", { description: err.message });
                }
            }
        );
        setIsSubmitting(false);
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
                        className="relative w-full max-w-xl glass-card p-10 space-y-10 overflow-hidden"
                    >
                        <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="h-1 w-8 bg-primary rounded-full" />
                                <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary">Tactical Egress</span>
                            </div>
                            <h3 className="text-3xl font-bold uppercase tracking-tighter text-white">Manual Broadcast</h3>
                            <p className="text-zinc-500 font-medium leading-relaxed">Force dispatch a neural asset to the <span className="text-primary font-bold">Global Distribution Network</span>.</p>
                        </div>

                        <form onSubmit={handleDeploy} className="space-y-6">
                            <div className="space-y-4">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                    <Video className="h-3 w-3" /> Source Video Path
                                </label>
                                <input
                                    type="text"
                                    placeholder="/outputs/final_video.mp4"
                                    value={videoPath}
                                    onChange={(e) => setVideoPath(e.target.value)}
                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-2xl py-5 px-6 text-white font-bold placeholder:text-zinc-800 focus:ring-2 focus:ring-primary/40 focus:outline-none transition-all"
                                />
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                    <Globe className="h-3 w-3" /> Target Node (Account)
                                </label>
                                <select
                                    value={selectedAccount}
                                    onChange={(e) => setSelectedAccount(e.target.value)}
                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-2xl py-5 px-6 text-white font-bold focus:ring-2 focus:ring-primary/40 focus:outline-none transition-all appearance-none"
                                >
                                    <option value="" className="bg-zinc-950">Select Node...</option>
                                    {accounts.map(acc => (
                                        <option key={acc.id} value={acc.id} className="bg-zinc-950">
                                            {acc.platform} - {acc.username}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <Tag className="h-3 w-3" /> Niche Context
                                    </label>
                                    <input
                                        type="text"
                                        value={niche}
                                        onChange={(e) => setNiche(e.target.value)}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-2xl py-5 px-6 text-white font-bold focus:ring-2 focus:ring-primary/40 focus:outline-none transition-all"
                                    />
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <Shield className="h-3 w-3" /> Security
                                    </label>
                                    <div className="w-full bg-zinc-950/50 border border-white/10 rounded-2xl py-5 px-6 flex items-center justify-between">
                                        <span className="text-zinc-500 text-[10px] font-bold uppercase">Remix</span>
                                        <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                                    </div>
                                </div>
                            </div>

                            <div 
                                onClick={() => setInjectMonetization(!injectMonetization)}
                                className={cn(
                                    "p-6 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group",
                                    injectMonetization 
                                        ? "bg-emerald-500/10 border-emerald-500/30" 
                                        : "bg-zinc-950/50 border-white/5 hover:border-white/10"
                                )}
                            >
                                <div className="flex items-center gap-4">
                                    <div className={cn(
                                        "h-12 w-12 rounded-xl flex items-center justify-center transition-all",
                                        injectMonetization ? "bg-emerald-500 text-white" : "bg-zinc-900 text-zinc-500 group-hover:text-zinc-300"
                                    )}>
                                        <DollarSign className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <h4 className={cn("text-xs font-bold uppercase tracking-widest transition-colors", injectMonetization ? "text-white" : "text-zinc-400 group-hover:text-zinc-200")}>
                                            Monetization Injection
                                        </h4>
                                        <p className="text-[10px] text-zinc-600 font-medium">Auto-append viral affiliate packets.</p>
                                    </div>
                                </div>
                                <div className={cn(
                                    "h-6 w-12 rounded-full border p-1 transition-all",
                                    injectMonetization ? "border-emerald-500/50 bg-emerald-500/20" : "border-white/10 bg-zinc-900"
                                )}>
                                    <div className={cn(
                                        "h-4 w-4 rounded-full transition-all duration-300 transform",
                                        injectMonetization ? "bg-emerald-500 translate-x-6" : "bg-zinc-700 translate-x-0"
                                    )} />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full bg-primary py-6 rounded-3xl text-white font-bold uppercase text-[10px] tracking-[0.3em] shadow-[0_20px_40px_rgba(var(--primary-rgb),0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                            >
                                {isSubmitting ? "Initializing Sequence..." : (
                                    <>
                                        Execute Deployment <Send className="h-4 w-4" />
                                    </>
                                )}
                            </button>
                        </form>

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

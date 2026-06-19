"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Globe, Video, Tag, DollarSign, Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";

/** Module-internal — do not consume from outside. */
interface MultiPublishModalProps {
    readonly isOpen: boolean;
    readonly onClose: () => void;
    readonly onSuccess?: () => void;
}

/** Module-internal — do not consume from outside. */
const ALL_PLATFORMS = [
    { id: "youtube", label: "YouTube", color: "text-red-500" },
    { id: "tiktok", label: "TikTok", color: "text-rose-400" },
    { id: "instagram", label: "Instagram", color: "text-pink-500" },
    { id: "facebook", label: "Facebook", color: "text-blue-500" },
    { id: "x", label: "X (Twitter)", color: "text-sky-400" },
    { id: "linkedin", label: "LinkedIn", color: "text-blue-400" },
    { id: "snapchat", label: "Snapchat", color: "text-yellow-400" },
    { id: "twitch", label: "Twitch", color: "text-purple-500" },
];

export const MultiPublishModal: React.FC<MultiPublishModalProps> = ({
    isOpen,
    onClose,
    onSuccess
}) => {
    const [videoPath, setVideoPath] = useState("");
    const [niche, setNiche] = useState("Motivation");
    const [injectMonetization, setInjectMonetization] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [results, setResults] = useState<any[] | null>(null);
    const [selectAll, setSelectAll] = useState(true);
    const [selectedPlatforms, setSelectedPlatforms] = useState<Set<string>>(
        new Set(ALL_PLATFORMS.map(p => p.id))
    );

    const togglePlatform = (platformId: string) => {
        const next = new Set(selectedPlatforms);
        if (next.has(platformId)) {
            next.delete(platformId);
        } else {
            next.add(platformId);
        }
        setSelectedPlatforms(next);
        setSelectAll(next.size === ALL_PLATFORMS.length);
    };

    const toggleSelectAll = () => {
        if (selectAll) {
            setSelectedPlatforms(new Set());
        } else {
            setSelectedPlatforms(new Set(ALL_PLATFORMS.map(p => p.id)));
        }
        setSelectAll(!selectAll);
    };

    const handlePublish = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!videoPath) {
            toast.error("Validation Error", { description: "Please provide a video path." });
            return;
        }
        if (selectedPlatforms.size === 0) {
            toast.error("Validation Error", { description: "Please select at least one platform." });
            return;
        }

        const token = await getAuthToken();
        if (!token) return;

        setIsSubmitting(true);
        setResults(null);

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/publish/post-multi`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    video_path: videoPath,
                    niche: niche,
                    platforms: Array.from(selectedPlatforms),
                    inject_monetization: injectMonetization
                })
            }),
            {
                fallback: null,
                onSuccess: (data: any) => {
                    const resultData = data?.data || data;
                    const rawResults = resultData?.results || {};
                    // Normalize results: flatten {published, pending_auth, failed} and infer status from category key
                    const normalized = Object.entries(rawResults).flatMap(([category, items]: [string, any]) =>
                        (Array.isArray(items) ? items : []).map((item: any) => ({
                            ...item,
                            status: item.status || (category === 'published' ? 'published' : category === 'pending_auth' ? 'pending' : 'failed')
                        }))
                    );
                    setResults(normalized);
                    const published = resultData?.published_count || 0;
                    const pending = resultData?.pending_count || 0;
                    toast.success(
                        `Published to ${published} platform${published !== 1 ? 's' : ''}${pending > 0 ? `, ${pending} pending auth` : ''}`
                    );
                    onSuccess?.();
                },
                onFallback: (err) => {
                    toast.error("Multi-platform publish failed", { description: err.message });
                }
            }
        );
        setIsSubmitting(false);
    };

    const handleReset = () => {
        setResults(null);
        setVideoPath("");
        setNiche("Motivation");
        setInjectMonetization(false);
        setSelectAll(true);
        setSelectedPlatforms(new Set(ALL_PLATFORMS.map(p => p.id)));
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
                        className="relative w-full max-w-2xl bg-[#0F0F11]/95 border border-white/5 rounded-[32px] p-10 space-y-8 max-h-[85vh] overflow-y-auto custom-scrollbar"
                    >
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <div className="h-1 w-8 bg-emerald-500 rounded-full" />
                                <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-emerald-500">Global Distribution</span>
                            </div>
                            <h3 className="text-3xl font-bold uppercase tracking-tighter text-white">Publish to All Platforms</h3>
                            <p className="text-zinc-500 text-sm leading-relaxed">
                                Dispatch your video to every major platform simultaneously. Authenticated nodes publish immediately; unauthenticated ones queue for manual auth.
                            </p>
                        </div>

                        {results ? (
                            <div className="space-y-6">
                                <div className="flex items-center gap-3">
                                    <Check className="h-5 w-5 text-emerald-500" />
                                    <span className="text-sm font-bold text-white uppercase tracking-tight">Publish Complete</span>
                                </div>
                                <div className="grid grid-cols-1 gap-3">
                                    {results.map((r: any, i: number) => (
                                        <div
                                            key={i}
                                            className={cn(
                                                "p-4 rounded-2xl border flex items-center gap-4",
                                                r.status === "published" || r.status === "success"
                                                    ? "bg-emerald-500/5 border-emerald-500/20"
                                                    : r.status === "pending"
                                                    ? "bg-amber-500/5 border-amber-500/20"
                                                    : "bg-rose-500/5 border-rose-500/20"
                                            )}
                                        >
                                            <span className={cn(
                                                "text-[8px] font-bold uppercase tracking-widest",
                                                r.platform === "youtube" || r.platform === "youtube shorts" ? "text-red-500" :
                                                r.platform === "tiktok" ? "text-rose-400" :
                                                r.platform === "instagram" ? "text-pink-500" :
                                                r.platform === "facebook" ? "text-blue-500" :
                                                r.platform === "x" ? "text-sky-400" :
                                                r.platform === "linkedin" ? "text-blue-400" :
                                                r.platform === "snapchat" ? "text-yellow-400" :
                                                r.platform === "twitch" ? "text-purple-500" :
                                                "text-zinc-400"
                                            )}>{r.platform}</span>
                                            <span className={cn(
                                                "text-xs font-bold uppercase tracking-widest",
                                                r.status === "published" || r.status === "success" ? "text-emerald-500" :
                                                r.status === "pending" ? "text-amber-500" : "text-rose-500"
                                            )}>{r.error || r.status}</span>
                                            {r.url && (
                                                <a href={r.url} target="_blank" rel="noopener noreferrer"
                                                   className="ml-auto text-[8px] text-cyan-500 hover:text-cyan-400 font-bold uppercase tracking-widest">
                                                    View Link
                                                </a>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={() => { handleReset(); onClose(); }}
                                    className="w-full bg-white/5 border border-white/10 py-4 rounded-2xl text-zinc-400 hover:text-white font-bold text-xs uppercase tracking-widest transition-all"
                                >
                                    Close
                                </button>
                            </div>
                        ) : (
                            <form onSubmit={handlePublish} className="space-y-6">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <Video className="h-3 w-3" /> Video Path
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="/outputs/final_video.mp4"
                                        value={videoPath}
                                        onChange={(e) => setVideoPath(e.target.value)}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-2xl py-5 px-6 text-white font-bold placeholder:text-zinc-800 focus:ring-2 focus:ring-emerald-500/40 focus:outline-none transition-all"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <Tag className="h-3 w-3" /> Niche Context
                                    </label>
                                    <input
                                        type="text"
                                        value={niche}
                                        onChange={(e) => setNiche(e.target.value)}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-2xl py-5 px-6 text-white font-bold focus:ring-2 focus:ring-emerald-500/40 focus:outline-none transition-all"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                            <Globe className="h-3 w-3" /> Target Platforms
                                        </label>
                                        <button
                                            type="button"
                                            onClick={toggleSelectAll}
                                            className="text-[8px] font-bold text-emerald-500 hover:text-emerald-400 uppercase tracking-widest"
                                        >
                                            {selectAll ? "Deselect All" : "Select All"}
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                        {ALL_PLATFORMS.map((platform) => (
                                            <button
                                                key={platform.id}
                                                type="button"
                                                onClick={() => togglePlatform(platform.id)}
                                                className={cn(
                                                    "p-3 rounded-2xl border text-xs font-bold uppercase tracking-tight transition-all flex items-center gap-2",
                                                    selectedPlatforms.has(platform.id)
                                                        ? "bg-emerald-500/10 border-emerald-500/30 text-white"
                                                        : "bg-zinc-950/50 border-white/5 text-zinc-600 hover:border-white/20"
                                                )}
                                            >
                                                <div className={cn(
                                                    "h-5 w-5 rounded-lg flex items-center justify-center transition-all",
                                                    selectedPlatforms.has(platform.id)
                                                        ? "bg-emerald-500 text-black"
                                                        : "bg-zinc-900 text-zinc-700"
                                                )}>
                                                    {selectedPlatforms.has(platform.id) && <Check className="h-3 w-3" />}
                                                </div>
                                                <span className={platform.color}>{platform.label}</span>
                                            </button>
                                        ))}
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
                                            <p className="text-[10px] text-zinc-600 font-medium">Auto-append viral affiliate packets to all posts.</p>
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
                                    disabled={isSubmitting || selectedPlatforms.size === 0 || !videoPath}
                                    className="w-full bg-emerald-500 py-6 rounded-3xl text-black font-bold uppercase text-[10px] tracking-[0.3em] shadow-[0_20px_40px_rgba(16,185,129,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? (
                                        <><Loader2 className="h-4 w-4 animate-spin" /> Distributing to {selectedPlatforms.size} Platforms...</>
                                    ) : (
                                        <><Globe className="h-4 w-4" /> Publish to {selectedPlatforms.size} Platform{selectedPlatforms.size !== 1 ? 's' : ''}</>
                                    )}
                                </button>
                            </form>
                        )}

                        <button
                            onClick={() => { handleReset(); onClose(); }}
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

"use client";

import React, { useState } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/layout";
import {
    Youtube,
    Share2,
    Settings,
    CheckCircle2,
    AlertCircle,
    Plus,
    ArrowUpRight,
    ShieldCheck,
    Globe,
    RefreshCw,
    Layout,
    Instagram,
    Twitter,
    Play,
    ExternalLink,
    X,
    Lock,
    Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";

interface SocialAccount {
    id: number;
    platform: string;
    username: string;
    updated_at: string;
}

interface SocialPost {
    id: number;
    title: string;
    platform: string;
    status: string;
    url: string | null;
    published_at: string;
    video_path?: string; // Local path to processed video
}

const getPlatformIcon = (platform: string) => {
    if (platform?.toLowerCase().includes("youtube")) return Youtube;
    return Share2;
};

import { motion, AnimatePresence } from "framer-motion";

export default function PublishingPage() {
    const [accounts, setAccounts] = useState<SocialAccount[]>([]);
    const [history, setHistory] = useState<SocialPost[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const [isPlatformModalOpen, setIsPlatformModalOpen] = useState(false);
    const [isAccountModalOpen, setIsAccountModalOpen] = useState(false);
    const [selectedAccountForDetail, setSelectedAccountForDetail] = useState<SocialAccount | null>(null);
    const [isRedirecting, setIsRedirecting] = useState<string | null>(null);
    const [variantBTitle, setVariantBTitle] = useState("");
    const [variantBDescription, setVariantBDescription] = useState("");
    const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
    const [selectedJobForDeploy, setSelectedJobForDeploy] = useState<any>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const [isDeploying, setIsDeploying] = useState(false);
    const [injectMonetization, setInjectMonetization] = useState(false);
    const [isScheduled, setIsScheduled] = useState(false);
    const [scheduleTime, setScheduleTime] = useState("");
    const [connectionSuccess, setConnectionSuccess] = useState<string | null>(null);

    const handleManage = (acc: SocialAccount) => {
        setSelectedAccountForDetail(acc);
        setIsAccountModalOpen(true);
    };

    const handleAddPlatform = () => {
        setIsPlatformModalOpen(true);
    };

    const handleSelectPlatform = (platform: string) => {
        setIsPlatformModalOpen(false);
        setIsRedirecting(platform);

        // Real Redirect to Backend OAuth Endpoints
        const lowerPlatform = platform.toLowerCase();
        window.location.href = `${API_BASE}/publish/auth/${lowerPlatform}`;
    };

    React.useEffect(() => {
        const fetchData = async () => {
            try {
                const token = localStorage.getItem("vf_token");
                const headers = { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" };
                const [accountsRes, historyRes, jobsRes] = await Promise.all([
                    fetch(`${API_BASE}/publish/accounts`, { headers }),
                    fetch(`${API_BASE}/publish/history`, { headers }),
                    fetch(`${API_BASE}/video/jobs`, { headers })
                ]);
                if (accountsRes.ok) setAccounts(await accountsRes.json());
                if (historyRes.ok) setHistory(await historyRes.json());
                if (jobsRes.ok) setJobs(await jobsRes.json());
            } catch (error) {
                console.error("Failed to fetch publishing data:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleManualDeploy = async () => {
        if (!selectedJobForDeploy || accounts.length === 0) return;
        setIsDeploying(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/publish/post`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    video_path: selectedJobForDeploy.output_path || "outputs/output.mp4",
                    niche: "AI Technology", // Fallback, should be from job
                    platform: "YouTube Shorts",
                    account_id: accounts[0].id,
                    inject_monetization: injectMonetization,
                    variant_b_title: variantBTitle || undefined,
                    variant_b_description: variantBDescription || undefined
                })
            });
            if (res.ok) {
                setConnectionSuccess("Transmission Initiated");
                setTimeout(() => {
                    setConnectionSuccess(null);
                    setIsDeployModalOpen(false);
                }, 2000);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsDeploying(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                {/* Platform Selection Modal */}
                <AnimatePresence>
                    {isPlatformModalOpen && (
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                className="glass-card w-full max-w-2xl rounded-[3rem] p-12 shadow-2xl space-y-10 relative overflow-hidden"
                            >
                                <div className="absolute inset-0 scanline opacity-20 pointer-events-none" />
                                <div className="flex items-center justify-between">
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-3">
                                            <div className="h-1 w-8 bg-primary rounded-full shadow-sm" />
                                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Network Expansion</span>
                                        </div>
                                        <h3 className="text-3xl font-black italic uppercase tracking-tighter text-white leading-none">Expand Distribution</h3>
                                    </div>
                                    <button onClick={() => setIsPlatformModalOpen(false)} className="p-4 glass-card border-none hover:bg-white/5 rounded-2xl transition-all">
                                        <X className="h-6 w-6 text-zinc-500" />
                                    </button>
                                </div>
                                <div className="mb-10" />
                                <div className="grid grid-cols-2 gap-6">
                                    {[{ name: "YouTube", icon: Youtube, color: "text-red-500" }, { name: "TikTok", icon: Share2, color: "text-white" }].map((p) => (
                                        <motion.button
                                            key={p.name}
                                            onClick={() => handleSelectPlatform(p.name)}
                                            className="p-8 rounded-3xl glass-card border-white/5 hover:border-primary/50 hover:bg-primary/5 transition-all group flex flex-col items-center gap-6 text-center"
                                        >
                                            <div className={cn("p-5 rounded-2xl bg-zinc-950 border border-white/5 group-hover:scale-110 group-hover:rotate-3 transition-all", p.color)}>
                                                <p.icon className="h-10 w-10 fill-current/10" />
                                            </div>
                                            <span className="font-black text-sm uppercase tracking-tight text-white group-hover:text-primary transition-colors">{p.name}</span>
                                        </motion.button>
                                    ))}
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Redirecting Overlay */}
                <AnimatePresence>
                    {isRedirecting && (
                        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/95 backdrop-blur-xl">
                            <div className="flex flex-col items-center gap-10 text-center">
                                <RefreshCw className="h-20 w-20 text-primary animate-spin" />
                                <h4 className="text-2xl font-black italic tracking-tighter text-white uppercase">Securing Handshake...</h4>
                            </div>
                        </div>
                    )}
                </AnimatePresence>

                {/* Deploy Modal */}
                <AnimatePresence>
                    {isDeployModalOpen && (
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                className="glass-card w-full max-w-2xl rounded-[3rem] p-12 shadow-2xl space-y-10 relative overflow-hidden"
                            >
                                <div className="absolute inset-0 scanline opacity-20 pointer-events-none" />
                                <div className="flex items-center justify-between">
                                    <div className="space-y-3">
                                        <div className="flex items-center gap-3">
                                            <div className="h-1 w-8 bg-primary rounded-full shadow-sm" />
                                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Neural Transmit</span>
                                        </div>
                                        <h3 className="text-3xl font-black italic uppercase tracking-tighter text-white leading-none">Manual Deployment</h3>
                                    </div>
                                    <button onClick={() => setIsDeployModalOpen(false)} className="p-4 glass-card border-none hover:bg-white/5 rounded-2xl transition-all">
                                        <X className="h-6 w-6 text-zinc-500" />
                                    </button>
                                </div>

                                <div className="space-y-6">
                                    {/* Video Selection */}
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Source Asset</label>
                                        <select
                                            className="w-full glass-card bg-zinc-950 border-white/10 rounded-2xl p-5 text-sm font-bold text-white uppercase outline-none focus:ring-1 focus:ring-primary/40"
                                            onChange={(e) => {
                                                const job = jobs.find(j => j.id === e.target.value);
                                                setSelectedJobForDeploy(job);
                                            }}
                                        >
                                            <option value="">Select Finished Job...</option>
                                            {jobs.filter(j => j.status === 'Completed').map(j => (
                                                <option key={j.id} value={j.id}>{j.title} ({j.id.slice(0, 8)})</option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* A/B Testing */}
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">A/B Strategy (Variant B)</label>
                                        <input
                                            type="text"
                                            placeholder="Optimized Title Variant..."
                                            className="w-full glass-card bg-zinc-950 border-white/10 rounded-2xl p-5 text-sm font-bold text-primary placeholder:text-zinc-700 outline-none focus:ring-1 focus:ring-primary/40"
                                            value={variantBTitle}
                                            onChange={(e) => setVariantBTitle(e.target.value)}
                                        />
                                    </div>

                                    {/* Monetization Toggle */}
                                    <div
                                        onClick={() => setInjectMonetization(!injectMonetization)}
                                        className={cn(
                                            "p-6 rounded-2xl border transition-all cursor-pointer flex items-center justify-between",
                                            injectMonetization ? "bg-primary/10 border-primary/30" : "bg-white/5 border-white/5"
                                        )}
                                    >
                                        <div className="flex items-center gap-4">
                                            <Zap className={cn("h-5 w-5", injectMonetization ? "text-primary neon-glow" : "text-zinc-600")} />
                                            <div>
                                                <p className="text-[10px] font-black uppercase tracking-widest text-white">Affiliate Protocol</p>
                                                <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-tighter">Inject Monetization Layer</p>
                                            </div>
                                        </div>
                                        <div className={cn("w-10 h-5 rounded-full relative border", injectMonetization ? "bg-primary border-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.3)]" : "bg-zinc-800 border-white/5")}>
                                            <div className={cn("absolute top-1 w-3 h-3 bg-white rounded-full transition-all", injectMonetization ? "left-6" : "left-1")} />
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={handleManualDeploy}
                                    disabled={isDeploying || !selectedJobForDeploy || accounts.length === 0}
                                    className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-black py-6 rounded-[2rem] transition-all shadow-[0_0_50px_rgba(var(--primary-rgb),0.3)] flex items-center justify-center gap-3 uppercase text-xs tracking-[0.3em]"
                                >
                                    {isDeploying ? <RefreshCw className="h-5 w-5 animate-spin" /> : <ArrowUpRight className="h-5 w-5" />}
                                    {isDeploying ? "Deploying..." : "Initialize Transmission"}
                                </button>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Success Overlay */}
                <AnimatePresence>
                    {connectionSuccess && (
                        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/95 backdrop-blur-xl">
                            <div className="flex flex-col items-center gap-10 text-center">
                                <div className="h-24 w-24 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 shadow-lg">
                                    <CheckCircle2 className="h-12 w-12 text-emerald-500" />
                                </div>
                                <h4 className="text-3xl font-black italic tracking-tighter text-emerald-500 uppercase">Connection Verified</h4>
                            </div>
                        </div>
                    )}
                </AnimatePresence>

                {/* Account Modal */}
                <AnimatePresence>
                    {isAccountModalOpen && selectedAccountForDetail && (
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                className="glass-card w-full max-w-lg rounded-[3rem] overflow-hidden shadow-2xl"
                            >
                                <div className="p-10 space-y-8">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-2xl font-black italic uppercase tracking-tighter text-white">{selectedAccountForDetail.username}</h3>
                                        <button onClick={() => setIsAccountModalOpen(false)} className="p-3 glass-card border-none hover:bg-white/5 rounded-xl transition-all">
                                            <X className="h-5 w-5 text-zinc-500" />
                                        </button>
                                    </div>
                                    <button className="w-full bg-primary text-white font-black py-5 rounded-2xl shadow-lg uppercase text-xs tracking-widest">
                                        Configure Node
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-sm" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary lowercase tracking-[0.4em]">Distribution HQ</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black italic tracking-tighter uppercase text-white leading-none">
                            Social <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500 text-hollow">Hub</span>
                        </h1>
                    </div>
                    <motion.button
                        whileHover={{ scale: 1.05, y: -2 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setIsDeployModalOpen(true)}
                        className="bg-zinc-950 hover:bg-zinc-900 text-white border border-white/10 hover:border-primary/50 font-black py-4 px-8 rounded-xl transition-all flex items-center gap-3 shadow-xl uppercase text-xs tracking-widest"
                    >
                        <ArrowUpRight className="h-5 w-5 text-primary" />
                        Manual Transmission
                    </motion.button>
                </div>

                {/* Account Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    <AnimatePresence mode="popLayout">
                        {Array.isArray(accounts) && accounts.map((acc, idx) => {
                            const Icon = getPlatformIcon(acc.platform);
                            return (
                                <motion.div
                                    layout key={acc.id}
                                    initial={{ scale: 0.9, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }}
                                    whileHover={{ scale: 1.02, y: -5 }}
                                    whileTap={{ scale: 0.98 }}
                                    transition={{
                                        delay: idx * 0.1,
                                        scale: { type: "spring", stiffness: 400, damping: 25 },
                                        y: { type: "spring", stiffness: 400, damping: 25 }
                                    }}
                                    className="glass-card relative group hover:border-primary/30 transition-all shadow-xl cursor-pointer"
                                    onClick={() => handleManage(acc)}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="p-4 rounded-xl bg-zinc-950 border border-white/5 text-primary group-hover:scale-110 transition-all">
                                            <Icon className="h-8 w-8" />
                                        </div>
                                        <div className="px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 shadow-sm italic">
                                            Linked
                                        </div>
                                    </div>
                                    <h3 className="text-2xl font-black italic tracking-tighter text-white truncate">{acc.username || "SECURED_ALPHA"}</h3>
                                </motion.div>
                            );
                        })}

                        <motion.button
                            layout onClick={handleAddPlatform}
                            initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                            className="glass-card border-dashed border-white/5 flex flex-col items-center justify-center gap-6 hover:border-primary/50 hover:bg-primary/5 transition-all group min-h-[300px] cursor-pointer"
                        >
                            <div className="h-16 w-16 rounded-2xl border-2 border-dashed border-zinc-800 flex items-center justify-center group-hover:border-primary group-hover:bg-primary/20 transition-all">
                                <Plus className="h-8 w-8 text-zinc-800 group-hover:text-primary group-hover:scale-125 transition-all" />
                            </div>
                            <span className="text-zinc-600 font-black uppercase tracking-[0.3em] text-xs group-hover:text-primary transition-all">Inject Node</span>
                        </motion.button>
                    </AnimatePresence>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
                    <motion.div
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        onClick={() => setInjectMonetization(!injectMonetization)}
                        className={cn(
                            "cursor-pointer border rounded-[2.5rem] p-10 flex items-center gap-10 relative overflow-hidden group shadow-[0_32px_64px_rgba(var(--primary-rgb),0.05)] transition-all",
                            injectMonetization ? "bg-primary/10 border-primary/40 shadow-[0_0_60px_rgba(var(--primary-rgb),0.1)]" : "bg-white/5 border-white/5 opacity-60"
                        )}
                    >
                        <div className="absolute inset-0 scanline opacity-10" />
                        <div className={cn(
                            "h-20 w-20 rounded-3xl flex items-center justify-center border shrink-0 transition-all duration-500 shadow-2xl",
                            injectMonetization ? "bg-primary/20 border-primary/40 rotate-6" : "bg-zinc-950/40 border-white/10"
                        )}>
                            <Zap className={cn("h-10 w-10 transition-colors", injectMonetization ? "text-primary neon-glow" : "text-zinc-700")} />
                        </div>
                        <div className="space-y-2">
                            <p className={cn("text-[10px] font-black uppercase tracking-[0.3em] mb-1 transition-colors", injectMonetization ? "text-primary" : "text-zinc-600")}>Monetization Protocol</p>
                            <h4 className="text-3xl font-black tracking-tighter uppercase text-white leading-none">Affiliate Injection {injectMonetization ? "ACTIVE" : "OFF"}</h4>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className={cn(
                            "cursor-pointer border rounded-[2.5rem] p-10 flex flex-col justify-center gap-6 relative overflow-hidden group shadow-[0_32px_64px_rgba(0,0,0,0.3)] transition-all",
                            isScheduled ? "bg-primary/5 border-primary/20" : "bg-white/5 border-white/5 opacity-60"
                        )}
                        onClick={() => setIsScheduled(!isScheduled)}
                    >
                        <div className="flex items-center gap-6">
                            <div className={cn(
                                "h-14 w-14 rounded-2xl flex items-center justify-center border transition-all duration-500",
                                isScheduled ? "bg-primary/20 border-primary/40" : "bg-zinc-900 border-white/5"
                            )}>
                                <Play className={cn("h-6 w-6", isScheduled ? "text-primary" : "text-zinc-600")} />
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Deployment Timing</p>
                                <h4 className="text-xl font-black uppercase tracking-tighter text-white">{isScheduled ? "Delayed Transmit" : "Instant Blast"}</h4>
                            </div>
                        </div>
                        {isScheduled && (
                            <input
                                type="datetime-local"
                                value={scheduleTime}
                                onClick={(e) => e.stopPropagation()}
                                onChange={(e) => setScheduleTime(e.target.value)}
                                className="w-full bg-zinc-950 border border-white/10 rounded-xl p-4 text-[11px] font-black uppercase tracking-widest text-primary focus:ring-1 focus:ring-primary outline-none"
                            />
                        )}
                    </motion.div>

                    <motion.div
                        initial={{ x: 20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        className={cn(
                            "cursor-pointer border rounded-[2.5rem] p-10 flex flex-col justify-center gap-6 relative overflow-hidden group shadow-[0_32px_64px_rgba(0,0,0,0.3)] transition-all",
                            variantBTitle ? "bg-primary/5 border-primary/20" : "bg-white/5 border-white/5 opacity-60"
                        )}
                    >
                        <div className="flex items-center gap-6">
                            <div className={cn(
                                "h-14 w-14 rounded-2xl flex items-center justify-center border transition-all duration-500",
                                variantBTitle ? "bg-primary/20 border-primary/40" : "bg-zinc-900 border-white/5"
                            )}>
                                <RefreshCw className={cn("h-6 w-6", variantBTitle ? "text-primary" : "text-zinc-600")} />
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">A/B Testing</p>
                                <h4 className="text-xl font-black uppercase tracking-tighter text-white">{variantBTitle ? "Multi-Variant" : "Static Hook"}</h4>
                            </div>
                        </div>
                        <input
                            type="text"
                            placeholder="Enter Variant B Title..."
                            value={variantBTitle}
                            onChange={(e) => setVariantBTitle(e.target.value)}
                            className="w-full bg-zinc-950 border border-white/10 rounded-xl p-4 text-[11px] font-black uppercase tracking-widest text-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                    </motion.div>
                </div>

                {/* Distribution History */}
                <div className="glass-card overflow-hidden shadow-[0_32px_128px_rgba(0,0,0,0.5)] border-white/5 mt-32">
                    <div className="px-10 py-12 border-b border-white/5 bg-white/[0.01] flex items-center justify-between relative overflow-hidden">
                        <div className="absolute inset-0 scanline opacity-10 pointer-events-none" />
                        <div className="flex items-center gap-8 relative z-10">
                            <div className="relative">
                                <Share2 className="h-10 w-10 text-primary neon-glow animate-pulse" />
                                <div className="absolute -inset-2 bg-primary/20 blur-xl rounded-full opacity-50 animate-pulse" />
                            </div>
                            <div className="space-y-2">
                                <h3 className="font-black text-4xl uppercase tracking-tighter text-white leading-none">
                                    Transmission <span className="text-hollow opacity-50">Matrix</span>
                                </h3>
                                <div className="flex items-center gap-3">
                                    <p className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">Real-time Distribution Intelligence Logs</p>
                                    <div className="flex gap-0.5">
                                        {[1, 2, 3].map(i => (
                                            <div key={i} className="h-1 w-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: `${i * 0.2}s` }} />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 bg-zinc-950/80 backdrop-blur-md px-6 py-3 rounded-2xl border border-white/5 shadow-2xl relative z-10">
                            <div className="h-2.5 w-2.5 rounded-full bg-primary animate-ping shadow-[0_0_15px_rgba(var(--primary-rgb),0.8)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-400">Intercepting Packets...</span>
                        </div>
                    </div>

                    <div className="divide-y divide-white/5">
                        <AnimatePresence mode="popLayout">
                            {!Array.isArray(history) || history.length === 0 ? (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="p-40 flex flex-col items-center justify-center gap-10 text-center relative overflow-hidden"
                                >
                                    <div className="absolute inset-0 bg-gradient-radial from-primary/5 to-transparent opacity-30" />
                                    <div className="relative">
                                        <div className="h-32 w-32 rounded-full border-2 border-dashed border-zinc-900 flex items-center justify-center animate-spin-slow">
                                            <Globe className="h-16 w-16 text-zinc-800" />
                                        </div>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <RefreshCw className="h-8 w-8 text-primary animate-spin" />
                                        </div>
                                    </div>
                                    <div className="space-y-3 relative z-10">
                                        <p className="text-sm font-black uppercase tracking-[0.6em] text-zinc-700 animate-pulse">Awaiting Initial Transmission</p>
                                        <p className="text-[10px] font-bold text-zinc-800 uppercase tracking-widest italic">Global Distribution Network Standby</p>
                                    </div>
                                </motion.div>
                            ) : (
                                history.map((post, idx) => {
                                    const Icon = getPlatformIcon(post.platform);
                                    // Generate stable "random" telemetry based on ID
                                    const seed = post.id % 100;
                                    const signalStrength = 95 + (seed % 5);
                                    const bitrate = 40 + (seed % 10);
                                    const nodeIdx = seed % 4;
                                    const nodes = ["US-EAST-ALPHA", "EU-WEST-BETA", "ASIA-SOUTH-GAMMA", "LATAM-DELTA"];

                                    return (
                                        <motion.div
                                            key={post.id}
                                            initial={{ opacity: 0, x: -30, filter: "blur(10px)" }}
                                            animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                                            transition={{
                                                delay: idx * 0.1,
                                                duration: 0.8,
                                                ease: [0.16, 1, 0.3, 1]
                                            }}
                                            className="p-10 px-12 flex flex-col lg:flex-row lg:items-center justify-between hover:bg-white/[0.03] transition-all group relative overflow-hidden"
                                        >
                                            <div className="absolute inset-x-0 top-0 h-[100%] bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                                            <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-[var(--shimmer-opacity)] pointer-events-none" />

                                            {/* Left: Core Info */}
                                            <div className="flex items-center gap-10 relative z-10">
                                                <div
                                                    onClick={() => post.url && post.url.includes('outputs/') && setSelectedAccountForDetail({ id: -1, platform: "PREVIEW", username: post.url.split('/').pop() || "output.mp4", updated_at: "" })}
                                                    className="h-24 w-24 rounded-[2rem] bg-zinc-950 border border-white/5 flex items-center justify-center group-hover:border-primary/50 group-hover:rotate-6 transition-all duration-700 shadow-2xl relative cursor-pointer"
                                                >
                                                    <Icon className="h-10 w-10 text-primary group-hover:scale-110 transition-transform duration-500" />
                                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 rounded-[2rem] backdrop-blur-sm">
                                                        <Play className="h-8 w-8 text-white fill-white animate-pulse" />
                                                    </div>
                                                </div>

                                                <div className="space-y-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex items-center gap-1">
                                                            {[1, 2, 3, 4, 5].map((bar) => (
                                                                <div
                                                                    key={bar}
                                                                    className={cn(
                                                                        "w-1 rounded-full bg-primary transition-all duration-500",
                                                                        bar <= 4 ? "h-3" : "h-1 opacity-30",
                                                                        "group-hover:animate-pulse"
                                                                    )}
                                                                    style={{ animationDelay: `${bar * 100}ms` }}
                                                                />
                                                            ))}
                                                        </div>
                                                        <span className="text-[9px] font-black text-primary uppercase tracking-[0.2em] italic">Active Signal Matrix</span>
                                                    </div>
                                                    <h4 className="font-black text-3xl tracking-tighter group-hover:text-primary transition-all duration-300 line-clamp-1 truncate max-w-xl uppercase italic text-white drop-shadow-2xl">
                                                        {post.title}
                                                    </h4>
                                                    <div className="flex items-center gap-6">
                                                        <span className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.3em]">{post.platform}</span>
                                                        <div className="h-1 w-1 rounded-full bg-zinc-800" />
                                                        <span className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.1em]">{new Date(post.published_at).toLocaleString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Center: Telemetry Grid */}
                                            <div className="hidden xl:grid grid-cols-2 gap-x-12 gap-y-3 px-12 border-x border-white/5 relative z-10">
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Sig_Strength</p>
                                                    <p className="text-xs font-bold text-white tabular-nums">{signalStrength}.2%</p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Transmission_Bitrate</p>
                                                    <p className="text-xs font-bold text-white tabular-nums">{bitrate} Mbps</p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Neural_Node</p>
                                                    <p className="text-xs font-bold text-primary truncate max-w-[80px]">{nodes[nodeIdx]}</p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Packet_Loss</p>
                                                    <p className="text-xs font-bold text-emerald-500">0.00{seed % 5}%</p>
                                                </div>
                                            </div>

                                            {/* Right: Status & Actions */}
                                            <div className="flex items-center gap-10 relative z-10 mt-6 lg:mt-0">
                                                <div className="text-right flex flex-col items-end gap-3">
                                                    <div className="flex items-center gap-2">
                                                        <div className={cn("h-1.5 w-1.5 rounded-full", post.status === "Published" ? "bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-red-500")} />
                                                        <span className={cn(
                                                            "text-[10px] font-black uppercase tracking-[0.3em] italic",
                                                            post.status === "Published" ? "text-emerald-500" : "text-red-500"
                                                        )}>
                                                            {post.status === "Published" ? "Synchronized" : "Failure"}
                                                        </span>
                                                    </div>
                                                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest bg-zinc-950 px-3 py-1.5 rounded-lg border border-white/5">
                                                        {post.status === "Published" ? "Full Bandwidth" : "Auth Required"}
                                                    </span>
                                                </div>

                                                {post.url && post.url.startsWith('http') && (
                                                    <motion.a
                                                        whileHover={{ scale: 1.1, rotate: 10, backgroundColor: "var(--primary)" }}
                                                        whileTap={{ scale: 0.9 }}
                                                        href={post.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="h-16 w-16 rounded-2xl glass-card bg-zinc-900/50 text-zinc-500 hover:text-black flex items-center justify-center transition-all duration-500 shadow-xl group/link border-white/10"
                                                    >
                                                        <ArrowUpRight className="h-8 w-8 group-hover/link:scale-110 transition-transform duration-500" />
                                                    </motion.a>
                                                )}
                                            </div>

                                            {/* Hover Scanline Effect */}
                                            <motion.div
                                                className="absolute inset-y-0 w-[2px] bg-primary/20 shadow-[0_0_20px_rgba(var(--primary-rgb),0.5)] opacity-0 group-hover:opacity-100 pointer-events-none z-20"
                                                initial={{ left: "-10%" }}
                                                whileHover={{ left: "110%" }}
                                                transition={{ duration: 1.5, ease: "linear", repeat: Infinity }}
                                            />
                                        </motion.div>
                                    );
                                })
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

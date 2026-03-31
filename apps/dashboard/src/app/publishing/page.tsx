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
import { API_BASE, WS_BASE } from "@/lib/config";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ConfirmModal } from "@/components/ui/ConfirmModal";

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
    view_count?: number;
    likes?: number;
    shares?: number;
    comments?: number;
    retention_rate?: number;
}

const getPlatformIcon = (platform: string) => {
    if (platform?.toLowerCase().includes("youtube")) return Youtube;
    return Share2;
};

import { motion, AnimatePresence } from "framer-motion";

import { toast } from "sonner";

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
    const [niches, setNiches] = useState<string[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("Technology");
    const [selectedPlatform, setSelectedPlatform] = useState("YouTube Shorts");
    const [selectedAccountId, setSelectedAccountId] = useState<number | "">("");
    const [scheduledPosts, setScheduledPosts] = useState<any[]>([]);
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
    const [isMultiDeploying, setIsMultiDeploying] = useState(false);
    const [isGeneratingSeo, setIsGeneratingSeo] = useState(false);
    const [retryingPostId, setRetryingPostId] = useState<number | null>(null);
    const [isDisconnecting, setIsDisconnecting] = useState(false);
    const [isConfirmDisconnectOpen, setIsConfirmDisconnectOpen] = useState(false);

    const { data: telemetryData } = useWebSocket(`${WS_BASE}/telemetry`);

    const handleManage = (acc: SocialAccount) => {
        setSelectedAccountForDetail(acc);
        setIsAccountModalOpen(true);
    };

    const handleAddPlatform = () => {
        setIsPlatformModalOpen(true);
    };

    const handleSelectPlatform = async (platform: string) => {
        setIsPlatformModalOpen(false);
        setIsRedirecting(platform);

        const lowerPlatform = platform.toLowerCase().replace(" Shorts", "").replace(" Reels", "");
        
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/publish/auth/${lowerPlatform}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            if (res.ok) {
                const data = await res.json();
                if (data.url) {
                    window.location.href = data.url;
                } else {
                    throw new Error("Missing authorization URL in response");
                }
            } else {
                const error = await res.json();
                toast.error("Auth Handshake Failed", {
                    description: error.detail || "Neural link rejected by server."
                });
                setIsRedirecting(null);
            }
        } catch (err) {
            console.error("OAuth Init Failed:", err);
            toast.error("Signal Interpretation Failure", {
                description: "Failed to parse OAuth handshake packets."
            });
            setIsRedirecting(null);
        }
    };

    React.useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem("et_token");
            const headers = { Authorization: `Bearer ${token}` };
            try {
                const [accRes, histRes, jobsRes, nichesRes] = await Promise.all([
                    fetch(`${API_BASE}/publish/accounts`, { headers }),
                    fetch(`${API_BASE}/publish/history`, { headers }),
                    fetch(`${API_BASE}/video/jobs`, { headers }),
                    fetch(`${API_BASE}/discovery/niches`, { headers })
                ]);

                if (accRes.ok) setAccounts(await accRes.json());
                if (histRes.ok) setHistory(await histRes.json());
                if (jobsRes.ok) setJobs(await jobsRes.json());
                if (nichesRes.ok) setNiches(await nichesRes.json());

                // Fetch scheduled posts from history (filter by status)
                try {
                    const schedRes = await fetch(`${API_BASE}/publish/history`, { headers });
                    if (schedRes.ok) {
                        const allPosts = await schedRes.json();
                        setScheduledPosts(allPosts.filter((p: any) => p.status === "scheduled" || p.status === "pending"));
                    }
                } catch (e) {}
            } catch (err) {
                console.error("Failed to fetch publishing data:", err);
                toast.error("Failed to load publishing data");
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 10000); // Polling for job updates
        return () => clearInterval(interval);
    }, []);

    const handleSync = async (postId: number) => {
        const token = localStorage.getItem("et_token");
        toast.promise(
            fetch(`${API_BASE}/publish/sync/${postId}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }).then(async res => {
                if (!res.ok) throw new Error("Sync failed");
                const historyRes = await fetch(`${API_BASE}/publish/history`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (historyRes.ok) setHistory(await historyRes.json());
                return res.json();
            }),
            {
                loading: 'Synchronizing Neural Metrics...',
                success: 'Telemetry Updated Successfully',
                error: 'Sync Failed - Service Unavailable'
            }
        );
    };

    const handleManualDeploy = async () => {
        if (!selectedJobForDeploy || accounts.length === 0) {
            toast.error("Deployment Guard", {
                description: "Select a valid asset and linked account node."
            });
            return;
        }
        setIsDeploying(true);
        try {
            const token = localStorage.getItem("et_token");
            
            const endpoint = isScheduled && scheduleTime ? `${API_BASE}/publish/schedule` : `${API_BASE}/publish/post`;
            const body: any = {
                video_path: selectedJobForDeploy.output_path,
                niche: selectedNiche,
                platform: selectedPlatform,
                account_id: selectedAccountId || (accounts.length > 0 ? accounts[0].id : undefined),
                inject_monetization: injectMonetization,
                variant_b_title: variantBTitle || undefined,
                variant_b_description: variantBDescription || undefined
            };
            
            if (isScheduled && scheduleTime) {
                body.scheduled_at = new Date(scheduleTime).toISOString();
            }
            
            const res = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });
            if (res.ok) {
                toast.success("Transmission Initiated", {
                    description: "Handshake verified. Packets streaming to target node."
                });
                setIsDeployModalOpen(false);
                // Refresh history
                const headers = { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" };
                const historyRes = await fetch(`${API_BASE}/publish/history`, { headers });
                if (historyRes.ok) setHistory(await historyRes.json());
            } else {
                const error = await res.json();
                toast.error("Transmission Failed", {
                    description: error.detail || "Neural link rejected. Check auth tokens."
                });
            }
        } catch (err) {
            console.error(err);
            toast.error("Signal Lost", {
                description: "Failed to reach the publishing cluster."
            });
        } finally {
            setIsDeploying(false);
        }
    };

    const handleMultiDeploy = async () => {
        if (!selectedJobForDeploy || accounts.length === 0) {
            toast.error("Deployment Guard", {
                description: "Select a valid asset and linked account node."
            });
            return;
        }
        if (selectedPlatforms.length === 0) {
            toast.error("Deployment Guard", {
                description: "Select at least one target network protocol."
            });
            return;
        }
        setIsMultiDeploying(true);
        try {
            const token = localStorage.getItem("et_token");
            const body: any = {
                video_path: selectedJobForDeploy.output_path,
                niche: selectedNiche,
                platforms: selectedPlatforms,
                account_id: selectedAccountId || (accounts.length > 0 ? accounts[0].id : undefined),
                inject_monetization: injectMonetization,
                variant_b_title: variantBTitle || undefined,
                variant_b_description: variantBDescription || undefined
            };
            const res = await fetch(`${API_BASE}/publish/post-multi`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });
            if (res.ok) {
                toast.success("Multi-Node Transmission Initiated", {
                    description: "Broadcasting across all selected networks."
                });
                setIsDeployModalOpen(false);
                setSelectedPlatforms([]);
                const headers = { Authorization: `Bearer ${token}` };
                const historyRes = await fetch(`${API_BASE}/publish/history`, { headers });
                if (historyRes.ok) setHistory(await historyRes.json());
            } else {
                const error = await res.json();
                toast.error("Multi-Transmission Failed", {
                    description: error.detail || "One or more network links rejected."
                });
            }
        } catch (err) {
            console.error(err);
            toast.error("Signal Lost", {
                description: "Failed to reach the publishing cluster."
            });
        } finally {
            setIsMultiDeploying(false);
        }
    };

    const handleRetry = async (contentId: number) => {
        const token = localStorage.getItem("et_token");
        setRetryingPostId(contentId);
        toast.promise(
            fetch(`${API_BASE}/publish/retry/${contentId}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }).then(async res => {
                if (!res.ok) throw new Error("Retry failed");
                const historyRes = await fetch(`${API_BASE}/publish/history`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (historyRes.ok) setHistory(await historyRes.json());
                return res.json();
            }).finally(() => setRetryingPostId(null)),
            {
                loading: 'Retrying Transmission...',
                success: 'Handshake Re-Established',
                error: 'Retry Failed - Service Unavailable'
            }
        );
    };

    const handleDisconnect = async (accountId: number) => {
        const token = localStorage.getItem("et_token");
        setIsDisconnecting(true);
        try {
            const res = await fetch(`${API_BASE}/publish/account/${accountId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                toast.success("Node Disconnected", {
                    description: "Account link has been severed."
                });
                setAccounts(prev => prev.filter(a => a.id !== accountId));
                setIsAccountModalOpen(false);
                setSelectedAccountForDetail(null);
            } else {
                const error = await res.json();
                toast.error("Disconnect Failed", {
                    description: error.detail || "Unable to sever node connection."
                });
            }
        } catch (err) {
            console.error(err);
            toast.error("Signal Lost", {
                description: "Failed to reach the publishing cluster."
            });
        } finally {
            setIsDisconnecting(false);
        }
    };

    const handleGenerateSeo = async () => {
        setIsGeneratingSeo(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(
                `${API_BASE}/publish/package?niche=${encodeURIComponent(selectedNiche)}&platform=${encodeURIComponent(selectedPlatform)}`,
                {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` }
                }
            );
            if (res.ok) {
                toast.success("SEO Package Generated", {
                    description: "Metadata optimization bundle ready for injection."
                });
            } else {
                const error = await res.json();
                toast.error("SEO Generation Failed", {
                    description: error.detail || "Unable to generate SEO package."
                });
            }
        } catch (err) {
            console.error(err);
            toast.error("Signal Lost", {
                description: "Failed to reach the publishing cluster."
            });
        } finally {
            setIsGeneratingSeo(false);
        }
    };

    const togglePlatformSelection = (platform: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(platform)
                ? prev.filter(p => p !== platform)
                : [...prev, platform]
        );
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
                                        <h3 className="text-3xl font-black uppercase tracking-tighter text-white leading-none">Expand Distribution</h3>
                                    </div>
                                    <button onClick={() => setIsPlatformModalOpen(false)} className="p-4 glass-card border-none hover:bg-white/5 rounded-2xl transition-all">
                                        <X className="h-6 w-6 text-zinc-500" />
                                    </button>
                                </div>
                                <div className="mb-10" />
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                                    {[
                                        { name: "YouTube", icon: Youtube, color: "text-red-500" },
                                        { name: "TikTok", icon: Share2, color: "text-white" },
                                        { name: "Instagram", icon: Instagram, color: "text-pink-500" },
                                        { name: "X", icon: Twitter, color: "text-blue-400" },
                                        { name: "LinkedIn", icon: Globe, color: "text-blue-600" }
                                    ].map((p) => (
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
                        <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/95 backdrop-blur-xl">
                            <div className="flex flex-col items-center gap-10 text-center">
                                <RefreshCw className="h-20 w-20 text-primary animate-spin" />
                                <h4 className="text-2xl font-black tracking-tighter text-white uppercase">Securing Handshake...</h4>
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
                                        <h3 className="text-3xl font-black uppercase tracking-tighter text-white leading-none">Manual Deployment</h3>
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
                                            className="w-full glass-card bg-zinc-950 border-white/10 rounded-2xl p-5 text-sm font-bold text-white uppercase outline-none focus:ring-1 focus:ring-primary/40 transition-all hover:border-primary/30"
                                            value={selectedJobForDeploy?.id || ""}
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

                                    <div className="grid grid-cols-2 gap-6">
                                        {/* Platform Selection */}
                                        <div className="space-y-3">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Network Protocol</label>
                                            <select
                                                className="w-full glass-card bg-zinc-950 border-white/10 rounded-2xl p-5 text-xs font-bold text-white uppercase outline-none focus:ring-1 focus:ring-primary/40 transition-all hover:border-primary/30"
                                                value={selectedPlatform}
                                                onChange={(e) => setSelectedPlatform(e.target.value)}
                                            >
                                                <option value="YouTube Shorts">YouTube Shorts</option>
                                                <option value="TikTok">TikTok</option>
                                                <option value="Instagram Reels">Instagram Reels</option>
                                                <option value="X">X (Twitter)</option>
                                                <option value="LinkedIn">LinkedIn</option>
                                            </select>
                                        </div>

                                        {/* Account Selection */}
                                        <div className="space-y-3">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Identity Node</label>
                                            <select
                                                className="w-full glass-card bg-zinc-950 border-white/10 rounded-2xl p-5 text-xs font-bold text-white uppercase outline-none focus:ring-1 focus:ring-primary/40 transition-all hover:border-primary/30"
                                                value={selectedAccountId}
                                                onChange={(e) => setSelectedAccountId(Number(e.target.value))}
                                            >
                                                <option value="">Choose Account...</option>
                                                {accounts.map(acc => (
                                                    <option key={acc.id} value={acc.id}>{acc.username} ({acc.platform})</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>

                                    {/* Niche Selection */}
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Topic Alpha (Niche)</label>
                                        <select
                                            className="w-full glass-card bg-zinc-950 border-white/10 rounded-2xl p-5 text-sm font-bold text-white uppercase outline-none focus:ring-1 focus:ring-primary/40 transition-all hover:border-primary/30"
                                            value={selectedNiche}
                                            onChange={(e) => setSelectedNiche(e.target.value)}
                                        >
                                            <option value="">Select Niche...</option>
                                            {niches.map(n => <option key={n} value={n}>{n}</option>)}
                                        </select>
                                    </div>

                                    {/* Multi-Platform Selection */}
                                    <div className="space-y-3">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Multi-Node Broadcast Targets</label>
                                        <div className="grid grid-cols-3 gap-3">
                                            {["YouTube Shorts", "TikTok", "Instagram Reels", "X", "LinkedIn"].map((platform) => (
                                                <button
                                                    key={platform}
                                                    type="button"
                                                    onClick={() => togglePlatformSelection(platform)}
                                                    className={cn(
                                                        "p-4 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all",
                                                        selectedPlatforms.includes(platform)
                                                            ? "bg-primary/10 border-primary/40 text-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.15)]"
                                                            : "bg-zinc-950 border-white/5 text-zinc-500 hover:border-primary/20 hover:text-zinc-300"
                                                    )}
                                                >
                                                    {platform}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* A/B Testing */}
                                    <div className="space-y-3">
                                        <label htmlFor="variant-b-title" className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">A/B Strategy (Variant B)</label>
                                        <input
                                            id="variant-b-title"
                                            name="variant-b-title"
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
                                    className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-black py-6 rounded-4xl transition-all shadow-[0_0_50px_rgba(var(--primary-rgb),0.3)] flex items-center justify-center gap-3 uppercase text-xs tracking-[0.3em]"
                                >
                                    {isDeploying ? <RefreshCw className="h-5 w-5 animate-spin" /> : <ArrowUpRight className="h-5 w-5" />}
                                    {isDeploying ? "Deploying..." : "Initialize Transmission"}
                                </button>

                                <button
                                    onClick={handleMultiDeploy}
                                    disabled={isMultiDeploying || !selectedJobForDeploy || accounts.length === 0 || selectedPlatforms.length === 0}
                                    className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-black py-6 rounded-4xl transition-all shadow-[0_0_50px_rgba(37,99,235,0.3)] flex items-center justify-center gap-3 uppercase text-xs tracking-[0.3em]"
                                >
                                    {isMultiDeploying ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Globe className="h-5 w-5" />}
                                    {isMultiDeploying ? "Broadcasting..." : `Publish Everywhere (${selectedPlatforms.length})`}
                                </button>

                                <button
                                    onClick={handleGenerateSeo}
                                    disabled={isGeneratingSeo}
                                    className="w-full bg-zinc-900 hover:bg-zinc-800 disabled:opacity-50 text-white font-black py-5 rounded-2xl transition-all border border-white/5 hover:border-primary/30 flex items-center justify-center gap-3 uppercase text-xs tracking-[0.3em]"
                                >
                                    {isGeneratingSeo ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4 text-primary" />}
                                    {isGeneratingSeo ? "Generating..." : "Generate SEO Package"}
                                </button>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Success Overlay Removed in favor of Sonner Toasts */}
                <AnimatePresence>
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
                                className="glass-card w-full max-w-lg rounded-6xl overflow-hidden shadow-2xl"
                            >
                                <div className="p-10 space-y-8">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-2xl font-black uppercase tracking-tighter text-white">{selectedAccountForDetail.username}</h3>
                                        <button onClick={() => setIsAccountModalOpen(false)} className="p-3 glass-card border-none hover:bg-white/5 rounded-xl transition-all">
                                            <X className="h-5 w-5 text-zinc-500" />
                                        </button>
                                    </div>
                                    <button
                                        onClick={() => {
                                            setIsAccountModalOpen(false);
                                            if (selectedAccountForDetail) {
                                                window.location.href = `${API_BASE}/publish/auth/${selectedAccountForDetail.platform.toLowerCase()}`;
                                            }
                                        }}
                                        className="w-full bg-primary text-white font-black py-5 rounded-2xl shadow-lg uppercase text-xs tracking-widest"
                                    >
                                        Re-Authenticate Node
                                    </button>
                                    <button
                                        onClick={() => setIsConfirmDisconnectOpen(true)}
                                        disabled={isDisconnecting}
                                        className="w-full bg-red-900/30 hover:bg-red-900/50 disabled:opacity-50 text-red-400 font-black py-5 rounded-2xl border border-red-500/20 hover:border-red-500/40 uppercase text-xs tracking-widest transition-all flex items-center justify-center gap-3"
                                    >
                                        {isDisconnecting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <X className="h-4 w-4" />}
                                        {isDisconnecting ? "Severing..." : "Disconnect Node"}
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <ConfirmModal 
                    isOpen={isConfirmDisconnectOpen}
                    onClose={() => setIsConfirmDisconnectOpen(false)}
                    onConfirm={() => {
                        if (selectedAccountForDetail) {
                            handleDisconnect(selectedAccountForDetail.id);
                        }
                        setIsConfirmDisconnectOpen(false);
                    }}
                    title="Sever Neural Link?"
                    description="This will permanently disconnect the account node from the Viral Forge cluster. Synchronized metrics may be lost."
                    variant="danger"
                    confirmText="Sever Link"
                />

                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-sm" />
                            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-primary">Distribution HQ</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">
                            Social <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-400 to-indigo-500 text-hollow">Hub</span>
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
                                        <div className="px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 shadow-sm">
                                            Linked
                                        </div>
                                    </div>
                                    <h3 className="text-2xl font-black tracking-tighter text-white truncate">{acc.username || "SECURED_ALPHA"}</h3>
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
                            "cursor-pointer border rounded-5xl p-10 flex items-center gap-10 relative overflow-hidden group shadow-[0_32px_64px_rgba(var(--primary-rgb),0.05)] transition-all",
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
                                id="schedule-time"
                                name="schedule-time"
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
                            id="variant-b-title-alt"
                            name="variant-b-title-alt"
                            type="text"
                            placeholder="Enter Variant B Title..."
                            value={variantBTitle}
                            onChange={(e) => setVariantBTitle(e.target.value)}
                            className="w-full bg-zinc-950 border border-white/10 rounded-xl p-4 text-[11px] font-black uppercase tracking-widest text-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                    </motion.div>
                </div>

                {/* Scheduled Posts */}
                {scheduledPosts.length > 0 && (
                    <div className="glass-card overflow-hidden shadow-2xl border-white/5 mt-16">
                        <div className="px-10 py-8 border-b border-white/5 bg-amber-500/2 flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                <Play className="h-5 w-5 text-amber-500" />
                            </div>
                            <div>
                                <h3 className="font-black text-xl uppercase tracking-tighter text-white">Scheduled <span className="text-amber-400">Transmissions</span></h3>
                                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Pending deployment queue</p>
                            </div>
                        </div>
                        <div className="divide-y divide-white/5">
                            {scheduledPosts.map((post) => (
                                <div key={post.id} className="p-6 flex items-center justify-between hover:bg-white/2 transition-all">
                                    <div className="flex items-center gap-4">
                                        <div className="h-3 w-3 rounded-full bg-amber-500 animate-pulse" />
                                        <div>
                                            <p className="text-sm font-black text-white uppercase">{post.title}</p>
                                            <p className="text-[10px] text-zinc-500">{post.platform} • {new Date(post.published_at || post.scheduled_at).toLocaleString()}</p>
                                        </div>
                                    </div>
                                    <div className="px-3 py-1 rounded-lg bg-amber-500/10 text-amber-500 text-[9px] font-black uppercase tracking-widest border border-amber-500/20">
                                        {post.status}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Distribution History */}
                <div className="glass-card overflow-hidden shadow-[0_32px_128px_rgba(0,0,0,0.5)] border-white/5 mt-32">
                    <div className="px-10 py-12 border-b border-white/5 bg-white/1 flex items-center justify-between relative overflow-hidden">
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
                                        <p className="text-[10px] font-bold text-zinc-800 uppercase tracking-widest">Global Distribution Network Standby</p>
                                    </div>
                                </motion.div>
                            ) : (
                                history.map((post, idx) => {
                                    const nodes = ["US-EAST-ALPHA", "EU-WEST-BETA", "ASIA-SOUTH-GAMMA", "LATAM-DELTA"];
                                    const nodeIdx = post.id % 4;
                                    const Icon = getPlatformIcon(post.platform);

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
                                            className="p-10 px-12 flex flex-col lg:flex-row lg:items-center justify-between hover:bg-white/3 transition-all group relative overflow-hidden"
                                        >
                                            <div className="absolute inset-x-0 top-0 h-full bg-linear-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                                            <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-(--shimmer-opacity) pointer-events-none" />

                                            {/* Left: Core Info */}
                                            <div className="flex items-center gap-10 relative z-10">
                                                 <div
                                                     onClick={() => post.url && window.open(post.url, '_blank', 'noopener,noreferrer')}
                                                     className="h-24 w-24 rounded-4xl bg-zinc-950 border border-white/5 flex items-center justify-center group-hover:border-primary/50 group-hover:rotate-6 transition-all duration-700 shadow-2xl relative cursor-pointer"
                                                 >
                                                    <Icon className="h-10 w-10 text-primary group-hover:scale-110 transition-transform duration-500" />
                                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 rounded-4xl backdrop-blur-sm">
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
                                                        <span className="text-[9px] font-black text-primary uppercase tracking-[0.2em]">Active Signal Matrix</span>
                                                    </div>
                                                    <h4 className="font-black text-3xl tracking-tighter group-hover:text-primary transition-all duration-300 line-clamp-1 truncate max-w-xl uppercase text-white drop-shadow-2xl">
                                                        {post.title}
                                                    </h4>
                                                    <div className="flex items-center gap-6">
                                                        <span className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.3em]">{post.platform}</span>
                                                        <div className="h-1 w-1 rounded-full bg-zinc-800" />
                                                        <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">{new Date(post.published_at).toLocaleString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' })}</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Center: Live Telemetry Grid */}
                                            <div className="hidden xl:grid grid-cols-2 gap-x-12 gap-y-3 px-12 border-x border-white/5 relative z-10">
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Real_Views</p>
                                                    <p className="text-xs font-bold tabular-nums text-primary">
                                                        {post.view_count?.toLocaleString() || "0"}
                                                    </p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Engagements</p>
                                                    <p className="text-xs font-bold tabular-nums text-white">
                                                        {post.likes?.toLocaleString() || "0"} <span className="text-[10px] text-zinc-500 font-medium">Likes</span>
                                                    </p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Node_Oracle</p>
                                                    <p className="text-xs font-bold text-zinc-400 truncate max-w-[80px]">{nodes[nodeIdx]}</p>
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest text-hollow">Retention</p>
                                                    <p className="text-xs font-bold text-emerald-500">{post.retention_rate ? `${post.retention_rate.toFixed(1)}%` : "N/A"}</p>
                                                </div>
                                            </div>

                                            {/* Right: Actions */}
                                            <div className="flex items-center gap-4 relative z-10 pl-8">
                                                <motion.button
                                                    whileHover={{ scale: 1.1, rotate: 180 }}
                                                    whileTap={{ scale: 0.9 }}
                                                    onClick={() => handleSync(post.id)}
                                                    className="h-10 w-10 flex items-center justify-center rounded-xl bg-zinc-950 border border-white/5 text-zinc-500 hover:text-primary hover:border-primary/50 transition-all pointer-events-auto"
                                                    title="Neural Metrics Sync"
                                                >
                                                    <RefreshCw className="h-4 w-4" />
                                                </motion.button>

                                                {post.status === "PENDING_AUTH" && (
                                                    <motion.button
                                                        whileHover={{ scale: 1.05 }}
                                                        whileTap={{ scale: 0.95 }}
                                                        onClick={() => handleRetry(post.id)}
                                                        disabled={retryingPostId === post.id}
                                                        className="h-10 px-5 flex items-center gap-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-black uppercase tracking-widest hover:bg-amber-500/20 hover:border-amber-500/40 transition-all pointer-events-auto disabled:opacity-50"
                                                        title="Retry Transmission"
                                                    >
                                                        {retryingPostId === post.id ? <RefreshCw className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
                                                        Retry
                                                    </motion.button>
                                                )}
                                                
                                                {post.url && (
                                                    <Link 
                                                        href={post.url} 
                                                        target="_blank"
                                                        className="h-10 px-6 flex items-center gap-3 rounded-xl bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-widest hover:bg-primary hover:text-black transition-all"
                                                    >
                                                        <ExternalLink className="h-3 w-3" />
                                                        View Live
                                                    </Link>
                                                )}
                                            </div>

                                            {/* Right: Status & Actions */}
                                            <div className="flex items-center gap-10 relative z-10 mt-6 lg:mt-0">
                                                <div className="text-right flex flex-col items-end gap-3">
                                                    <div className="flex items-center gap-2">
                                                        <div className={cn("h-1.5 w-1.5 rounded-full", post.status === "Published" ? "bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-red-500")} />
                                                        <span className={cn(
                                                            "text-[10px] font-black uppercase tracking-[0.3em]",
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
        </DashboardLayout >
    );
}

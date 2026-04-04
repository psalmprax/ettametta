"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
import {
    Globe,
    Zap,
    Cpu,
    ShieldCheck,
    AlertTriangle,
    RefreshCw,
    Layers,
    Copy,
    TrendingUp,
    ChevronRight,
    Search,
    MessageSquareQuote,
    ShoppingBag,
    LinkIcon,
    Package
} from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import dynamic from "next/dynamic";

const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });
import { ConfirmModal } from "@/components/ui/ConfirmModal";

export default function EmpirePage() {
    const [sentinelStatus, setSentinelStatus] = useState<any>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [selectedStrategy, setSelectedStrategy] = useState<any>(null);
    const [cloningNiche, setCloningNiche] = useState("");
    const [promoProduct, setPromoProduct] = useState("");
    const [isGeneratingPromo, setIsGeneratingPromo] = useState(false);
    const [promoScript, setPromoScript] = useState<any>(null);
    const [affiliateLinks, setAffiliateLinks] = useState<any[]>([]);
    const [newLink, setNewLink] = useState({ product_name: "", niche: "", link: "", cta_text: "" });
    const [isAddingLink, setIsAddingLink] = useState(false);
    const [revenueReport, setRevenueReport] = useState<any>(null);
    const [autoMerchTopic, setAutoMerchTopic] = useState("");
    const [isGeneratingMerch, setIsGeneratingMerch] = useState(false);
    const [recommendNiche, setRecommendNiche] = useState("");
    const [recommendScript, setRecommendScript] = useState("");
    const [recommendations, setRecommendations] = useState<any[]>([]);
    const [isRecommending, setIsRecommending] = useState(false);
    const [isSyncingShopify, setIsSyncingShopify] = useState(false);
    const [isCloneModalOpen, setIsCloneModalOpen] = useState(false);
    const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);
    const [availableNiches, setAvailableNiches] = useState<string[]>([]);

    const fetchSentinel = async () => {
        setIsRefreshing(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/no-face/sentinel/status`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSentinelStatus(data);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to load sentinel status");
        } finally {
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        fetchSentinel();
    }, []);

    const [empireMetrics, setEmpireMetrics] = useState<any>(null);
    const [blueprints, setBlueprints] = useState<any[]>([]);

    const handleClone = async () => {
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/monetization/empire/clone`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        source_niche: selectedStrategy?.niche || availableNiches[0] || "Stoic Wisdom",
                        target_niche: cloningNiche
                    })
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Strategy Cloned Successfully", {
                        description: `Neural weights for ${selectedStrategy?.niche || "Original"} have been successfully mapped to the ${cloningNiche} niche.`
                    });
                },
                onFallback: () => {
                    toast.error("Cloning Failed", {
                        description: "Neural cluster was unable to replicate the strategy at this time."
                    });
                }
            }
        );
    };

    const fetchEmpireMetrics = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/empire/metrics`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setEmpireMetrics(data);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to load empire metrics");
        }
    };

    const fetchBlueprints = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/empire/blueprints`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setBlueprints(data);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to load blueprints");
        }
    };

    const fetchAvailableNiches = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/discovery/niches`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAvailableNiches(data);
                if (data.length > 0 && !cloningNiche) {
                    setCloningNiche(data[0]);
                }
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchAffiliateLinks = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/links`, {
                method: "GET",
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setAffiliateLinks(data.links || data || []);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to load affiliate links");
        }
    };

    const handleAddAffiliateLink = async () => {
        if (!newLink.product_name || !newLink.link) return;
        setIsAddingLink(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/links`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(newLink)
            });
            if (res.ok) {
                toast.success("Affiliate Link Added", {
                    description: `"${newLink.product_name}" is now available in the viral injection catalog.`
                });
                setNewLink({ product_name: "", niche: "", link: "", cta_text: "" });
                fetchAffiliateLinks();
            } else {
                toast.error("Processing Error", {
                    description: "Failed to register the link in the affiliate database."
                });
            }
        } catch (err) {
            console.error(err);
            toast.error("Nexus Disconnect", {
                description: "Failed to persist the affiliate link."
            });
        } finally {
            setIsAddingLink(false);
        }
    };

    const fetchRevenueReport = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/report`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setRevenueReport(data);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to load revenue report");
        }
    };

    useEffect(() => {
        fetchSentinel();
        fetchEmpireMetrics();
        fetchBlueprints();
        fetchAffiliateLinks();
        fetchRevenueReport();
        fetchAvailableNiches();
    }, []);

    const handleGeneratePromo = async () => {
        if (!promoProduct) return;
        setIsGeneratingPromo(true);
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/monetization/promo/generate`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({ product_name: promoProduct, niche: cloningNiche })
                });
            },
            {
                fallback: null,
                onSuccess: (data) => setPromoScript(data),
                onFallback: () => toast.error("Failed to generate promo")
            }
        );
        setIsGeneratingPromo(false);
    };

    const handleAutoMerch = async () => {
        if (!autoMerchTopic) return;
        setIsGeneratingMerch(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/auto-merch`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ trend_topic: autoMerchTopic })
            });
            if (res.ok) {
                const data = await res.json();
                toast.success("Auto-Merch Generated", { description: data.message || `Merch created for "${autoMerchTopic}"` });
                setAutoMerchTopic("");
            } else {
                toast.error("Auto-Merch Failed", { description: "Could not generate auto-merch." });
            }
        } catch (err) {
            console.error(err);
            toast.error("Network Error", { description: "Failed to reach server." });
        } finally {
            setIsGeneratingMerch(false);
        }
    };

    const handleRecommendLinks = async () => {
        if (!recommendNiche || !recommendScript) return;
        setIsRecommending(true);
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/monetization/recommend-links`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({ niche: recommendNiche, script_text: recommendScript })
                });
            },
            {
                fallback: [],
                onSuccess: (data: any) => {
                    const links = data.links || data || [];
                    setRecommendations(links);
                    toast.success("Recommendations Ready", { description: `${links.length} links found.` });
                },
                onFallback: () => toast.error("Recommendation Failed", { description: "Could not fetch link recommendations." })
            }
        );
        setIsRecommending(false);
    };

    const handleShopifySync = async () => {
        setIsSyncingShopify(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/commerce/sync`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                }
            });
            if (res.ok) {
                const data = await res.json();
                toast.success("Shopify Synced", { description: data.message || "Commerce data synchronized." });
            } else {
                toast.error("Sync Failed", { description: "Could not sync Shopify data." });
            }
        } catch (err) {
            console.error(err);
            toast.error("Network Error", { description: "Failed to reach server." });
        } finally {
            setIsSyncingShopify(false);
        }
    };

    const [networkData, setNetworkData] = useState<any>({ nodes: [], links: [] });
    const [timelineEvents, setTimelineEvents] = useState<any[]>([]);

    const fetchNetwork = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/empire/network`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setNetworkData(data);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to load network data");
        }
    };

    const fetchTimelineEvents = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/monetization/empire/activity`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setTimelineEvents(data);
            }
        } catch (err) {
            console.error("Failed to fetch empire activity:", err);
        }
    };

    useEffect(() => {
        fetchNetwork();
        fetchTimelineEvents();
        const interval = setInterval(fetchTimelineEvents, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    // Removed simulated timeline generator in favor of Real-First backend telemetry


    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-end justify-between">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" style={{ width: "85%" }} />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Empire Protocol</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">Command <span className="text-transparent bg-clip-text bg-linear-to-r from-violet-500 to-cyan-400 text-hollow">Center</span></h1>
                        <p className="text-zinc-500 font-medium tracking-tight">Managing multi-account <span className="text-cyan-400 font-black">global scaling</span> and algorithm synchronization.</p>
                    </div>
                    <button
                        onClick={fetchSentinel}
                        disabled={isRefreshing}
                        className="glass-card px-6 py-4 rounded-xl flex items-center gap-3 group hover:border-neon-cyan/50 transition-all font-black uppercase tracking-widest text-[10px] shadow-glow-cyan/10"
                    >
                        <RefreshCw className={cn("h-4 w-4 text-zinc-500 group-hover:text-neon-cyan transition-colors", isRefreshing && "animate-spin")} />
                        <span className="text-zinc-500 group-hover:text-white">Sync Sentinel</span>
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Algorithm Sentinel Monitor */}
                    <div className="space-y-8">
                        <div className="glass-card space-y-8 relative overflow-hidden h-fit">
                            <div className="absolute inset-0 pointer-events-none opacity-(--scanline-opacity) bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.03),rgba(0,255,0,0.01),rgba(0,0,255,0.03))] bg-[length:100%_4px,3px_100%]" />
                            <div className="flex items-center justify-between">
                                <div className="space-y-1">
                                    <h3 className="font-black uppercase tracking-tight text-white">Algorithm Sentinel</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Platform Drift Analyzer</p>
                                </div>
                                <div className={cn(
                                    "px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all shadow-glow-violet/20",
                                    sentinelStatus?.status === "NOMINAL" ? "bg-neon-cyan/10 border-neon-cyan/30 text-neon-cyan shadow-glow-cyan/20" : "bg-neon-violet/10 border-neon-violet/30 text-neon-violet shadow-glow-violet/20"
                                )}>
                                    {sentinelStatus?.status || "CONNECTING..."}
                                </div>
                            </div>

                            {/* Sync Meter */}
                            <div className="flex flex-col items-center gap-6 py-4">
                                <div className="relative h-40 w-40 flex items-center justify-center">
                                    <svg className="w-full h-full -rotate-90">
                                        <circle
                                            cx="80" cy="80" r="70"
                                            className="fill-none stroke-zinc-900 stroke-[8px]"
                                        />
                                        <motion.circle
                                            cx="80" cy="80" r="70"
                                            className="fill-none stroke-neon-violet stroke-[8px]"
                                            strokeDasharray="440"
                                            initial={{ strokeDashoffset: 440 }}
                                            animate={{ strokeDashoffset: 440 - (440 * (sentinelStatus?.score || 0)) / 100 }}
                                            transition={{ duration: 1.5, ease: "easeOut" }}
                                            strokeLinecap="round"
                                        />
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center space-y-1">
                                        <span className="text-4xl font-black text-white leading-none">{sentinelStatus?.score || "--"}%</span>
                                        <span className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Sync Score</span>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500 border-b border-white/5 pb-3">Strategic Pivots Required:</p>
                                {sentinelStatus?.recommendations.map((rec: string, i: number) => (
                                    <div key={i} className="flex gap-4 group cursor-pointer hover:bg-white/[0.02] p-2 rounded-xl transition-all">
                                        <ChevronRight className="h-4 w-4 text-primary shrink-0 transition-transform group-hover:translate-x-1" />
                                        <p className="text-[11px] text-zinc-400 font-medium leading-relaxed">{rec}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Global Status Info */}
                        <div className="glass-card bg-indigo-500/5 border-indigo-500/10 flex items-center gap-6">
                            <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.2)]">
                                <Globe className="h-6 w-6 text-indigo-500" />
                            </div>
                            <div className="space-y-1">
                                <h4 className="text-[10px] font-black uppercase tracking-widest text-indigo-500">Regional Footprint</h4>
                                <p className="text-sm font-black text-white">Multi-Account: {empireMetrics?.account_count || 0}</p>
                            </div>
                        </div>
                    </div>

                    {/* Empire Strategy Management */}
                    <div className="lg:col-span-2 space-y-10">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="glass-card space-y-4 flex flex-col justify-between">
                                <div className="space-y-4">
                                    <div className="h-10 w-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                                        <Layers className="h-5 w-5 text-orange-500" />
                                    </div>
                                    <h3 className="font-black uppercase text-white tracking-tight">Strategy Lab</h3>
                                    <p className="text-xs text-zinc-500 leading-relaxed font-medium">Select a winning blueprint and clone it to related niches with one click.</p>
                                </div>
                                <div className="space-y-3 pt-4">
                                    <select
                                        value={cloningNiche}
                                        onChange={(e) => setCloningNiche(e.target.value)}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-[10px] font-black uppercase tracking-widest text-zinc-300 outline-none cursor-pointer hover:bg-zinc-900/50 transition-all"
                                    >
                                        {availableNiches.map((niche) => (
                                            <option key={niche} value={niche}>{niche}</option>
                                        ))}
                                        {availableNiches.length === 0 && (
                                            <option disabled>NO NICHES FOUND</option>
                                        )}
                                    </select>
                                    <button
                                        onClick={() => setIsCloneModalOpen(true)}
                                        className="w-full bg-primary hover:bg-primary/90 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]"
                                    >
                                        <Copy className="h-4 w-4" />
                                        Launch Empire Mode
                                    </button>
                                </div>
                            </div>

                            <div className="glass-card space-y-4">
                                <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                                    <TrendingUp className="h-5 w-5 text-cyan-500" />
                                </div>
                                <h3 className="font-black uppercase text-white tracking-tight">Cross-Account Velocity</h3>
                                <div className="space-y-6 pt-4">
                                    {empireMetrics?.velocity.length > 0 ? empireMetrics.velocity.map((v: any, i: number) => (
                                        <div key={i} className="space-y-2">
                                            <div className="flex justify-between text-[8px] font-black uppercase tracking-widest text-zinc-600">
                                                <span>{v.name}</span>
                                                <span className="text-emerald-500">{v.growth}</span>
                                            </div>
                                            <div className="h-1 bg-zinc-900 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-1000"
                                                    style={{ width: `${Math.min(100, Math.max(10, parseInt(v.growth) || 45))}%` }}
                                                />
                                            </div>
                                        </div>
                                    )) : (
                                        <p className="text-[10px] text-zinc-600 font-bold text-center py-4">Establish accounts to see velocity metrics.</p>
                                    )}
                                </div>
                            </div>

                            <div className="glass-card space-y-4 bg-emerald-500/5 border-emerald-500/10">
                                <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                    <TrendingUp className="h-5 w-5 text-emerald-500" />
                                </div>
                                <h3 className="font-black uppercase text-white tracking-tight">Revenue Matrix</h3>
                                <div className="space-y-4 pt-4">
                                    <div className="flex justify-between items-center">
                                        <span className="text-[10px] text-zinc-500 uppercase tracking-widest">Total Revenue</span>
                                        <span className="text-xl font-black text-neon-cyan neon-glow-cyan">${revenueReport?.total_revenue?.toFixed(2) || "0.00"}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">EPM</span>
                                        <span className="text-lg font-black text-white">${revenueReport?.epm?.toFixed(2) || "0.00"}</span>
                                    </div>
                                    {revenueReport?.by_platform && Object.entries(revenueReport.by_platform).map(([platform, amount]: [string, any]) => (
                                        <div key={platform} className="flex justify-between items-center text-[10px]">
                                            <span className="text-zinc-600 font-bold uppercase">{platform}</span>
                                            <span className="text-zinc-400 font-bold">${Number(amount).toFixed(2)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Promo Generator Section */}
                        <div className="glass-card bg-primary/5 border-primary/10 space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity)" />
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-primary/20 flex items-center justify-center border border-primary/30">
                                    <Zap className="h-6 w-6 text-primary neon-glow" />
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="font-black uppercase tracking-tight text-white">Monetization Engine</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Digital Product Promo Generator</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <p className="text-xs text-zinc-500 font-medium">Enter product name to generate a high-conversion affiliate video script.</p>
                                    <input
                                        id="promo-product"
                                        name="promo-product"
                                        type="text"
                                        placeholder="e.g. Zen Stoic Journal"
                                        value={promoProduct}
                                        onChange={(e) => setPromoProduct(e.target.value)}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-primary/50 transition-all font-bold placeholder:text-zinc-600"
                                    />
                                    <button
                                        onClick={handleGeneratePromo}
                                        disabled={isGeneratingPromo || !promoProduct}
                                        className="w-full bg-primary hover:bg-primary/90 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px] disabled:opacity-50"
                                    >
                                        {isGeneratingPromo ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                                        Generate High-ROI Promo
                                    </button>
                                </div>

                                <div className="bg-zinc-950/40 rounded-3xl border border-white/5 p-6 h-48 overflow-y-auto relative">
                                    {promoScript ? (
                                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-700">
                                            <h4 className="text-primary font-black text-xs uppercase tracking-tighter">{promoScript.title}</h4>
                                            {promoScript.segments?.map((s: any, i: number) => (
                                                <div key={i} className="text-[10px] text-zinc-400 font-medium leading-relaxed border-l border-primary/30 pl-3">
                                                    {s.text}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                                            <Search className="h-8 w-8 text-zinc-700 mb-2" />
                                            <p className="text-[9px] font-black uppercase tracking-widest text-zinc-700">Awaiting Product Intel</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Affiliate Link Manager */}
                        <div className="glass-card bg-amber-500/5 border-amber-500/10 space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity)" />
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
                                    <TrendingUp className="h-6 w-6 text-amber-500" />
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="font-black uppercase tracking-tight text-white">Affiliate Network</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Link Management & Tracking</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <p className="text-xs text-zinc-500 font-medium">Add affiliate links to auto-inject into your content.</p>
                                    <input
                                        type="text"
                                        placeholder="Product Name"
                                        value={newLink.product_name}
                                        onChange={(e) => setNewLink({ ...newLink, product_name: e.target.value })}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-amber-500/50 transition-all font-bold placeholder:text-zinc-600"
                                    />
                                    <input
                                        type="text"
                                        placeholder="Affiliate URL"
                                        value={newLink.link}
                                        onChange={(e) => setNewLink({ ...newLink, link: e.target.value })}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-amber-500/50 transition-all font-bold placeholder:text-zinc-600"
                                    />
                                    <input
                                        type="text"
                                        placeholder="CTA Text (e.g. Get 20% Off)"
                                        value={newLink.cta_text}
                                        onChange={(e) => setNewLink({ ...newLink, cta_text: e.target.value })}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-amber-500/50 transition-all font-bold placeholder:text-zinc-600"
                                    />
                                    <button
                                        onClick={handleAddAffiliateLink}
                                        disabled={isAddingLink || !newLink.product_name || !newLink.link}
                                        className="w-full bg-amber-500 hover:bg-amber-600 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px] disabled:opacity-50"
                                    >
                                        {isAddingLink ? <RefreshCw className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
                                        Add Affiliate Link
                                    </button>
                                </div>

                                <div className="bg-zinc-950/40 rounded-3xl border border-white/5 p-6 h-64 overflow-y-auto relative">
                                    {affiliateLinks.length > 0 ? (
                                        <div className="space-y-3">
                                            {affiliateLinks.map((link: any, i: number) => (
                                                <div key={link.id || i} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-1">
                                                    <p className="text-[10px] font-black text-white uppercase tracking-wider">{link.product_name}</p>
                                                    <p className="text-[9px] text-zinc-500 truncate">{link.link}</p>
                                                    {link.cta_text && <p className="text-[9px] text-amber-500 font-bold">{link.cta_text}</p>}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                                            <Search className="h-8 w-8 text-zinc-700 mb-2" />
                                            <p className="text-[9px] font-black uppercase tracking-widest text-zinc-700">No Affiliate Links</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Auto-Merch Generator */}
                        <div className="glass-card bg-purple-500/5 border-purple-500/10 space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity)" />
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-purple-500/20 flex items-center justify-center border border-purple-500/30">
                                    <ShoppingBag className="h-6 w-6 text-purple-500" />
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="font-black uppercase tracking-tight text-white">Auto-Merch Engine</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Trend-Driven Product Generation</p>
                                </div>
                            </div>
                            <div className="space-y-4">
                                <p className="text-xs text-zinc-500 font-medium">Enter a trending topic to auto-generate merchandise.</p>
                                <input
                                    type="text"
                                    placeholder="e.g. Stoic Quotes 2026"
                                    value={autoMerchTopic}
                                    onChange={(e) => setAutoMerchTopic(e.target.value)}
                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-purple-500/50 transition-all font-bold placeholder:text-zinc-600"
                                />
                                <button
                                    onClick={handleAutoMerch}
                                    disabled={isGeneratingMerch || !autoMerchTopic}
                                    className="w-full bg-purple-500 hover:bg-purple-600 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px] disabled:opacity-50"
                                >
                                    {isGeneratingMerch ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShoppingBag className="h-4 w-4" />}
                                    Generate Auto-Merch
                                </button>
                            </div>
                        </div>

                        {/* Shopify Sync */}
                        <div className="glass-card bg-green-500/5 border-green-500/10 space-y-6 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity)" />
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-green-500/20 flex items-center justify-center border border-green-500/30">
                                    <Package className="h-6 w-6 text-green-500" />
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="font-black uppercase tracking-tight text-white">Commerce Sync</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Shopify Integration</p>
                                </div>
                            </div>
                                <button
                                    onClick={() => setIsSyncModalOpen(true)}
                                    disabled={isSyncingShopify}
                                    className="w-full bg-green-500 hover:bg-green-600 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px] disabled:opacity-50"
                                >
                                    {isSyncingShopify ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                                    Sync Shopify
                                </button>
                        </div>

                        {/* AI Link Recommendations */}
                        <div className="glass-card bg-sky-500/5 border-sky-500/10 space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity)" />
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-sky-500/20 flex items-center justify-center border border-sky-500/30">
                                    <LinkIcon className="h-6 w-6 text-sky-500" />
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="font-black uppercase tracking-tight text-white">AI Link Recommender</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Smart Affiliate Suggestions</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <input
                                        type="text"
                                        placeholder="Niche (e.g. Stoic Wisdom)"
                                        value={recommendNiche}
                                        onChange={(e) => setRecommendNiche(e.target.value)}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-sky-500/50 transition-all font-bold placeholder:text-zinc-600"
                                    />
                                    <textarea
                                        placeholder="Paste your script text here..."
                                        value={recommendScript}
                                        onChange={(e) => setRecommendScript(e.target.value)}
                                        rows={4}
                                        className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-sky-500/50 transition-all font-bold placeholder:text-zinc-600 resize-none"
                                    />
                                    <button
                                        onClick={handleRecommendLinks}
                                        disabled={isRecommending || !recommendNiche || !recommendScript}
                                        className="w-full bg-sky-500 hover:bg-sky-600 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px] disabled:opacity-50"
                                    >
                                        {isRecommending ? <RefreshCw className="h-4 w-4 animate-spin" /> : <LinkIcon className="h-4 w-4" />}
                                        Get Recommendations
                                    </button>
                                </div>
                                <div className="bg-zinc-950/40 rounded-3xl border border-white/5 p-6 h-64 overflow-y-auto relative">
                                    {recommendations.length > 0 ? (
                                        <div className="space-y-3">
                                            {recommendations.map((rec: any, i: number) => (
                                                <div className="p-1 rounded-lg hover:bg-white/2 transition-colors cursor-pointer" onClick={fetchSentinel}>
                                                    <p className="text-[10px] font-black text-white uppercase tracking-wider">{rec.product_name || rec.name || `Link ${i + 1}`}</p>
                                                    <p className="text-[9px] text-zinc-500 truncate">{rec.link || rec.url}</p>
                                                    {rec.reason && <p className="text-[9px] text-sky-500 font-bold">{rec.reason}</p>}
                                                    {rec.cta_text && <p className="text-[9px] text-sky-400 font-bold">{rec.cta_text}</p>}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                                            <LinkIcon className="h-8 w-8 text-zinc-700 mb-2" />
                                            <p className="text-[9px] font-black uppercase tracking-widest text-zinc-700">Awaiting Script Analysis</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Recent Blueprint History */}
                        <div className="glass-card overflow-hidden shadow-2xl">
                            <div className="p-8 border-b border-white/5 bg-white/[0.02] flex items-center gap-4">
                                <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                    <MessageSquareQuote className="h-5 w-5 text-primary neon-glow" />
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="font-black uppercase tracking-tight text-white">Neural Repositories</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Winning Blueprint History</p>
                                </div>
                            </div>
                            <div className="p-8 space-y-4">
                                {blueprints.length > 0 ? blueprints.map((bp) => (
                                    <div
                                        key={bp.id}
                                        onClick={() => setSelectedStrategy(bp)}
                                        className={cn(
                                            "flex items-center justify-between group p-4 rounded-2xl bg-white/[0.02] border transition-all cursor-pointer",
                                            selectedStrategy?.id === bp.id ? "border-primary/50 bg-primary/5" : "border-white/5 hover:border-primary/30"
                                        )}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                "h-2 w-2 rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]",
                                                selectedStrategy?.id === bp.id ? "bg-primary" : "bg-zinc-600"
                                            )} />
                                            <div>
                                                <p className="text-[10px] font-black uppercase text-white tracking-widest leading-none mb-1">{bp.title}</p>
                                                <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-tighter">{bp.niche || "Universal Pattern"}</p>
                                            </div>
                                        </div>
                                        <div className="text-[10px] font-black text-emerald-500">{bp.performance}</div>
                                    </div>
                                )) : (
                                    <div className="text-zinc-700 font-black uppercase text-[10px] text-center py-20 tracking-[0.3em] opacity-40 uppercase">
                                        Waiting for Initial Conquests...
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Network Mesh Visualization */}
                    <div className="lg:col-span-2 space-y-10">
                        {networkData.nodes.length > 0 ? (
                            <NetworkMesh nodes={networkData.nodes} links={networkData.links} />
                        ) : (
                            <div className="glass-card p-10 text-center animate-pulse text-zinc-500 text-xs font-mono">
                                INITIALIZING NEURAL LINK...
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mt-10">
                            {/* Strategic Timeline */}
                            <div className="glass-card p-10 space-y-8">
                                <div className="space-y-1">
                                    <h3 className="font-black uppercase tracking-tight text-white">Strategic <span className="text-cyan-400">Timeline</span></h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Sentinel Drift Events</p>
                                </div>
                                <div className="space-y-6">
                                    {timelineEvents.map((item, i) => (
                                        <div key={i} className="flex gap-6 group">
                                            <div className="flex flex-col items-center gap-2">
                                                <div className="h-0.5 rounded-full bg-linear-to-r from-emerald-500/0 via-emerald-500/20 to-emerald-500/0" />
                                                <div className="h-3 w-3 rounded-full border-2 border-primary bg-zinc-950 group-hover:bg-primary transition-colors" />
                                                <div className="w-px flex-1 bg-white/5 group-last:hidden" />
                                            </div>
                                            <div className="pb-6">
                                                <p className="text-[10px] font-black text-primary mb-1 tracking-widest">{item.time_label || item.time}</p>
                                                <p className="text-white font-black uppercase text-xs mb-1">{item.type || item.event}</p>
                                                <p className="text-zinc-500 text-[10px] font-medium leading-relaxed">{item.message || item.desc}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Automation Pulse */}
                            <div className="glass-card p-10 flex flex-col justify-center bg-zinc-900 shadow-inner">
                                <div className="space-y-6 text-center">
                                    <div className="mx-auto h-20 w-20 rounded-full bg-primary/20 flex items-center justify-center relative">
                                        <div className="absolute inset-0 rounded-full border border-primary animate-ping opacity-20" />
                                        <Layers className="h-10 w-10 text-primary" />
                                    </div>
                                    <h4 className="text-2xl font-black text-white tracking-tighter uppercase">{sentinelStatus?.score || 0}% Autonomy</h4>
                                    <p className="text-zinc-500 text-xs font-medium">System is operating in <span className={`${sentinelStatus?.status === "NOMINAL" ? "text-emerald-500" : "text-amber-500"} font-bold`}>{sentinelStatus?.status || "CONNECTING"}</span> mode. {sentinelStatus?.status === "NOMINAL" ? "No manual overrides required." : "Review sentinel recommendations."}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Confirmation Modals */}
            <ConfirmModal
                isOpen={isCloneModalOpen}
                onClose={() => setIsCloneModalOpen(false)}
                onConfirm={() => {
                    handleClone();
                    setIsCloneModalOpen(false);
                }}
                title="Initialize Empire Mode?"
                description={`This will replicate the neural weights and monetization strategies from ${selectedStrategy?.niche || "Original"} to ${cloningNiche}. This is a non-reversible strategic expansion.`}
                confirmText="Execute Expansion"
                variant="primary"
            />

            <ConfirmModal
                isOpen={isSyncModalOpen}
                onClose={() => setIsSyncModalOpen(false)}
                onConfirm={() => {
                    handleShopifySync();
                    setIsSyncModalOpen(false);
                }}
                title="Sync Shopify Node?"
                description="Synchronizing commerce data will overwrite local cache with live storefront telemetry. Ensure your API connection is stable."
                confirmText="Sync Now"
                variant="success"
            />
        </DashboardLayout>
    );
}

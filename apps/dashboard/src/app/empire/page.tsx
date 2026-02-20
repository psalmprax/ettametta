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
    MessageSquareQuote
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import dynamic from "next/dynamic";

const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });

export default function EmpirePage() {
    const [sentinelStatus, setSentinelStatus] = useState<any>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [selectedStrategy, setSelectedStrategy] = useState<any>(null);
    const [cloningNiche, setCloningNiche] = useState("Stoic Wisdom");
    const [promoProduct, setPromoProduct] = useState("");
    const [isGeneratingPromo, setIsGeneratingPromo] = useState(false);
    const [promoScript, setPromoScript] = useState<any>(null);

    const fetchSentinel = async () => {
        setIsRefreshing(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/sentinel/status`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSentinelStatus(data);
            }
        } catch (err) {
            console.error(err);
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
        setIsRefreshing(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/monetization/empire/clone`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    source_niche: selectedStrategy?.niche || "Stoic Wisdom",
                    target_niche: cloningNiche
                })
            });
            if (res.ok) {
                alert(`SUCCESS: Strategy cloned to ${cloningNiche} niche.`);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsRefreshing(false);
        }
    };

    const fetchEmpireMetrics = async () => {
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/monetization/empire/metrics`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setEmpireMetrics(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchBlueprints = async () => {
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/monetization/empire/blueprints`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setBlueprints(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchSentinel();
        fetchEmpireMetrics();
        fetchBlueprints();
    }, []);

    const handleGeneratePromo = async () => {
        if (!promoProduct) return;
        setIsGeneratingPromo(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/monetization/promo/generate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ product_name: promoProduct, niche: cloningNiche })
            });
            if (res.ok) {
                const data = await res.json();
                setPromoScript(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsGeneratingPromo(false);
        }
    };

    const [networkData, setNetworkData] = useState<any>({ nodes: [], links: [] });

    const fetchNetwork = async () => {
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/monetization/empire/network`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setNetworkData(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchNetwork();
    }, []);

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-end justify-between">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Empire Protocol</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter italic uppercase text-white leading-none">Command <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-amber-600 text-hollow">Center</span></h1>
                        <p className="text-zinc-500 font-medium">Managing multi-account <span className="text-zinc-300 font-bold">global scaling</span> and algorithm synchronization.</p>
                    </div>
                    <button
                        onClick={fetchSentinel}
                        disabled={isRefreshing}
                        className="glass-card px-6 py-4 rounded-xl flex items-center gap-3 group hover:border-primary/50 transition-all font-black uppercase tracking-widest text-[10px]"
                    >
                        <RefreshCw className={cn("h-4 w-4 text-zinc-500 group-hover:text-primary transition-colors", isRefreshing && "animate-spin")} />
                        <span className="text-zinc-500 group-hover:text-white">Sync Sentinel</span>
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Algorithm Sentinel Monitor */}
                    <div className="space-y-8">
                        <div className="glass-card space-y-8 relative overflow-hidden h-fit">
                            <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                            <div className="flex items-center justify-between">
                                <div className="space-y-1">
                                    <h3 className="font-black uppercase tracking-tight text-white">Algorithm Sentinel</h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Platform Drift Analyzer</p>
                                </div>
                                <div className={cn(
                                    "px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-widest",
                                    sentinelStatus?.status === "NOMINAL" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500" : "bg-amber-500/10 border-amber-500/30 text-amber-500"
                                )}>
                                    {sentinelStatus?.status || "SYNCING..."}
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
                                            className="fill-none stroke-primary stroke-[8px]"
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
                                        <option>Stoic Wisdom</option>
                                        <option>Billionaire Mindset</option>
                                        <option>AI Productivity</option>
                                        <option>Historical Facts</option>
                                    </select>
                                    <button
                                        onClick={handleClone}
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
                                                    style={{ width: `${v.score}%` }}
                                                />
                                            </div>
                                        </div>
                                    )) : (
                                        <p className="text-[10px] text-zinc-600 font-bold text-center py-4">Establish accounts to see velocity metrics.</p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Promo Generator Section */}
                        <div className="glass-card bg-primary/5 border-primary/10 space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)]" />
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
                                    <h3 className="font-black uppercase tracking-tight text-white italic">Strategic <span className="text-cyan-400">Timeline</span></h3>
                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Sentinel Drift Events</p>
                                </div>
                                <div className="space-y-6">
                                    {[
                                        { time: "02:45", event: "Algorithm Shift Detected", desc: "TikTok hook retention metrics updated globally." },
                                        { time: "01:20", event: "Node Expansion", desc: "Cloned 'Stoic Wisdom' strategy to 4 new regional accounts." },
                                        { time: "22:10", event: "Sentinel Correction", desc: "Auto-adjusted caption density for viral optimization." }
                                    ].map((item, i) => (
                                        <div key={i} className="flex gap-6 group">
                                            <div className="flex flex-col items-center gap-2">
                                                <div className="h-3 w-3 rounded-full border-2 border-primary bg-zinc-950 group-hover:bg-primary transition-colors" />
                                                <div className="w-px flex-1 bg-white/5 group-last:hidden" />
                                            </div>
                                            <div className="pb-6">
                                                <p className="text-[10px] font-black text-primary mb-1 tracking-widest">{item.time} ZULU</p>
                                                <p className="text-white font-black uppercase text-xs mb-1">{item.event}</p>
                                                <p className="text-zinc-500 text-[10px] font-medium leading-relaxed">{item.desc}</p>
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
                                    <h4 className="text-2xl font-black text-white italic tracking-tighter uppercase">98% Autonomy</h4>
                                    <p className="text-zinc-500 text-xs font-medium">System is operating in <span className="text-emerald-500 font-bold italic">FULL_AUTO</span> mode. No manual overrides required.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

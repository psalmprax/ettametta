"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
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
    Package,
    Trash2,
    Share2,
    Database,
    Network,
    Terminal,
    Target,
    Dna,
    Radar,
    ShieldCheck as ShieldCheckIcon,
    Database as DatabaseIcon,
    Terminal as TerminalIcon,
    ShoppingBag as ShoppingBagIcon
} from "lucide-react";
import { toast } from "sonner";
import { useTelemetry } from "@/context/TelemetryContext";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });
import { ConfirmModal } from "@/components/ui/ConfirmModal";

function EmpireContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents: telemetryAgents, logs: systemLogs, status, pulse } = useTelemetry();
    
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "registry");
    const [networkData, setNetworkData] = useState<any>({ nodes: [], links: [] });
    const [blueprints, setBlueprints] = useState<any[]>([]);
    const [revenueReport, setRevenueReport] = useState<any>(null);
    const [sentinelStatus, setSentinelStatus] = useState<any>(null);
    const [availableNiches, setAvailableNiches] = useState<string[]>([]);
    const [cloningNiche, setCloningNiche] = useState("");
    const [isCloneModalOpen, setIsCloneModalOpen] = useState(false);
    const [affiliateLinks, setAffiliateLinks] = useState<any[]>([]);
    const [commerceStatus, setCommerceStatus] = useState<any>(null);
    const [actionLogs, setActionLogs] = useState<string[]>(["EMPIRE_INITIALIZED", "SYNCHRONIZING_GLOBAL_NODES"]);

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
    }, [searchParams]);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback<any>(
                () => fetch(`${API_BASE}/no-face/sentinel/status`, { headers }),
                { fallback: null, onSuccess: (data) => setSentinelStatus(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/monetization/empire/blueprints`, { headers }),
                { 
                    fallback: { blueprints: [] }, 
                    onSuccess: (data) => {
                        const list = Array.isArray(data) ? data : (data?.blueprints || []);
                        setBlueprints(list);
                    } 
                }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/monetization/report`, { headers }),
                { fallback: null, onSuccess: (data) => setRevenueReport(data) }
            ),
            withRealFallback<any[]>(
                () => fetch(`${API_BASE}/discovery/niches`, { headers }),
                { 
                    fallback: [], 
                    onSuccess: (data) => {
                        if (Array.isArray(data) && data.length > 0) {
                            const nicheNames = data.map(n => typeof n === 'string' ? n : (n.niche || 'General'));
                            setAvailableNiches(nicheNames);
                        }
                    } 
                }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/monetization/empire/network`, { headers }),
                { fallback: { nodes: [], links: [] }, onSuccess: (data) => setNetworkData(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/monetization/links`, { headers }),
                { fallback: { links: [] }, onSuccess: (data) => setAffiliateLinks(Array.isArray(data.links) ? data.links : []) }
            )
        ]);
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleClone = async () => {
        if (!cloningNiche) return;
        setActionLogs((prev: string[]) => [`[PROTOCOL] Initializing Strategic Clone: ${cloningNiche}`, ...prev]);
        await withRealFallback(
            async () => {
                const token = await getAuthToken();
                if (!token) return;
                return fetch(`${API_BASE}/monetization/empire/clone`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                    body: JSON.stringify({ source_niche: "Motivation", target_niche: cloningNiche, auto_publish: true })
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Strategy Cloned");
                    setActionLogs((prev: string[]) => [`[SUCCESS] Neural weights mapped to ${cloningNiche}`, ...prev]);
                    setIsCloneModalOpen(false);
                }
            }
        );
    };

    // Merge system logs and action logs for display
    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "EMPIRE",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...(Array.isArray(systemLogs) ? systemLogs : [])
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

    return (
        <CommandCenterLayout
            title="EMPIRE REGISTRY"
            subtitle="STRATEGIC_MONETIZATION_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "registry", label: "Empire Registry", icon: DatabaseIcon },
                        { id: "sentinel", label: "Algo Sentinel", icon: ShieldCheckIcon },
                        { id: "monetization", label: "Promo Hub", icon: Zap },
                        { id: "commerce", label: "Commerce Matrix", icon: ShoppingBagIcon },
                        { id: "logs", label: "Registry Logs", icon: TerminalIcon },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                setActiveEngine(item.id);
                                router.replace(`/empire?engine=${item.id}`);
                            }}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-amber-500/10 text-amber-500 border border-amber-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={telemetryAgents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Revenue Pulse</h4>
                        <div className="flex flex-col">
                            <span className="text-2xl font-bold text-white">${revenueReport?.total_revenue?.toFixed(2) || "0.00"}</span>
                            <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-widest">+8.4% Velocity</span>
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "registry" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex-1 min-h-[400px] bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden relative">
                                    <div className="absolute inset-0">
                                        <NetworkMesh nodes={networkData?.nodes || []} links={networkData?.links || []} />
                                    </div>
                                    <div className="absolute top-8 left-8 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-sm">
                                        <h4 className="text-white font-bold uppercase tracking-widest text-xs">Neural Strategy Mesh</h4>
                                        <p className="text-zinc-500 text-[10px] leading-relaxed italic">Visualizing cross-pollination of winning narrative patterns.</p>
                                    </div>
                                    <div className="absolute top-8 right-8 flex gap-4">
                                        <select
                                            value={cloningNiche}
                                            onChange={(e) => setCloningNiche(e.target.value)}
                                            className="bg-black/60 backdrop-blur-xl border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-white outline-none"
                                        >
                                            <option value="">SELECT_NICHE</option>
                                            {Array.isArray(availableNiches) && availableNiches.map(n => <option key={n} value={n}>{n}</option>)}
                                        </select>
                                        <Button onClick={() => setIsCloneModalOpen(true)} className="bg-amber-500 text-black font-bold h-10 px-6 rounded-xl">Clone Protocol</Button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 shrink-0 overflow-x-auto p-1">
                                    {Array.isArray(blueprints) && blueprints.map((blueprint) => (
                                        <DesignCard
                                            key={blueprint.id || blueprint.niche}
                                            title={blueprint.name || blueprint.niche}
                                            status={blueprint.status || "ACTIVE"}
                                            metrics={[
                                                { label: "Success", value: `${((blueprint.avg_score || 0) * 100).toFixed(1)}%`, progress: (blueprint.avg_score || 0) * 100, color: "text-emerald-400" },
                                                { label: "Reach", value: blueprint.total_views ? `${(blueprint.total_views / 1000).toFixed(0)}K` : "---", color: "text-cyan-400" }
                                            ]}
                                            footerInfo={`ID: ${(blueprint.id || blueprint.niche).slice(0, 8)}`}
                                            toolsStatus="Synced"
                                            credits={pulse?.credits || 0}
                                            onRefresh={() => {
                                                setActionLogs(prev => [`[SYSTEM] Refreshing ${blueprint.niche} blueprint...`, ...prev]);
                                                fetchData();
                                                toast.info(`Refreshing ${blueprint.niche} metrics...`);
                                            }}
                                            onMore={() => {
                                                setActionLogs(prev => [`[INSPECT] Opening Deep Diagnostics for ${blueprint.niche}`, ...prev]);
                                                toast.info(`Inspecting strategy: ${blueprint.niche}`);
                                            }}
                                            onDelete={() => {
                                                setBlueprints(prev => prev.filter(b => b.id !== blueprint.id));
                                                setActionLogs(prev => [`[WARNING] Blueprint Purged: ${blueprint.niche}`, ...prev]);
                                                toast.error(`Purged Blueprint: ${blueprint.niche}`);
                                            }}
                                            onShare={() => {
                                                navigator.clipboard.writeText(`https://ettametta.ai/strategy/${blueprint.id || blueprint.niche}`);
                                                toast.success("Strategy Blueprint Link Copied");
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {activeEngine === "sentinel" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                <DesignCard
                                    title="Algorithm Sentinel"
                                    status={sentinelStatus?.status || "NOMINAL"}
                                    metrics={[
                                        { label: "Sync Score", value: `${sentinelStatus?.score || 0}%`, progress: sentinelStatus?.score || 0, color: "text-violet-400" },
                                        { label: "Platform Drift", value: "Minimal", color: "text-cyan-400" }
                                    ]}
                                    footerInfo="SCANNING: GLOBAL_ALGO_MATRIX"
                                    toolsStatus="Active"
                                    credits={pulse?.credits || 0}
                                    onRefresh={() => {
                                        fetchData();
                                        toast.info("Resyncing Algorithm Sentinel...");
                                    }}
                                    onMore={() => {
                                        toast.promise(fetchData(), {
                                            loading: 'Accessing Deep Diagnostics...',
                                            success: 'Sentinel Diagnostics Fetched',
                                            error: 'Failed to access neural core'
                                        });
                                    }}
                                    onShare={() => {
                                        navigator.clipboard.writeText(`https://ettametta.ai/sentinel/status`);
                                        toast.success("Sentinel Data Shared");
                                    }}
                                    onDelete={() => {
                                        toast.error("Security Protocol: System Core Protection Active. Deletion restricted.");
                                    }}
                                />
                                <div className="lg:col-span-2 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                        <ShieldCheck className="h-5 w-5 text-violet-400" />
                                        Strategic Intelligence
                                    </h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        {Array.isArray(sentinelStatus?.recommendations) && sentinelStatus.recommendations.map((rec: string, i: number) => (
                                            <div key={i} className="p-5 bg-white/5 border border-white/5 rounded-2xl flex items-center gap-4 group hover:border-violet-500/30 transition-all">
                                                <Target className="h-4 w-4 text-violet-400 shrink-0" />
                                                <p className="text-xs text-zinc-400 font-medium leading-relaxed">{rec}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "monetization" && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full min-h-0">
                                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col min-h-0">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                            <Zap className="h-5 w-5 text-amber-500" />
                                            Affiliate Registry
                                        </h3>
                                        <Button className="h-8 px-4 text-[10px] bg-white/5 hover:bg-white/10 text-white rounded-lg border border-white/10 uppercase tracking-widest font-bold">Add Link</Button>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
                                        {affiliateLinks.map((link, i) => (
                                            <div key={link.id || i} className="p-6 bg-white/5 border border-white/5 rounded-[24px] group hover:border-amber-500/30 transition-all flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="h-12 w-12 rounded-2xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                                        <LinkIcon className="h-5 w-5 text-amber-500" />
                                                    </div>
                                                    <div>
                                                        <h4 className="text-sm font-bold text-white">{link.product_name}</h4>
                                                        <p className="text-[10px] text-zinc-500 font-medium">Niche: {link.niche}</p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-sm font-bold text-white">${link.commission || "0.00"}</div>
                                                    <div className="text-[10px] text-emerald-500 font-bold tracking-widest uppercase">{link.conversion_rate || "0.0"}% CR</div>
                                                </div>
                                            </div>
                                        ))}
                                        {affiliateLinks.length === 0 && (
                                            <div className="flex flex-col items-center justify-center py-20 opacity-20 gap-4">
                                                <LinkIcon className="h-12 w-12" />
                                                <p className="text-[10px] font-bold uppercase tracking-widest">No Active Links Found</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                
                                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col min-h-0">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                        <MessageSquareQuote className="h-5 w-5 text-cyan-400" />
                                        Promo Generator
                                    </h3>
                                    <div className="flex-1 space-y-6">
                                        <div className="space-y-4">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Select Target Link</label>
                                            <select className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-xs font-bold text-white outline-none">
                                                <option>Product_1 Special</option>
                                                <option>Product_2 Special</option>
                                            </select>
                                        </div>
                                        <div className="space-y-4">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Context Script</label>
                                            <textarea 
                                                className="w-full h-40 bg-white/5 border border-white/10 rounded-[24px] px-6 py-6 text-xs font-medium text-zinc-300 outline-none resize-none"
                                                placeholder="Paste your video script here to optimize the call-to-action..."
                                            />
                                        </div>
                                        <Button className="w-full h-14 bg-amber-500 text-black font-bold rounded-2xl uppercase tracking-widest text-xs hover:shadow-[0_0_20px_rgba(245,158,11,0.3)] transition-all">Generate Optimized CTA</Button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "commerce" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-lg font-bold text-white flex items-center gap-3">
                                            <ShoppingBagIcon className="h-5 w-5 text-emerald-400" />
                                            Store Sync
                                        </h3>
                                        <div className={cn("h-2 w-2 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)]", commerceStatus?.status === "success" ? "bg-emerald-500" : "bg-zinc-700")} />
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-zinc-500 uppercase font-bold tracking-widest text-[9px]">Platform</span>
                                            <span className="text-white font-bold">{commerceStatus?.source || "None"}</span>
                                        </div>
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-zinc-500 uppercase font-bold tracking-widest text-[9px]">Status</span>
                                            <span className="text-white font-bold">{commerceStatus?.status || "Awaiting Sync"}</span>
                                        </div>
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-zinc-500 uppercase font-bold tracking-widest text-[9px]">Products</span>
                                            <span className="text-white font-bold">{commerceStatus?.sample_count || 0}</span>
                                        </div>
                                    </div>
                                    <Button 
                                        onClick={async () => {
                                            const token = await getAuthToken();
                                            if (!token) return;
                                            toast.info("Initializing Commerce Sync...");
                                            await withRealFallback(
                                                () => fetch(`${API_BASE}/monetization/commerce/sync?niche=General`, { 
                                                    method: "POST",
                                                    headers: { Authorization: `Bearer ${token}` }
                                                }),
                                                {
                                                    fallback: null,
                                                    onSuccess: (data) => {
                                                        setCommerceStatus(data);
                                                        toast.success("Store Synchronized");
                                                    }
                                                }
                                            );
                                        }}
                                        className="w-full h-12 bg-white/5 hover:bg-white/10 text-white rounded-xl border border-white/10 uppercase tracking-widest text-[10px] font-bold"
                                    >
                                        Manual Refresh
                                    </Button>
                                </div>

                                <div className="xl:col-span-2 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-lg font-bold text-white flex items-center gap-3">
                                            <Package className="h-5 w-5 text-indigo-400" />
                                            Reverse Monetization
                                        </h3>
                                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Trend {"->"} Merch</span>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div className="space-y-4">
                                            <div className="aspect-square rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center relative group overflow-hidden">
                                                <RefreshCw className="h-8 w-8 text-zinc-700 group-hover:rotate-180 transition-all duration-700" />
                                                <div className="absolute inset-x-0 bottom-0 p-4 bg-linear-to-t from-black/80 to-transparent">
                                                    <p className="text-[10px] text-white font-bold text-center">Awaiting Trend Detection...</p>
                                                </div>
                                            </div>
                                            <Button className="w-full h-12 bg-indigo-500 text-white font-bold rounded-xl uppercase tracking-widest text-[10px] hover:shadow-[0_0_20px_rgba(99,102,241,0.3)]">Scan Viral Design Opportunity</Button>
                                        </div>
                                        <div className="space-y-6">
                                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5 space-y-2">
                                                <h5 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Design Logic</h5>
                                                <p className="text-xs text-zinc-300 leading-relaxed italic">"Identify high-engagement typography from Motivation niche and map to heavyweight hoodies."</p>
                                            </div>
                                            <div className="space-y-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-1.5 w-1.5 rounded-full bg-zinc-700" />
                                                    <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Auto-Design Neural Model</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="h-1.5 w-1.5 rounded-full bg-zinc-700" />
                                                    <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Print-on-Demand Egress</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <TerminalIcon className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Strategic Event Horizon</h3>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-[9px] font-bold text-emerald-500 uppercase">Observer_Active</span>
                                        </div>
                                        <Button className="h-8 w-8 p-0 flex items-center justify-center bg-white/5 hover:bg-rose-500/20 text-zinc-500 hover:text-rose-500 rounded-lg transition-all">
                                            <Trash2 className="h-3.5 w-3.5" />
                                        </Button>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {displayLogs.map((log: any, i: number) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                "shrink-0 font-bold tracking-widest uppercase text-[9px] px-2 py-0.5 rounded",
                                                log.level === "ACTION" ? "bg-cyan-500/10 text-cyan-500" :
                                                log.level === "ERROR" ? "bg-rose-500/10 text-rose-500" :
                                                log.level === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" : "bg-white/5 text-zinc-500"
                                            )}>
                                                {log.level || "INFO"}
                                            </span>
                                            <span className={cn(
                                                "leading-relaxed",
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-400"
                                            )}>
                                                <span className="text-zinc-600">[{log.module || "SYSTEM"}]</span> {log.message}
                                            </span>
                                        </div>
                                    ))}
                                    <div className="h-4" />
                                </div>
                            </div>
                        )}

                        {activeEngine === "registry" && (
                            <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Registry Logs</span>
                                    <span className="text-[8px] font-mono text-amber-500/50">{status === "open" ? "LIVE_SYNC" : "OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                    {Array.isArray(displayLogs) && displayLogs.slice(0, 15).map((log: any, i: number) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-600"
                                            )}>
                                                {log.module ? `[${log.module}] ` : ""}{log.message}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>

            <ConfirmModal
                isOpen={isCloneModalOpen}
                onClose={() => setIsCloneModalOpen(false)}
                onConfirm={handleClone}
                title="Initialize Empire Protocol?"
                description={`Cloning neural strategy weights into the "${cloningNiche}" cluster will initiate autonomous synthesis. Proceed?`}
                confirmText="Execute Protocol"
                variant="primary"
            />
        </CommandCenterLayout>
    );
}

export default function EmpirePage() {
    return (
        <Suspense fallback={null}>
            <EmpireContent />
        </Suspense>
    );
}

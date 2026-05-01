"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
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
    Radar
} from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import dynamic from "next/dynamic";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });
import { ConfirmModal } from "@/components/ui/ConfirmModal";

export default function EmpirePage() {
    const [activeEngine, setActiveEngine] = useState("registry");
    const [sentinelStatus, setSentinelStatus] = useState<any>(null);
    const [cloningNiche, setCloningNiche] = useState("");
    const [promoProduct, setPromoProduct] = useState("");
    const [isGeneratingPromo, setIsGeneratingPromo] = useState(false);
    const [promoScript, setPromoScript] = useState<any>(null);
    const [affiliateLinks, setAffiliateLinks] = useState<any[]>([]);
    const [revenueReport, setRevenueReport] = useState<any>(null);
    const [availableNiches, setAvailableNiches] = useState<string[]>([]);
    const [blueprints, setBlueprints] = useState<any[]>([]);
    const [networkData, setNetworkData] = useState<any>({ nodes: [], links: [] });
    const [isCloneModalOpen, setIsCloneModalOpen] = useState(false);
    const [isSyncingShopify, setIsSyncingShopify] = useState(false);
    const [logs, setLogs] = useState<string[]>(["EMPIRE_INITIALIZED", "SYNCHRONIZING_GLOBAL_NODES"]);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback<any>(
                () => fetch(`${API_BASE}/no-face/sentinel/status`, { headers }),
                { fallback: null, onSuccess: (data) => setSentinelStatus(data) }
            ),
            withRealFallback<any[]>(
                () => fetch(`${API_BASE}/monetization/empire/blueprints`, { headers }),
                { fallback: [], onSuccess: (data) => setBlueprints(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/monetization/report`, { headers }),
                { fallback: null, onSuccess: (data) => setRevenueReport(data) }
            ),
            withRealFallback<string[]>(
                () => fetch(`${API_BASE}/discovery/niches`, { headers }),
                { fallback: [], onSuccess: (data) => setAvailableNiches(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/monetization/empire/network`, { headers }),
                { fallback: { nodes: [], links: [] }, onSuccess: (data) => setNetworkData(data) }
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
        setLogs((prev: string[]) => [`[PROTOCOL] Initializing Strategic Clone: ${cloningNiche}`, ...prev]);
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
                    setLogs((prev: string[]) => [`[SUCCESS] Neural weights mapped to ${cloningNiche}`, ...prev]);
                    setIsCloneModalOpen(false);
                }
            }
        );
    };

    // Prepare Agent Data
    const agents = [
        { id: "STRAT_01", name: "Yield Optimizer", icon: Zap, status: "ACTIVE" as any, latency: 12, load: 5, details: "Optimizing CPC" },
        { id: "SENT_01", name: "Algo Sentinel", icon: ShieldCheck, status: "ACTIVE" as any, latency: 85, load: 12, details: "Scanning Platform Drift" },
        { id: "CLONE_01", name: "Neural Cloner", icon: Copy, status: "IDLE" as any, latency: 1, load: 0, details: "Standby" },
    ];

    return (
        <CommandCenterLayout
            title="EMPIRE REGISTRY"
            subtitle="STRATEGIC_MONETIZATION_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "registry", label: "Empire Registry", icon: Database },
                        { id: "sentinel", label: "Algo Sentinel", icon: ShieldCheck },
                        { id: "monetization", label: "Promo Hub", icon: Zap },
                        { id: "commerce", label: "Commerce Matrix", icon: ShoppingBag },
                        { id: "logs", label: "Registry Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
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
                    <AgentMatrix agents={agents} />
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
                                        <NetworkMesh nodes={networkData.nodes} links={networkData.links} />
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
                                            {availableNiches.map(n => <option key={n} value={n}>{n}</option>)}
                                        </select>
                                        <Button onClick={() => setIsCloneModalOpen(true)} className="bg-amber-500 text-black font-bold h-10 px-6 rounded-xl">Clone Protocol</Button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 shrink-0 overflow-x-auto p-1">
                                    {blueprints.map((blueprint) => (
                                        <DesignCard
                                            key={blueprint.id}
                                            title={blueprint.name}
                                            status={blueprint.status}
                                            metrics={[
                                                { label: "Success", value: `${(blueprint.avg_score * 100).toFixed(1)}%`, progress: blueprint.avg_score * 100, color: "text-emerald-400" },
                                                { label: "Reach", value: "840K", color: "text-cyan-400" }
                                            ]}
                                            footerInfo={`ID: ${blueprint.id.slice(0, 8)}`}
                                            toolsStatus="Synced"
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
                                />
                                <div className="lg:col-span-2 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                        <ShieldCheck className="h-5 w-5 text-violet-400" />
                                        Strategic Intelligence
                                    </h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        {sentinelStatus?.recommendations?.map((rec: string, i: number) => (
                                            <div key={i} className="p-5 bg-white/5 border border-white/5 rounded-2xl flex items-center gap-4 group hover:border-violet-500/30 transition-all">
                                                <Target className="h-4 w-4 text-violet-400 shrink-0" />
                                                <p className="text-xs text-zinc-400 font-medium leading-relaxed">{rec}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Registry Logs</span>
                                <span className="text-[8px] font-mono text-amber-500/50">EMPIRE_MATRIX_ACTIVE</span>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[PROTOCOL]") ? "text-cyan-400" :
                                            log.includes("[SUCCESS]") ? "text-emerald-500" : "text-zinc-600"
                                        )}>{log}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
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

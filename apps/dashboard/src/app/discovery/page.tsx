"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef, Suspense } from "react";
import dynamic from "next/dynamic";
import { 
    Search, 
    Activity, 
    Zap, 
    TrendingUp, 
    Globe, 
    ShieldAlert, 
    Cpu,
    ArrowUpRight,
    Play,
    BarChart3,
    RefreshCw,
    Network,
    Target,
    Radar,
    Loader2,
    Terminal
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

const Geomap = dynamic(() => import("@/components/ui/Geomap"), { ssr: false });
const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });

interface ContentCandidate {
    id: string;
    platform: string;
    category: string;
    title: string;
    viral_score: number;
    view_count: number;
    creator_name: string;
}

function DiscoveryContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents, logs: systemLogs, pulse } = useTelemetry();
    
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "trends");
    const [candidates, setCandidates] = useState<ContentCandidate[]>([]);
    const [activeNiche, setActiveNiche] = useState(searchParams.get("q") || "Motivation");
    const [actionLogs, setActionLogs] = useState<string[]>([]);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [intelData, setIntelData] = useState<any>(null);

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
    }, [searchParams]);

    const fetchTrends = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        setActionLogs((prev: string[]) => [`[SCAN] Initiating Trend Analysis: ${activeNiche}`, ...prev]);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/discovery/trends?niche=${encodeURIComponent(activeNiche)}`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (data) => {
                    const trends = Array.isArray(data) ? data : (data?.trends || []);
                    setCandidates(trends);
                    setActionLogs((prev: string[]) => [`[SUCCESS] Found ${trends.length} Viral Candidates.`, ...prev]);
                }
            }
        );
    }, [activeNiche]);

    const fetchAlerts = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any[]>(
            () => fetch(`${API_BASE}/discovery/alerts`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (data) => setAlerts(data)
            }
        );
    }, []);

    const fetchIntel = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/discovery/insights/${encodeURIComponent(activeNiche)}`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => setIntelData(data)
            }
        );
    }, [activeNiche]);

    useEffect(() => {
        fetchTrends();
    }, [fetchTrends]);

    useEffect(() => {
        if (activeEngine === "alerts") fetchAlerts();
        if (activeEngine === "intel") fetchIntel();
    }, [activeEngine, fetchAlerts, fetchIntel]);

    // Merge system logs and action logs for display
    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "DISCOVERY",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...systemLogs
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

    // Derive map points from candidates
    const mapPoints = useMemo(() => {
        return candidates.map(c => ({
            id: c.id,
            lat: (Math.random() - 0.5) * 120,
            lng: (Math.random() - 0.5) * 240,
            intensity: c.viral_score / 100,
            label: c.title
        }));
    }, [candidates]);

    // Mock network data for intel view
    const networkData = useMemo(() => ({
        nodes: [
            { id: "root", group: 1, label: activeNiche },
            ...candidates.slice(0, 5).map(c => ({ id: c.id, group: 2, label: c.title }))
        ],
        links: candidates.slice(0, 5).map(c => ({ source: "root", target: c.id, value: 1 }))
    }), [activeNiche, candidates]);

    return (
        <CommandCenterLayout
            title="VIRAL INTELLIGENCE"
            subtitle="GLOBAL_DISCOVERY_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "trends", label: "Viral Trends", icon: TrendingUp },
                        { id: "intel", label: "Niche Intel", icon: Cpu },
                        { id: "alerts", label: "Neural Alerts", icon: ShieldAlert },
                        { id: "hotspots", label: "Hotspots", icon: Globe },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                setActiveEngine(item.id);
                                // Sync URL for sidebar consistency
                                router.replace(`/discovery?engine=${item.id}`);
                            }}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-primary/10 text-primary border border-primary/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(var(--primary-rgb),0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Scanner Metrics</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Candidates</span>
                                <span className="text-xl font-bold text-white">{pulse?.real_stats?.total_discovered || candidates.length}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Active Jobs</span>
                                <span className="text-xl font-bold text-rose-500">{pulse?.real_stats?.active_jobs || 0}</span>
                            </div>
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "trends" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex items-center gap-6 shrink-0">
                                    <div className="relative flex-1">
                                        <input
                                            type="text"
                                            placeholder="SCAN_NICHE_FOR_VIRALITY..."
                                            value={activeNiche}
                                            onChange={(e) => setActiveNiche(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && fetchTrends()}
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 pl-14 text-white font-mono text-lg focus:outline-none focus:border-primary/50"
                                        />
                                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
                                    </div>
                                    <Button onClick={fetchTrends} className="h-20 px-10 bg-primary text-black font-bold text-lg rounded-2xl uppercase tracking-widest">
                                        Initiate Scan
                                    </Button>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 overflow-y-auto custom-scrollbar p-1">
                                    {candidates.map((c, i) => (
                                        <DesignCard
                                            key={c.id}
                                            title={c.title}
                                            status="Viral"
                                            metrics={[
                                                { label: "Viral Score", value: `${c.viral_score}%`, progress: c.viral_score, color: "text-emerald-400" },
                                                { label: "Views", value: `${(c.view_count / 1000).toFixed(1)}K`, color: "text-cyan-400" }
                                            ]}
                                            footerInfo={`${c.platform.toUpperCase()} • ${c.creator_name}`}
                                            toolsStatus="Live"
                                            onClick={() => router.push(`/creation?seed=${encodeURIComponent(c.title)}`)}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {activeEngine === "intel" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-12 flex flex-col gap-8">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Niche Intelligence: {activeNiche}</h3>
                                    <div className="px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-widest">Live Analysis Active</div>
                                </div>
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 flex-1 min-h-0">
                                    <div className="rounded-2xl bg-white/5 border border-white/5 p-8 overflow-hidden relative">
                                        <NetworkMesh nodes={networkData.nodes} links={networkData.links} />
                                        <div className="absolute inset-0 bg-linear-to-t from-[#0F0F11] via-transparent to-transparent" />
                                        <div className="absolute bottom-8 left-8 right-8 space-y-4">
                                            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Growth Vector Analysis</h4>
                                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                <motion.div initial={{ width: 0 }} animate={{ width: "75%" }} className="h-full bg-primary" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-6 overflow-y-auto custom-scrollbar pr-4">
                                        {intelData?.insights?.map((insight: any, i: number) => (
                                            <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] font-bold text-primary uppercase tracking-widest">{insight.type}</span>
                                                    <span className="text-[10px] font-mono text-zinc-500">{insight.confidence}% CONF</span>
                                                </div>
                                                <p className="text-sm text-zinc-300 leading-relaxed">{insight.message}</p>
                                            </div>
                                        )) || (
                                            <div className="h-full flex flex-col items-center justify-center opacity-20 gap-4">
                                                <Radar className="h-12 w-12" />
                                                <span className="text-xs font-bold uppercase tracking-[0.4em]">Scanning Neural Patterns...</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "alerts" && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                                {alerts.map((alert, i) => (
                                    <div key={i} className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col justify-between group hover:border-primary/20 transition-all">
                                        <div className="space-y-6">
                                            <div className="flex items-center justify-between">
                                                <div className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                                                    <ShieldAlert className="h-5 w-5 text-primary" />
                                                </div>
                                                <span className="text-[10px] font-mono text-zinc-600 uppercase">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                                            </div>
                                            <div className="space-y-2">
                                                <h4 className="text-lg font-bold text-white uppercase tracking-tight">{alert.title}</h4>
                                                <p className="text-xs text-zinc-500 leading-relaxed">{alert.description}</p>
                                            </div>
                                        </div>
                                        <div className="mt-8 flex items-center justify-between">
                                            <div className="flex gap-2">
                                                {alert.tags?.map((tag: string) => (
                                                    <span key={tag} className="px-3 py-1 rounded-full bg-white/5 text-[8px] font-bold text-zinc-400 uppercase">{tag}</span>
                                                ))}
                                            </div>
                                            <Button variant="outline" className="h-10 border-white/10 text-white text-[10px] uppercase font-bold group-hover:bg-primary group-hover:text-black">Investigate</Button>
                                        </div>
                                    </div>
                                ))}
                                {alerts.length === 0 && (
                                    <div className="col-span-2 h-full flex flex-col items-center justify-center opacity-10 gap-6">
                                        <ShieldAlert className="h-24 w-24" />
                                        <span className="text-xl font-black uppercase tracking-[1em]">Scanning for Outbreaks</span>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "hotspots" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative">
                                <Geomap points={mapPoints} />
                                <div className="absolute top-8 right-8 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-xs space-y-2">
                                    <h4 className="text-white font-bold uppercase tracking-widest text-xs">Live Geolocation Feed</h4>
                                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">Mapping {mapPoints.length} active viral outbreaks across platform clusters.</p>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Discovery Engine Logs</h3>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-[9px] font-bold text-emerald-500 uppercase">Engine_Active</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {displayLogs.map((log, i) => (
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

                        {activeEngine !== "logs" && (
                            <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Scanner Logs</span>
                                    <span className="text-[8px] font-mono text-primary/50">{status === "open" ? "LIVE_SYNC" : "OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                    {displayLogs.map((log, i) => (
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
        </CommandCenterLayout>
    );
}

export default function DiscoveryPage() {
    return (
        <Suspense fallback={null}>
            <DiscoveryContent />
        </Suspense>
    );
}

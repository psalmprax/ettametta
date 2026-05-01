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
    const [activeEngine, setActiveEngine] = useState("trends");
    const [candidates, setCandidates] = useState<ContentCandidate[]>([]);
    const [activeNiche, setActiveNiche] = useState(searchParams.get("q") || "Motivation");
    const [logs, setLogs] = useState<string[]>(["SCANNER_INITIALIZED", "POOLING_GLOBAL_TELEMETRY"]);
    const [telemetry, setTelemetry] = useState<any>(null);

    const fetchTrends = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        setLogs((prev: string[]) => [`[SCAN] Initiating Trend Analysis: ${activeNiche}`, ...prev]);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/discovery/trends?niche=${encodeURIComponent(activeNiche)}`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (data) => {
                    const trends = Array.isArray(data) ? data : (data?.trends || []);
                    setCandidates(trends);
                    setLogs((prev: string[]) => [`[SUCCESS] Found ${trends.length} Viral Candidates.`, ...prev]);
                }
            }
        );
    }, [activeNiche]);

    useEffect(() => {
        fetchTrends();
    }, [fetchTrends]);

    // Prepare Agent Data
    const agents = [
        { id: "SCAN_01", name: "Viral Radar", icon: Radar, status: "ACTIVE" as any, latency: 850, load: 12, details: "Scraping TikTok/YT" },
        { id: "INTEL_01", name: "Trend Engine", icon: Cpu, status: "ACTIVE" as any, latency: 45, load: 5, details: "Cross-pollinating Niches" },
        { id: "GEO_01", name: "Global Sentinel", icon: Globe, status: "IDLE" as any, latency: 2, load: 0, details: "Ready" },
    ];

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
                            onClick={() => setActiveEngine(item.id)}
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
                                <span className="text-xl font-bold text-white">{candidates.length}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Alerts</span>
                                <span className="text-xl font-bold text-rose-500">2</span>
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

                        {activeEngine === "hotspots" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative">
                                <Geomap points={[]} />
                                <div className="absolute top-8 right-8 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-xs space-y-2">
                                    <h4 className="text-white font-bold uppercase tracking-widest text-xs">Live Geolocation Feed</h4>
                                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">Mapping real-time viral outbreaks across platform clusters.</p>
                                </div>
                            </div>
                        )}

                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Scanner Logs</span>
                                <span className="text-[8px] font-mono text-primary/50">SYSTEM_READY</span>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[SCAN]") ? "text-cyan-400" :
                                            log.includes("[SUCCESS]") ? "text-emerald-500" : "text-zinc-600"
                                        )}>{log}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
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

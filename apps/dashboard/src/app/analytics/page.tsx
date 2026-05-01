"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import {
    BarChart3,
    TrendingUp,
    Zap,
    Activity,
    Globe,
    Cpu,
    Target,
    Layers,
    RefreshCw,
    Shield,
    Database,
    Share2,
    PieChart,
    ChevronRight,
    ArrowUpRight,
    Terminal,
    Radar,
    LineChart
} from "lucide-react";
import { cn } from "@/lib/utils";
import dynamic from "next/dynamic";
import { API_BASE, WS_BASE } from "@/lib/config";
import { withRealFallback } from "@/lib/real_first_utils";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ResponsiveContainer
} from "recharts";

const GlobalPulseGlobe = dynamic(() => import("@/components/ui/GlobalPulseGlobe"), { ssr: false });

interface AnalyticsMetrics {
    views: number;
    retention: number;
    shares: number;
    engagement: number;
    velocity: string;
    engineLoad: string;
    retentionData: { time: number; value: number }[];
}

export default function AnalyticsPage() {
    const [activeEngine, setActiveEngine] = useState("overview");
    const [metrics, setMetrics] = useState<AnalyticsMetrics>({
        views: 0,
        retention: 0.82,
        shares: 0,
        engagement: 0.05,
        velocity: "Nominal",
        engineLoad: "12%",
        retentionData: Array.from({ length: 20 }, (_, i) => ({ time: i, value: Math.max(20, 100 - i * 4 + Math.random() * 10) }))
    });
    const [logs, setLogs] = useState<string[]>(["ANALYTICS_INITIALIZED", "SYNCHRONIZING_HISTORICAL_DATA"]);

    const fetchAnalytics = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/analytics/stats/summary`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const stats = data.data || data;
                    setMetrics((prev: AnalyticsMetrics) => ({
                        ...prev,
                        views: stats.total_views || 0,
                        engagement: stats.engagement_score || 0,
                        velocity: stats.velocity || "Nominal",
                        engineLoad: stats.engine_load || "5%"
                    }));
                    setLogs((prev: string[]) => [`[DATA] Metrics synchronized. Total Reach: ${stats.total_views}`, ...prev]);
                }
            }
        );
    }, []);

    useEffect(() => {
        fetchAnalytics();
    }, [fetchAnalytics]);

    // Prepare Agent Data
    const agents = [
        { id: "INTEL_01", name: "Data Aggregator", icon: Database, status: "ACTIVE" as any, latency: 12, load: 4, details: "Syncing DB Clusters" },
        { id: "ANALYZ_01", name: "Neural Analytics", icon: Cpu, status: "ACTIVE" as any, latency: 85, load: 15, details: "Predicting Trend Drift" },
        { id: "PULSE_01", name: "Signal Monitor", icon: Radar, status: "ACTIVE" as any, latency: 1, load: 2, details: "Monitoring Global Pulse" },
    ];

    return (
        <CommandCenterLayout
            title="INTEL CORE"
            subtitle="PERFORMANCE_MATRIX_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "overview", label: "Intel Overview", icon: BarChart3 },
                        { id: "retention", label: "Attention Decay", icon: Activity },
                        { id: "patterns", label: "Neural Patterns", icon: Cpu },
                        { id: "propagation", label: "Global Pulse", icon: Globe },
                        { id: "logs", label: "Telemetry Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-violet-500/10 text-violet-400 border border-violet-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Reach</h4>
                        <div className="flex flex-col">
                            <span className="text-2xl font-bold text-white">{(metrics.views / 1000).toFixed(1)}K</span>
                            <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-widest">+14.2% Growth</span>
                        </div>
                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full w-[72%] bg-violet-500" />
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
                        {activeEngine === "overview" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                                <DesignCard
                                    title="Net Reach"
                                    status="Nominal"
                                    metrics={[
                                        { label: "Total Views", value: metrics.views >= 1000 ? `${(metrics.views/1000).toFixed(1)}K` : metrics.views, progress: 85, color: "text-cyan-400" },
                                        { label: "Growth", value: "+14.2%", color: "text-emerald-400" }
                                    ]}
                                    footerInfo="BASELINE: STABLE"
                                    toolsStatus="Online"
                                />
                                <DesignCard
                                    title="Retention"
                                    status="Optimized"
                                    metrics={[
                                        { label: "Attention Decay", value: `${(metrics.retention * 100).toFixed(0)}%`, progress: metrics.retention * 100, color: "text-emerald-400" },
                                        { label: "Stability", value: "Locked", color: "text-cyan-400" }
                                    ]}
                                    footerInfo="HOOK_EFFICIENCY: HIGH"
                                    toolsStatus="Online"
                                />
                                <DesignCard
                                    title="Viral Velocity"
                                    status="Current"
                                    metrics={[
                                        { label: "Propagation", value: metrics.velocity, progress: metrics.velocity === "High" ? 95 : 60, color: "text-violet-400" },
                                        { label: "Load", value: metrics.engineLoad, color: "text-slate-500" }
                                    ]}
                                    footerInfo="SYSTEM_PULSE: ACTIVE"
                                    toolsStatus="Online"
                                />
                                <DesignCard
                                    title="Conversion"
                                    status="Active"
                                    metrics={[
                                        { label: "Engagement", value: `${(metrics.engagement * 100).toFixed(1)}%`, progress: metrics.engagement * 10, color: "text-amber-400" },
                                        { label: "Success Rate", value: "98.2%", color: "text-emerald-400" }
                                    ]}
                                    footerInfo="NEURAL_CONVERSION_READY"
                                    toolsStatus="Online"
                                />
                            </div>
                        )}

                        {activeEngine === "retention" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-10 flex flex-col">
                                <div className="flex items-center justify-between mb-8">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                        <Activity className="h-5 w-5 text-emerald-400" />
                                        Attention Decay Analysis
                                    </h3>
                                    <div className="flex gap-2">
                                        <div className="h-2 w-2 rounded-full bg-emerald-500" />
                                        <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Optimized Node</span>
                                    </div>
                                </div>
                                <div className="flex-1 min-h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={metrics.retentionData}>
                                            <defs>
                                                <linearGradient id="colorRetention" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                            <XAxis dataKey="time" hide />
                                            <YAxis hide />
                                            <Area type="monotone" dataKey="value" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorRetention)" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}

                        {activeEngine === "propagation" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative">
                                <GlobalPulseGlobe pulseIntensity={1} />
                                <div className="absolute bottom-10 left-10 p-8 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-sm space-y-2">
                                    <h4 className="text-white font-bold uppercase tracking-widest text-xs">Global Propagation Matrix</h4>
                                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">Mapping the trajectory of neural propagation across global platform clusters.</p>
                                </div>
                            </div>
                        )}

                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Telemetry Logs</span>
                                <span className="text-[8px] font-mono text-violet-500/50">DATA_CORE_ACTIVE</span>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[DATA]") ? "text-cyan-400" :
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

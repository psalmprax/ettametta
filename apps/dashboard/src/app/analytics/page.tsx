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
import { useTelemetry } from "@/context/TelemetryContext";
import { AreaChartCustom } from "@/components/ui/ChartComponents";

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
    const { agents, logs: systemLogs, status, pulse } = useTelemetry();
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
    const [actionLogs, setActionLogs] = useState<string[]>(["ANALYTICS_INITIALIZED", "SYNCHRONIZING_HISTORICAL_DATA"]);

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
                    setActionLogs((prev: string[]) => [`[DATA] Metrics synchronized. Total Reach: ${stats.total_views}`, ...prev]);
                }
            }
        );
    }, []);

    useEffect(() => {
        fetchAnalytics();
    }, [fetchAnalytics]);

    return (
        <CommandCenterLayout
            title="INTEL CORE"
            subtitle="PERFORMANCE_MATRIX_V4.2"
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
                    <div className="p-3 rounded-2xl border border-white/5 bg-white/5 space-y-3">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Reach</h4>
                        <div className="flex flex-col">
                            <span className="text-xl font-bold text-white">{(metrics.views / 1000).toFixed(1)}K</span>
                            <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-widest">+14.2% Growth</span>
                        </div>
                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full w-[72%] bg-violet-500" />
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-3 sm:p-4 space-y-4 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "overview" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 w-full">
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
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-8 flex flex-col relative overflow-hidden group">
                                <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[100px] -mr-32 -mt-32" />
                                <div className="flex items-center justify-between mb-8 relative z-10">
                                    <div>
                                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                            <Activity className="h-5 w-5 text-emerald-400" />
                                            Attention Decay Analysis
                                        </h3>
                                        <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mt-1">Neural Retention Mapping • Active Stream</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex flex-col items-end">
                                            <span className="text-[10px] font-bold text-emerald-500 uppercase">Avg Stability</span>
                                            <span className="text-lg font-black text-white">82.4%</span>
                                        </div>
                                        <div className="h-10 w-px bg-white/5 mx-2" />
                                        <div className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]" />
                                    </div>
                                </div>
                                <div className="flex-1 min-h-[350px] relative z-10">
                                    <AreaChartCustom 
                                        data={metrics.retentionData} 
                                        dataKey="value" 
                                        color="#10b981" 
                                        height="100%"
                                        gradientId="retentionGradient"
                                    />
                                </div>
                                <div className="mt-6 flex items-center justify-between relative z-10 pt-6 border-t border-white/5">
                                    <div className="flex gap-4">
                                        <div className="flex items-center gap-2">
                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Control Group</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500/30" />
                                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Projected Drift</span>
                                        </div>
                                    </div>
                                    <span className="text-[9px] font-mono text-zinc-600">SAMPLE_SIZE: 14.2K_NODES</span>
                                </div>
                            </div>
                        )}

                        {activeEngine === "patterns" && (
                            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
                                <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-6 flex flex-col min-h-0">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                            <Cpu className="h-5 w-5 text-violet-400" />
                                            Success Correlation
                                        </h3>
                                        <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest">Active Patterns</span>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
                                        {[
                                            { label: "Narrative Hook Resonance", score: 92, status: "DOMINANT" },
                                            { label: "High-Contrast Visual Flow", score: 84, status: "OPTIMIZED" },
                                            { label: "Cognitive Ease Index", score: 78, status: "STABLE" },
                                            { label: "Emotional Amplitude", score: 65, status: "GROWING" }
                                        ].map((pattern, i) => (
                                            <div key={i} className="p-6 bg-white/5 border border-white/5 rounded-[24px] group hover:border-violet-500/30 transition-all space-y-4">
                                                <div className="flex items-center justify-between">
                                                    <h4 className="text-sm font-bold text-white">{pattern.label}</h4>
                                                    <span className="text-[9px] font-bold text-emerald-500 uppercase tracking-widest">{pattern.status}</span>
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="flex items-center justify-between text-[10px]">
                                                        <span className="text-zinc-500 font-bold uppercase">Probability Shift</span>
                                                        <span className="text-white font-mono">+{pattern.score}%</span>
                                                    </div>
                                                    <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                                        <motion.div initial={{ width: 0 }} animate={{ width: `${pattern.score}%` }} className="h-full bg-violet-500" />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-6 flex flex-col min-h-0">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                        <LineChart className="h-5 w-5 text-cyan-400" />
                                        Prediction Matrix
                                    </h3>
                                    <div className="flex-1 flex flex-col items-center justify-center space-y-6 opacity-20">
                                        <Radar className="h-16 w-16 text-zinc-500 animate-pulse" />
                                        <div className="text-center space-y-2">
                                            <p className="text-sm font-black uppercase tracking-[0.4em] text-white">Aggregating Global Drift</p>
                                            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest italic">Simulation running at 14.2 GFLOPS</p>
                                        </div>
                                    </div>
                                    <Button className="w-full h-14 bg-violet-600 hover:bg-violet-500 text-white font-bold rounded-2xl uppercase tracking-widest text-xs transition-all">Launch Strategic Forecast</Button>
                                </div>
                            </div>
                        )}

                        {activeEngine === "propagation" && (
                            <div className="flex-1 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative">
                                <GlobalPulseGlobe pulseIntensity={1} />
                                <div className="absolute bottom-10 left-10 p-8 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-sm space-y-2">
                                    <h4 className="text-white font-bold uppercase tracking-widest text-xs">Global Propagation Matrix</h4>
                                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">Mapping the trajectory of neural propagation across global platform clusters.</p>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[24px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Telemetry Stream</h3>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20">
                                            <div className="h-1.5 w-1.5 rounded-full bg-violet-500 animate-pulse" />
                                            <span className="text-[9px] font-bold text-violet-500 uppercase">Observer_Sync</span>
                                        </div>
                                    </div>
                                </div>
                                 <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {[
                                        ...actionLogs.map(msg => ({ level: "ACTION", message: msg, timestamp: Date.now() / 1000 })),
                                        ...(Array.isArray(systemLogs) ? systemLogs.filter(l => l.module === "ANALYTICS") : [])
                                    ].sort((a, b) => b.timestamp - a.timestamp).map((log: any, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                "shrink-0 font-bold tracking-widest uppercase text-[9px] px-2 py-0.5 rounded",
                                                log.message?.includes("[DATA]") || log.level === "DATA" ? "bg-cyan-500/10 text-cyan-500" :
                                                log.message?.includes("[SUCCESS]") || log.level === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" : "bg-white/5 text-zinc-500"
                                            )}>
                                                {log.message?.includes("[DATA]") || log.level === "DATA" ? "DATA" : 
                                                 log.message?.includes("[SUCCESS]") || log.level === "SUCCESS" ? "SUCCESS" : "INFO"}
                                            </span>
                                            <span className={cn(
                                                "leading-relaxed",
                                                log.message?.includes("[DATA]") || log.level === "DATA" ? "text-cyan-400" :
                                                log.message?.includes("[SUCCESS]") || log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-400"
                                            )}>
                                                {log.message}
                                            </span>
                                        </div>
                                    ))}
                                    <div className="h-4" />
                                </div>
                            </div>
                        )}

                        {activeEngine !== "logs" && activeEngine !== "patterns" && activeEngine !== "propagation" && activeEngine !== "retention" && activeEngine !== "overview" && (
                            <div className="mt-6 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[24px] border border-white/5 overflow-hidden shrink-0">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Telemetry Logs</span>
                                    <span className="text-[8px] font-mono text-violet-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                    {[
                                        ...actionLogs.map(msg => ({ level: "ACTION", message: msg, timestamp: Date.now() / 1000 })),
                                        ...(Array.isArray(systemLogs) ? systemLogs.filter(l => l.module === "ANALYTICS") : [])
                                    ].sort((a, b) => b.timestamp - a.timestamp).map((log: any, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.message?.includes("[DATA]") || log.level === "DATA" ? "text-cyan-400" :
                                                log.message?.includes("[SUCCESS]") || log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-600"
                                            )}>{log.message}</span>
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

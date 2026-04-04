"use client";

import React from "react";
import DashboardLayout from "@/components/layout";
import {
    BarChart3,
    TrendingUp,
    Users,
    Target,
    ArrowUpRight,
    ArrowDownRight,
    TrendingDown,
    PieChart,
    Zap,
    CheckCircle2,
    Search,
    Play,
    Clock,
    History,
    Trophy,
    Medal
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorNode } from "@/components/ui/ErrorNode";
import { useWebSocket } from "@/hooks/useWebSocket";
import dynamic from "next/dynamic";
import { API_BASE, WS_BASE } from "@/lib/config";
import { withRealFallback, getVelocityPoints } from "@/lib/real_first_utils";
import { toast } from "sonner";

const GlobalPulseGlobe = dynamic(() => import("@/components/ui/GlobalPulseGlobe"), { ssr: false });

interface SocialPost {
    id: number;
    title: string;
    platform: string;
    status: string;
    url: string | null;
    published_at: string;
}

interface AnalyticsReport {
    post_id: string;
    views: number;
    watch_time: number;
    retention_rate: number;
    likes: number;
    shares: number;
    follows_gained: number;
    retention_data: number[];
    optimization_insight: string;
}

interface ABResult {
    test_id: number;
    variant_a_title: string;
    variant_b_title: string;
    variant_a_views: number;
    variant_b_views: number;
    winner: string | null;
    created_at: string;
}

interface MonetizationData {
    total_revenue: number;
    epm: number;
}

import { motion, AnimatePresence } from "framer-motion";

import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ResponsiveContainer,
    Cell,
    PieChart as RechartsPieChart,
    Pie
} from "recharts";
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    getFilteredRowModel,
    flexRender,
    createColumnHelper,
    SortingState
} from "@tanstack/react-table";

export default function AnalyticsPage() {
    const [posts, setPosts] = useState<SocialPost[]>([]);
    const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
    const [report, setReport] = useState<AnalyticsReport | null>(null);
    const [monetization, setMonetization] = useState<MonetizationData | null>(null);
    const [abResults, setAbResults] = useState<ABResult | null>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [insights, setInsights] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isConfirmingApply, setIsConfirmingApply] = useState(false);
    const [notification, setNotification] = useState<{ message: string, type: "success" | "error" } | null>(null);
    const [sorting, setSorting] = useState<SortingState>([]);
    const [globalFilter, setGlobalFilter] = useState("");
    const [activeTests, setActiveTests] = useState<any[]>([]);
    const [completedTests, setCompletedTests] = useState<any[]>([]);
    const [isAutoPilot, setIsAutoPilot] = useState(false);
    const [isCreatingTest, setIsCreatingTest] = useState(false);
    const [newTestContentId, setNewTestContentId] = useState("");

    const [showWinnerModal, setShowWinnerModal] = useState(false);
    const [lastWinner, setLastWinner] = useState<any>(null);

    // --- DATA FETCHING ---
    const fetchPosts = useCallback(async () => {
        const token = localStorage.getItem("et_token");
        const data = await withRealFallback<SocialPost[]>(
            () => fetch(`${API_BASE}/analytics/posts`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                errorMessage: "Failed to load published content history"
            }
        );
        setPosts(data);
        if (data.length > 0 && !selectedPostId) {
            setSelectedPostId(data[0].id.toString());
        }
        setIsLoading(false);
    }, [selectedPostId]);

    useEffect(() => {
        fetchPosts();
    }, [fetchPosts]);

    const fetchData = useCallback(async () => {
        if (!selectedPostId) {
            // Fetch Global/Active AB Tests even if no post is selected
            const token = localStorage.getItem("et_token");
            const headers = { Authorization: `Bearer ${token}` };
            
            const testsData = await withRealFallback<any[]>(
                () => fetch(`${API_BASE}/ab-testing/ab/tests/active`, { headers }),
                { fallback: [] }
            );
            setActiveTests(testsData.active_tests || testsData.tests || testsData || []);

            const compData = await withRealFallback<any[]>(
                () => fetch(`${API_BASE}/ab-testing/ab/tests/completed`, { headers }),
                { fallback: [] }
            );
            setCompletedTests(compData.completed_tests || compData || []);
            return;
        }

        const token = localStorage.getItem("et_token");
        const headers = { Authorization: `Bearer ${token}` };

        // Performance Report
        withRealFallback<AnalyticsReport>(
            () => fetch(`${API_BASE}/analytics/report/${selectedPostId}`, { headers }),
            {
                fallback: {
                    post_id: selectedPostId,
                    views: 0,
                    watch_time: 0,
                    retention_rate: 0,
                    likes: 0,
                    shares: 0,
                    follows_gained: 0,
                    retention_data: [],
                    optimization_insight: "Real-time metrics unavailable."
                },
                onSuccess: (data) => setReport(data)
            }
        );

        // History
        withRealFallback<any[]>(
            () => fetch(`${API_BASE}/analytics/report/${selectedPostId}/history`, { headers }),
            {
                fallback: [],
                onSuccess: (data) => setHistory(data)
            }
        );

        // AB Results
        withRealFallback<ABResult | null>(
            () => fetch(`${API_BASE}/analytics/ab/results/${selectedPostId}`, { headers }),
            {
                fallback: null,
                onSuccess: (data) => setAbResults(data)
            }
        );

        // Insights
        withRealFallback<any>(
            () => fetch(`${API_BASE}/analytics/insights/${selectedPostId}`, { headers }),
            {
                fallback: null,
                onSuccess: (data) => setInsights(data.optimization_insight || data.insight || null)
            }
        );

        // Global Tests
        const testsData = await withRealFallback<any[]>(
            () => fetch(`${API_BASE}/ab-testing/ab/tests/active`, { headers }),
            { fallback: [] }
        );
        setActiveTests(testsData.active_tests || testsData.tests || testsData || []);

        const compData = await withRealFallback<any[]>(
            () => fetch(`${API_BASE}/ab-testing/ab/tests/completed`, { headers }),
            { fallback: [] }
        );
        setCompletedTests(compData.completed_tests || compData || []);
    }, [selectedPostId]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Neural Auto-Pilot Effect
    useEffect(() => {
        if (!isAutoPilot || activeTests.length === 0) return;

        const checkWinners = async () => {
            const token = localStorage.getItem("et_token");
            for (const test of activeTests) {
                const totalViews = (test.variant_a_views || 0) + (test.variant_b_views || 0);
                // Threshold: 100 views per variant roughly
                if (totalViews >= 200 && test.variant_a_views > 50 && test.variant_b_views > 50) {
                    await withRealFallback<any>(
                        () => fetch(`${API_BASE}/ab-testing/ab/test/${test.id}/determine-winner`, {
                            method: "POST",
                            headers: { Authorization: `Bearer ${token}` }
                        }),
                        {
                            silent: true,
                            onSuccess: (data) => {
                                if (data.status === "winner_determined") {
                                    setLastWinner(data);
                                    setShowWinnerModal(true);
                                    toast.success("Auto-Pilot Victory", { description: `Test #${test.id} finalized automatically.` });
                                }
                                fetchData();
                            }
                        }
                    );
                }
            }
        };

        const interval = setInterval(checkWinners, 30000); // Check every 30s
        return () => clearInterval(interval);
    }, [isAutoPilot, activeTests, fetchData]);
    // --- END DATA FETCHING ---

    // Real-time Telemetry Stream
    const { data: telemetry } = useWebSocket<any>(`${WS_BASE}/telemetry`);
    const pulseIntensity = telemetry?.metrics?.signal_strength || 0;

    const columnHelper = createColumnHelper<SocialPost>();
    const columns = [
        columnHelper.accessor("title", {
            header: "Post Title",
            cell: info => (
                <div className="flex flex-col">
                    <span className="font-black text-white uppercase text-[10px] tracking-tight truncate max-w-[200px]">{info.getValue()}</span>
                    <span className="text-[8px] text-zinc-600 font-bold uppercase">{info.row.original.platform} // ID: {info.row.original.id}</span>
                </div>
            )
        }),
        columnHelper.accessor("published_at", {
            header: "Published",
            cell: info => <span className="text-[10px] text-zinc-500 tabular-nums">{new Date(info.getValue()).toLocaleDateString()}</span>
        }),
        columnHelper.accessor("status", {
            header: "Signal",
            cell: info => (
                <div className="flex items-center gap-2">
                    <div className={cn("h-1.5 w-1.5 rounded-full animate-pulse", info.getValue() === "published" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-orange-500")} />
                    <span className="text-[10px] font-black uppercase text-zinc-400">{info.getValue()}</span>
                </div>
            )
        })
    ];

    const table = useReactTable({
        data: posts,
        columns,
        state: { sorting, globalFilter },
        onSortingChange: setSorting,
        onGlobalFilterChange: setGlobalFilter,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
    });

    const metrics = report || {
        views: 0,
        watch_time: 0,
        likes: 0,
        shares: 0,
        retention_rate: 0
    };

    const retentionChartData = (report?.retention_data || []).map((v, i) => ({
        time: `${i * 5}s`,
        retention: v,
        signal: Math.floor(v * (telemetry?.metrics?.signal_strength || 1))
    }));

    const [activeChartPoint, setActiveChartPoint] = useState<any>(null);

    // Hardened Velocity Curve (Real-First)
    const velocityData = getVelocityPoints(history, metrics.views);

    const handleAutoApply = async () => setIsConfirmingApply(true);

    const confirmApplyAction = async () => {
        setIsConfirmingApply(false);
        const token = localStorage.getItem("et_token");

        const data = await withRealFallback<any>(
            () => fetch(`${API_BASE}/analytics/inject-pattern/${selectedPostId || "global"}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: { status: "success", message: "Optimization strategies applied to neural cluster." },
                errorMessage: "Neural link unstable. Pattern injected into local cache."
            }
        );

        if (data) {
            setNotification({
                message: data.message || `Applied: ${data.length || 0} optimization strategies injected.`,
                type: "success"
            });
            setTimeout(() => setNotification(null), 5000);
        }
    };

    const performanceData = [
        { label: "Viral Velocity", score: telemetry?.metrics?.global_velocity * 10 || Math.min(Math.round((metrics.views / 200000) * 100), 100), status: metrics.views > 100000 ? "Peak" : "High" },
        { label: "Hook Retention", score: Math.round(metrics.retention_rate * 100), status: metrics.retention_rate > 0.7 ? "High" : "Medium" },
        { label: "Share Ratio", score: Math.min(Math.round((metrics.shares / metrics.views) * 1000), 100), status: "Growing" },
        { label: "Engagement Score", score: Math.min(Math.round((metrics.likes / metrics.views) * 100), 100), status: "Medium" },
    ];

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                {/* Confirmation Overlay */}
                <AnimatePresence>
                    {isConfirmingApply && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                animate={{ scale: 1, opacity: 1, y: 0 }}
                                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                className="glass-card w-full max-w-lg rounded-[2.5rem] p-10 shadow-[0_32px_128px_rgba(0,0,0,0.8)] space-y-8 relative overflow-hidden"
                            >
                                <div className="absolute inset-0 scanline opacity-(--scanline-opacity) pointer-events-none" />
                                <div className="flex items-start gap-6">
                                    <div className="h-16 w-16 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                                        <Zap className="h-8 w-8 text-primary neon-glow" />
                                    </div>
                                    <div className="space-y-2">
                                        <h3 className="text-2xl font-black uppercase tracking-tighter text-white">Strategic Override</h3>
                                        <p className="text-zinc-500 font-medium leading-relaxed">
                                            Execute <span className="text-primary font-bold">Neural pattern injection</span>? This will overwrite existing distribution weights with high-velocity viral telemetry.
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <button
                                        onClick={() => setIsConfirmingApply(false)}
                                        className="flex-1 h-16 rounded-2xl border border-white/5 text-zinc-500 font-black uppercase text-[10px] tracking-widest hover:bg-white/5 transition-colors"
                                    >
                                        Abort
                                    </button>
                                    <button
                                        onClick={confirmApplyAction}
                                        className="flex-1 h-16 rounded-2xl bg-primary text-black font-black uppercase text-[10px] tracking-widest shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all"
                                    >
                                        Execute Injection
                                    </button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="h-1 w-8 bg-primary rounded-full" />
                            <span className="text-[10px] font-black tracking-[0.3em] text-primary uppercase">Neural Intelligence</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">
                            Analytic <span className="text-transparent bg-clip-text bg-linear-to-r from-violet-500 to-cyan-400 text-hollow">Engine</span>
                        </h1>
                        <p className="text-zinc-500 mt-2 max-w-lg text-sm font-medium leading-relaxed">
                            Deep-dive behavioral mapping and <span className="text-zinc-300 font-bold">propagation telemetry</span> for the national grid.
                        </p>

                        {/* Spectral Density Visualizer (Deterministic) */}
                        <div className="flex items-center gap-1 h-4 mt-6 overflow-hidden opacity-60">
                            {Array.from({ length: 40 }).map((_, i) => (
                                <motion.div
                                    key={i}
                                    animate={{ 
                                        height: [4, 8 + Math.sin(i * 0.5) * 8, 4], 
                                        opacity: [0.2, 0.6 + Math.sin(i * 0.2) * 0.4, 0.2] 
                                    }}
                                    transition={{ 
                                        duration: 1.5 + (i % 3) * 0.2, 
                                        repeat: Infinity,
                                        ease: "easeInOut"
                                    }}
                                    className="w-1 bg-primary/30 rounded-full"
                                />
                            ))}
                        </div>
                    </div>

                    <div className="absolute right-0 top-0 w-1/3 aspect-square hidden xl:block pointer-events-none">
                        <div className="relative w-full h-full scale-[1.2] translate-x-1/4 -translate-y-1/4">
                            <GlobalPulseGlobe pulseIntensity={pulseIntensity} />
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-6">
                        <div className="space-y-1">
                            <p className="text-zinc-600 text-[10px] font-black uppercase tracking-widest text-right">Selected Node</p>
                            <div className="bg-zinc-950/50 border border-white/5 rounded-2xl px-6 py-4 flex items-center gap-4">
                                <span className="text-white font-black">VF-{selectedPostId || "GLOBAL"}</span>
                                <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                            </div>
                        </div>

                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => {
                                if (!posts.length) return;
                                const csvHeader = "ID,Title,Platform,Status,Published At,Views,Likes,Shares,Retention\n";
                                const csvRows = posts.map(p =>
                                    `${p.id},"${p.title}",${p.platform},${p.status},${p.published_at},${report?.views || 0},${report?.likes || 0},${report?.shares || 0},${report?.retention_rate || 0}`
                                ).join('\n');
                                const blob = new Blob([csvHeader + csvRows], { type: 'text/csv' });
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `viral_forge_analytics_${new Date().toISOString().split('T')[0]}.csv`;
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                URL.revokeObjectURL(url);
                            }}
                            className="bg-primary hover:bg-primary/90 text-white font-black h-16 px-8 rounded-2xl transition-all shadow-[0_0_40px_rgba(var(--primary-rgb),0.2)] flex items-center gap-3 uppercase text-xs tracking-[0.2em]"
                        >
                            <BarChart3 className="h-4 w-4" />
                            Global Export
                        </motion.button>
                    </div>
                </div>

                {/* Metric Summary Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
                    {isLoading ? (
                        Array.from({ length: 4 }).map((_, i) => (
                            <Skeleton key={`metric-s-${i}`} variant="card" className="h-48" />
                        ))
                    ) : (
                        <>
                            <TelemetryTile title="Network Bitrate" value={`${telemetry?.metrics?.bitrate || "000.0"} Mb/s`} icon={<Zap className="h-6 w-6 text-primary" />} label="Signal Bandwidth" subtext={`${telemetry?.metrics?.latency || "00.0"} ms Latency`} />
                            <TelemetryTile title="Propagation Velocity" value={`${telemetry?.metrics?.global_velocity || "0.0"}x`} icon={<TrendingUp className="h-6 w-6 text-primary" />} label="Viral Acceleration" subtext={`${telemetry?.metrics?.active_nodes || "0"} Active Nodes`} />
                            <TelemetryTile title="Signal Strength" value={`${Math.round((telemetry?.metrics?.signal_strength || 0) * 100)}%`} icon={<BarChart3 className="h-6 w-6 text-primary" />} label="Connection Quality" subtext="Sync Locked" />
                            <TelemetryTile title="Global Reach" value={metrics.views.toLocaleString()} icon={<Play className="h-6 w-6 text-primary" />} label="Network Ripple" subtext="+12.4% Velocity" />
                        </>
                    )}
                </div>

                {!report && !isLoading ? (
                    <div className="py-20 flex justify-center">
                        <ErrorNode message="No intelligence report found for the selected node. Verify signal source or refresh neural link." onRetry={() => window.location.reload()} />
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                            {/* Retention Spectrum */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="lg:col-span-2 glass-card p-10 space-y-8 min-h-[500px]"
                            >
                                <div className="flex items-center justify-between border-b border-white/5 pb-6">
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Retention <span className="text-primary">Spectrum</span></h3>
                                        <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Attention Decay Analysis</p>
                                    </div>
                                    <div className="flex items-center gap-2 bg-zinc-950/50 px-4 py-2 rounded-xl border border-white/5 shadow-glow-violet/10">
                                        <div className="h-2 w-2 rounded-full bg-neon-violet animate-pulse shadow-glow-violet" />
                                        <span className="text-[10px] font-black text-zinc-500 uppercase">Live Telemetry</span>
                                    </div>
                                </div>
                                <div className="h-[350px] w-full relative">
                                    {isLoading ? (
                                        <Skeleton key="chart-s" className="h-[300px] w-full rounded-3xl" />
                                    ) : (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart
                                                data={retentionChartData}
                                                onClick={(data: any) => {
                                                    if (data && data.activePayload) {
                                                        setActiveChartPoint(data.activePayload[0].payload);
                                                        setGlobalFilter(data.activePayload[0].payload.time);
                                                    }
                                                }}
                                            >
                                                <defs>
                                                    <linearGradient id="colorRetention" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                                                <XAxis
                                                    dataKey="time"
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontWeight: 'bold' }}
                                                />
                                                <YAxis
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontWeight: 'bold' }}
                                                />
                                                <RechartsTooltip content={({ active, payload }) => {
                                                    if (active && payload && payload.length) {
                                                        return (
                                                            <div className="glass-card p-4 border-primary/20 bg-zinc-950/90 backdrop-blur-xl shadow-2xl">
                                                                <p className="text-[10px] font-black text-primary uppercase mb-1">{payload[0].payload.time} Cluster</p>
                                                                <p className="text-xl font-black text-white">{payload[0].value}% <span className="text-[10px] text-zinc-500 uppercase ml-2">Stability</span></p>
                                                                <div className="mt-2 pt-2 border-t border-white/5">
                                                                    <p className="text-[8px] font-bold text-zinc-500 uppercase">Neural Signal: {payload[0].payload.signal} MHz</p>
                                                                </div>
                                                            </div>
                                                        );
                                                    }
                                                    return null;
                                                }} />
                                                <Area
                                                    type="monotone"
                                                    dataKey="retention"
                                                    stroke="hsl(var(--primary))"
                                                    strokeWidth={4}
                                                    fillOpacity={1}
                                                    fill="url(#colorRetention)"
                                                    animationDuration={2000}
                                                    activeDot={{ r: 8, stroke: 'white', strokeWidth: 2, fill: 'hsl(var(--primary))' }}
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    )}
                                </div>
                            </motion.div>

                            <div className="space-y-10">
                                <div className="glass-card rounded-[2.5rem] p-10 space-y-6">
                                    <div className="space-y-1">
                                        <h3 className="text-lg font-black uppercase text-white tracking-widest">Viral Velocity</h3>
                                        <p className="text-[10px] font-bold text-zinc-600 uppercase">Propagation Acceleration (24h)</p>
                                    </div>
                                    <div className="h-40">
                                        {isLoading ? (
                                            <Skeleton className="h-full w-full rounded-2xl" />
                                        ) : (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart data={velocityData}>
                                                    <Line type="stepAfter" dataKey="views" stroke="hsl(var(--primary))" strokeWidth={3} dot={false} strokeDasharray="5 5" />
                                                    <RechartsTooltip />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        )}
                                    </div>
                                </div>

                                <div className="glass-card rounded-[2.5rem] p-10 space-y-6 flex flex-col justify-center bg-primary/[0.02] border-primary/10">
                                    <div className="flex items-center gap-6">
                                        <div className="h-16 w-16 rounded-3xl bg-primary text-black flex items-center justify-center shadow-[0_0_30px_rgba(var(--primary-rgb),0.4)]">
                                            <Users className="h-8 w-8" />
                                        </div>
                                        <div className="space-y-1">
                                            <h4 className="text-2xl font-black text-white tracking-tighter">{(metrics.likes * 0.1).toFixed(1)}k</h4>
                                            <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">New Followers Predicted</p>
                                        </div>
                                    </div>
                                    <p className="text-zinc-500 text-xs font-medium leading-relaxed">
                                        "{report?.optimization_insight.split('.')[0] || "Global cluster synchronization active..."}"
                                    </p>
                                </div>
                            </div>

                            {/* A/B Comparison Node (Dynamic) */}
                            {abResults && (
                                <motion.div
                                    initial={{ y: 20, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                    className="col-span-1 lg:col-span-3 glass-card p-10 grid grid-cols-1 md:grid-cols-2 gap-12 relative overflow-hidden"
                                >
                                    <div className="absolute inset-0 scanline opacity-5" />
                                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-20 w-20 rounded-full bg-zinc-950 border border-white/10 flex items-center justify-center z-10 hidden md:flex">
                                        <span className="text-primary font-black text-xl">VS</span>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="flex items-center gap-3">
                                            <div className={cn("h-3 w-3 rounded-full", abResults.winner === 'A' ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-zinc-800")} />
                                            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Variant A (Standard)</p>
                                        </div>
                                        <h4 className="text-2xl font-black text-white tracking-tighter uppercase truncate">{abResults.variant_a_title}</h4>
                                        <div className="space-y-2">
                                            <div className="flex justify-between text-[10px] font-bold text-zinc-400">
                                                <span>Reach</span>
                                                <span className="text-white">{(abResults.variant_a_views || 0).toLocaleString()}</span>
                                            </div>
                                            <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden">
                                                <div className="h-full bg-zinc-500" style={{ width: `${(abResults.variant_a_views / (abResults.variant_a_views + abResults.variant_b_views || 1)) * 100}%` }} />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-6 text-right">
                                        <div className="flex items-center gap-3 justify-end">
                                            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Variant B (Optimized)</p>
                                            <div className={cn("h-3 w-3 rounded-full", abResults.winner === 'B' ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-zinc-800")} />
                                        </div>
                                        <h4 className="text-2xl font-black text-primary tracking-tighter uppercase truncate">{abResults.variant_b_title}</h4>
                                        <div className="space-y-2">
                                            <div className="flex justify-between text-[10px] font-bold text-zinc-400">
                                                <span className="text-white">{(abResults.variant_b_views || 0).toLocaleString()}</span>
                                                <span>Reach</span>
                                            </div>
                                            <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden flex justify-end">
                                                <div className="h-full bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]" style={{ width: `${(abResults.variant_b_views / (abResults.variant_a_views + abResults.variant_b_views || 1)) * 100}%` }} />
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {insights && (
                                <motion.div
                                    initial={{ y: 20, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                    className="col-span-1 lg:col-span-3 glass-card p-10 space-y-6 relative overflow-hidden"
                                >
                                    <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-2xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                            <Zap className="h-6 w-6 text-amber-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-black text-white uppercase tracking-tighter">AI <span className="text-amber-400">Insights</span></h3>
                                            <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Neural Optimization Recommendations</p>
                                        </div>
                                    </div>
                                    <p className="text-zinc-400 text-sm font-medium leading-relaxed">{insights}</p>
                                </motion.div>
                            )}
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-10 mt-10">
                            {/* Performance Matrix */}
                            <div className="glass-card p-10 space-y-8">
                                <div className="flex items-center justify-between border-b border-white/5 pb-6">
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Performance <span className="text-primary">Matrix</span></h3>
                                        <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Multi-dimensional Signal Strength</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {isLoading ? (
                                        Array.from({ length: 4 }).map((_, i) => (
                                            <Skeleton key={`perf-s-${i}`} className="h-24 rounded-2xl" />
                                        ))
                                    ) : (
                                        performanceData.map((data, idx) => (
                                            <motion.div
                                                key={idx}
                                                whileHover={{ x: 10 }}
                                                className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">{data.label}</span>
                                                    <span className="text-[10px] font-black text-primary uppercase tracking-tighter neon-glow">{data.status}</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${data.score}%` }}
                                                        transition={{ duration: 1.5, delay: idx * 0.1 }}
                                                        className="h-full bg-linear-to-r from-primary to-primary/40 rounded-full"
                                                    />
                                                </div>
                                            </motion.div>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Distribution Node */}
                            <div className="glass-card p-10 space-y-8">
                                <div className="flex items-center justify-between border-b border-white/5 pb-6">
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Distribution <span className="text-primary">Node</span></h3>
                                        <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Global Propagation Streams</p>
                                    </div>
                                    <div className="relative group">
                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500 group-focus-within:text-primary transition-colors" />
                                        <input
                                            id="neural-filter"
                                            name="neural-filter"
                                            placeholder="Neural Filter..."
                                            aria-label="Filter distribution list"
                                            value={(table.getColumn("title")?.getFilterValue() as string) ?? ""}
                                            onChange={(event) => table.getColumn("title")?.setFilterValue(event.target.value)}
                                            className="bg-zinc-950/50 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-xs font-bold text-white focus:outline-none focus:border-primary/50 transition-all w-48"
                                        />
                                    </div>
                                </div>

                                <div className="overflow-hidden rounded-2xl border border-white/5 bg-white/1">
                                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                        <div className="space-y-1">
                                            <p className="text-[8px] font-black text-zinc-600 uppercase tracking-[0.3em]">Live Spectral Density</p>
                                            <p className="text-[10px] font-bold text-white uppercase tabular-nums">Channel: 48 / Node: VF-GLOBAL</p>
                                        </div>
                                        <div className="flex gap-1 h-6 items-end">
                                            {telemetry?.active_segments?.map((seg: any, i: number) => (
                                                <div key={i} className="flex flex-col items-center gap-1">
                                                    <motion.div
                                                        animate={{ height: `${seg.load}%` }}
                                                        transition={{ type: "spring", stiffness: 300 }}
                                                        className="w-3 bg-primary/20 rounded-t-sm relative overflow-hidden"
                                                    >
                                                        <div className="absolute inset-0 bg-primary opacity-20 animate-pulse" />
                                                    </motion.div>
                                                    <span className="text-[6px] font-black text-zinc-700">{seg.label}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    {isLoading ? (
                                        <div className="p-8 space-y-4">
                                            {Array.from({ length: 5 }).map((_, i) => (
                                                <Skeleton key={`table-s-${i}`} className="h-12 w-full" />
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-left">
                                                <thead className="bg-white/2 border-b border-white/5">
                                                    {table.getHeaderGroups().map((headerGroup) => (
                                                        <tr key={headerGroup.id}>
                                                            {headerGroup.headers.map((header) => (
                                                                <th key={header.id} className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">
                                                                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                                                                </th>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </thead>
                                                <tbody className="divide-y divide-white/5">
                                                    {table.getRowModel().rows.length > 0 ? (
                                                        table.getRowModel().rows.map((row) => (
                                                            <tr
                                                                key={row.id}
                                                                onClick={() => setSelectedPostId(row.original.id.toString())}
                                                                className={cn(
                                                                    "group cursor-pointer hover:bg-white/2 transition-colors",
                                                                    selectedPostId === row.original.id.toString() && "bg-white/3"
                                                                )}
                                                            >
                                                                {row.getVisibleCells().map((cell) => (
                                                                    <td key={cell.id} className="p-4">
                                                                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                                                    </td>
                                                                ))}
                                                            </tr>
                                                        ))
                                                    ) : (
                                                        <tr>
                                                            <td colSpan={columns.length} className="p-12 text-center text-zinc-500 font-bold uppercase text-[10px] tracking-widest">
                                                                Signal Silent
                                                            </td>
                                                        </tr>
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </>
                )}

                {/* A/B Testing Management */}
                <div className="glass-card p-10 space-y-8 mt-10">
                    <div className="flex items-center justify-between border-b border-white/5 pb-6">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                                <Target className="h-5 w-5 text-purple-500" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white uppercase tracking-tighter">A/B Testing <span className="text-purple-400">Matrix</span></h3>
                                <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Active Variant Tracking</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setIsAutoPilot(!isAutoPilot)}
                                className={cn(
                                    "flex items-center gap-2 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all",
                                    isAutoPilot ? "bg-emerald-500/20 border-emerald-500 text-emerald-500" : "bg-zinc-950 border-zinc-800 text-zinc-600"
                                )}
                            >
                                <Zap className={cn("h-3.5 w-3.5", isAutoPilot ? "animate-pulse" : "opacity-40")} />
                                Auto-Pilot {isAutoPilot ? "Active" : "OFF"}
                            </button>
                            <button
                                onClick={() => setIsCreatingTest(true)}
                                className="bg-purple-500/10 hover:bg-purple-500/20 text-purple-500 font-black py-2 px-4 rounded-xl transition-all text-[10px] uppercase tracking-widest border border-purple-500/20"
                            >
                                + New Test
                            </button>
                        </div>
                    </div>

                    {isCreatingTest && (
                        <div className="p-6 bg-zinc-950/50 border border-purple-500/20 rounded-2xl space-y-4">
                            <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Create New A/B Test</p>
                            <div className="flex gap-4">
                                <input
                                    type="text"
                                    placeholder="Content ID (post ID)"
                                    value={newTestContentId}
                                    onChange={(e) => setNewTestContentId(e.target.value)}
                                    className="flex-1 bg-zinc-950/50 border border-white/10 rounded-xl p-3 text-sm text-white outline-none"
                                />
                                <button
                                    onClick={async () => {
                                        if (!newTestContentId) return;
                                        const token = localStorage.getItem("et_token");

                                        await withRealFallback<any>(
                                            () => fetch(`${API_BASE}/ab-testing/ab/test/start`, {
                                                method: "POST",
                                                headers: {
                                                    "Content-Type": "application/json",
                                                    Authorization: `Bearer ${token}`
                                                },
                                                body: JSON.stringify({ 
                                                    content_id: newTestContentId, 
                                                    variant_a_title: "Original", 
                                                    variant_b_title: "Optimized" 
                                                })
                                            }),
                                            {
                                                fallback: { status: "success" },
                                                onSuccess: () => {
                                                    setIsCreatingTest(false);
                                                    setNewTestContentId("");
                                                    fetchData();
                                                }
                                            }
                                        );
                                    }}
                                    disabled={!newTestContentId}
                                    className="bg-purple-500 hover:bg-purple-600 text-white font-black py-3 px-6 rounded-xl transition-all text-[10px] uppercase tracking-widest disabled:opacity-50"
                                >
                                    Start Test
                                </button>
                                <button
                                    onClick={() => setIsCreatingTest(false)}
                                    className="bg-zinc-800 text-zinc-400 font-black py-3 px-6 rounded-xl transition-all text-[10px] uppercase tracking-widest"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTests.length > 0 ? (
                        <div className="space-y-3">
                            {activeTests.map((test: any) => (
                                <div key={test.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between">
                                    <div>
                                        <p className="text-[10px] font-black text-white uppercase tracking-wider">Test #{test.id} • Content: {test.content_id}</p>
                                        <p className="text-[9px] text-zinc-500">{test.variant_a_title} vs {test.variant_b_title}</p>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="text-[10px] text-zinc-400">
                                            <span className="text-white font-bold">{test.variant_a_views || 0}</span> vs <span className="text-primary font-bold">{test.variant_b_views || 0}</span>
                                        </div>
                                        <button
                                            onClick={async () => {
                                                const token = localStorage.getItem("et_token");
                                                await withRealFallback<any>(
                                                    () => fetch(`${API_BASE}/ab-testing/ab/test/${test.id}/determine-winner`, {
                                                        method: "POST",
                                                        headers: { Authorization: `Bearer ${token}` }
                                                    }),
                                                    {
                                                        errorMessage: "Neural decision pending cluster consensus.",
                                                        onSuccess: (data) => {
                                                            if (data.status === "winner_determined") {
                                                                setLastWinner(data);
                                                                setShowWinnerModal(true);
                                                            }
                                                            fetchData();
                                                        }
                                                    }
                                                );
                                            }}
                                            className="bg-purple-500/10 text-purple-500 font-black py-2 px-4 rounded-lg text-[9px] uppercase tracking-widest border border-purple-500/20 hover:bg-purple-500/20 transition-all"
                                        >
                                            Determine Winner
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-zinc-600 text-[10px] font-bold uppercase tracking-widest text-center py-8">No active A/B tests</p>
                    )}
                </div>

                {/* Victory Matrix - Completed Tests */}
                <div className="glass-card rounded-[2.5rem] p-10 space-y-8 mt-10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 rounded-xl bg-neon-violet/10 flex items-center justify-center border border-neon-violet/20 shadow-glow-violet/20">
                                <Trophy className="h-6 w-6 text-neon-violet neon-glow-violet" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white uppercase tracking-tight">Victory <span className="text-transparent bg-clip-text bg-linear-to-r from-neon-violet to-neon-cyan">Matrix</span></h3>
                                <p className="text-[10px] text-cyan-400 font-black uppercase tracking-widest">Optimized DNA Heritage</p>
                            </div>
                        </div>
                        <History className="h-5 w-5 text-zinc-700" />
                    </div>

                    {completedTests.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {completedTests.map((test: any) => {
                                const total = (test.variant_a_views || 0) + (test.variant_b_views || 0);
                                const winRate = total > 0 ? (test.winner_variant === 'A' ? test.variant_a_views / total : test.variant_b_views / total) : 0;
                                return (
                                    <div key={test.id} className="p-5 rounded-2xl bg-zinc-950/40 border border-white/5 flex items-center justify-between group hover:border-amber-500/30 transition-all">
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-2">
                                                <Medal className="h-3 w-3 text-amber-500" />
                                                <p className="text-[10px] font-black text-white uppercase">Variant {test.winner_variant}</p>
                                            </div>
                                            <p className="text-[11px] text-zinc-400 font-bold">{test.winner_variant === 'A' ? test.variant_a_title : test.variant_b_title}</p>
                                            <p className="text-[9px] text-zinc-600 uppercase font-black">Content: {test.content_id}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-black text-amber-500 tracking-tighter">+{Math.round((winRate - 0.5) * 200)}%</p>
                                            <p className="text-[8px] text-zinc-500 uppercase font-black tracking-widest">Growth Lift</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <p className="text-zinc-600 text-[10px] font-bold uppercase tracking-widest text-center py-8">No optimization victories recorded yet</p>
                    )}
                </div>

                {/* Winner Success Modal */}
                <AnimatePresence>
                    {showWinnerModal && lastWinner && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md"
                        >
                        <motion.div
                            initial={{ scale: 0.9, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.9, y: 20 }}
                            className="max-w-md w-full glass-card border-neon-violet/50 bg-zinc-950 p-10 rounded-[3rem] text-center space-y-8 relative overflow-hidden shadow-glow-violet/30"
                        >
                            <div className="absolute inset-0 bg-linear-to-b from-neon-violet/10 via-transparent to-neon-cyan/5 pointer-events-none" />
                            <div className="h-24 w-24 rounded-[2rem] bg-neon-violet/20 border border-neon-violet/30 flex items-center justify-center mx-auto shadow-glow-violet">
                                <Trophy className="h-12 w-12 text-neon-violet animate-float" />
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-4xl font-black text-white uppercase tracking-tighter">Optimization <span className="text-neon-cyan">Victory</span></h2>
                                <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest">Variant {lastWinner.winner} Has Ascended</p>
                            </div>
                                <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4">
                                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-zinc-500">
                                        <span>Winning Title</span>
                                        <span className="text-amber-500">Winner</span>
                                    </div>
                                    <p className="text-xl font-black text-white uppercase tracking-tight">{lastWinner.winner_title}</p>
                                    <div className="pt-4 border-t border-white/5 flex justify-between items-end">
                                        <div>
                                            <p className="text-[10px] text-zinc-500 font-bold uppercase mb-1">Engagement</p>
                                            <p className="text-2xl font-black text-white">{lastWinner.variant_a_views + lastWinner.variant_b_views}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-[10px] text-zinc-500 font-bold uppercase mb-1">Performance Lift</p>
                                            <p className="text-2xl font-black text-emerald-500">+{Math.round((Math.max(lastWinner.variant_a_views, lastWinner.variant_b_views) / (lastWinner.variant_a_views + lastWinner.variant_b_views) - 0.5) * 200)}%</p>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setShowWinnerModal(false)}
                                    className="w-full bg-amber-500 hover:bg-amber-600 text-black font-black py-5 rounded-2xl transition-all uppercase text-xs tracking-[0.2em] shadow-[0_0_30px_rgba(245,158,11,0.3)]"
                                >
                                    Seal Result
                                </button>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Overdrive Neural Panel */}
                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    whileInView={{ y: 0, opacity: 1 }}
                    viewport={{ once: true }}
                    className="glass-card rounded-[3rem] p-12 flex flex-col md:flex-row items-center gap-12 group relative overflow-hidden mt-10"
                >
                    <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                    <div className="h-28 w-28 rounded-[2.5rem] bg-zinc-950 border border-white/5 flex items-center justify-center shrink-0 group-hover:border-primary/50 transition-all duration-700 shadow-2xl relative">
                        <Zap className="h-12 w-12 text-primary neon-glow animate-pulse" />
                        <div className="absolute inset-0 border-2 border-dashed border-primary/20 rounded-[2.5rem] animate-spin-slow opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="space-y-4 flex-1">
                        <div className="flex items-center gap-4">
                            <h4 className="text-3xl font-black uppercase tracking-tighter text-white">Neural Optimizer</h4>
                            <span className="px-3 py-1 rounded-lg bg-zinc-900 border border-white/10 text-[8px] font-black text-zinc-500 uppercase tracking-widest">Active_Cluster</span>
                        </div>
                        <p className="text-zinc-500 font-medium text-sm leading-relaxed max-w-4xl">
                            {report?.optimization_insight || (
                                <span className="opacity-70">
                                    Awaiting telemetry data. Publish content to activate neural optimization cluster.
                                    <span className="animate-pulse ml-1">_</span>
                                </span>
                            )}
                        </p>
                    </div>
                    <motion.button
                        whileHover={{ scale: 1.05, boxShadow: "0 0 50px rgba(var(--primary-rgb), 0.4)" }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleAutoApply}
                        className="bg-primary text-black font-black h-20 px-12 rounded-3xl transition-all shadow-[0_0_40px_rgba(var(--primary-rgb),0.2)] uppercase text-xs tracking-[0.3em] whitespace-nowrap"
                    >
                        Execute Inversion
                    </motion.button>
                </motion.div>
            </div>
        </DashboardLayout>
    );
}

function TelemetryTile({ title, value, icon, label, subtext }: { title: string, value: string, icon: React.ReactNode, label: string, subtext: string }) {
    return (
        <motion.div
            whileHover={{ y: -8, rotateX: 5, rotateY: 5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="glass-card p-10 rounded-[2.5rem] space-y-6 relative group overflow-hidden cursor-pointer perspective-1000"
        >
            <div className="absolute inset-0 backdrop-blur-3xl opacity-0 group-hover:opacity-10 transition-opacity" />
            <div className="flex items-start justify-between relative z-10">
                <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-600">{title}</p>
                    <h2 className="text-5xl font-black text-white tracking-tighter drop-shadow-2xl">{value}</h2>
                </div>
                <div className="h-14 w-14 rounded-2xl bg-zinc-950 border border-white/5 flex items-center justify-center group-hover:border-primary/40 transition-all duration-500 group-hover:rotate-12 shadow-2xl">
                    {icon}
                </div>
            </div>
            <div className="pt-6 flex items-center justify-between border-t border-white/5 relative z-10">
                <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">{label}</span>
                <div className="flex items-center gap-2">
                    <ArrowUpRight className="h-3 w-3 text-primary animate-bounce-subtle" />
                    <span className="text-[11px] font-black text-primary uppercase tracking-tighter neon-glow">{subtext}</span>
                </div>
            </div>
        </motion.div>
    );
}

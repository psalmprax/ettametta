"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import DashboardLayout from "@/components/layout";
import {
    BarChart3,
    TrendingUp,
    Users,
    Target,
    Zap,
    RefreshCw,
    Globe,
    Activity,
    Shield,
    Terminal,
    ArrowRight,
    Play,
    Cpu,
    Fingerprint,
    Lock,
    Radio,
    Infinity as InfinityIcon,
    Database
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useWebSocket } from "@/hooks/useWebSocket";
import dynamic from "next/dynamic";
import { API_BASE, WS_BASE } from "@/lib/config";
import { withRealFallback, getVelocityPoints } from "@/lib/real_first_utils";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { Canvas } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";

import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ResponsiveContainer
} from "recharts";

const GlobalPulseGlobe = dynamic(() => import("@/components/ui/GlobalPulseGlobe"), { ssr: false });
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

function AnalyticsBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#d05bff" />
                    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
                        <Sphere args={[1, 64, 64]} scale={2.5}>
                            <MeshDistortMaterial
                                color="#d05bff"
                                speed={4}
                                distort={0.4}
                                radius={1}
                                wireframe
                                transparent
                                opacity={0.1}
                            />
                        </Sphere>
                    </Float>
                </Suspense>
            </Canvas>
        </div>
    );
}


export default function AnalyticsPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [metrics, setMetrics] = useState({
        views: 0,
        retention: 0,
        shares: 0,
        engagement: 0,
        activeTrends: 0,
        successRate: "0%",
        engineLoad: "0%",
        velocity: "Nominal",
        retentionData: [] as any[]
    });
    const [historyData, setHistoryData] = useState<any[]>([]);

    const fetchAnalytics = useCallback(async () => {
        try {
            const token = await getAuthToken();
            const headers = { Authorization: `Bearer ${token}` };

            const [summaryRes, reportRes, postsRes] = await Promise.all([
                fetch(`${API_BASE}/analytics/stats/summary`, { headers }),
                fetch(`${API_BASE}/analytics/report`, { headers }),
                fetch(`${API_BASE}/analytics/posts?size=1`, { headers })
            ]);

            if (summaryRes.ok && reportRes.ok) {
                const summary = (await summaryRes.json()).data;
                const report = (await reportRes.json()).data;

                // Get latest post for detailed chart/matrix
                const postsRes = await fetch(`${API_BASE}/analytics/posts?size=1`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                const posts = (await postsRes.json()).data.items || [];
                let retentionData = [];
                
                if (posts.length > 0) {
                    const latestReportRes = await fetch(`${API_BASE}/analytics/report/${posts[0].id}`, {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    const latestReport = (await latestReportRes.json()).data;
                    retentionData = latestReport.retention_data || [];
                }

                setMetrics({
                    views: report.total_views,
                    retention: report.avg_retention,
                    shares: report.total_shares,
                    engagement: report.total_views > 0 ? (report.total_likes / report.total_views) : 0,
                    activeTrends: summary.active_trends,
                    successRate: summary.success_rate,
                    engineLoad: summary.engine_load,
                    velocity: summary.velocity,
                    retentionData: retentionData.length > 0 ? retentionData.map((v: number, i: number) => ({ time: i, value: v })) : []
                });
            }

            if (postsRes.ok) {
                const postsData = (await postsRes.json()).data;
                const latestPost = postsData.items?.[0];
                if (latestPost) {
                    const historyRes = await fetch(`${API_BASE}/analytics/report/${latestPost.id}/history`, { headers });
                    if (historyRes.ok) {
                        const history = (await historyRes.json()).data;
                        if (history && history.length > 0) {
                            setHistoryData(history.map((h: any) => ({
                                time: new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                                value: h.view_count
                            })));
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Analytics fetch failed:", err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const handleReOptimize = async () => {
        try {
            const token = await getAuthToken();
            const postsRes = await fetch(`${API_BASE}/analytics/posts?size=1`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const postsData = (await postsRes.json()).data;
            const latestPost = postsData.items?.[0];

            if (!latestPost) {
                toast.error("No active content found for re-optimization");
                return;
            }

            const res = await fetch(`${API_BASE}/analytics/inject-pattern/${latestPost.id}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                const result = await res.json();
                toast.success(result.data?.message || "Neural pattern successfully injected");
            } else {
                toast.error("Optimization sequence failed");
            }
        } catch (err) {
            toast.error("System connection error");
        }
    };

    const handleExport = async () => {
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/analytics/export`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ettametta_analytics_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                toast.success("Export started");
            } else {
                toast.error("Export failed");
            }
        } catch (err) {
            toast.error("Network error during export");
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, [fetchAnalytics]);

    const retentionData = [
        { time: "0s", value: 100 },
        { time: "5s", value: 85 },
        { time: "10s", value: 72 },
        { time: "15s", value: 68 },
        { time: "20s", value: 62 },
        { time: "25s", value: 58 },
        { time: "30s", value: 55 },
    ];

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <AnalyticsBackground />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    
                    {/* ANALYTICS HEADER HUD */}
                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                        <div className="space-y-6">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 120 }}
                                className="h-1 bg-purple-500 shadow-[0_0_20px_#d05bff]"
                            />
                            <div className="space-y-2">
                                <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none  " data-text="INTEL_CORE">
                                    Intel Core
                                </h1>
                                <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                                    <Radio className="h-3 w-3 text-purple-400 animate-pulse" />
                                    SIGNAL_STRENGTH: 98.4%
                                    <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                                    ENCRYPTION: AES_256_NEURAL
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="surface-glass rim-light p-6 flex flex-col items-end">
                                <span className="font-data-mono text-[8px] text-zinc-600 mb-1">SYSTEM_TIME</span>
                                <span className="text-xl font-bold text-white tabular-nums tracking-tighter">
                                    {new Date().toLocaleTimeString()}
                                </span>
                            </div>
                            <button 
                                onClick={handleExport}
                                className="action-primary h-20 px-12  text-xs tracking-tighter"
                            >
                                EXPORT_DATA_PACK
                            </button>
                        </div>
                    </header>

                    {/* TOP STATS GRID */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
                        {[
                            { label: "NET_REACH", val: metrics.views >= 1000000 ? `${(metrics.views / 1000000).toFixed(1)}M` : metrics.views >= 1000 ? `${(metrics.views / 1000).toFixed(1)}K` : metrics.views, icon: Globe, color: "text-cyan-400" },
                            { label: "ATTENTION_DECAY", val: `${(metrics.retention * 100).toFixed(0)}%`, icon: Activity, color: "text-emerald-400" },
                            { label: "VIRAL_VELOCITY", val: metrics.velocity, icon: Zap, color: "text-purple-400" },
                            { label: "NEURAL_CONVERSION", val: `${(metrics.engagement * 100).toFixed(1)}%`, icon: Cpu, color: "text-amber-400" },
                        ].map((stat, i) => (
                            <motion.div 
                                key={stat.label}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="surface-glass rim-light p-8 space-y-4 hover:rim-glow-cyan transition-all group"
                            >
                                <div className="flex items-center justify-between">
                                    <stat.icon className={cn("h-5 w-5", stat.color)} />
                                    <span className="font-data-mono text-[8px] text-zinc-700 tracking-[0.5em]">{stat.label}</span>
                                </div>
                                <div className="space-y-1">
                                    <h4 className="text-4xl font-bold text-white tracking-tighter  group-hover:text-cyan-400 transition-colors">{stat.val}</h4>
                                    <div className="flex items-center gap-2">
                                        <TrendingUp className="h-3 w-3 text-emerald-500" />
                                        <span className="text-[9px] font-bold text-emerald-500">+14.2%</span>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* MAIN ANALYTICS CORE */}
                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12">
                        
                        {/* RETENTION SPECTRUM */}
                        <div className="xl:col-span-8 surface-glass rim-light p-10 space-y-10 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-5" />
                            <div className="flex items-center justify-between border-b border-white/5 pb-8">
                                <div className="space-y-2">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter ">Retention Spectrum</h3>
                                    <p className="font-data-mono text-zinc-500 text-[9px]">DEEP_BEHAVIORAL_MAPPING // T+0_INITIAL_HOOK</p>
                                </div>
                                <div className="flex gap-2">
                                    <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_10px_#00fbfb]" />
                                    <div className="h-2 w-2 rounded-full bg-zinc-800" />
                                    <div className="h-2 w-2 rounded-full bg-zinc-800" />
                                </div>
                            </div>

                            <div className="h-[400px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={historyData.length > 0 ? historyData : retentionData}>
                                        <defs>
                                            <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#00fbfb" stopOpacity={0.3}/>
                                                <stop offset="95%" stopColor="#00fbfb" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                        <XAxis 
                                            dataKey="time" 
                                            axisLine={false} 
                                            tickLine={false} 
                                            tick={{ fill: '#4b5563', fontSize: 8, fontWeight: 'bold' }} 
                                        />
                                        <YAxis 
                                            hide 
                                        />
                                        <RechartsTooltip 
                                            content={({ active, payload }) => {
                                                if (active && payload && payload.length) {
                                                    return (
                                                        <div className="surface-glass rim-light p-6 backdrop-blur-3xl shadow-2xl space-y-2">
                                                            <p className="font-data-mono text-[10px] text-cyan-400">{payload[0].payload.time} NODE</p>
                                                            <p className="text-3xl font-bold text-white tracking-tighter">{payload[0].value}%</p>
                                                            <p className="font-data-mono text-[8px] text-zinc-600 uppercase">STABILITY_LOCKED</p>
                                                        </div>
                                                    );
                                                }
                                                return null;
                                            }}
                                        />
                                        <Area 
                                            type="monotone" 
                                            dataKey="value" 
                                            stroke="#00fbfb" 
                                            strokeWidth={4} 
                                            fillOpacity={1} 
                                            fill="url(#colorVal)" 
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* INSIGHTS CLUSTER */}
                        <div className="xl:col-span-4 space-y-12">
                            <section className="surface-glass rim-light p-10 space-y-8 relative group overflow-hidden">
                                <div className="absolute inset-0 bg-cyan-400/0 group-hover:bg-cyan-400/[0.02] transition-colors" />
                                <h3 className="font-label-caps text-xs text-zinc-500 flex items-center gap-3">
                                    <Target className="h-4 w-4 text-cyan-400" />
                                    AI_OPTIMIZATION
                                </h3>
                                <div className="space-y-6">
                                    <div className="p-6 bg-white/2 border border-white/5 space-y-3">
                                        <p className="text-sm font-bold text-white leading-relaxed">
                                            "The signal drops by 14% at the 5s mark. Recommend injecting a high-velocity visual hook at this node."
                                        </p>
                                        <p className="font-data-mono text-[8px] text-zinc-600">CONFIDENCE: 99.2%</p>
                                    </div>
                                    <button 
                                        onClick={handleReOptimize}
                                        className="w-full action-primary py-5  text-[10px] tracking-tighter"
                                    >
                                        RE-OPTIMIZE_SEGMENT
                                    </button>
                                </div>
                            </section>

                            <section className="surface-glass rim-light p-10 space-y-10">
                                <h3 className="font-label-caps text-xs text-zinc-500 flex items-center gap-3">
                                    <Shield className="h-4 w-4" />
                                    NETWORK_RELIABILITY
                                </h3>
                                <div className="space-y-6">
                                    <div className="flex items-center justify-between">
                                        <span className="font-data-mono text-[9px] text-zinc-600">ORACLE_MAE:</span>
                                        <span className="text-white font-bold ">0.024</span>
                                    </div>
                                    <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden">
                                        <motion.div 
                                            initial={{ width: 0 }}
                                            animate={{ width: "98%" }}
                                            className="h-full bg-cyan-400 shadow-[0_0_15px_#00fbfb]"
                                        />
                                    </div>
                                    <p className="text-center font-data-mono text-[8px] text-emerald-500 animate-pulse">SYSTEM_OPTIMIZED</p>
                                </div>
                            </section>
                        </div>
                    </div>

                    {/* GLOBAL PROPAGATION GRID */}
                    <div className="mt-12 grid grid-cols-1 xl:grid-cols-2 gap-12">
                        <div className="surface-glass rim-light p-10 h-96 relative overflow-hidden group">
                            <div className="absolute inset-0 z-0">
                                <GlobalPulseGlobe />
                            </div>
                            <div className="relative z-10 space-y-2">
                                <h3 className="text-xl font-bold text-white  tracking-tighter">Global Propagation</h3>
                                <p className="font-data-mono text-zinc-500 text-[8px]">LIVE_GEOSPATIAL_STREAM</p>
                            </div>
                            <div className="absolute bottom-8 right-8 z-10 flex items-center gap-4">
                                <div className="h-3 w-3 bg-cyan-400 animate-ping rounded-full" />
                                <span className="font-data-mono text-[9px] text-cyan-400">ACTIVE_PULSE</span>
                            </div>
                        </div>

                        <div className="surface-glass rim-light p-10 space-y-8">
                             <div className="flex items-center justify-between">
                                <h3 className="text-xl font-bold text-white  tracking-tighter">Viral Matrix</h3>
                                <Database className="h-5 w-5 text-zinc-600" />
                             </div>
                             <div className="space-y-4">
                                {[
                                    { name: "Retention Hook", score: 92, status: "PEAK" },
                                    { name: "Share Velocity", score: 84, status: "STABLE" },
                                    { name: "Comment Sentiment", score: 76, status: "RECOVERING" },
                                    { name: "Thumbnail CTR", score: 95, status: "PEAK" },
                                ].map((item, i) => (
                                    <div key={item.name} className="p-6 bg-white/2 border border-white/5 flex items-center justify-between group hover:bg-white/5 transition-colors">
                                        <div className="space-y-1">
                                            <span className="font-label-caps text-[9px] text-zinc-500">{item.name}</span>
                                            <div className="h-1 w-48 bg-zinc-950 rounded-full overflow-hidden">
                                                <motion.div 
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${item.score}%` }}
                                                    className="h-full bg-cyan-400"
                                                />
                                            </div>
                                        </div>
                                        <span className={cn(
                                            "font-data-mono text-[8px]",
                                            item.status === "PEAK" ? "text-cyan-400" : "text-zinc-600"
                                        )}>{item.status}</span>
                                    </div>
                                ))}
                             </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/layout";
import { 
    Zap, 
    Target, 
    Activity, 
    BarChart3, 
    TrendingUp, 
    RefreshCw, 
    Play, 
    AlertTriangle, 
    ChevronRight,
    Terminal,
    ArrowRight,
    CheckCircle2,
    XCircle,
    Info,
    Layout
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { HighVelocityTicker } from "@/components/ui/HighVelocityTicker";

interface ABTest {
    id: string;
    content_id: string;
    status: "ACTIVE" | "COMPLETED";
    variant_a_title: string;
    variant_b_title: string;
    variant_a_view_count: number;
    variant_b_view_count: number;
    target_metric: string;
    total_events: number;
    created_at: string;
    winner_variant?: string;
    confidence_level?: number;
}

interface TestDetail extends ABTest {
    variant_a: {
        title: string;
        description: string;
        view_count: number;
        click_count: number;
        conversion_count: number;
        conversion_rate: number;
    };
    variant_b: {
        title: string;
        description: string;
        view_count: number;
        click_count: number;
        conversion_count: number;
        conversion_rate: number;
    };
    statistics: {
        significant: boolean;
        confidence_level: number;
        winner: string | null;
        p_value: number | null;
        effect_size: number;
        interpretation: string;
    };
    winner_variant: string | null;
}

export default function ABTestingStudio() {
    const [activeTests, setActiveTests] = useState<ABTest[]>([]);
    const [completedTests, setCompletedTests] = useState<ABTest[]>([]);
    const [selectedTestId, setSelectedTestId] = useState<string | null>(null);
    const [testDetail, setTestDetail] = useState<TestDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        setIsLoading(true);
        await Promise.all([
            withRealFallback<{ active_tests: ABTest[] }>(
                () => fetch(`${API_BASE}/ab-testing/tests/active`, { headers }),
                { fallback: { active_tests: [] }, onSuccess: (data) => setActiveTests(data.active_tests) }
            ),
            withRealFallback<{ completed_tests: ABTest[] }>(
                () => fetch(`${API_BASE}/ab-testing/tests/completed`, { headers }),
                { fallback: { completed_tests: [] }, onSuccess: (data) => setCompletedTests(data.completed_tests) }
            )
        ]);
        setIsLoading(false);
    }, []);

    const fetchDetail = useCallback(async (testId: string) => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await withRealFallback<TestDetail>(
            () => fetch(`${API_BASE}/ab-testing/test/${testId}`, { headers }),
            { 
                fallback: null as any, 
                onSuccess: (data) => setTestDetail(data)
            }
        );
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        if (selectedTestId) {
            fetchDetail(selectedTestId);
        }
    }, [selectedTestId, fetchDetail]);

    const handleDetermineWinner = async (testId: string) => {
        setIsProcessing(true);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/ab-testing/test/${testId}/determine-winner`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    if (data.status === "winner_determined") {
                        toast.success(`Winner Determined: Variant ${data.winner}`);
                        fetchData();
                        fetchDetail(testId);
                    } else {
                        toast.info(data.message || "Test inconclusive yet");
                    }
                },
                onFallback: (err) => toast.error("Calculation Error", { description: err.message })
            }
        );
        setIsProcessing(false);
    };

    const handleTriggerEvolution = async (parentId: string) => {
        setIsProcessing(true);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/ab-testing/evolution/${parentId}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    toast.success("Flywheel Evolution Complete", { description: "Pruning underperforming variants and scaling winner." });
                    fetchData();
                },
                onFallback: (err) => toast.error("Evolution Failed", { description: err.message })
            }
        );
        setIsProcessing(false);
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                
                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    <HighVelocityTicker />

                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                        <div className="space-y-6">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 120 }}
                                className="h-1 bg-cyan-400 shadow-[0_0_20px_#00fbfb]"
                            />
                            <div className="space-y-2">
                                <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none">
                                    Neural A/B <span className="text-hollow">Studio</span>
                                </h1>
                                <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3 uppercase tracking-widest">
                                    <Activity className="h-3 w-3 text-cyan-400 animate-pulse" />
                                    Experiment Hub // Statistical_Confidence: {testDetail?.statistics?.confidence_level || "0"}%
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="surface-glass p-6 text-right">
                                <span className="font-data-mono text-[8px] text-zinc-600 uppercase block mb-1">Active Clusters</span>
                                <span className="text-xl font-bold text-white tabular-nums tracking-tighter">{activeTests.length}</span>
                            </div>
                            <button 
                                onClick={fetchData}
                                className="action-primary h-20 px-12 text-[10px] tracking-widest uppercase font-bold"
                            >
                                <RefreshCw className={cn("h-4 w-4 mr-3", isLoading && "animate-spin")} />
                                Resync_Experiments
                            </button>
                        </div>
                    </header>

                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12 items-start">
                        {/* EXPERIMENT LIST */}
                        <div className="xl:col-span-4 space-y-8">
                            <section className="surface-glass rim-light p-8 space-y-6">
                                <h3 className="font-label-caps text-[10px] text-zinc-500 flex items-center gap-3 uppercase tracking-[0.2em]">
                                    <Terminal className="h-4 w-4 text-cyan-400" />
                                    Active Experiments
                                </h3>
                                
                                <div className="space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar">
                                    {activeTests.length === 0 && (
                                        <div className="py-20 text-center opacity-30 flex flex-col items-center gap-4">
                                            <BarChart3 className="h-12 w-12" />
                                            <p className="text-[10px] font-bold uppercase tracking-widest">No Active Tests</p>
                                        </div>
                                    )}
                                    {activeTests.map(test => (
                                        <button
                                            key={test.id}
                                            onClick={() => setSelectedTestId(test.id)}
                                            className={cn(
                                                "w-full p-6 text-left border transition-all group relative overflow-hidden",
                                                selectedTestId === test.id 
                                                    ? "bg-cyan-400/5 border-cyan-400/30" 
                                                    : "bg-white/2 border-white/5 hover:border-white/10"
                                            )}
                                        >
                                            <div className="flex justify-between items-start mb-4">
                                                <div className="h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#00fbfb]" />
                                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{test.target_metric}</span>
                                            </div>
                                            <h4 className="text-sm font-bold text-white mb-2 uppercase truncate">{test.variant_a_title} vs {test.variant_b_title}</h4>
                                            <div className="flex items-center justify-between text-[10px] font-data-mono text-zinc-500">
                                                <span>{test.total_events} Samples</span>
                                                <ChevronRight className={cn("h-4 w-4 transition-transform", selectedTestId === test.id && "translate-x-1 text-cyan-400")} />
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </section>

                            <section className="surface-glass rim-light p-8 space-y-6 bg-zinc-950/40">
                                <h3 className="font-label-caps text-[10px] text-zinc-500 uppercase tracking-[0.2em]">History_Log</h3>
                                <div className="space-y-4">
                                    {completedTests.slice(0, 3).map(test => (
                                        <div key={test.id} className="p-4 border-l-2 border-emerald-500 bg-white/2 flex justify-between items-center">
                                            <div>
                                                <p className="text-[10px] font-bold text-white uppercase truncate max-w-[150px]">{test.variant_a_title}</p>
                                                <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">Confidence: {test.confidence_level}%</span>
                                            </div>
                                            <div className="text-[8px] font-bold text-emerald-500 uppercase">WINNER: {test.winner_variant}</div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </div>

                        {/* DETAIL WORKSPACE */}
                        <div className="xl:col-span-8">
                            <AnimatePresence mode="wait">
                                {testDetail ? (
                                    <motion.div
                                        key={testDetail.id}
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        className="space-y-10"
                                    >
                                        <section className="surface-glass rim-light p-12 space-y-12 relative overflow-hidden">
                                            <div className="absolute top-0 right-0 p-8">
                                                <div className={cn(
                                                    "px-6 py-2 rounded-full text-[10px] font-bold tracking-widest border uppercase",
                                                    testDetail.statistics.significant 
                                                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                                                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                                )}>
                                                    {testDetail.statistics.significant ? "STATISTICALLY_SIGNIFICANT" : "COLLECTING_SIGNALS"}
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <span className="font-data-mono text-[10px] text-cyan-400 uppercase tracking-[0.3em]">Neural Deep Dive</span>
                                                <h2 className="text-3xl font-bold text-white uppercase tracking-tighter leading-none">
                                                    Analysis: {testDetail.variant_a_title} <span className="text-zinc-700">/</span> {testDetail.variant_b_title}
                                                </h2>
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                                {/* Variant A Card */}
                                                <div className="p-8 bg-white/2 border border-white/5 space-y-8 relative overflow-hidden group">
                                                    {testDetail.winner_variant === "A" && <div className="absolute top-0 right-0 h-1 w-24 bg-emerald-500" />}
                                                    <div className="flex justify-between items-start">
                                                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Variant A (Control)</span>
                                                        {testDetail.winner_variant === "A" && <CheckCircle2 className="h-5 w-5 text-emerald-500" />}
                                                    </div>
                                                    <div className="space-y-2">
                                                        <h4 className="text-lg font-bold text-white uppercase">{testDetail.variant_a.title}</h4>
                                                        <p className="text-[10px] text-zinc-500 leading-relaxed uppercase">{testDetail.variant_a.description || "Baseline performance variant."}</p>
                                                    </div>
                                                    <div className="flex items-end justify-between pt-6 border-t border-white/5">
                                                        <div>
                                                            <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-1">Conversion Rate</span>
                                                            <span className="text-3xl font-bold text-white">{(testDetail.variant_a.conversion_rate * 100).toFixed(2)}%</span>
                                                        </div>
                                                        <div className="text-right">
                                                            <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-1">Samples</span>
                                                            <span className="text-xl font-bold text-zinc-400">{(testDetail.variant_a.view_count / 1000).toFixed(1)}K</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Variant B Card */}
                                                <div className="p-8 bg-white/2 border border-white/5 space-y-8 relative overflow-hidden group">
                                                    {testDetail.winner_variant === "B" && <div className="absolute top-0 right-0 h-1 w-24 bg-emerald-500" />}
                                                    <div className="flex justify-between items-start">
                                                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Variant B (Challenger)</span>
                                                        {testDetail.winner_variant === "B" && <CheckCircle2 className="h-5 w-5 text-emerald-500" />}
                                                    </div>
                                                    <div className="space-y-2">
                                                        <h4 className="text-lg font-bold text-white uppercase">{testDetail.variant_b.title}</h4>
                                                        <p className="text-[10px] text-zinc-500 leading-relaxed uppercase">{testDetail.variant_b.description || "Optimization challenger variant."}</p>
                                                    </div>
                                                    <div className="flex items-end justify-between pt-6 border-t border-white/5">
                                                        <div>
                                                            <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-1">Conversion Rate</span>
                                                            <span className={cn(
                                                                "text-3xl font-bold",
                                                                testDetail.variant_b.conversion_rate > testDetail.variant_a.conversion_rate ? "text-emerald-400" : "text-white"
                                                            )}>{(testDetail.variant_b.conversion_rate * 100).toFixed(2)}%</span>
                                                        </div>
                                                        <div className="text-right">
                                                            <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-1">Samples</span>
                                                            <span className="text-xl font-bold text-zinc-400">{(testDetail.variant_b.view_count / 1000).toFixed(1)}K</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* STATS HUD */}
                                            <div className="p-10 bg-cyan-400/5 border-y border-cyan-400/20 flex flex-col md:flex-row items-center justify-between gap-10">
                                                <div className="flex items-center gap-8">
                                                    <div className="h-24 w-24 rounded-full border-4 border-white/5 flex items-center justify-center relative">
                                                        <div className="absolute inset-2 border-2 border-cyan-400/30 rounded-full animate-pulse" />
                                                        <span className="text-2xl font-bold text-white tracking-tighter">{testDetail.statistics.confidence_level.toFixed(1)}%</span>
                                                    </div>
                                                    <div className="space-y-2">
                                                        <h5 className="font-data-mono text-[10px] text-zinc-500 uppercase tracking-widest">Statistical Power</h5>
                                                        <p className="text-sm font-bold text-white uppercase tracking-tight">Effect Size: <span className="text-cyan-400">{testDetail.statistics.effect_size.toFixed(4)} ({testDetail.statistics.interpretation})</span></p>
                                                        <p className="text-[9px] font-bold text-zinc-600 uppercase">P-VALUE: {testDetail.statistics.p_value?.toFixed(4) || "N/A"}</p>
                                                    </div>
                                                </div>

                                                <div className="flex gap-4">
                                                    <button 
                                                        onClick={() => handleDetermineWinner(testDetail.id)}
                                                        disabled={isProcessing || testDetail.status === "COMPLETED"}
                                                        className="px-10 py-5 bg-white text-black font-bold text-[10px] uppercase tracking-widest hover:bg-cyan-400 transition-all disabled:opacity-50"
                                                    >
                                                        Determine Winner
                                                    </button>
                                                    <button 
                                                        onClick={() => handleTriggerEvolution(testDetail.content_id)}
                                                        disabled={isProcessing}
                                                        className="px-10 py-5 bg-cyan-400/10 border border-cyan-400/30 text-cyan-400 font-bold text-[10px] uppercase tracking-widest hover:bg-cyan-400 hover:text-black transition-all flex items-center gap-3"
                                                    >
                                                        <Zap className="h-4 w-4" />
                                                        Trigger Flywheel
                                                    </button>
                                                </div>
                                            </div>
                                        </section>

                                        {/* ADVISORY HUD */}
                                        <div className="surface-glass p-8 flex items-start gap-6 bg-purple-500/5 border-purple-500/10">
                                            <Info className="h-5 w-5 text-purple-400 shrink-0 mt-1" />
                                            <div className="space-y-2">
                                                <h6 className="text-[10px] font-bold text-white uppercase tracking-widest">Flywheel Advisory</h6>
                                                <p className="text-[11px] text-zinc-500 leading-relaxed font-medium">
                                                    Running an evolution cycle will automatically prune the bottom 70% of variants for this parent job and prepare the winner for immediate iteration across the propagation mesh.
                                                </p>
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <div className="h-[800px] flex flex-col items-center justify-center space-y-10 opacity-40">
                                        <div className="w-48 h-48 relative">
                                            <motion.div 
                                                animate={{ rotate: 360 }}
                                                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                                                className="absolute inset-0 border border-cyan-400/10 rounded-full border-t-cyan-400/40"
                                            />
                                            <div className="absolute inset-8 rounded-full bg-white/5 flex items-center justify-center">
                                                <BarChart3 className="h-16 w-16 text-zinc-600" />
                                            </div>
                                        </div>
                                        <div className="text-center space-y-4">
                                            <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-[0.5em]">Workspace_Idle</h3>
                                            <p className="font-data-mono text-[9px] text-zinc-700 uppercase tracking-widest">Select An active experiment to initialize analysis</p>
                                        </div>
                                    </div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

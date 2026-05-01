"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
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
    Layout,
    FlaskConical,
    Microscope,
    History,
    Dna,
    Cpu,
    Radar,
    Database,
    ShieldCheck
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

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
    winner_variant?: string | null;
    confidence_level?: number;
}

export default function ABTestingStudio() {
    const [activeEngine, setActiveEngine] = useState("lab");
    const [activeTests, setActiveTests] = useState<ABTest[]>([]);
    const [completedTests, setCompletedTests] = useState<ABTest[]>([]);
    const [selectedTestId, setSelectedTestId] = useState<string | null>(null);
    const [testDetail, setTestDetail] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const [logs, setLogs] = useState<string[]>(["LAB_INITIALIZED", "SYNCHRONIZING_NEURAL_EXPERIMENTS"]);

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

        setLogs(prev => [`[ANALYSIS] Pulling deep metrics for Node: ${testId}`, ...prev]);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/ab-testing/test/${testId}`, { headers }),
            { 
                fallback: null, 
                onSuccess: (data) => {
                    setTestDetail(data);
                    setActiveEngine("analysis");
                    setLogs(prev => [`[SUCCESS] Neural mapping complete. Confidence: ${data.statistics?.confidence_level}%`, ...prev]);
                }
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

        setLogs(prev => [`[WINNER] Calculating statistical significance...`, ...prev]);
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
                        setLogs(prev => [`[SUCCESS] Variant ${data.winner} is the superior pattern.`, ...prev]);
                        fetchData();
                        fetchDetail(testId);
                    } else {
                        toast.info(data.message || "Test inconclusive yet");
                        setLogs(prev => [`[INFO] ${data.message || "Sample size insufficient."}`, ...prev]);
                    }
                }
            }
        );
        setIsProcessing(false);
    };

    const handleTriggerEvolution = async (parentId: string) => {
        setIsProcessing(true);
        const token = await getAuthToken();
        if (!token) return;

        setLogs(prev => [`[EVOLUTION] Triggering Flywheel Neural Evolution...`, ...prev]);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/ab-testing/evolution/${parentId}`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ parent_id: parentId })
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Flywheel Evolution Complete");
                    setLogs(prev => [`[SUCCESS] New neural cluster established.`, ...prev]);
                    fetchData();
                }
            }
        );
        setIsProcessing(false);
    };

    // Prepare Agent Data
    const agents = [
        { id: "STAT_01", name: "Bayesian Analyst", icon: BarChart3, status: "ACTIVE" as any, latency: 12, load: 2, details: "Analyzing Variances" },
        { id: "NEURAL_01", name: "Pattern Injector", icon: Dna, status: "ACTIVE" as any, latency: 145, load: 32, details: "Cloning Winning Nodes" },
        { id: "DATA_01", name: "Vault Synchronizer", icon: Database, status: "IDLE" as any, latency: 2, load: 0, details: "Standby" },
    ];

    return (
        <CommandCenterLayout
            title="NEURAL AB STUDIO"
            subtitle="STATISTICAL_EVOLUTION_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "lab", label: "Active Lab", icon: FlaskConical },
                        { id: "analysis", label: "Neural Analysis", icon: Microscope },
                        { id: "vault", label: "Experiment Vault", icon: History },
                        { id: "logs", label: "Evolution Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Lab Metrics</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Active</span>
                                <span className="text-xl font-bold text-white">{activeTests.length}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Archived</span>
                                <span className="text-xl font-bold text-zinc-500">{completedTests.length}</span>
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
                        {activeEngine === "lab" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {activeTests.map((test) => (
                                    <DesignCard 
                                        key={test.id}
                                        title={`${test.variant_a_title} VS ${test.variant_b_title}`}
                                        status="Active"
                                        metrics={[
                                            { label: "Samples", value: test.total_events, color: "text-cyan-400" },
                                            { label: "Target", value: test.target_metric, color: "text-zinc-500" }
                                        ]}
                                        footerInfo={`ID: ${test.id}`}
                                        toolsStatus="Live Polling"
                                        onClick={() => setSelectedTestId(test.id)}
                                    />
                                ))}
                                {activeTests.length === 0 && (
                                    <div className="col-span-full py-40 flex flex-col items-center justify-center space-y-6 opacity-30 grayscale">
                                        <FlaskConical className="h-16 w-16" />
                                        <p className="text-[10px] font-bold uppercase tracking-[0.5em]">No active experiments</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "analysis" && (
                            <div className="space-y-12 overflow-y-auto custom-scrollbar flex-1 p-1">
                                {testDetail ? (
                                    <>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="p-10 rounded-[32px] bg-[#0F0F11] border border-white/5 space-y-8 relative overflow-hidden group">
                                                {testDetail.winner_variant === "A" && <div className="absolute top-0 right-0 h-1 w-32 bg-emerald-500 shadow-[0_0_15px_#10b981]" />}
                                                <div className="flex justify-between items-start">
                                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Variant A (Control)</span>
                                                    {testDetail.winner_variant === "A" && <CheckCircle2 className="h-5 w-5 text-emerald-500" />}
                                                </div>
                                                <h3 className="text-2xl font-bold text-white uppercase">{testDetail.variant_a.title}</h3>
                                                <div className="flex items-end justify-between pt-8 border-t border-white/5">
                                                    <div>
                                                        <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-2">Conversion Rate</span>
                                                        <span className="text-4xl font-bold text-white">{(testDetail.variant_a.conversion_rate * 100).toFixed(2)}%</span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="p-10 rounded-[32px] bg-[#0F0F11] border border-white/5 space-y-8 relative overflow-hidden group">
                                                {testDetail.winner_variant === "B" && <div className="absolute top-0 right-0 h-1 w-32 bg-emerald-500 shadow-[0_0_15px_#10b981]" />}
                                                <div className="flex justify-between items-start">
                                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Variant B (Challenger)</span>
                                                    {testDetail.winner_variant === "B" && <CheckCircle2 className="h-5 w-5 text-emerald-500" />}
                                                </div>
                                                <h3 className="text-2xl font-bold text-white uppercase">{testDetail.variant_b.title}</h3>
                                                <div className="flex items-end justify-between pt-8 border-t border-white/5">
                                                    <div>
                                                        <span className="text-[9px] font-bold text-zinc-600 uppercase block mb-2">Conversion Rate</span>
                                                        <span className={cn("text-4xl font-bold", testDetail.variant_b.conversion_rate > testDetail.variant_a.conversion_rate ? "text-emerald-400" : "text-white")}>
                                                            {(testDetail.variant_b.conversion_rate * 100).toFixed(2)}%
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="p-10 rounded-[32px] bg-cyan-500/5 border border-cyan-500/10 flex flex-col md:flex-row items-center justify-between gap-10">
                                            <div className="flex items-center gap-8">
                                                <div className="h-24 w-24 rounded-full border-4 border-white/5 flex items-center justify-center relative">
                                                    <div className="absolute inset-2 border-2 border-cyan-400/30 rounded-full animate-pulse" />
                                                    <span className="text-2xl font-bold text-white">{testDetail.statistics?.confidence_level.toFixed(1)}%</span>
                                                </div>
                                                <div className="space-y-2">
                                                    <h5 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Statistical Power</h5>
                                                    <p className="text-sm font-bold text-white uppercase">{testDetail.statistics?.interpretation}</p>
                                                </div>
                                            </div>
                                            <div className="flex gap-4">
                                                <Button 
                                                    onClick={() => handleDetermineWinner(testDetail.id)}
                                                    disabled={isProcessing || testDetail.status === "COMPLETED"}
                                                    className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold h-16 px-10 rounded-2xl"
                                                >
                                                    Determine Winner
                                                </Button>
                                                <Button 
                                                    onClick={() => handleTriggerEvolution(testDetail.content_id)}
                                                    disabled={isProcessing}
                                                    variant="outline"
                                                    className="border-cyan-400/30 text-cyan-400 h-16 px-10 rounded-2xl gap-2"
                                                >
                                                    <Dna className="h-4 w-4" />
                                                    Scale Winner
                                                </Button>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-30 py-40">
                                        <Microscope className="h-16 w-16" />
                                        <p className="text-[10px] font-bold uppercase tracking-[0.5em]">Select an experiment for deep analysis</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "vault" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar flex-1 p-1">
                                {completedTests.map((test) => (
                                    <DesignCard 
                                        key={test.id}
                                        title={`${test.variant_a_title} VS ${test.variant_b_title}`}
                                        status="Completed"
                                        metrics={[
                                            { label: "Winner", value: `Variant ${test.winner_variant || "---"}`, color: "text-emerald-400" },
                                            { label: "Confidence", value: `${test.confidence_level || 0}%`, color: "text-zinc-500" }
                                        ]}
                                        footerInfo={`Finished: ${new Date(test.created_at).toLocaleDateString()}`}
                                        toolsStatus="Archived"
                                    />
                                ))}
                            </div>
                        )}

                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Evolution Logs</span>
                                <span className="text-[8px] font-mono text-cyan-500/50">NEURAL_LAB_ACTIVE</span>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[ANALYSIS]") ? "text-cyan-400" :
                                            log.includes("[SUCCESS]") ? "text-emerald-500" :
                                            log.includes("[WINNER]") ? "text-amber-500" :
                                            log.includes("[EVOLUTION]") ? "text-violet-500" : "text-zinc-600"
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

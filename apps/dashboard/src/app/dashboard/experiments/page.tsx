"use client";

import React, { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/layout";
import { 
    Activity, 
    Zap, 
    TrendingUp, 
    CheckCircle2, 
    Plus, 
    Trash2, 
    RefreshCw,
    BarChart2,
    FlaskConical,
    Target,
    ArrowRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { cn } from "@/lib/utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function ExperimentsPage() {
    const [activeTests, setActiveTests] = useState<any[]>([]);
    const [completedTests, setCompletedTests] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    
    // Form state
    const [newTest, setNewTest] = useState({
        content_id: "global", // Default or user provided
        variant_a_title: "",
        variant_b_title: "",
        target_metric: "views"
    });

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback<any>((signal) => fetch(`${API_BASE}/ab-testing/tests/active`, { headers, signal }),
                {
                    fallback: { active_tests: [] },
                    onSuccess: (data) => setActiveTests(data.active_tests || [])
                }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/ab-testing/tests/completed`, { headers, signal }),
                {
                    fallback: { completed_tests: [] },
                    onSuccess: (data) => setCompletedTests(data.completed_tests || [])
                }
            )
        ]);
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleCreateTest = async () => {
        if (!newTest.variant_a_title || !newTest.variant_b_title) {
            toast.error("Validation Error", { description: "Both variant titles are required." });
            return;
        }

        setIsCreating(true);
        const token = await getAuthToken();
        try {
            const res = await fetch(`${API_BASE}/ab-testing/test/start`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(newTest)
            });

            if (!res.ok) throw new Error("Failed to initialize test");
            
            toast.success("Experiment Initialized", { description: "Variant tracking is now active." });
            setNewTest({ content_id: "global", variant_a_title: "", variant_b_title: "", target_metric: "views" });
            fetchData();
        } catch (err) {
            toast.error("Initialization Failed");
        } finally {
            setIsCreating(false);
        }
    };

    const handleDetermineWinner = async (testId: string) => {
        const token = await getAuthToken();
        try {
            const res = await fetch(`${API_BASE}/ab-testing/test/${testId}/determine-winner`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });
            const data = await res.json();
            
            if (data.status === "winner_determined") {
                toast.success("Winner Determined!", { description: `Variant ${data.data.winner} is the winner with ${data.data.confidence} confidence.` });
                fetchData();
            } else if (data.status === "insufficient_data") {
                toast.info("Insufficient Data", { description: data.message });
            } else {
                toast.warning("Inconclusive", { description: data.message || "Not enough statistical evidence yet." });
            }
        } catch (err) {
            toast.error("Statistical Analysis Failed");
        }
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20 animate-fade-in">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-violet-500 rounded-full" />
                            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-violet-400">Laboratory Alpha</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold tracking-tight uppercase text-white leading-none">
                            Experimental <span className="text-cyan-400">Protocol</span>
                        </h1>
                        <p className="text-slate-500 font-medium max-w-xl">
                            Run high-fidelity A/B tests on your viral hooks and scripts using Bayesian statistical significance.
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <Card variant="solid" className="px-6 py-4 flex flex-col items-end gap-1 rounded-2xl">
                            <span className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Active Tests</span>
                            <span className="text-xl font-bold text-white tabular-nums">{activeTests.length}</span>
                        </Card>
                        <Button 
                            variant="primary" 
                            size="lg" 
                            className="rounded-full px-8 shadow-lg shadow-violet-900/20 bg-violet-500 hover:bg-violet-400"
                            onClick={() => document.getElementById('new-experiment')?.scrollIntoView({ behavior: 'smooth' })}
                        >
                            <Plus className="h-4 w-4 mr-2" />
                            NEW_EXPERIMENT
                        </Button>
                    </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-10">
                    {/* NEW EXPERIMENT FORM */}
                    <div className="xl:col-span-1 space-y-8">
                        <Card id="new-experiment" variant="solid" className="p-8 space-y-8 rounded-2xl border-white/5 bg-slate-900/40 relative overflow-hidden">
                            <div className="absolute inset-0 pointer-events-none opacity-5 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(0,251,251,0.03),rgba(0,0,0,0),rgba(0,251,251,0.03))] bg-size-[100%_4px,3px_100%]" />
                            
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                                    <FlaskConical className="h-5 w-5 text-violet-400" />
                                </div>
                                <h3 className="font-bold uppercase tracking-tight text-white">Initialize Lab</h3>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 ml-1">Variant A Title</label>
                                    <Input 
                                        value={newTest.variant_a_title}
                                        onChange={(e) => setNewTest({...newTest, variant_a_title: e.target.value})}
                                        placeholder="e.g. The Stoic Secret..."
                                        className="bg-black/40 border-white/10"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 ml-1">Variant B Title</label>
                                    <Input 
                                        value={newTest.variant_b_title}
                                        onChange={(e) => setNewTest({...newTest, variant_b_title: e.target.value})}
                                        placeholder="e.g. Why Stoics Fail..."
                                        className="bg-black/40 border-white/10"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 ml-1">Target Metric</label>
                                    <select 
                                        value={newTest.target_metric}
                                        onChange={(e) => setNewTest({...newTest, target_metric: e.target.value})}
                                        className="w-full bg-black/40 border border-white/10 rounded-2xl p-4 text-xs font-bold uppercase tracking-widest text-slate-300 outline-none focus:border-violet-400/50 transition-all"
                                    >
                                        <option value="views">Views (Retention)</option>
                                        <option value="clicks">Clicks (CTR)</option>
                                        <option value="conversions">Conversions (Sales)</option>
                                    </select>
                                </div>

                                <Button 
                                    onClick={handleCreateTest}
                                    disabled={isCreating}
                                    variant="primary" 
                                    className="w-full py-6 rounded-2xl bg-violet-500 hover:bg-violet-400 shadow-glow-purple/10"
                                >
                                    {isCreating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4 mr-2" />}
                                    INJECT_EXPERIMENT
                                </Button>
                            </div>
                        </Card>

                        {/* STATS PREVIEW */}
                        <div className="glass-card p-8 rounded-2xl bg-cyan-500/5 border-cyan-500/10 space-y-6">
                            <div className="flex items-center gap-3">
                                <Target className="h-4 w-4 text-cyan-500" />
                                <span className="text-[9px] font-bold uppercase tracking-widest text-cyan-500">Neural Accuracy</span>
                            </div>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Confidence Baseline</span>
                                    <span className="text-sm font-bold text-white">95.0%</span>
                                </div>
                                <div className="h-1 bg-slate-900 rounded-full overflow-hidden">
                                    <div className="h-full bg-cyan-500 w-[95%] shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                                </div>
                                <p className="text-[10px] text-slate-500 leading-relaxed font-medium">
                                    Experiments use Z-test proportions to ensure statistical significance before declaring winners.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* ACTIVE EXPERIMENTS */}
                    <div className="xl:col-span-2 space-y-8">
                        <div className="flex items-center justify-between border-b border-white/5 pb-6">
                            <h2 className="text-2xl font-bold text-white uppercase tracking-tight flex items-center gap-3">
                                <Activity className="h-6 w-6 text-emerald-500" />
                                Live Egress Tests
                            </h2>
                            <button onClick={fetchData} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                                <RefreshCw className={cn("h-4 w-4 text-slate-500", isLoading && "animate-spin")} />
                            </button>
                        </div>

                        {isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin" />
                            </div>
                        ) : activeTests.length === 0 ? (
                            <div className="h-64 surface-glass rounded-2xl flex flex-col items-center justify-center text-center p-12 border-dashed border-white/5">
                                <FlaskConical className="h-12 w-12 text-slate-800 mb-4" />
                                <h3 className="text-white font-bold uppercase tracking-tight">No Active Protocols</h3>
                                <p className="text-slate-500 text-xs mt-1">Initialize a new experiment to begin neural testing.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 gap-6">
                                {activeTests.map((test) => (
                                    <motion.div 
                                        key={test.id}
                                        layout
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="surface-glass p-8 rounded-2xl border border-white/5 hover:border-violet-500/30 transition-all group"
                                    >
                                        <div className="flex flex-col md:flex-row gap-8">
                                            <div className="flex-1 space-y-6">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[9px] font-bold text-violet-400 uppercase tracking-[0.2em]">Experiment #{test.id.slice(-4)}</span>
                                                    <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">{test.target_metric} focus</span>
                                                </div>
                                                
                                                <div className="grid grid-cols-2 gap-8">
                                                    <div className="space-y-4">
                                                        <div className="flex items-center gap-2">
                                                            <div className="h-2 w-2 bg-violet-400 rounded-full" />
                                                            <span className="text-xs font-bold text-slate-300 uppercase truncate">{test.variant_a_title}</span>
                                                        </div>
                                                        <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                                                            <div 
                                                                className="h-full bg-violet-400" 
                                                                style={{ width: `${(test.variant_a_view_count / (test.total_events || 1)) * 100}%` }} 
                                                            />
                                                        </div>
                                                        <span className="text-lg font-bold text-white">{test.variant_a_view_count} <span className="text-[10px] text-slate-600 font-medium">Events</span></span>
                                                    </div>
                                                    <div className="space-y-4">
                                                        <div className="flex items-center gap-2">
                                                            <div className="h-2 w-2 bg-cyan-500 rounded-full" />
                                                            <span className="text-xs font-bold text-slate-300 uppercase truncate">{test.variant_b_title}</span>
                                                        </div>
                                                        <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                                                            <div 
                                                                className="h-full bg-cyan-500" 
                                                                style={{ width: `${(test.variant_b_view_count / (test.total_events || 1)) * 100}%` }} 
                                                            />
                                                        </div>
                                                        <span className="text-lg font-bold text-white">{test.variant_b_view_count} <span className="text-[10px] text-slate-600 font-medium">Events</span></span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="md:w-48 flex flex-col justify-between pt-4 md:pt-0">
                                                <div className="text-center space-y-1">
                                                    <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Statistical Power</p>
                                                    <p className="text-2xl font-bold text-white">{Math.min(100, Math.round((test.total_events / 30) * 100))}%</p>
                                                </div>
                                                <Button 
                                                    onClick={() => handleDetermineWinner(test.id)}
                                                    variant="outline" 
                                                    size="sm" 
                                                    className="w-full py-4 rounded-2xl border-white/10 hover:border-violet-500/50 hover:bg-violet-500/5 text-[10px] font-bold uppercase tracking-widest"
                                                >
                                                    ANALYZE_WINNER
                                                </Button>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}

                        {/* COMPLETED TESTS */}
                        <div className="space-y-6 pt-12">
                            <div className="flex items-center gap-3">
                                <CheckCircle2 className="h-5 w-5 text-slate-700" />
                                <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-slate-500">Completed Protocols</h3>
                            </div>
                            
                            <div className="space-y-4">
                                {completedTests.map((test) => (
                                    <div key={test.id} className="surface-glass p-6 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-emerald-500/20 transition-all">
                                        <div className="flex items-center gap-6">
                                            <div className="h-10 w-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                            </div>
                                            <div className="space-y-1">
                                                <h4 className="text-sm font-bold text-white uppercase tracking-tight">
                                                    Winner: <span className="text-emerald-400">{test.winner_variant === 'A' ? test.variant_a_title : test.variant_b_title}</span>
                                                </h4>
                                                <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                                                    Confidence: {test.confidence_level?.toFixed(1)}% • Finished {new Date(test.completed_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="text-right">
                                                <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">P-Value</p>
                                                <p className="text-xs font-bold text-white tabular-nums">{test.p_value?.toFixed(4)}</p>
                                            </div>
                                            <ArrowRight className="h-4 w-4 text-slate-800 group-hover:text-emerald-500 transition-colors" />
                                        </div>
                                    </div>
                                ))}
                                {completedTests.length === 0 && (
                                    <p className="text-[10px] text-slate-700 font-bold uppercase tracking-widest text-center py-8">No archived experiments found.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

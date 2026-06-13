"use client";

import React, { useState } from "react";
import DashboardLayout from "@/components/layout";
import { 
    Cpu, 
    Users,
    Shield,
    Workflow,
    Terminal,
    Sparkles,
    RefreshCw
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function IntelligencePage() {
    const [reasoningPrompt, setReasoningPrompt] = useState("");
    const [reasoningResult, setReasoningResult] = useState<any>(null);
    const [isReasoning, setIsReasoning] = useState(false);
    const [activeTab, setActiveTab] = useState<'reasoning' | 'crews'>('reasoning');
    
    // Crew states
    const [crewTopic, setCrewTopic] = useState("");
    const [crewResult, setCrewResult] = useState<any>(null);
    const [isCrewRunning, setIsCrewRunning] = useState(false);

    const handleReason = async () => {
        if (!reasoningPrompt.trim()) return;
        setIsReasoning(true);
        const token = await getAuthToken();
        try {
            const res = await fetch(`${API_BASE}/reason`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ prompt: reasoningPrompt, depth: 3 })
            });
            const data = await res.json();
            if (res.ok) {
                setReasoningResult(data.data);
                toast.success("Reasoning Cycle Complete");
            } else {
                throw new Error(data.detail || "Reasoning failed");
            }
        } catch (err: any) {
            toast.error("Reasoning Error", { description: err.message });
        } finally {
            setIsReasoning(false);
        }
    };

    const handleRunCrew = async (type: 'content' | 'affiliate') => {
        if (!crewTopic.trim()) {
            toast.error("Input Required", { description: "Please provide a topic for the crew." });
            return;
        }
        setIsCrewRunning(true);
        const token = await getAuthToken();
        try {
            const res = await fetch(`${API_BASE}/tools/crew/run`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ crew_type: type, topic: crewTopic })
            });
            const data = await res.json();
            if (res.ok) {
                setCrewResult(data.data.result);
                toast.success("Crew Mission Accomplished");
            } else {
                throw new Error("Crew mission failed");
            }
        } catch (err: any) {
            toast.error("Crew Error");
        } finally {
            setIsCrewRunning(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20 animate-fade-in">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-violet-500 rounded-full" />
                            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-violet-400">Neural Nexus</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold tracking-tight uppercase text-white leading-none">
                            Intelligence <span className="text-violet-400">OS</span>
                        </h1>
                        <p className="text-slate-500 font-medium max-w-xl">
                            Access high-fidelity reasoning engines and multi-agent crews for complex content strategy and execution.
                        </p>
                    </div>

                    <div className="flex p-1 bg-white/5 rounded-2xl border border-white/5">
                        <button 
                            onClick={() => setActiveTab('reasoning')}
                            className={cn(
                                "px-6 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all",
                                activeTab === 'reasoning' ? "bg-violet-500 text-white shadow-glow-purple/20" : "text-slate-500 hover:text-white"
                            )}
                        >
                            DEEP_REASONING
                        </button>
                        <button 
                            onClick={() => setActiveTab('crews')}
                            className={cn(
                                "px-6 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all",
                                activeTab === 'crews' ? "bg-violet-500 text-white shadow-glow-purple/20" : "text-slate-500 hover:text-white"
                            )}
                        >
                            AGENT_CREWS
                        </button>
                    </div>
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'reasoning' ? (
                        <motion.div 
                            key="reasoning"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="grid grid-cols-1 xl:grid-cols-12 gap-12"
                        >
                            <div className="xl:col-span-4 space-y-8">
                                <Card variant="solid" className="p-8 space-y-8 rounded-2xl border-white/5 bg-slate-900/40 relative overflow-hidden">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                                            <Cpu className="h-5 w-5 text-violet-400" />
                                        </div>
                                        <h3 className="font-bold uppercase tracking-tight text-white">Problem Injection</h3>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500 ml-1">Complexity Prompt</label>
                                            <textarea 
                                                value={reasoningPrompt}
                                                onChange={(e) => setReasoningPrompt(e.target.value)}
                                                placeholder="Explain the optimal viral strategy for a Stoicism-based TikTok account targeting Gen-Z..."
                                                className="w-full bg-black/40 border border-white/10 rounded-2xl p-6 text-sm text-slate-300 min-h-[160px] outline-none focus:border-violet-400/50 transition-all resize-none"
                                            />
                                        </div>

                                        <Button 
                                            onClick={handleReason}
                                            disabled={isReasoning}
                                            variant="primary" 
                                            className="w-full py-6 rounded-2xl bg-violet-500 hover:bg-violet-400 shadow-glow-purple/10"
                                        >
                                            {isReasoning ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
                                            TRIGGER_SYNTHESIS
                                        </Button>
                                    </div>
                                </Card>

                                <div className="glass-card p-8 rounded-2xl bg-violet-400/5 border-violet-400/10 space-y-4">
                                    <div className="flex items-center gap-3 text-violet-400">
                                        <Shield className="h-4 w-4" />
                                        <span className="text-[9px] font-bold uppercase tracking-widest">Logic Tier 10</span>
                                    </div>
                                    <p className="text-[10px] text-slate-500 leading-relaxed font-medium">
                                        The reasoning engine uses recursive depth-loops to cross-reference trends, psychological triggers, and platform algorithms.
                                    </p>
                                </div>
                            </div>

                            <div className="xl:col-span-8">
                                <Card variant="solid" className="min-h-[500px] rounded-2xl border-white/5 bg-black/20 p-10 overflow-hidden relative">
                                    {!reasoningResult && !isReasoning && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-20 opacity-20">
                                            <Terminal className="h-20 w-20 text-slate-700 mb-6" />
                                            <h3 className="text-xl font-bold text-white uppercase tracking-tight">Awaiting Neural Input</h3>
                                            <p className="text-slate-500 text-sm mt-2">Inject a prompt to begin the high-fidelity reasoning trace.</p>
                                        </div>
                                    )}

                                    {isReasoning && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center space-y-6">
                                            <div className="h-16 w-16 border-2 border-violet-500 border-t-transparent rounded-full animate-spin shadow-glow-purple/20" />
                                            <div className="space-y-1 text-center">
                                                <p className="text-xs font-bold text-white uppercase tracking-[0.4em] animate-pulse">Thinking...</p>
                                                <p className="text-[8px] text-slate-600 uppercase tracking-widest">Recursive Loop Phase {Math.floor(Date.now() / 1000) % 3 + 1}</p>
                                            </div>
                                        </div>
                                    )}

                                    {reasoningResult && (
                                        <div className="space-y-10 animate-fade-in">
                                            <div className="space-y-4">
                                                <h3 className="text-[10px] font-bold text-violet-400 uppercase tracking-widest flex items-center gap-2">
                                                    <Workflow className="h-4 w-4" />
                                                    Reasoning Trace
                                                </h3>
                                                <div className="p-6 rounded-2xl bg-white/2 border border-white/5 font-mono text-[11px] text-slate-400 whitespace-pre-wrap leading-relaxed">
                                                    {reasoningResult.trace}
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <h3 className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest flex items-center gap-2">
                                                    <CheckCircle2 className="h-4 w-4" />
                                                    Neural Answer
                                                </h3>
                                                <div className="p-8 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 text-slate-200 leading-relaxed text-lg font-medium italic">
                                                    "{reasoningResult.answer}"
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </Card>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div 
                            key="crews"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="space-y-12"
                        >
                            <div className="max-w-3xl mx-auto space-y-8">
                                <Card variant="solid" className="p-8 rounded-2xl border-white/5 bg-slate-900/40 space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-xl bg-blue-600/10 border border-blue-600/20 flex items-center justify-center">
                                            <Users className="h-5 w-5 text-blue-500" />
                                        </div>
                                        <h3 className="font-bold uppercase tracking-tight text-white">Mission Topic</h3>
                                    </div>
                                    <Input 
                                        value={crewTopic}
                                        onChange={(e) => setCrewTopic(e.target.value)}
                                        placeholder="e.g. Modern Productivity for High-Performers"
                                        className="bg-black/40 border-white/10"
                                    />
                                </Card>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <Card variant="solid" className="p-8 rounded-2xl border-white/5 hover:border-blue-500/30 transition-all cursor-pointer group" onClick={() => handleRunCrew('content')}>
                                        <div className="flex flex-col items-center text-center space-y-6">
                                            <div className="h-20 w-20 rounded-full bg-blue-600/10 border border-blue-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                                                <Workflow className="h-8 w-8 text-blue-500" />
                                            </div>
                                            <div className="space-y-2">
                                                <h3 className="text-xl font-bold text-white uppercase tracking-tight">Content Team</h3>
                                                <p className="text-xs text-slate-500 font-medium">Research, scriptwriting, and optimization agents.</p>
                                            </div>
                                            <Button variant="outline" className="w-full py-4 border-white/10 rounded-xl text-[10px] tracking-widest uppercase">Launch_Team</Button>
                                        </div>
                                    </Card>

                                    <Card variant="solid" className="p-8 rounded-2xl border-white/5 hover:border-emerald-500/30 transition-all cursor-pointer group" onClick={() => handleRunCrew('affiliate')}>
                                        <div className="flex flex-col items-center text-center space-y-6">
                                            <div className="h-20 w-20 rounded-full bg-emerald-600/10 border border-emerald-600/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                                                <Users className="h-8 w-8 text-emerald-500" />
                                            </div>
                                            <div className="space-y-2">
                                                <h3 className="text-xl font-bold text-white uppercase tracking-tight">Affiliate Team</h3>
                                                <p className="text-xs text-slate-500 font-medium">Monetization, campaign, and link placement agents.</p>
                                            </div>
                                            <Button variant="outline" className="w-full py-4 border-white/10 rounded-xl text-[10px] tracking-widest uppercase">Launch_Team</Button>
                                        </div>
                                    </Card>
                                </div>
                            </div>

                            {isCrewRunning && (
                                <div className="py-20 flex flex-col items-center justify-center space-y-6">
                                    <div className="h-16 w-16 border-2 border-blue-600 border-t-transparent rounded-full animate-spin shadow-glow-blue/20" />
                                    <p className="text-xs font-bold text-white uppercase tracking-[0.4em] animate-pulse">Agents Collaborating...</p>
                                </div>
                            )}

                            {crewResult && (
                                <motion.div 
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="max-w-4xl mx-auto"
                                >
                                    <Card variant="solid" className="p-10 rounded-2xl border-white/5 bg-slate-900/40 space-y-8">
                                        <div className="flex items-center justify-between border-b border-white/5 pb-6">
                                            <h3 className="text-[10px] font-bold text-blue-500 uppercase tracking-widest flex items-center gap-3">
                                                <Terminal className="h-4 w-4" />
                                                Mission Report
                                            </h3>
                                            <Button variant="primary" size="sm" onClick={() => setCrewResult(null)} className="rounded-full px-6">DISMISS</Button>
                                        </div>
                                        <div className="prose prose-invert max-w-none text-slate-300 leading-relaxed">
                                            {typeof crewResult === 'string' ? crewResult : JSON.stringify(crewResult, null, 2)}
                                        </div>
                                    </Card>
                                </motion.div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </DashboardLayout>
    );
}

// Helper icons
function CheckCircle2(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <circle cx="12" cy="12" r="10" />
            <path d="m9 12 2 2 4-4" />
        </svg>
    )
}

"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    Cpu,
    Play,
    Pause,
    Activity,
    Terminal,
    Search,
    Layers,
    Share2,
    RefreshCw,
    AlertCircle,
    CheckCircle2,
    AlertOctagon,
    Zap,
    Target,
    ShieldCheck,
    Dna,
    Radar,
    Clock,
    Sparkles,
    ArrowUpRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";
import { useTelemetry } from "@/context/TelemetryContext";

function AutonomousContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents, logs: systemLogs, status, pulse } = useTelemetry();
    
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "launch");
    const [isRunning, setIsRunning] = useState(false);
    const [actionLogs, setActionLogs] = useState<string[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentStep, setCurrentStep] = useState("IDLE");
    const [insights, setInsights] = useState<any>(null);
    const [lastRun, setLastRun] = useState<number | null>(null);
    const [nextRun, setNextRun] = useState<number | null>(null);

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
    }, [searchParams]);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback<any>(
                () => fetch(`${API_BASE}/zero/status`, { headers }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        if (!data) return;
                        setIsRunning(data.is_running);
                        setCurrentStep(data.current_step);
                        setLastRun(data.last_run);
                        setNextRun(data.next_run);
                    }
                }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/zero/insights`, { headers }),
                {
                    fallback: null,
                    onSuccess: (data) => data && setInsights(data.insights || data)
                }
            )
        ]);
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleToggle = async () => {
        setIsProcessing(true);
        const action = isRunning ? "stop" : "start";
        const token = await getAuthToken();
        if (!token) {
            setIsProcessing(false);
            return;
        }

        setActionLogs((prev: string[]) => [`[PROTOCOL] Sending ${action.toUpperCase()} signal to Agent Zero...`, ...prev]);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/zero/${action}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setIsRunning(!isRunning);
                    setActionLogs((prev: string[]) => [`[SUCCESS] ${data?.message || `Agent Zero ${action}ed`}`, ...prev]);
                    toast.success(`Agent Zero ${action === 'start' ? 'Activated' : 'Halted'}`);
                    fetchData();
                }
            }
        );
        setIsProcessing(false);
    };

    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "ZERO",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...systemLogs.filter(l => l.module === "AGENT_ZERO" || l.module === "SYSTEM")
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

    return (
        <CommandCenterLayout
            title="AUTONOMOUS DIRECTOR"
            subtitle="AGENT_ZERO_V4.2"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "launch", label: "Launch Control", icon: Play },
                        { id: "logic", label: "Logic Flow", icon: Layers },
                        { id: "oracle", label: "Insight Oracle", icon: Sparkles },
                        { id: "market", label: "Market Pulse", icon: Radar },
                        { id: "console", label: "System Console", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                setActiveEngine(item.id);
                                router.replace(`/autonomous?engine=${item.id}`);
                            }}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && (
                                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                            )}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Loop Status</h4>
                        <div className="flex flex-col">
                            <span className={cn("text-2xl font-bold uppercase tracking-tighter", isRunning ? "text-emerald-500" : "text-white")}>
                                {isRunning ? "Running" : "Standby"}
                            </span>
                            <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">Iteration: {nextRun ? new Date(nextRun * 1000).toLocaleTimeString() : "PENDING"}</span>
                        </div>
                    </div>
                    <Button 
                        onClick={handleToggle} 
                        disabled={isProcessing} 
                        className={cn(
                            "w-full font-bold h-14 rounded-2xl transition-all",
                            isRunning ? "bg-zinc-950 border border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10" : "bg-emerald-500 text-black hover:bg-emerald-400"
                        )}
                    >
                        {isProcessing ? "Transmitting..." : (isRunning ? "Halt Director" : "Launch Director")}
                    </Button>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={cn("flex-1 pr-4 space-y-10", activeEngine !== "console" && "overflow-y-auto custom-scrollbar")}
                    >
                        {activeEngine === "launch" && (
                            <>
                                <div className="glass-card aspect-21/9 rounded-[40px] flex items-center justify-center relative overflow-hidden bg-[#0F0F11]/60 border border-white/5">
                                    <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                                    <div className="flex items-center gap-12 relative z-10">
                                        <LogicNode icon={Search} label="Scout" active={isRunning && currentStep === "SCOUTING"} pulse={currentStep === "SCOUTING"} />
                                        <Connector active={isRunning && ["SCREENING", "BRAINSTORMING", "RENDERING", "PUBLISHING", "WAITING"].includes(currentStep)} />
                                        <LogicNode icon={Cpu} label="Brain" active={isRunning && ["SCREENING", "BRAINSTORMING"].includes(currentStep)} pulse={currentStep === "BRAINSTORMING"} />
                                        <Connector active={isRunning && ["RENDERING", "PUBLISHING", "WAITING"].includes(currentStep)} />
                                        <LogicNode icon={Layers} label="Render" active={isRunning && currentStep === "RENDERING"} pulse={currentStep === "RENDERING"} />
                                        <Connector active={isRunning && ["PUBLISHING", "WAITING"].includes(currentStep)} />
                                        <LogicNode icon={Share2} label="Post" active={isRunning && currentStep === "PUBLISHING"} pulse={currentStep === "PUBLISHING"} />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                                    <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                                        <div className="flex items-center gap-3">
                                            <Sparkles className="h-4 w-4 text-emerald-500" />
                                            <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Autonomous Insight Oracle</h3>
                                        </div>
                                        {insights ? (
                                            <div className="space-y-4">
                                                <h4 className="text-3xl font-bold text-white uppercase tracking-tighter">{insights.title}</h4>
                                                <p className="text-zinc-500 text-sm leading-relaxed">{insights.hook}</p>
                                            </div>
                                        ) : (
                                            <div className="h-32 flex flex-col items-center justify-center opacity-20">
                                                <Radar className="h-10 w-10 animate-pulse" />
                                                <span className="text-[8px] font-bold mt-2">LISTENING_FOR_PULSES</span>
                                            </div>
                                        )}
                                    </div>

                                    <div className="p-10 rounded-[32px] bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-8">
                                        <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                                            <Activity className="h-8 w-8" />
                                        </div>
                                        <div className="space-y-1">
                                            <span className="text-[10px] font-bold text-emerald-500/60 uppercase tracking-widest">Self-Correction Mode</span>
                                            <p className="text-white font-bold uppercase">Dynamic Optimization Active</p>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}

                        {activeEngine === "logic" && (
                            <div className="h-full min-h-[400px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10">
                                    <Layers className="h-16 w-16 text-emerald-500 animate-pulse" />
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Logic Flow Mapping</h3>
                                    <span className="text-[10px] text-zinc-500 font-mono italic">REAL_TIME_PROCESS_VISUALIZATION_ACTIVE</span>
                                </div>
                            </div>
                        )}

                        {activeEngine === "oracle" && (
                            <div className="h-full min-h-[400px] p-12 border border-white/5 bg-[#0F0F11]/60 rounded-[40px] space-y-8">
                                <div className="flex items-center gap-4">
                                    <Sparkles className="h-8 w-8 text-emerald-500" />
                                    <h3 className="text-2xl font-black text-white uppercase tracking-tighter">Strategic Insight Oracle</h3>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="p-8 rounded-3xl bg-white/2 border border-white/5 space-y-4">
                                        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Hypothesis</label>
                                        <p className="text-white text-lg font-bold leading-tight">{insights?.title || "HYPOTHESIS_PENDING"}</p>
                                    </div>
                                    <div className="p-8 rounded-3xl bg-white/2 border border-white/5 space-y-4">
                                        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Market Alignment</label>
                                        <div className="flex items-center gap-4">
                                            <div className="h-2 flex-1 bg-white/5 rounded-full overflow-hidden">
                                                <div className="h-full bg-emerald-500 w-[78%]" />
                                            </div>
                                            <span className="text-emerald-500 font-bold">78%</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-8 rounded-3xl bg-emerald-500/5 border border-emerald-500/10">
                                    <p className="text-zinc-400 leading-relaxed italic">"{insights?.hook || "Waiting for autonomous agents to report high-confidence signals..."}"</p>
                                </div>
                            </div>
                        )}

                        {activeEngine === "market" && (
                            <div className="h-full min-h-[400px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px]">
                                <div className="flex flex-col items-center gap-6">
                                    <Radar className="h-16 w-16 text-emerald-500 animate-spin-slow" />
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Market Pulse Radar</h3>
                                    <span className="text-[10px] text-zinc-500 font-mono italic">SCANNING_GLOBAL_TREND_SIGNAL_VECTORS</span>
                                </div>
                            </div>
                        )}

                        {activeEngine === "console" && (
                            <div className="h-full flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <Terminal className="h-4 w-4 text-emerald-500" />
                                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Full Spectrum System Console</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-[8px] font-mono text-emerald-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                                        <div className={cn("h-1.5 w-1.5 rounded-full", status === "open" ? "bg-emerald-500 animate-pulse" : "bg-zinc-800")} />
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                                    {displayLogs.map((log, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-red-500" :
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

                {activeEngine !== "console" && (
                    <div className="mt-8 h-64 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                        <div className="p-4 border-b border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Terminal className="h-3 w-3 text-emerald-500" />
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">System Console</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-[8px] font-mono text-emerald-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                                <div className={cn("h-1.5 w-1.5 rounded-full", status === "open" ? "bg-emerald-500 animate-pulse" : "bg-zinc-800")} />
                            </div>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                            {displayLogs.map((log, i) => (
                                <div key={i} className="flex gap-4">
                                    <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                    <span className={cn(
                                        log.level === "ACTION" ? "text-cyan-400" :
                                        log.level === "ERROR" ? "text-red-500" :
                                        log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-600"
                                    )}>
                                        {log.module ? `[${log.module}] ` : ""}{log.message}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </CommandCenterLayout>
    );
}

function LogicNode({ icon: Icon, label, active, pulse }: any) {
    return (
        <div className="flex flex-col items-center gap-4">
            <div className={cn(
                "h-20 w-20 rounded-[32px] flex items-center justify-center transition-all duration-700 relative",
                active ? "bg-emerald-500 text-black shadow-[0_0_40px_rgba(16,185,129,0.4)]" : "bg-black/40 text-zinc-800 border border-white/5"
            )}>
                <Icon className="h-8 w-8" />
                {active && pulse && (
                    <div className="absolute inset-0 rounded-[32px] border-2 border-emerald-500 animate-ping opacity-20" />
                )}
            </div>
            <span className={cn(
                "text-[10px] font-bold uppercase tracking-widest transition-colors duration-500",
                active ? "text-emerald-500" : "text-zinc-800"
            )}>{label}</span>
        </div>
    );
}

function Connector({ active }: any) {
    return (
        <div className="h-px w-12 bg-white/5 relative">
            {active && (
                <div className="absolute inset-0 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
            )}
        </div>
    );
}

export default function AutonomousPage() {
    return (
        <Suspense fallback={null}>
            <AutonomousContent />
        </Suspense>
    );
}

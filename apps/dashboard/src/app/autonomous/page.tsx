"use client";

import React, { useState, useEffect, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import DashboardLayout from "@/components/layout";
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
    CheckCircle2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { getAuthToken } from "@/lib/auth_utils";
import { ConfirmModal } from "@/components/ui/ConfirmModal";

export default function AutonomousPage() {
    const [isRunning, setIsRunning] = useState(false);
    const [status, setStatus] = useState("Idle");
    const [logs, setLogs] = useState<string[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isConfirmStopOpen, setIsConfirmStopOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState("IDLE");
    const [insights, setInsights] = useState<any>(null);
    const [lastRun, setLastRun] = useState<number | null>(null);
    const [nextRun, setNextRun] = useState<number | null>(null);

    // --- DATA FETCHING ---
    const fetchStatus = useCallback(async () => {
        const token = getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        // Zero Status
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
                    setStatus(data.is_running ? `Autonomous Active: ${data.current_step}` : "Idle");
                }
            }
        );

        // Insights
        withRealFallback<any>(
            () => fetch(`${API_BASE}/zero/insights`, { headers }),
            {
                fallback: null,
                onSuccess: (data) => data && setInsights(data.insights || data)
            }
        );
    }, [isRunning, currentStep, lastRun, nextRun, insights]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);

        const wsUrl = API_BASE.replace("http", "ws") + "/ws/logs";
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "log" && (data.module === "AGENT_ZERO" || data.module === "SYSTEM")) {
                    setLogs(prev => [`[${data.level}] ${data.message}`, ...prev.slice(0, 49)]);
                }
            } catch (e) {}
        };

        return () => {
            clearInterval(interval);
            ws.close();
        };
    }, [fetchStatus]);

    const handleToggle = async () => {
        if (isRunning && !isConfirmStopOpen) {
            setIsConfirmStopOpen(true);
            return;
        }

        setIsProcessing(true);
        const action = isRunning ? "stop" : "start";
        const token = getAuthToken();
        if (!token) {
            setIsProcessing(false);
            return;
        }

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/zero/${action}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setIsRunning(!isRunning);
                    setStatus(!isRunning ? "Initializing Engine..." : "Halt Signal Sent");
                    setLogs(prev => [`[SYSTEM] ${data?.message || `Agent Zero ${action}ed`}`, ...prev]);
                    toast.success(`Agent Zero ${action === 'start' ? 'Activated' : 'Halted'}`);
                },
                onFallback: () => {
                    toast.error(`Failed to ${action} Agent Zero`);
                }
            }
        );
        setIsProcessing(false);
    };

    const handleForceKill = async () => {
        const token = getAuthToken();
        if (!token) return;

        toast.promise(
            fetch(`${API_BASE}/zero/kill`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                loading: 'Sending Force Kill signal...',
                success: () => {
                    setIsRunning(false);
                    setStatus("Engine Terminated");
                    setLogs(prev => [`[CRITICAL] SIGKILL sent to Agent Zero. Cleanup initiated.`, ...prev]);
                    return 'Engine Terminated via Force Kill';
                },
                error: 'Failed to send Kill signal'
            }
        );
    };

    const handleExportLogs = () => {
        const logContent = logs.join("\n");
        const blob = new Blob([logContent], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `agent_zero_logs_${new Date().toISOString()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Logs exported successfully");
    };

    const StatusCard = ({ icon: Icon, label, value, color }: any) => (
        <div className="glass-card p-6 flex items-center gap-5 transition-all hover:bg-white/[0.02]">
            <div className={cn("h-12 w-12 rounded-2xl flex items-center justify-center border", color)}>
                <Icon className="h-6 w-6" />
            </div>
            <div className="space-y-1">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">{label}</p>
                <h4 className="text-sm font-black text-white uppercase tracking-tight">{value}</h4>
            </div>
        </div>
    );

    return (
        <DashboardLayout>
            <div className="space-y-12 pb-24">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Autonomous Director</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">
                            Agent <span className="text-transparent bg-clip-text bg-linear-to-r from-emerald-400 to-emerald-600 text-hollow">Zero</span>
                        </h1>
                        <p className="text-zinc-500 font-medium max-w-xl">
                            Orchestrating the full faceless cycle: <span className="text-zinc-300 font-bold">Trend scouting, Analysis, Synthesis, and Publishing</span>.
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <ConfirmModal 
                            isOpen={isConfirmStopOpen}
                            onClose={() => setIsConfirmStopOpen(false)}
                            onConfirm={() => {
                                setIsConfirmStopOpen(false);
                                handleToggle();
                            }}
                            title="Halt Autonomous Operations?"
                            description="Stopping Agent Zero will terminate all active social scans and video pattern injections. Progress in current threads may be lost."
                            variant="danger"
                            confirmText="Halt Engine"
                        />
                        {isRunning && (
                            <motion.button
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                onClick={handleForceKill}
                                className="h-14 w-14 rounded-2xl flex items-center justify-center border border-rose-500/30 text-rose-500 hover:bg-rose-500/10 transition-all shadow-xl group"
                                title="Emergency Force Kill"
                            >
                                <AlertCircle className="h-6 w-6 group-hover:scale-110 transition-transform" />
                            </motion.button>
                        )}
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleToggle}
                            disabled={isProcessing}
                            className={cn(
                                "py-5 px-10 rounded-2xl flex items-center gap-3 shadow-2xl transition-all uppercase text-xs font-black tracking-widest",
                                isRunning
                                    ? "bg-zinc-950 border border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
                                    : "bg-emerald-500 text-black shadow-[0_0_50px_rgba(16,185,129,0.3)]"
                            )}
                        >
                            {isProcessing ? <RefreshCw className="h-5 w-5 animate-spin" /> : (isRunning ? <Pause className="h-5 w-5 fill-emerald-500" /> : <Play className="h-5 w-5 fill-black" />)}
                            {isRunning ? "Stop Director" : "Launch Director"}
                        </motion.button>
                    </div>
                </div>

                {/* Status Matrix */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatusCard
                        icon={Activity}
                        label="Engine State"
                        value={isRunning ? `${currentStep}` : "Deactivated"}
                        color={isRunning ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-zinc-900 text-zinc-600 border-white/5"}
                    />
                    <StatusCard
                        icon={RefreshCw}
                        label="Next Iteration"
                        value={nextRun ? new Date(nextRun * 1000).toLocaleTimeString() : "Pending"}
                        color="bg-primary/10 text-primary border-primary/20"
                    />
                    <StatusCard
                        icon={CheckCircle2}
                        label="Loop Integrity"
                        value={currentStep === "ERROR" ? "Degraded" : "Nominal"}
                        color={currentStep === "ERROR" ? "bg-rose-500/10 text-rose-500 border-rose-500/20" : "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"}
                    />
                    <StatusCard
                        icon={AlertCircle}
                        label="Policy"
                        value={isRunning ? "Self-Correcting" : "Static"}
                        color="bg-amber-500/10 text-amber-500 border-amber-500/20"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Visual Logic Flow */}
                    <div className="lg:col-span-2 space-y-8">
                        <div className="glass-card aspect-[16/10] rounded-[3rem] p-12 flex flex-col items-center justify-center relative overflow-hidden bg-white/[0.01]">
                            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

                            <div className="flex items-center gap-12 relative">
                                <LogicNode icon={Search} label="Scout" active={isRunning && currentStep === "SCOUTING"} pulse={currentStep === "SCOUTING"} />
                                <Connector active={isRunning && ["SCREENING", "BRAINSTORMING", "RENDERING", "PUBLISHING", "WAITING"].includes(currentStep)} />
                                <LogicNode icon={Cpu} label="Brain" active={isRunning && ["SCREENING", "BRAINSTORMING"].includes(currentStep)} pulse={currentStep === "BRAINSTORMING"} />
                                <Connector active={isRunning && ["RENDERING", "PUBLISHING", "WAITING"].includes(currentStep)} />
                                <LogicNode icon={Layers} label="Render" active={isRunning && currentStep === "RENDERING"} pulse={currentStep === "RENDERING"} />
                                <Connector active={isRunning && ["PUBLISHING", "WAITING"].includes(currentStep)} />
                                <LogicNode icon={Share2} label="Post" active={isRunning && currentStep === "PUBLISHING"} pulse={currentStep === "PUBLISHING"} />
                            </div>

                            <div className="mt-16 text-center space-y-2 opacity-50">
                                <p className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-500">Faceless Production Mesh</p>
                                <p className="text-[8px] font-bold text-zinc-600">Dynamic scaling enabled via high-velocity neural clusters</p>
                            </div>
                        </div>

                        {/* Autonomous Insight Oracle */}
                        <div className="space-y-6 px-4">
                            <div className="flex items-center gap-3">
                                <Activity className="h-4 w-4 text-primary neon-glow" />
                                <h3 className="text-[10px] font-black uppercase tracking-widest text-white">Autonomous Intelligence Oracle</h3>
                            </div>
                            <div className="glass-card p-8 border-primary/20 bg-primary/[0.02] relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4">
                                     <div className="h-1.5 w-1.5 rounded-full bg-primary animate-ping" />
                                </div>
                                {insights ? (
                                    <div className="space-y-6">
                                        <div className="space-y-2">
                                            <p className="text-[8px] font-black text-primary uppercase tracking-[0.4em]">Current Strategy</p>
                                            <h4 className="text-2xl font-black tracking-tighter text-white uppercase">{insights.title}</h4>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="space-y-1">
                                                <p className="text-[8px] font-black text-zinc-500 uppercase tracking-widest">Recommended Product</p>
                                                <p className="text-xs font-bold text-emerald-400">{insights.recommended_product}</p>
                                            </div>
                                            <div className="space-y-1">
                                                <p className="text-[8px] font-black text-zinc-500 uppercase tracking-widest">Viral Hook</p>
                                                <p className="text-[10px] text-zinc-300 leading-relaxed">"{insights.hook}"</p>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="py-10 flex flex-col items-center justify-center gap-4 text-center">
                                        <Search className="h-8 w-8 text-zinc-800 animate-pulse" />
                                        <p className="text-[9px] font-black uppercase tracking-widest text-zinc-700">Listening for Market Pulses...</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Live Console Hub */}
                    <div className="lg:col-span-1 flex flex-col gap-8">
                        <div className="glass-card rounded-[2.5rem] flex-1 flex flex-col overflow-hidden bg-black/40 border-white/5">
                            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                                <div className="flex items-center gap-3">
                                    <Terminal className="h-4 w-4 text-primary" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-white">System Console</span>
                                </div>
                                <div className="flex items-center gap-4">
                                    <button 
                                        onClick={handleExportLogs}
                                        className="text-[8px] font-black uppercase tracking-widest text-zinc-500 hover:text-white transition-colors"
                                    >
                                        Export
                                    </button>
                                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                                </div>
                            </div>
                            <div className="p-6 font-mono text-[10px] space-y-3 overflow-y-auto h-[400px] custom-scrollbar">
                                {logs.length === 0 && (
                                    <p className="text-zinc-700">Initializing secure console link...</p>
                                )}
                                {logs.map((log, i) => (
                                    <motion.p
                                        initial={{ opacity: 0, x: -5 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        key={i}
                                        className={cn(
                                            "leading-relaxed",
                                            log.includes("[SYSTEM]") ? "text-primary" : "text-zinc-500"
                                        )}
                                    >
                                        <span className="text-zinc-800 mr-2">[{new Date().toLocaleTimeString()}]</span>
                                        {log}
                                    </motion.p>
                                ))}
                                {isRunning && (
                                    <motion.p
                                        animate={{ opacity: [1, 0.4, 1] }}
                                        transition={{ repeat: Infinity, duration: 2 }}
                                        className="text-emerald-500/50"
                                    >
                                        &gt; Director monitoring clusters...
                                    </motion.p>
                                )}
                            </div>
                        </div>

                        {/* Optimization Card */}
                        <div className="glass-card p-8 rounded-[2rem] bg-emerald-500/5 border-emerald-500/10 space-y-4">
                            <div className="flex items-center gap-3">
                                <Sparkles className="h-4 w-4 text-emerald-500" />
                                <span className="text-[9px] font-black uppercase tracking-widest text-emerald-500">Autonomous Insight</span>
                            </div>
                            <p className="text-[11px] text-zinc-400 leading-relaxed font-medium">
                                {insights ? (
                                    <>"{insights.title || `Agent Zero monitoring ${insights.recommended_product || 'market pulses'} for high-velocity opportunities.`}"</>
                                ) : (
                                    <>"Awaiting market intelligence. Launch Director to activate autonomous scouting."</>
                                )}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

function LogicNode({ icon: Icon, label, active, pulse, delay = 0 }: any) {
    return (
        <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay }}
            className="flex flex-col items-center gap-4"
        >
            <div className={cn(
                "h-20 w-20 rounded-[1.5rem] flex items-center justify-center transition-all duration-700 relative",
                active ? "bg-emerald-500 text-black shadow-[0_0_40px_rgba(16,185,129,0.4)]" : "bg-zinc-950 text-zinc-800 border border-white/5"
            )}>
                <Icon className="h-8 w-8" />
                {active && pulse && (
                    <div className="absolute inset-0 rounded-[1.5rem] border-2 border-emerald-500 animate-ping opacity-20" />
                )}
            </div>
            <span className={cn(
                "text-[10px] font-black uppercase tracking-[0.2em] transition-colors duration-500",
                active ? "text-emerald-500" : "text-zinc-800"
            )}>{label}</span>
        </motion.div>
    );
}

function Connector({ active, delay = 0 }: any) {
    return (
        <div className="h-[2px] w-12 bg-zinc-900 relative">
            {active && (
                <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ delay, duration: 1 }}
                    className="absolute inset-0 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] origin-left"
                />
            )}
        </div>
    );
}

function Sparkles(props: any) {
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
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            <path d="M5 3v4" />
            <path d="M19 17v4" />
            <path d="M3 5h4" />
            <path d="M17 19h4" />
        </svg>
    );
}

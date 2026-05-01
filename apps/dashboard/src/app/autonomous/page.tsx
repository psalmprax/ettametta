"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
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
    Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { getAuthToken } from "@/lib/auth_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";

export default function AutonomousPage() {
    const [isRunning, setIsRunning] = useState(false);
    const [status, setStatus] = useState("Idle");
    const [logs, setLogs] = useState<string[]>(["AGENT_ZERO_INITIALIZED", "AWAITING_LAUNCH_SIGNAL"]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentStep, setCurrentStep] = useState("IDLE");
    const [insights, setInsights] = useState<any>(null);
    const [lastRun, setLastRun] = useState<number | null>(null);
    const [nextRun, setNextRun] = useState<number | null>(null);

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

        const wsUrl = `${WS_BASE}/logs`;
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
    }, [fetchData]);

    const handleToggle = async () => {
        setIsProcessing(true);
        const action = isRunning ? "stop" : "start";
        const token = await getAuthToken();
        if (!token) {
            setIsProcessing(false);
            return;
        }

        setLogs(prev => [`[PROTOCOL] Sending ${action.toUpperCase()} signal to Agent Zero...`, ...prev]);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/zero/${action}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setIsRunning(!isRunning);
                    setLogs(prev => [`[SUCCESS] ${data?.message || `Agent Zero ${action}ed`}`, ...prev]);
                    toast.success(`Agent Zero ${action === 'start' ? 'Activated' : 'Halted'}`);
                    fetchData();
                }
            }
        );
        setIsProcessing(false);
    };

    // Prepare Agent Data
    const agents = [
        { id: "ZERO_01", name: "Agent Zero", icon: Target, status: isRunning ? "ACTIVE" : "IDLE" as any, latency: 4, load: isRunning ? 45 : 0, details: isRunning ? `Step: ${currentStep}` : "Standby" },
        { id: "SCOUT_01", name: "Trend Scout", icon: Search, status: isRunning && currentStep === "SCOUTING" ? "ACTIVE" : "IDLE" as any, latency: 12, load: isRunning && currentStep === "SCOUTING" ? 80 : 0, details: "Scrutinizing Feed" },
        { id: "SYNTH_01", name: "Neural Synth", icon: Dna, status: isRunning && currentStep === "RENDERING" ? "ACTIVE" : "IDLE" as any, latency: 2, load: isRunning && currentStep === "RENDERING" ? 95 : 0, details: "Crystallizing Media" },
    ];

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
                  onClick={() => setActiveEngine(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                    activeEngine === item.id || (item.id === "launch" && !["logic", "oracle", "market", "console"].includes(activeEngine)) ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                  {(activeEngine === item.id || (item.id === "launch" && !["logic", "oracle", "market", "console"].includes(activeEngine))) && (
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
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-10">
              {/* Logic Flow Visualization */}
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

              {/* Insight Oracle */}
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
            </div>

            {/* Console Log Area */}
            <div className="mt-8 h-64 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Terminal className="h-3 w-3 text-emerald-500" />
                  <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">System Console</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[8px] font-mono text-emerald-500/50">LINK_ESTABLISHED</span>
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                    <span className={cn(
                      log.includes("[ERROR]") ? "text-red-500" :
                      log.includes("[SUCCESS]") ? "text-emerald-500" : 
                      log.includes("[PROTOCOL]") ? "text-cyan-400" : "text-zinc-600"
                    )}>{log}</span>
                  </div>
                ))}
              </div>
            </div>
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
        <div className="h-[1px] w-12 bg-white/5 relative">
            {active && (
                <div className="absolute inset-0 bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
            )}
        </div>
    );
}

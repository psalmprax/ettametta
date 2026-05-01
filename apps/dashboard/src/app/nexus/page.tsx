"use client";

import React, { useState, useEffect, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    Zap,
    Layers,
    Cpu,
    Sparkles,
    Share2,
    Database,
    Plus,
    Play,
    Settings2,
    RefreshCw,
    Loader2,
    CheckCircle2,
    AlertCircle,
    Activity,
    ExternalLink,
    ChevronRight,
    Search,
    User,
    Video,
    ImageIcon,
    MessageSquare,
    Send,
    Bot,
    ShieldCheck,
    Trash2,
    X,
    Terminal,
    Fingerprint,
    Brain,
    Network,
    Mic2,
    Clapperboard
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { NexusNode, NodeType } from "@/components/ui/NexusNode";
import { useWebSocket } from "@/hooks/useWebSocket";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { CommandPod } from "@/components/ui/CommandPod";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

import { Blueprint, NexusJob, Persona } from "@/lib/types";

export default function NexusPage() {
    const [activeEngine, setActiveEngine] = useState("orchestrator");
    const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
    const [activeBlueprint, setActiveBlueprint] = useState<Blueprint | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);
    const [nexusJobs, setNexusJobs] = useState<NexusJob[]>([]);
    const [niches, setNiches] = useState<string[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("");
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
    const [logStream, setLogStream] = useState<string[]>([]);

    // Telemetry & WebSocket
    const [telemetry, setTelemetry] = useState<any>(null);
    const { data: jobUpdate } = useWebSocket<{ type: string, data: NexusJob }>(`${WS_BASE}/jobs`);
    const { data: logUpdate } = useWebSocket<{ type: string, module: string, level: string, message: string }>(`${WS_BASE}/logs`);
    const { data: telemetryUpdate } = useWebSocket<any>(`${WS_BASE}/nexus/telemetry`);

    useEffect(() => {
        if (telemetryUpdate) setTelemetry(telemetryUpdate);
    }, [telemetryUpdate]);

    // Fetch initial data
    useEffect(() => {
        const fetchData = async () => {
            const token = await getAuthToken();
            if (!token) return;
            const headers = { Authorization: `Bearer ${token}` };

            await Promise.all([
                withRealFallback<Blueprint[]>(
                    () => fetch(`${API_BASE}/nexus/blueprints`, { headers }),
                    {
                        fallback: [],
                        onSuccess: (data) => {
                            setBlueprints(data);
                            if (data.length > 0) setActiveBlueprint(data[0]);
                        }
                    }
                ),
                withRealFallback<string[]>(
                    () => fetch(`${API_BASE}/discovery/niches`, { headers }),
                    {
                        fallback: [],
                        onSuccess: (data) => {
                            setNiches(data);
                            if (data.length > 0) setSelectedNiche(data[0]);
                        }
                    }
                ),
                withRealFallback<NexusJob[]>(
                    () => fetch(`${API_BASE}/nexus/jobs`, { headers }),
                    {
                        fallback: [],
                        onSuccess: (data) => setNexusJobs(data)
                    }
                ),
                withRealFallback<any>(
                    () => fetch(`${API_BASE}/nexus/telemetry`, { headers }),
                    {
                        fallback: null,
                        onSuccess: (data) => setTelemetry(data)
                    }
                ),
            ]);
        };

        fetchData();
    }, []);

    useEffect(() => {
        if (jobUpdate && jobUpdate.type === "nexus_job_update") {
            const updatedJob = jobUpdate.data;
            setNexusJobs(prev => {
                const exists = prev.find(j => j.id === updatedJob.id);
                if (exists) {
                    return prev.map(j => j.id === updatedJob.id ? { ...j, ...updatedJob } : j);
                }
                return [updatedJob, ...prev];
            });
        }
    }, [jobUpdate]);

    useEffect(() => {
        if (logUpdate && logUpdate.type === "log") {
            setLogStream(prev => [`[${logUpdate.level}] ${logUpdate.message}`, ...prev.slice(0, 49)]);
        }
    }, [logUpdate]);

    const handleLaunchPipeline = async () => {
        if (!selectedNiche || !activeBlueprint) return;
        setIsLaunching(true);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback(
            () => fetch(`${API_BASE}/nexus/compose`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    niche: selectedNiche,
                    blueprint_id: activeBlueprint.id,
                    cinema_mode: true
                })
            }),
            {
                fallback: null,
                onSuccess: (data: any) => {
                    setActiveJobId(String(data.job_id));
                    toast.success("Pipeline Dispatched");
                }
            }
        );
        setIsLaunching(false);
    };

    // Prepare Agent Data
    const agents = [
        { id: "ORCH_01", name: "Nexus Orchestrator", icon: Cpu, status: "ACTIVE" as any, latency: 4, load: 15, details: "Managing Pipeline_X4" },
        { id: "TELE_01", name: "Telemetry Node", icon: Activity, status: "ACTIVE" as any, latency: 1, load: 2, details: `Uptime: ${telemetry?.uptime || "99.9%"}` },
        { id: "STORAGE_01", name: "Storage Cluster", icon: Database, status: telemetry?.storage_status || "ACTIVE" as any, latency: 45, load: 32, details: "Read/Write: 1.2 GB/s" },
    ];

    return (
        <CommandCenterLayout
            title="NEXUS ENGINE"
            subtitle="PIPELINE_ORCHESTRATOR_V4.2"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "orchestrator", label: "Orchestrator", icon: Cpu },
                        { id: "identities", label: "Neural IDs", icon: Fingerprint },
                        { id: "command", label: "Command Pod", icon: Terminal },
                        { id: "history", label: "Pipeline History", icon: Layers },
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
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="space-y-4">
                        <h3 className="text-[10px] font-bold text-zinc-500 tracking-[0.2em] uppercase">Pipeline Queue</h3>
                        <div className="space-y-2">
                            {nexusJobs.slice(0, 3).map((job) => (
                                <div key={job.id} className="p-3 rounded-xl border border-white/5 bg-white/5 flex items-center justify-between">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] font-bold text-white uppercase">{job.niche}</span>
                                        <span className="text-[8px] text-zinc-600 font-mono">{job.status}</span>
                                    </div>
                                    <div className="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full bg-cyan-500" style={{ width: `${job.progress || 0}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "orchestrator" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
                                    <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Neural Target</label>
                                        <select 
                                            value={selectedNiche}
                                            onChange={(e) => setSelectedNiche(e.target.value)}
                                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none"
                                        >
                                            {niches.map(n => <option key={n} value={n} className="bg-zinc-900">{n}</option>)}
                                        </select>
                                    </div>
                                    <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Active Architecture</label>
                                        <select 
                                            value={activeBlueprint?.id}
                                            onChange={(e) => setActiveBlueprint(blueprints.find(b => b.id === e.target.value) || null)}
                                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none"
                                        >
                                            {blueprints.map(b => <option key={b.id} value={b.id} className="bg-zinc-900">{b.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="flex flex-col justify-end">
                                        <Button 
                                            onClick={handleLaunchPipeline}
                                            disabled={isLaunching || !selectedNiche}
                                            className="w-full h-16 bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-lg rounded-2xl shadow-[0_0_30px_rgba(34,211,238,0.3)] transition-all uppercase tracking-widest"
                                        >
                                            {isLaunching ? <Loader2 className="h-6 w-6 animate-spin" /> : "Dispatch Pipeline"}
                                        </Button>
                                    </div>
                                </div>

                                <div className="flex-1 min-h-[400px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">
                                    <div className="absolute inset-0 architect-grid pointer-events-none opacity-40" />
                                    <div className="absolute inset-0 flex items-center justify-around px-20">
                                        {activeBlueprint?.nodes.map((node, idx) => (
                                            <div key={idx} className="relative z-10">
                                                <NexusNode 
                                                    type={node.type as any}
                                                    label={node.label}
                                                    description={node.desc}
                                                    status={idx === selectedNodeIndex ? "processing" : "pending"}
                                                    active={selectedNodeIndex === idx}
                                                    onClick={() => setSelectedNodeIndex(idx)}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                    
                                    {/* Connection Mesh Overlay */}
                                    <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
                                        <svg className="w-full h-full">
                                            <defs>
                                                <linearGradient id="meshGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" stopColor="#22d3ee" stopOpacity="0" />
                                                    <stop offset="50%" stopColor="#22d3ee" stopOpacity="0.5" />
                                                    <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                                                </linearGradient>
                                            </defs>
                                            <path d="M 0 50 Q 500 0 1000 50" stroke="url(#meshGrad)" strokeWidth="2" fill="none" className="animate-pulse" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "history" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {nexusJobs.map((job) => (
                                    <DesignCard 
                                        key={job.id}
                                        title={`PIPELINE_${job.id}`}
                                        status={job.status}
                                        metrics={[
                                            { label: "Completion", value: `${job.progress || 0}%`, progress: job.progress, color: "text-cyan-400" },
                                            { label: "Niche", value: job.niche, color: "text-zinc-500" }
                                        ]}
                                        footerInfo={new Date(job.created_at).toLocaleString()}
                                        toolsStatus="Verified"
                                    />
                                ))}
                            </div>
                        )}

                        {activeEngine === "command" && (
                            <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-[32px] border border-white/5 overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                    <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">Log Stream</h3>
                                    <span className="text-[8px] font-mono text-cyan-400">NEXUS_CORE_ACTIVE</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                                    {logStream.map((log, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-700">[{new Date().toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.includes("ERROR") ? "text-rose-500" : 
                                                log.includes("SUCCESS") ? "text-emerald-500" : "text-zinc-500"
                                            )}>{log}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
            <style jsx global>{`
                .architect-grid {
                    background-image: 
                        linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px);
                    background-size: 40px 40px;
                }
            `}</style>
        </CommandCenterLayout>
    );
}

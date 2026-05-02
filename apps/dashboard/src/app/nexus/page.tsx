"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
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
    Clapperboard,
    PlusCircle
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { NexusNode, NodeType } from "@/components/ui/NexusNode";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { CommandPod } from "@/components/ui/CommandPod";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

import { Blueprint, NexusJob, Persona } from "@/lib/types";
import { useTelemetry } from "@/context/TelemetryContext";

function NexusContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents, logs: systemLogs, lastJobUpdate, pulse, status } = useTelemetry();
    
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "orchestrator");
    const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
    const [activeBlueprint, setActiveBlueprint] = useState<Blueprint | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);
    const [nexusJobs, setNexusJobs] = useState<NexusJob[]>([]);
    const [niches, setNiches] = useState<any[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("");
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
    const [actionLogs, setActionLogs] = useState<string[]>(["NEXUS_CORE_ONLINE", "AWAITING_PIPELINE_ORCHESTRATION"]);

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
    }, [searchParams]);

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
                            const nicheList = Array.isArray(data) ? data : [];
                            setNiches(nicheList);
                            if (nicheList.length > 0) setSelectedNiche(nicheList[0]);
                        }
                    }
                ),
                withRealFallback<NexusJob[]>(
                    () => fetch(`${API_BASE}/nexus/jobs`, { headers }),
                    {
                        fallback: [],
                        onSuccess: (data) => setNexusJobs(Array.isArray(data) ? data : [])
                    }
                ),
            ]);
        };

        fetchData();
    }, []);

    useEffect(() => {
        if (lastJobUpdate && (lastJobUpdate.type === "nexus_job_update" || lastJobUpdate.type === "job_update")) {
            const updatedJob = lastJobUpdate.data;
            setNexusJobs(prev => {
                const exists = prev.find(j => j.id === updatedJob.id);
                if (exists) {
                    return prev.map(j => j.id === updatedJob.id ? { ...j, ...updatedJob } : j);
                }
                return [updatedJob, ...prev];
            });
        }
    }, [lastJobUpdate]);

    const handleLaunchPipeline = async () => {
        if (!selectedNiche || !activeBlueprint) return;
        setIsLaunching(true);
        setActionLogs(prev => [`[PIPELINE] Dispatching: ${activeBlueprint.name} for ${selectedNiche}`, ...prev]);
        
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
                    setActionLogs(prev => [`[SUCCESS] Pipeline Job ID: ${data.job_id}`, ...prev]);
                }
            }
        );
        setIsLaunching(false);
    };

    const [personas, setPersonas] = useState<Persona[]>([]);

    const fetchPersonas = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any[]>(
            () => fetch(`${API_BASE}/discovery/niches`, { headers: { Authorization: `Bearer ${token}` } }),
            { fallback: [], onSuccess: setNiches }
        );
        await withRealFallback<Persona[]>(
            () => fetch(`${API_BASE}/persona/list`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (data) => setPersonas(Array.isArray(data) ? data : [])
            }
        );
    }, []);

    useEffect(() => {
        if (activeEngine === "identities") fetchPersonas();
    }, [activeEngine, fetchPersonas]);

    // Derived active job for orchestrator visualization
    const activePipelineJob = useMemo(() => {
        return nexusJobs.find(j => j.status === "Active" || j.status === "Processing") || nexusJobs[0];
    }, [nexusJobs]);

    // Unified logs pattern
    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs?.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "NEXUS",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...systemLogs
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

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
                            onClick={() => {
                                setActiveEngine(item.id);
                                router.replace(`/nexus?engine=${item.id}`);
                            }}
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
                        <div className="flex items-center justify-between">
                            <h3 className="text-[10px] font-bold text-zinc-500 tracking-[0.2em] uppercase">Pipeline Queue</h3>
                            <div className="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded text-[8px] font-bold text-cyan-400 uppercase">
                                Live_Status
                            </div>
                        </div>
                        <div className="space-y-2">
                            {nexusJobs?.slice(0, 3).map((job) => (
                                <div key={job.id} className="p-4 rounded-2xl border border-white/5 bg-white/5 flex items-center justify-between group hover:bg-white/8 transition-all">
                                    <div className="flex flex-col gap-1">
                                        <span className="text-[10px] font-bold text-white uppercase tracking-tight">{job.niche}</span>
                                        <div className="flex items-center gap-2">
                                            <div className={cn("h-1 w-1 rounded-full", job.status === "Active" ? "bg-emerald-500" : "bg-zinc-600")} />
                                            <span className="text-[8px] text-zinc-500 font-mono uppercase tracking-tighter">{job.status}</span>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end gap-1.5">
                                        <span className="text-[10px] font-bold text-cyan-400">{job.progress || 0}%</span>
                                        <div className="h-0.5 w-16 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-cyan-500" style={{ width: `${job.progress || 0}%` }} />
                                        </div>
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
                        {activeEngine === "registry" && (
                            <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Database className="h-16 w-16 text-cyan-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Empire Registry</h3>
                                    <div className="flex flex-col gap-1 items-center">
                                        <span className="text-[10px] text-zinc-500 font-mono italic">SECURE_STORAGE_ORCHESTRATION_ACTIVE</span>
                                        <span className="text-[8px] text-cyan-500/50 font-mono">ENCRYPTED_VOXEL_HASH: 0x93F...A2</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "forge" && (
                            <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Zap className="h-16 w-16 text-cyan-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Neural Forge</h3>
                                    <div className="flex flex-col gap-1 items-center">
                                        <span className="text-[10px] text-zinc-500 font-mono italic">CREATIVE_SYNTHESIS_PIPELINE_READY</span>
                                        <span className="text-[8px] text-cyan-500/50 font-mono">ACTIVE_TEMP: 4200K_NEURAL_BURN</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "network" && (
                            <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Network className="h-16 w-16 text-cyan-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Global Network Mesh</h3>
                                    <div className="flex flex-col gap-1 items-center">
                                        <span className="text-[10px] text-zinc-500 font-mono italic">SWARM_INTELLIGENCE_ROUTING_ACTIVE</span>
                                        <span className="text-[8px] text-cyan-500/50 font-mono">NODES_CONNECTED: 4,092_DIRECT_LINKS</span>
                                    </div>
                                </div>
                            </div>
                        )}

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
                                            {niches?.map((n) => (
                                                <option key={typeof n === 'string' ? n : n.niche} value={typeof n === 'string' ? n : n.niche} className="bg-zinc-900">
                                                    {typeof n === 'string' ? n : n.niche}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Active Architecture</label>
                                        <select 
                                            value={activeBlueprint?.id}
                                            onChange={(e) => setActiveBlueprint(blueprints.find(b => b.id === e.target.value) || null)}
                                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none"
                                        >
                                            {blueprints?.map((b) => <option key={b.id} value={b.id} className="bg-zinc-900">{b.name}</option>)}
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
                                        {activeBlueprint?.nodes?.map((node, idx) => {
                                            const isProcessing = activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                                            const isComplete = activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                                            
                                            return (
                                                <div key={idx} className="relative z-10">
                                                    <NexusNode 
                                                        type={node.type as any}
                                                        label={node.label}
                                                        description={node.desc}
                                                        status={isComplete ? "complete" : isProcessing ? "processing" : "pending"}
                                                        progress={isProcessing ? activePipelineJob.progress : undefined}
                                                        active={selectedNodeIndex === idx}
                                                        onClick={() => setSelectedNodeIndex(idx)}
                                                    />
                                                </div>
                                            );
                                        })}
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

                        {activeEngine === "identities" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex items-center justify-between shrink-0">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Neural Identity Lab</h3>
                                    <Button className="bg-white/5 border border-white/10 hover:bg-white/10 text-white gap-2">
                                        <PlusCircle className="h-4 w-4" /> Register New ID
                                    </Button>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 overflow-y-auto custom-scrollbar p-1">
                                    {personas?.map((persona) => (
                                        <div key={persona.id} className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6 group hover:border-cyan-500/20 transition-all">
                                            <div className="aspect-square rounded-2xl bg-zinc-900 overflow-hidden relative border border-white/5">
                                                {persona.reference_image_uri ? (
                                                    <img src={persona.reference_image_uri} alt={persona.name} className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center">
                                                        <User className="h-12 w-12 text-zinc-800" />
                                                    </div>
                                                )}
                                                <div className="absolute inset-0 bg-linear-to-t from-black/80 via-transparent to-transparent" />
                                                <div className="absolute bottom-4 left-4">
                                                    <span className="text-[8px] font-bold text-cyan-400 uppercase tracking-widest px-2 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full">Active_ID</span>
                                                </div>
                                            </div>
                                            <div className="space-y-1">
                                                <h4 className="text-lg font-bold text-white uppercase tracking-tight">{persona.name}</h4>
                                                <p className="text-[10px] font-mono text-zinc-600">ID: {persona.id}</p>
                                            </div>
                                            <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                                <div className="flex gap-2">
                                                    <div className="h-6 w-6 rounded bg-white/5 flex items-center justify-center"><Mic2 className="h-3 w-3 text-zinc-500" /></div>
                                                    <div className="h-6 w-6 rounded bg-white/5 flex items-center justify-center"><Video className="h-3 w-3 text-zinc-500" /></div>
                                                </div>
                                                <Button variant="outline" className="h-8 text-[9px] uppercase font-bold border-white/10 text-white hover:bg-cyan-500 hover:text-black">Modify</Button>
                                            </div>
                                        </div>
                                    ))}
                                    {personas.length === 0 && (
                                        <div className="col-span-4 h-full flex flex-col items-center justify-center opacity-10 gap-6 py-20">
                                            <Fingerprint className="h-24 w-24" />
                                            <span className="text-xl font-black uppercase tracking-[1em]">No Neural IDs Found</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeEngine === "history" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar">
                                {nexusJobs?.map((job) => (
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
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <CommandPod 
                                    name="Nexus Core" 
                                    status="nominal" 
                                    load={15} 
                                    circuitBreaker="closed" 
                                    description="Primary orchestration layer for Nexus Workforce."
                                />
                                <CommandPod 
                                    name="Neural Gateway" 
                                    status="nominal" 
                                    load={8} 
                                    circuitBreaker="closed" 
                                    description="High-throughput ingress for autonomous discovery signals."
                                />
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-[32px] border border-white/5 overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                    <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">Log Stream</h3>
                                    <span className="text-[8px] font-mono text-cyan-400">{status === "open" ? "NEXUS_CORE_ACTIVE" : "OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                                    {displayLogs?.map((log, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-700">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-500"
                                            )}>{log.module ? `[${log.module}] ` : ""}{log.message}</span>
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

export default function NexusPage() {
    return (
        <Suspense fallback={null}>
            <NexusContent />
        </Suspense>
    );
}

"use client";

import React, { useState, useEffect, Suspense, useMemo, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { DesignCard } from "@/components/ui/DesignCard";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import {
    Video,
    Layers,
    Cpu,
    Play,
    Clock,
    Settings2,
    Eye,
    Film,
    Sparkles,
    CheckCircle2,
    RefreshCw,
    ArrowUpRight,
    PlusCircle,
    Link as LinkIcon,
    Circle,
    X,
    Monitor,
    Loader2,
    Activity,
    Box,
    Terminal,
    Target,
    Zap,
    ZapOff
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { useTelemetry } from "@/context/TelemetryContext";
import { useSearchParams, useRouter } from "next/navigation";

interface VideoJob {
    id: string;
    title: string;
    status: string;
    progress: number;
    output_path?: string;
    created_at?: string;
}

function TransformationContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "studio");
    const [processingJobs, setProcessingJobs] = useState<VideoJob[]>([]);
    const [selectedJob, setSelectedJob] = useState<VideoJob | null>(null);
    const [actionLogs, setActionLogs] = useState<string[]>([]);

    const { agents, logs: systemLogs, lastJobUpdate, pulse, status } = useTelemetry();

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
    }, [searchParams]);

    useEffect(() => {
        if (lastJobUpdate && (lastJobUpdate.type === "job_update" || lastJobUpdate.type === "nexus_job_update")) {
            const updatedJob = lastJobUpdate.data;
            setProcessingJobs(prev => {
                const exists = prev.find(j => j.id === updatedJob.id);
                if (exists) return prev.map(j => j.id === updatedJob.id ? { ...j, ...updatedJob } : j);
                return [updatedJob, ...prev];
            });
            if (selectedJob?.id === updatedJob.id) setSelectedJob(updatedJob);
        }
    }, [lastJobUpdate, selectedJob]);

    useEffect(() => {
        const fetchData = async () => {
            const token = await getAuthToken();
            if (!token) return;
            await withRealFallback<VideoJob[]>(
                () => fetch(`${API_BASE}/video/jobs`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                {
                    fallback: [],
                    onSuccess: (jobs) => {
                        setProcessingJobs(jobs);
                        if (jobs.length > 0) setSelectedJob(jobs[0]);
                    }
                }
            );
        };
        fetchData();
    }, []);

    const handleAbort = async (id: string) => {
        const token = await getAuthToken();
        if (!token) return;
        setActionLogs((prev: string[]) => [`[SIGNAL] Aborting Job: ${id}`, ...prev]);
        
        await withRealFallback(
            () => fetch(`${API_BASE}/video/jobs/${id}/abort`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Job Aborted Successfully");
                    setActionLogs((prev: string[]) => [`[SUCCESS] Job ${id} Terminated.`, ...prev]);
                }
            }
        );
    };

    const handleAutoLinks = async (id: string) => {
        const token = await getAuthToken();
        if (!token) return;
        setActionLogs((prev: string[]) => [`[SIGNAL] Triggering Neural Link Insertion for ${id}`, ...prev]);
        
        await withRealFallback(
            () => fetch(`${API_BASE}/video/auto-insert-links`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ job_id: id })
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Affiliate Nodes Injected");
                    setActionLogs((prev: string[]) => [`[SUCCESS] Links injected into ${id}`, ...prev]);
                }
            }
        );
    };

    const getStaticUrl = (path: string | undefined) => {
        if (!path) return null;
        if (path.startsWith('http')) return path;
        const filename = path.split('/').pop();
        return `${API_BASE}/static/${filename}`;
    };

    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "STUDIO",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...systemLogs
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

    return (
        <CommandCenterLayout
            title="ORIGINALITY STUDIO"
            subtitle="ASSET_TRANSFORMATION_V4.2"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "studio", label: "Studio Control", icon: Activity },
                        { id: "mass", label: "Mass Deployment", icon: Layers },
                        { id: "queue", label: "Render Queue", icon: Clock },
                        { id: "nodes", label: "Neural Nodes", icon: Box },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                setActiveEngine(item.id);
                                router.replace(`/transformation?engine=${item.id}`);
                            }}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Quotas</h4>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-[10px] text-zinc-600 font-bold uppercase">Render Time</span>
                                <span className="text-[10px] text-white font-bold">14.2h / 24h</span>
                            </div>
                            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full w-[60%] bg-rose-500" />
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
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className={cn("flex-1 flex flex-col min-h-0", activeEngine !== "logs" && "overflow-y-auto custom-scrollbar pr-4")}
                    >
                        {activeEngine === "studio" && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
                                <div className="lg:col-span-2 rounded-[32px] border border-white/5 bg-[#0F0F11]/60 p-8 flex flex-col overflow-hidden">
                                    <div className="flex items-center justify-between mb-8">
                                        <div className="flex items-center gap-3">
                                            <Monitor className="h-5 w-5 text-rose-500" />
                                            <h3 className="text-sm font-bold text-white uppercase tracking-widest">Live Production Feed</h3>
                                        </div>
                                        {selectedJob && (
                                            <div className="flex items-center gap-4">
                                                <span className="text-[10px] font-mono text-zinc-600">ID: {selectedJob.id}</span>
                                                <Button onClick={() => handleAbort(selectedJob.id)} variant="outline" className="h-10 border-rose-500/20 text-rose-500 text-[10px] uppercase font-bold hover:bg-rose-500/10">
                                                    <ZapOff className="h-3 w-3 mr-2" /> Abort Job
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex-1 bg-black rounded-2xl border border-white/5 overflow-hidden flex items-center justify-center relative group min-h-[400px]">
                                        {selectedJob?.status === "Completed" && getStaticUrl(selectedJob.output_path) ? (
                                            <video src={getStaticUrl(selectedJob.output_path)!} controls className="w-full h-full object-contain" />
                                        ) : selectedJob ? (
                                            <div className="flex flex-col items-center gap-6">
                                                <RefreshCw className="h-12 w-12 text-rose-500 animate-spin" />
                                                <div className="text-center">
                                                    <p className="text-lg font-bold text-white uppercase">{selectedJob.status}</p>
                                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{selectedJob.progress}% Synchronized</p>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center gap-4 opacity-10">
                                                <Video className="h-16 w-16" />
                                                <span className="text-[10px] font-bold uppercase tracking-[0.5em]">Feed Offline</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="space-y-6">
                                    <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                                        <h3 className="text-[10px] font-bold text-zinc-500 tracking-[0.2em] uppercase">Neural Overrides</h3>
                                        <div className="space-y-4">
                                            <Button 
                                                onClick={() => handleAutoLinks(selectedJob?.id || "")}
                                                disabled={!selectedJob}
                                                className="w-full h-14 bg-white/5 border border-white/10 hover:bg-white/10 text-white font-bold text-xs uppercase rounded-xl flex items-center gap-3"
                                            >
                                                <LinkIcon className="h-4 w-4 text-rose-500" />
                                                Auto-Inject Affiliate Nodes
                                            </Button>
                                            <Button 
                                                disabled={!selectedJob}
                                                className="w-full h-14 bg-white/5 border border-white/10 hover:bg-white/10 text-white font-bold text-xs uppercase rounded-xl flex items-center gap-3"
                                            >
                                                <Sparkles className="h-4 w-4 text-violet-400" />
                                                Neural Upscale (4K)
                                            </Button>
                                            <Button 
                                                disabled={!selectedJob}
                                                className="w-full h-14 bg-white/5 border border-white/10 hover:bg-white/10 text-white font-bold text-xs uppercase rounded-xl flex items-center gap-3"
                                            >
                                                <Target className="h-4 w-4 text-cyan-400" />
                                                Test Drive Generation
                                            </Button>
                                        </div>
                                    </div>
                                    <DesignCard 
                                        title="System Load"
                                        status={status === "open" ? "Active" : "Offline"}
                                        metrics={[
                                            { label: "GPU Load", value: `${Math.round((pulse?.load_avg || 0) * 100)}%`, progress: (pulse?.load_avg || 0) * 100, color: "text-rose-500" },
                                            { label: "Memory", value: pulse?.memory_usage ? `${pulse.memory_usage.toFixed(1)}GB` : "---", progress: pulse?.memory_usage ? (pulse.memory_usage / 32) * 100 : 0, color: "text-rose-500" }
                                        ]}
                                        footerInfo={pulse?.uptime ? `Uptime: ${pulse.uptime}` : "Synchronizing..."}
                                        toolsStatus="Stable"
                                    />
                                </div>
                            </div>
                        )}

                        {activeEngine === "mass" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {processingJobs.map((job) => (
                                    <DesignCard 
                                        key={job.id}
                                        title={job.title || "VIRAL_TRANSFORM"}
                                        status={job.status}
                                        metrics={[
                                            { label: "Completion", value: `${job.progress}%`, progress: job.progress, color: "text-rose-500" }
                                        ]}
                                        footerInfo={`PIPELINE: ${job.id}`}
                                        toolsStatus="Verified"
                                        onClick={() => {
                                            setSelectedJob(job);
                                            setActiveEngine("studio");
                                            router.replace("/transformation?engine=studio");
                                        }}
                                    />
                                ))}
                            </div>
                        )}

                        {activeEngine === "queue" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-10 overflow-hidden flex flex-col">
                                <div className="flex items-center justify-between mb-8">
                                    <h3 className="text-xl font-bold text-white uppercase tracking-tighter">Render Queue Status</h3>
                                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-500 uppercase tracking-widest">
                                        {processingJobs.filter(j => j.status === "Processing" || j.status === "Active").length} Active Renders
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-4">
                                    {processingJobs.map((job) => (
                                        <div key={job.id} className="p-6 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-between group hover:bg-white/8 transition-all">
                                            <div className="flex items-center gap-6">
                                                <div className={cn(
                                                    "h-12 w-12 rounded-xl flex items-center justify-center border",
                                                    job.status === "Completed" ? "bg-emerald-500/20 border-emerald-500/20 text-emerald-400" :
                                                    job.status === "Error" ? "bg-rose-500/20 border-rose-500/20 text-rose-400" : "bg-white/5 border-white/10 text-zinc-500"
                                                )}>
                                                    {job.status === "Completed" ? <CheckCircle2 className="h-6 w-6" /> : <Clock className="h-6 w-6" />}
                                                </div>
                                                <div className="flex flex-col gap-1">
                                                    <span className="text-sm font-bold text-white uppercase tracking-tight">{job.title || "PIPELINE_JOB"}</span>
                                                    <span className="text-[10px] font-mono text-zinc-500 uppercase">{job.id} • {job.created_at ? new Date(job.created_at).toLocaleString() : "Recently Dispatched"}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-8">
                                                <div className="flex flex-col items-end gap-2">
                                                    <span className="text-[10px] font-bold text-rose-500 uppercase">{job.progress}%</span>
                                                    <div className="h-1 w-32 bg-white/5 rounded-full overflow-hidden">
                                                        <div className="h-full bg-rose-500" style={{ width: `${job.progress}%` }} />
                                                    </div>
                                                </div>
                                                <Button onClick={() => { setSelectedJob(job); setActiveEngine("studio"); router.replace("/transformation?engine=studio"); }} className="h-10 w-10 p-0 bg-white/5 border border-white/10 hover:bg-white/10">
                                                    <Eye className="h-4 w-4 text-white" />
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {activeEngine === "nodes" && (
                            <div className="h-full min-h-[400px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Box className="h-16 w-16 text-rose-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-rose-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Neural Transformation Nodes</h3>
                                    <span className="text-[10px] text-zinc-500 font-mono italic">DISTRIBUTED_VFX_PIPELINE_ACTIVE</span>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Global Engine Stream</span>
                                    <span className="text-[8px] font-mono text-rose-500/50">{status === "open" ? "LIVE_SYNC" : "OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                    {displayLogs.map((log, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
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
            </div>
        </CommandCenterLayout>
    );
}

export default function TransformationPage() {
    return (
        <Suspense fallback={
            <div className="h-screen w-full flex items-center justify-center bg-[#050505]">
                <Loader2 className="h-12 w-12 text-primary animate-spin" />
            </div>
        }>
            <TransformationContent />
        </Suspense>
    );
}

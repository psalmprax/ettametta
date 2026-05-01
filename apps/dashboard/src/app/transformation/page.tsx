"use client";

import React, { useState, useEffect, Suspense } from "react";
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
import { useWebSocket } from "@/hooks/useWebSocket";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";

interface VideoJob {
    id: string;
    title: string;
    status: string;
    progress: number;
    output_path?: string;
}

export default function TransformationPage() {
    const [activeEngine, setActiveEngine] = useState("control");
    const [processingJobs, setProcessingJobs] = useState<VideoJob[]>([]);
    const [selectedJob, setSelectedJob] = useState<VideoJob | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [logs, setLogs] = useState<string[]>(["STUDIO_INITIALIZED", "AWAITING_SOURCE_TELEMETRY"]);
    const [telemetry, setTelemetry] = useState<any>(null);

    const { data: jobUpdate } = useWebSocket<any>(`${WS_BASE}/jobs`);
    const { data: telemetryUpdate } = useWebSocket<any>(`${WS_BASE}/nexus/telemetry`);

    useEffect(() => {
        if (telemetryUpdate) setTelemetry(telemetryUpdate);
    }, [telemetryUpdate]);

    useEffect(() => {
        if (jobUpdate && jobUpdate.type === "job_update") {
            const updatedJob = jobUpdate.data;
            setProcessingJobs(prev => {
                const exists = prev.find(j => j.id === updatedJob.id);
                if (exists) return prev.map(j => j.id === updatedJob.id ? { ...j, ...updatedJob } : j);
                return [updatedJob, ...prev];
            });
            if (selectedJob?.id === updatedJob.id) setSelectedJob(updatedJob);
        }
    }, [jobUpdate, selectedJob]);

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
        setLogs(prev => [`[SIGNAL] Aborting Job: ${id}`, ...prev]);
        
        await withRealFallback(
            () => fetch(`${API_BASE}/video/jobs/${id}/abort`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Job Aborted Successfully");
                    setLogs(prev => [`[SUCCESS] Job ${id} Terminated.`, ...prev]);
                }
            }
        );
    };

    const handleAutoLinks = async (id: string) => {
        const token = await getAuthToken();
        if (!token) return;
        setLogs(prev => [`[SIGNAL] Triggering Neural Link Insertion for ${id}`, ...prev]);
        
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
                    setLogs(prev => [`[SUCCESS] Links injected into ${id}`, ...prev]);
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

    // Prepare Agent Data
    const agents = [
        { id: "RENDER_01", name: "Remotion Cluster", icon: Film, status: "ACTIVE" as any, latency: 120, load: 85, details: "Rendering Frame_2401" },
        { id: "FFMPEG_01", name: "Codec Engine", icon: Video, status: "ACTIVE" as any, latency: 450, load: 32, details: "Encoding: VP9/H.265" },
        { id: "LINK_01", name: "Affiliate Bot", icon: LinkIcon, status: "IDLE" as any, latency: 5, load: 0, details: "Waiting for Commit" },
    ];

    return (
        <CommandCenterLayout
            title="ORIGINALITY STUDIO"
            subtitle="ASSET_TRANSFORMATION_V4.2"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "control", label: "Studio Control", icon: Activity },
                        { id: "queue", label: "Mass Deployment", icon: Layers },
                        { id: "nodes", label: "Neural Nodes", icon: Box },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
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
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "control" && (
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
                                    <div className="flex-1 bg-black rounded-2xl border border-white/5 overflow-hidden flex items-center justify-center relative group">
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
                                        status="Active"
                                        metrics={[
                                            { label: "GPU Load", value: "85%", progress: 85, color: "text-rose-500" },
                                            { label: "VRAM", value: "11.2GB", progress: 92, color: "text-rose-500" }
                                        ]}
                                        footerInfo="Cluster is operating at peak capacity."
                                        toolsStatus="Stable"
                                    />
                                </div>
                            </div>
                        )}

                        {activeEngine === "queue" && (
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
                                            setActiveEngine("control");
                                        }}
                                    />
                                ))}
                            </div>
                        )}

                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Transformation Node Logs</span>
                                <span className="text-[8px] font-mono text-rose-500/50">ENGINE_ACTIVE</span>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[ERROR]") ? "text-rose-500" :
                                            log.includes("[SUCCESS]") ? "text-emerald-500" :
                                            log.includes("[SIGNAL]") ? "text-cyan-400" : "text-zinc-600"
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

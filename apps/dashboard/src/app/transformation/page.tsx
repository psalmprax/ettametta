"use client";

import React, { useState, useEffect, Suspense } from "react";
import DashboardLayout from "@/components/layout";
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
    Circle
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import dynamic from "next/dynamic";

const ProcessingFlow = dynamic(() => import("@/components/ui/ProcessingFlow"), { ssr: false });
import { useWebSocket } from "@/hooks/useWebSocket";
import { WS_BASE } from "@/lib/config";

interface VideoJob {
    id: string;
    title: string;
    status: string;
    progress: number;
    time_remaining?: string;
    output_path?: string;
}

import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

function TransformationPageContent() {
    const searchParams = useSearchParams();
    const [processingJobs, setProcessingJobs] = useState<VideoJob[]>([]);
    const [activeFilters, setActiveFilters] = useState<any[]>([]);
    const [selectedJob, setSelectedJob] = useState<VideoJob | null>(null);
    const [isJobModalOpen, setIsJobModalOpen] = useState(false);
    const [newJobUrl, setNewJobUrl] = useState("");
    const [targetPlatform, setTargetPlatform] = useState("YouTube Shorts");
    const [generateThumbnail, setGenerateThumbnail] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const urlParam = searchParams.get("url");
        if (urlParam) {
            setNewJobUrl(urlParam);
            setIsJobModalOpen(true);
        }
    }, [searchParams]);

    // ... handleNewJob update
    const handleNewJob = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!newJobUrl) return;

        setIsSubmitting(true);
        try {
            const token = localStorage.getItem("et_token");
            const response = await fetch(`${API_BASE}/video/transform`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    input_url: newJobUrl,
                    platform: targetPlatform,
                    niche: "AI Technology",
                    generate_thumbnail: generateThumbnail
                })
            });
            // ...
            if (response.ok) {
                setNewJobUrl("");
                setIsJobModalOpen(false);
                const jobsRes = await fetch(`${API_BASE}/video/jobs`, {
                    headers: { Authorization: `Bearer ${token}` }
                }).then(r => r.json());
                setProcessingJobs(jobsRes);
            }
        } catch (error) {
            console.error("New job error:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleToggleFilter = async (id: string) => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/settings/filters/${id}/toggle`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const updated = await res.json();
                setActiveFilters(prev => prev.map(f => f.id === id ? updated : f));
            }
        } catch (error) {
            console.error("Failed to toggle filter:", error);
        }
    };

    const getStaticUrl = (path: string | undefined) => {
        if (!path) return `${API_BASE}/static/output.mp4`;
        if (path.startsWith('http')) return path;

        // Handle local paths
        if (!path.includes('.mp4') && !path.includes('.')) return `${API_BASE}/static/output.mp4`;

        const parts = path.split('/');
        const filename = parts[parts.length - 1];
        return `${API_BASE}/static/${filename}`;
    };

    const handleAbort = async (id: string) => {
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/video/jobs/${id}/abort`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const updated = await res.json();
                setProcessingJobs(prev => prev.map(j => j.id === id ? { ...j, status: "Aborted" } : j));
                if (selectedJob?.id === id) {
                    setSelectedJob(prev => prev ? { ...prev, status: "Aborted" } : null);
                }
            }
        } catch (error) {
            console.error("Failed to abort job:", error);
        }
    };

    const { data: jobUpdate } = useWebSocket<any>(`${WS_BASE}/ws/jobs`);

    useEffect(() => {
        if (!jobUpdate) return;

        if (jobUpdate.type === "job_update") {
            const updatedJob = jobUpdate.data;
            setProcessingJobs(prev => {
                const exists = prev.find(j => j.id === updatedJob.id);
                if (exists) {
                    return prev.map(j => j.id === updatedJob.id ? { ...j, ...updatedJob } : j);
                } else {
                    return [updatedJob, ...prev];
                }
            });

            // Update selected job if it's the one that changed
            setSelectedJob(prev => {
                if (prev && prev.id === updatedJob.id) {
                    return { ...prev, ...updatedJob };
                }
                return prev;
            });
        }
    }, [jobUpdate]);

    React.useEffect(() => {
        const fetchData = async () => {
            try {
                const token = localStorage.getItem("et_token");
                if (!token) return;
                const headers = { Authorization: `Bearer ${token}` };

                const [jobsRes, filtersRes] = await Promise.all([
                    fetch(`${API_BASE}/video/jobs`, { headers }).then(r => r.json()),
                    fetch(`${API_BASE}/settings/filters`, { headers }).then(r => r.json())
                ]);
                setProcessingJobs(jobsRes);
                setActiveFilters(filtersRes);
                if (jobsRes.length > 0 && !selectedJob) {
                    setSelectedJob(jobsRes[0]);
                } else if (selectedJob) {
                    const updated = jobsRes.find((j: any) => j.id === selectedJob.id);
                    if (updated) setSelectedJob(updated);
                }
            } catch (error) {
                console.error("Failed to fetch initial data:", error);
            }
        };

        fetchData();
    }, []); // Only fetch initial data on mount

    const activeFilterCount = Array.isArray(activeFilters) ? activeFilters.filter(f => f.enabled).length : 0;



    const [flowSteps, setFlowSteps] = useState<{ id: string; label: string; status: "pending" | "active" | "complete" }[]>([
        { id: "ingest", label: "Packet Ingestion", status: "pending" },
        { id: "analyze", label: "Semantic Analysis", status: "pending" },
        { id: "remix", label: "Neural Patterning", status: "pending" },
        { id: "render", label: "Final Synthesis", status: "pending" }
    ]);

    useEffect(() => {
        if (!selectedJob) return;

        // Map backend status to flow steps
        // Example statuses: 'queued', 'downloading', 'processing', 'completed', 'failed'
        const status = selectedJob.status.toLowerCase();

        let activeIdx = -1;
        if (status === 'queued') activeIdx = 0;
        else if (status === 'downloading') activeIdx = 0;
        else if (status === 'processing') activeIdx = 1; // Simplify for demo
        else if (status === 'rendering') activeIdx = 3;
        else if (status === 'completed') activeIdx = 4; // All done

        setFlowSteps(prev => prev.map((step, idx) => {
            if (activeIdx > idx) return { ...step, status: "complete" as const };
            if (activeIdx === idx) return { ...step, status: "active" as const };
            return { ...step, status: "pending" as const };
        }));

    }, [selectedJob]);

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                {/* Custom Modal for New Job */}
                <AnimatePresence>
                    {isJobModalOpen && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                animate={{ scale: 1, opacity: 1, y: 0 }}
                                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                className="glass-card w-full max-w-xl rounded-[3rem] p-12 shadow-[0_32px_128px_rgba(0,0,0,0.8)] space-y-10 relative overflow-hidden"
                            >
                                <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3">
                                        <div className="h-1 w-8 bg-primary rounded-full" />
                                        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Engine Initialization</span>
                                    </div>
                                    <h3 className="text-3xl font-black uppercase tracking-tighter text-white">Launch Transformation</h3>
                                    <p className="text-zinc-500 font-medium leading-relaxed">Input source telemetry (Video URL) to apply high-velocity <span className="text-primary font-bold">Neural pattern injection</span>.</p>
                                </div>
                                <form onSubmit={handleNewJob} className="space-y-8">
                                    <div className="relative group">
                                        <Video className="absolute left-6 top-1/2 -translate-y-1/2 h-6 w-6 text-zinc-600 group-focus-within:text-primary transition-all duration-300" />
                                        <input
                                            id="video-url"
                                            name="video-url"
                                            autoFocus
                                            type="url"
                                            placeholder="https://tiktok.com/video/123..."
                                            value={newJobUrl}
                                            onChange={(e) => setNewJobUrl(e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-6 pl-16 pr-6 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all text-white font-bold placeholder:text-zinc-700 tracking-tight"
                                        />
                                    </div>

                                    {/* Platform Targeting */}
                                    <div className="grid grid-cols-2 gap-4">
                                        {["YouTube Shorts", "TikTok"].map((p) => (
                                            <button
                                                key={p}
                                                type="button"
                                                onClick={() => setTargetPlatform(p)}
                                                className={cn(
                                                    "py-4 rounded-xl border font-black uppercase text-[10px] tracking-widest transition-all",
                                                    targetPlatform === p
                                                        ? "bg-primary/20 border-primary text-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]"
                                                        : "bg-zinc-950/30 border-white/10 text-zinc-600 hover:text-zinc-400"
                                                )}
                                            >
                                                {p}
                                            </button>
                                        ))}
                                    </div>

                                    {/* AI Thumbnail Toggle */}
                                    <div className="bg-zinc-950/30 border border-white/10 p-6 rounded-xl flex items-center justify-between group/toggle hover:border-primary/30 transition-all cursor-pointer" onClick={() => setGenerateThumbnail(!generateThumbnail)}>
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                "p-3 rounded-lg transition-all",
                                                generateThumbnail ? "bg-primary/20 text-primary" : "bg-zinc-900 text-zinc-600"
                                            )}>
                                                <Sparkles className="h-5 w-5" />
                                            </div>
                                            <div className="space-y-0.5">
                                                <span className="text-[11px] font-black uppercase tracking-tight text-white">Neural Thumbnail Generator</span>
                                                <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">AI-Optimized Click-Through Vector</p>
                                            </div>
                                        </div>
                                        <div className={cn(
                                            "w-12 h-6 rounded-full transition-all relative border",
                                            generateThumbnail ? "bg-primary border-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.3)]" : "bg-zinc-800 border-white/5"
                                        )}>
                                            <motion.div
                                                animate={{ x: generateThumbnail ? 24 : 4 }}
                                                className="absolute top-1 w-3 h-3 bg-white rounded-full transition-all"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex gap-4">
                                        <button
                                            type="button"
                                            onClick={() => setIsJobModalOpen(false)}
                                            className="flex-1 bg-zinc-950/50 border border-white/10 hover:bg-white/5 text-zinc-400 font-black py-5 rounded-xl transition-all uppercase text-xs tracking-widest"
                                        >
                                            Abort
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={isSubmitting || !newJobUrl}
                                            className="flex-1 bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-black py-5 rounded-xl transition-all shadow-[0_0_40px_rgba(var(--primary-rgb),0.3)] flex items-center justify-center gap-3 uppercase text-xs tracking-widest"
                                        >
                                            {isSubmitting ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Layers className="h-5 w-5" />}
                                            {isSubmitting ? "Locking..." : "Start Engine"}
                                        </button>
                                    </div>
                                </form>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Processing Flow Diagram */}
                <div className="mb-16">
                    <ProcessingFlow steps={flowSteps} />
                </div>

                <div className="flex items-end justify-between mb-12">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Production Hub</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter italic uppercase text-white leading-none">Originality <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-rose-500 text-hollow">Studio</span></h1>
                        <p className="text-zinc-500 font-medium">Applying cinematic filters and managing <span className="text-zinc-300 font-bold">social compliance</span> workflows.</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="glass-card px-6 py-4 rounded-2xl flex items-center gap-4">
                            <div className="flex -space-x-3">
                                {Array.isArray(activeFilters) && activeFilters.filter(f => f.enabled).slice(0, 3).map((f, i) => (
                                    <div key={i} className="h-8 w-8 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center backdrop-blur-md shadow-sm">
                                        <Sparkles className="h-4 w-4 text-primary" />
                                    </div>
                                ))}
                            </div>
                            <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">
                                {activeFilterCount} Active Nodes
                            </span>
                        </div>
                        <motion.button
                            whileHover={{ scale: 1.05, y: -2 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setIsJobModalOpen(true)}
                            className="bg-primary hover:bg-primary/90 text-white font-black py-4 px-8 rounded-xl transition-all flex items-center gap-3 shadow-[0_0_40px_rgba(var(--primary-rgb),0.2)] uppercase text-xs tracking-widest"
                        >
                            <Film className="h-5 w-5" />
                            Launch Studio
                        </motion.button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Active Jobs Section */}
                    <div className="lg:col-span-2 space-y-10">
                        {/* Live Studio Preview */}
                        <div className="glass-card overflow-hidden flex flex-col shadow-[0_32px_64px_rgba(0,0,0,0.4)] relative">
                            <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                            <div className="p-8 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                        <Play className="h-5 w-5 text-emerald-500 neon-glow" />
                                    </div>
                                    <div className="space-y-0.5">
                                        <h3 className="font-black uppercase tracking-tight text-white">Live Monitor</h3>
                                        <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Real-time Node Rendering</p>
                                    </div>
                                </div>
                                {selectedJob && (
                                    <div className="flex items-center gap-6">
                                        <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500 font-mono">
                                            JOB_ID: {selectedJob.id.slice(0, 8)}
                                        </span>
                                        <a
                                            href={getStaticUrl(selectedJob.output_path)}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="glass-card hover:border-primary/50 text-zinc-400 hover:text-white text-[10px] font-black py-2 px-4 rounded-xl transition-all flex items-center gap-2 uppercase tracking-widest"
                                        >
                                            <ArrowUpRight className="h-3 w-3" />
                                            Raw Intel
                                        </a>
                                    </div>
                                )}
                            </div>

                            <div className="aspect-video bg-zinc-950 relative flex items-center justify-center group overflow-hidden">
                                {selectedJob?.status === "Completed" ? (
                                    <video
                                        src={getStaticUrl(selectedJob.output_path)}
                                        controls
                                        className="w-full h-full object-contain"
                                    />
                                ) : selectedJob ? (
                                    <div className="flex flex-col items-center gap-8 p-12 text-center relative z-10">
                                        <div className="relative">
                                            <RefreshCw className="h-32 w-32 text-primary/10 animate-spin-slow transition-transform" />
                                            <div className="absolute inset-0 flex items-center justify-center">
                                                <Layers className="h-14 w-14 text-primary animate-pulse shadow-[0_0_50px_rgba(var(--primary-rgb),0.4)]" />
                                            </div>
                                        </div>
                                        <div className="space-y-3">
                                            <h4 className="text-3xl font-black tracking-tighter text-white uppercase">Injecting Originality...</h4>
                                            <p className="text-zinc-500 font-medium max-w-sm mx-auto leading-relaxed">Applying high-velocity neural transforms to maximize reach and bypass platform signatures.</p>
                                        </div>
                                        <div className="w-80 space-y-3">
                                            <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-zinc-500">
                                                <span>Render Progress</span>
                                                <span className="text-primary">{selectedJob.progress}%</span>
                                            </div>
                                            <div className="bg-zinc-900 h-2 rounded-full overflow-hidden border border-white/5">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${selectedJob.progress}%` }}
                                                    transition={{ duration: 1 }}
                                                    className="bg-primary h-full shadow-[0_0_20px_rgba(var(--primary-rgb),0.5)]"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center gap-6 opacity-30">
                                        <Video className="h-24 w-24 text-zinc-800" />
                                        <p className="text-xs font-black uppercase tracking-[0.3em] text-zinc-700">Offline // Select Pipeline Job</p>
                                    </div>
                                )}

                                {/* Premium Success Overlay */}
                                <AnimatePresence>
                                    {selectedJob?.status === "Completed" && (
                                        <motion.div
                                            initial={{ y: 20, opacity: 0 }}
                                            animate={{ y: 0, opacity: 1 }}
                                            className="absolute bottom-8 left-8 right-8 p-6 glass-card border-none bg-black/60 backdrop-blur-xl rounded-3xl flex items-center justify-between opacity-0 group-hover:opacity-100 transition-all shadow-2xl"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className="h-12 w-12 rounded-2xl bg-emerald-500 flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.4)]">
                                                    <CheckCircle2 className="h-7 w-7 text-black" />
                                                </div>
                                                <div className="space-y-0.5">
                                                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500">Intel Validated</p>
                                                    <h5 className="text-sm font-black text-white uppercase tracking-tighter">Ready for Global Distribution</h5>
                                                </div>
                                            </div>
                                            <Link href="/publishing" className="bg-primary text-white text-[11px] font-black px-6 py-3 rounded-2xl hover:shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)] transition-all uppercase tracking-widest">
                                                Deploy Matrix
                                            </Link>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Queue List */}
                        <div className="space-y-6">
                            <div className="flex items-center justify-between px-4">
                                <div className="flex items-center gap-3">
                                    <Clock className="h-5 w-5 text-zinc-500" />
                                    <h3 className="text-xs font-black uppercase tracking-[0.25em] text-zinc-500">Active Pipeline Jobs</h3>
                                </div>
                                <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">{processingJobs.length} NODES</span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <AnimatePresence mode="popLayout">
                                    {!Array.isArray(processingJobs) || processingJobs.length === 0 ? (
                                        <div className="col-span-full py-16 glass-card border-dashed rounded-[2.5rem] flex flex-col items-center gap-4 opacity-40">
                                            <PlusCircle className="h-10 w-10 text-zinc-700" />
                                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Pipeline Offline</p>
                                        </div>
                                    ) : (
                                        processingJobs.map((job, idx) => (
                                            <motion.div
                                                layout
                                                key={job.id}
                                                initial={{ scale: 0.9, opacity: 0 }}
                                                animate={{ scale: 1, opacity: 1 }}
                                                whileHover={{ scale: 1.02, y: -2 }}
                                                whileTap={{ scale: 0.98 }}
                                                transition={{
                                                    delay: idx * 0.05,
                                                    scale: { type: "spring", stiffness: 400, damping: 25 },
                                                    y: { type: "spring", stiffness: 400, damping: 25 }
                                                }}
                                                onClick={() => setSelectedJob(job)}
                                                className={cn(
                                                    "group flex items-center gap-5 relative overflow-hidden transition-all cursor-pointer",
                                                    selectedJob?.id === job.id
                                                        ? "glass-card border-primary/40 bg-primary/10 shadow-[0_0_40px_rgba(var(--primary-rgb),0.1)]"
                                                        : "glass-card hover:border-zinc-700"
                                                )}
                                            >
                                                <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-[var(--shimmer-opacity)] transition-opacity pointer-events-none" />
                                                <div className={cn(
                                                    "h-14 w-14 rounded-2xl flex items-center justify-center shrink-0 transition-all duration-500 group-hover:scale-110",
                                                    job.status === "Completed" ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]" : "bg-primary/10 text-primary border border-primary/20"
                                                )}>
                                                    {job.status === "Completed" ? (
                                                        <CheckCircle2 className="h-7 w-7 neon-glow" />
                                                    ) : (
                                                        <RefreshCw className={cn("h-7 w-7", job.status === "Rendering" && "animate-spin")} />
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0 space-y-3">
                                                    <div className="flex items-center justify-between gap-2">
                                                        <h4 className="font-black text-sm tracking-tight truncate uppercase text-white">{job.title || "VIRAL_TRANSFORM_1"}</h4>
                                                        {job.status !== "Completed" && job.status !== "Failed" && job.status !== "Aborted" && (
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handleAbort(job.id);
                                                                }}
                                                                className="text-[8px] font-black text-rose-500 hover:text-rose-400 uppercase tracking-widest px-2 py-1 rounded-md border border-rose-500/20 hover:border-rose-500/50 transition-all"
                                                            >
                                                                Abort
                                                            </button>
                                                        )}
                                                    </div>
                                                    <div className="space-y-2">
                                                        <div className="flex justify-between text-[8px] font-black uppercase tracking-widest text-zinc-500">
                                                            <span>{job.status}</span>
                                                            <span className={job.status === 'Completed' ? 'text-emerald-500' : 'text-primary'}>{job.progress}%</span>
                                                        </div>
                                                        <div className="bg-zinc-950 h-1 rounded-full overflow-hidden border border-white/5">
                                                            <motion.div
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${job.progress}%` }}
                                                                transition={{ duration: 0.8 }}
                                                                className={cn(
                                                                    "h-full",
                                                                    job.status === "Completed" ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-primary"
                                                                )}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ))
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </div>

                    {/* Filter Configuration Sidebar */}
                    <div className="space-y-10">
                        <div className="flex items-center gap-4">
                            <h3 className="text-xl font-black uppercase tracking-tighter text-white">Engine Nodes</h3>
                            <div className="h-[1px] flex-1 bg-white/5" />
                        </div>

                        <div className="glass-card rounded-[2.5rem] overflow-hidden shadow-2xl flex flex-col max-h-[700px]">
                            <div className="flex-1 overflow-y-auto divide-y divide-white/5 custom-scrollbar">
                                {(!Array.isArray(activeFilters) || activeFilters.length === 0) && (
                                    <div className="p-8 text-zinc-600 font-black uppercase tracking-[0.2em] text-[10px] text-center">Nodes Desynchronized</div>
                                )}
                                {Array.isArray(activeFilters) && activeFilters.map((filter: any, idx: number) => (
                                    <motion.div
                                        key={filter.id}
                                        initial={{ x: 20, opacity: 0 }}
                                        animate={{ x: 0, opacity: 1 }}
                                        transition={{ delay: idx * 0.05 }}
                                        onClick={() => handleToggleFilter(filter.id)}
                                        className="p-8 flex flex-col gap-4 group cursor-pointer hover:bg-white/[0.02] transition-colors relative"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className={cn(
                                                    "h-10 w-10 rounded-xl flex items-center justify-center transition-all border",
                                                    filter.enabled ? "bg-primary/20 border-primary/30 shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)]" : "bg-zinc-900 border-white/5"
                                                )}>
                                                    <Sparkles className={cn("h-5 w-5", filter.enabled ? "text-primary neon-glow" : "text-zinc-700")} />
                                                </div>
                                                <div className="space-y-0.5">
                                                    <span className="font-black text-xs tracking-[0.05em] uppercase text-white">{filter.name}</span>
                                                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{filter.enabled ? 'Active' : 'Standby'}</p>
                                                </div>
                                            </div>
                                            {/* Toggle Switch */}
                                            <div className={cn(
                                                "w-12 h-6 rounded-full transition-all relative border",
                                                filter.enabled ? "bg-primary border-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.3)]" : "bg-zinc-800 border-white/5"
                                            )}>
                                                <motion.div
                                                    animate={{ x: filter.enabled ? 24 : 4 }}
                                                    className="absolute top-1 w-3 h-3 bg-white rounded-full transition-all"
                                                />
                                            </div>
                                        </div>
                                        <p className="text-[11px] text-zinc-500 font-medium leading-relaxed">{filter.description}</p>
                                    </motion.div>
                                ))}
                            </div>

                        </div>

                        {/* AI Assistant Insight */}
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="glass-card p-8 rounded-[2rem] space-y-5 relative overflow-hidden"
                        >
                            <div className="absolute inset-0 scanline opacity-5" />
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                    <Cpu className="h-4 w-4 text-emerald-500 animate-pulse" />
                                </div>
                                <span className="text-emerald-500 text-[10px] font-black uppercase tracking-[0.2em]">Neural Recommendation</span>
                            </div>
                            <p className="text-zinc-400 text-xs leading-relaxed font-medium">
                                "{Array.isArray(activeFilters) ? activeFilters.filter(f => f.enabled).map(f => f.name).join(" + ") : 'N/A'} is recommended for this niche to maximize reach in US regions."
                            </p>
                            <div className="pt-2">
                                <span className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Confidence: 94.2% Alpha</span>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

export default function TransformationPage() {
    return (
        <Suspense fallback={
            <DashboardLayout>
                <div className="flex items-center justify-center min-h-screen bg-black relative overflow-hidden">
                    <div className="absolute inset-0 scanline opacity-20 pointer-events-none" />
                    <div className="flex flex-col items-center gap-6">
                        <RefreshCw className="h-16 w-16 animate-spin text-primary shadow-[0_0_30px_rgba(var(--primary-rgb),0.4)]" />
                        <p className="text-[10px] font-black uppercase tracking-[0.4em] text-primary animate-pulse">Initializing Neural Core...</p>
                    </div>
                </div>
            </DashboardLayout>
        }>
            <TransformationPageContent />
        </Suspense>
    );
}

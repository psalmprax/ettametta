"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
import {
    Zap,
    Layers,
    Search,
    Cpu,
    Sparkles,
    Share2,
    Database,
    Plus,
    Play,
    Settings2,
    RefreshCw,
    Loader2,
    CheckCircle2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { NexusNode, NodeType } from "@/components/ui/NexusNode";
import { useWebSocket } from "@/hooks/useWebSocket";

interface Blueprint {
    id: string;
    name: string;
    description: string;
    nodes: { type: NodeType; label: string; desc: string }[];
}

const BLUEPRINTS: Blueprint[] = [
    {
        id: "viral-reskin",
        name: "Viral Re-skinner",
        description: "Auto-discovery of high-velocity clips with neural style injection.",
        nodes: [
            { type: 'ingress', label: "Deep Discovery", desc: "Scanning TikTok clusters for niche alpha." },
            { type: 'cognition', label: "Viral DNA Match", desc: "Llama-3 analysis of hook retention." },
            { type: 'synthesis', label: "Neural Remix", desc: "Applying cinematic overlays and speed ramping." },
            { type: 'egress', label: "Global Sync", desc: "Scheduled dispatch to all social hubs." }
        ]
    },
    {
        id: "story-factory",
        name: "Storytelling Engine",
        description: "Script-to-video autonomous workflow for long-form quality.",
        nodes: [
            { type: 'ingress', label: "Script Pulse", desc: "Generating high-retention narrative scripts." },
            { type: 'cognition', label: "Vibe Mapping", desc: "Mapping visual prompts to emotional peaks." },
            { type: 'synthesis', label: "Nexus Assembly", desc: "Synthesizing voiceover, music, and stock visuals." },
            { type: 'egress', label: "HDP Publish", desc: "High-definition export and cloud archiving." }
        ]
    }
];

export default function NexusPage() {
    const [activeBlueprint, setActiveBlueprint] = useState<Blueprint | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);
    const [nexusJobs, setNexusJobs] = useState<any[]>([]);
    const [niches, setNiches] = useState<string[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("");
    const [userTier, setUserTier] = useState<string>("free");
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
    const { data: jobUpdate } = useWebSocket<any>(`${WS_BASE}/ws/jobs`);

    // Fetch initial data
    useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem("et_token");
            if (!token) return;

            try {
                // Fetch User Tier
                const userRes = await fetch(`${API_BASE}/auth/me`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (userRes.ok) {
                    const userData = await userRes.json();
                    setUserTier(userData.subscription.toLowerCase());
                }

                // Fetch Niches
                const nicheRes = await fetch(`${API_BASE}/discovery/niches`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (nicheRes.ok) {
                    const nicheData = await nicheRes.json();
                    setNiches(nicheData);
                    if (nicheData.length > 0) setSelectedNiche(nicheData[0]);
                }

                // Fetch Initial Jobs
                const jobsRes = await fetch(`${API_BASE}/nexus/jobs`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (jobsRes.ok) {
                    setNexusJobs(await jobsRes.json());
                }
            } catch (err) {
                console.error("Failed to fetch Nexus data:", err);
            }
        };

        fetchData();
    }, []);

    // Handle WebSocket updates
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

    // Button handlers
    const handleClusterSettings = () => {
        // Navigate to settings page
        window.location.href = '/settings';
    };

    const handleCustomRecipe = () => {
        // Navigate to creation page for custom workflows
        window.location.href = '/creation';
    };

    const handleInspectResult = (job: any) => {
        if (job.output_path) {
            window.open(`/api/${job.output_path}`, '_blank');
        } else {
            alert("Output not available yet.");
        }
    };

    const handleLaunch = async () => {
        if (!activeBlueprint) return;
        setIsLaunching(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/nexus/compose`, {
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
            });
            if (res.ok) {
                const data = await res.json();
                setActiveJobId(String(data.job_id));
                alert("Nexus Pipeline Launched. Check the active nodes below.");
            }
        } catch (err) {
            console.error("Launch failed:", err);
        } finally {
            setIsLaunching(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-12 pb-24">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Automation Command</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black italic tracking-tighter uppercase text-white leading-none">
                            Nexus <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-primary text-hollow">Flow</span>
                        </h1>
                        <p className="text-zinc-500 font-medium max-w-xl">
                            Orchestrating autonomous content loops through high-fidelity <span className="text-zinc-300 font-bold">Neural Pipelines</span>.
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <select
                            value={selectedNiche}
                            onChange={(e) => setSelectedNiche(e.target.value)}
                            className="glass-card bg-zinc-950 border-white/10 rounded-2xl px-6 py-4 text-[10px] font-black uppercase tracking-widest text-primary outline-none focus:ring-2 focus:ring-primary/20 transition-all hover:border-primary/40 cursor-pointer"
                        >
                            <option value="">Select Niche...</option>
                            {niches.map(n => <option key={n} value={n}>{n}</option>)}
                        </select>
                        <button
                            onClick={handleClusterSettings}
                            className="glass-card px-6 py-4 rounded-2xl flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-white hover:border-white/20 transition-all bg-zinc-950/20"
                        >
                            <Settings2 className="h-4 w-4" />
                            Cluster Settings
                        </button>
                        <motion.button
                            whileHover={{ scale: 1.05, boxShadow: "0 0 60px rgba(var(--primary-rgb),0.5)" }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleLaunch}
                            disabled={!activeBlueprint || isLaunching}
                            className={cn(
                                "bg-gradient-to-br from-primary via-primary to-blue-600 text-white font-black py-4 px-10 rounded-2xl flex items-center gap-3 shadow-[0_0_40px_rgba(var(--primary-rgb),0.25)] transition-all uppercase text-xs tracking-[0.2em] relative overflow-hidden group/btn",
                                (!activeBlueprint || isLaunching) && "opacity-50 cursor-not-allowed grayscale shadow-none"
                            )}
                        >
                            <div className="absolute inset-0 bg-white/10 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-500" />
                            {isLaunching ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5 fill-white group-hover/btn:scale-110 transition-transform" />}
                            <span className="relative z-10">{isLaunching ? "Spinning Up..." : "Initiate Cinema Mode"}</span>
                        </motion.button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">
                    {/* Blueprints Sidebar */}
                    <div className="lg:col-span-1 space-y-8">
                        <div className="flex items-center gap-4">
                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Available Recipes</h3>
                            <div className="h-[1px] flex-1 bg-white/5" />
                        </div>

                        <div className="space-y-4">
                            {BLUEPRINTS.map((bp) => {
                                const isGated = bp.id === "story-factory" && userTier === "free";
                                return (
                                    <motion.div
                                        key={bp.id}
                                        whileHover={!isGated ? { x: 5, backgroundColor: "rgba(255,255,255,0.03)" } : {}}
                                        onClick={() => !isGated && setActiveBlueprint(bp)}
                                        className={cn(
                                            "p-6 rounded-[2rem] border transition-all duration-500 relative overflow-hidden group/bp",
                                            activeBlueprint?.id === bp.id
                                                ? "bg-primary/10 border-primary/50 shadow-[0_0_30px_rgba(var(--primary-rgb),0.1)]"
                                                : "bg-zinc-950/40 border-white/5",
                                            isGated ? "opacity-50 cursor-not-allowed grayscale" : "cursor-pointer hover:border-white/10"
                                        )}
                                    >
                                        {activeBlueprint?.id === bp.id && (
                                            <div className="absolute inset-0 shimmer-elite opacity-20 pointer-events-none" />
                                        )}
                                        <div className="flex items-center justify-between mb-4">
                                            <div className={cn(
                                                "h-12 w-12 rounded-2xl flex items-center justify-center transition-all duration-500 shadow-lg",
                                                activeBlueprint?.id === bp.id
                                                    ? "bg-primary text-white scale-110 shadow-primary/30"
                                                    : "bg-zinc-900 text-zinc-600 group-hover/bp:text-zinc-300"
                                            )}>
                                                <Layers className="h-6 w-6" />
                                            </div>
                                            {isGated ? (
                                                <div className="px-3 py-1 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-500 text-[8px] font-black uppercase tracking-[0.2em] flex items-center gap-1.5 shadow-[0_0_10px_rgba(245,158,11,0.1)]">
                                                    <div className="h-1 w-1 rounded-full bg-amber-500 animate-pulse" />
                                                    Locked
                                                </div>
                                            ) : activeBlueprint?.id === bp.id && (
                                                <div className="h-2 w-2 rounded-full bg-primary animate-ping" />
                                            )}
                                        </div>
                                        <h4 className="font-black text-sm uppercase tracking-tight text-white mb-2 italic flex items-center gap-2 group-hover/bp:text-primary transition-colors">
                                            {bp.name}
                                        </h4>
                                        <p className="text-[10px] font-medium text-zinc-500 leading-relaxed group-hover/bp:text-zinc-400 transition-colors">
                                            {bp.description}
                                        </p>
                                    </motion.div>
                                )
                            })}

                            <button
                                onClick={handleCustomRecipe}
                                className="w-full p-6 rounded-[2rem] border border-dashed border-white/5 flex flex-col items-center justify-center gap-3 text-zinc-700 hover:text-zinc-500 hover:border-white/10 transition-all group"
                            >
                                <Plus className="h-8 w-8 group-hover:scale-110 transition-transform" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em]">Custom Recipe</span>
                            </button>
                        </div>
                    </div>

                    {/* Main Workspace / active Pipeline */}
                    <div className="lg:col-span-3 space-y-12">
                        <div className="glass-card rounded-[3rem] p-12 min-h-[500px] relative overflow-hidden flex flex-col items-center justify-center border-white/5 bg-white/[0.01]">
                            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />

                            <AnimatePresence mode="wait">
                                {activeBlueprint ? (
                                    <motion.div
                                        key={activeBlueprint.id}
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        className="w-full flex flex-col items-center"
                                    >
                                        <div className="w-full flex flex-wrap items-center justify-center gap-8 relative">
                                            {activeBlueprint.nodes.map((node, idx) => {
                                                const activeJob = nexusJobs.find(j => String(j.id) === activeJobId);
                                                let status: 'pending' | 'processing' | 'complete' | 'error' = 'pending';
                                                let progress: number | undefined = undefined;

                                                if (activeJob) {
                                                    // Simple heuristic: map job status and progress to nodes
                                                    // In a real app, each node would have its own status in the job object
                                                    if (activeJob.status === 'COMPLETED') {
                                                        status = 'complete';
                                                    } else if (activeJob.status === 'FAILED') {
                                                        status = 'error';
                                                    } else {
                                                        // Distribute job progress across nodes
                                                        const nodeThreshold = (idx + 1) * (100 / activeBlueprint.nodes.length);
                                                        const prevThreshold = idx * (100 / activeBlueprint.nodes.length);

                                                        if (activeJob.progress >= nodeThreshold) {
                                                            status = 'complete';
                                                        } else if (activeJob.progress > prevThreshold) {
                                                            status = 'processing';
                                                            progress = Math.round(((activeJob.progress - prevThreshold) / (100 / activeBlueprint.nodes.length)) * 100);
                                                        }
                                                    }
                                                }

                                                return (
                                                    <React.Fragment key={idx}>
                                                        <NexusNode
                                                            type={node.type}
                                                            label={node.label}
                                                            description={node.desc}
                                                            status={status}
                                                            active={
                                                                (activeJob && status === 'processing') ||
                                                                (!activeJob && selectedNodeIndex === idx) ||
                                                                (activeJob && activeJob.status === 'COMPLETED' && selectedNodeIndex === idx)
                                                            }
                                                            progress={progress}
                                                            onClick={() => setSelectedNodeIndex(idx)}
                                                            metrics={[
                                                                { label: "Stability", value: "99.9%" },
                                                                { label: "Sync", value: "Alpha" }
                                                            ]}
                                                        />
                                                        {idx < activeBlueprint.nodes.length - 1 && (
                                                            <div className={cn(
                                                                "hidden xl:block h-[2px] w-12 transition-all duration-1000",
                                                                status === 'complete' ? "bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" : "bg-white/10"
                                                            )} />
                                                        )}
                                                    </React.Fragment>
                                                );
                                            })}
                                        </div>

                                        <div className="mt-16 text-center space-y-2">
                                            <p className="text-xs font-black uppercase tracking-[0.4em] text-zinc-600 italic">Pipeline Configuration Active</p>
                                            <p className="text-[10px] font-bold text-zinc-400">Ready to initiate high-fidelity automation sequence.</p>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="flex flex-col items-center text-center gap-6"
                                    >
                                        <div className="h-24 w-24 rounded-[2.5rem] bg-zinc-950 border border-white/5 flex items-center justify-center relative">
                                            <Zap className="h-10 w-10 text-zinc-800" />
                                            <div className="absolute -inset-4 border border-zinc-900 rounded-[3rem] animate-pulse" />
                                        </div>
                                        <div className="space-y-2">
                                            <h3 className="text-xl font-black uppercase tracking-tighter text-zinc-600 italic">Workspace Desynchronized</h3>
                                            <p className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest">Drag a Blueprint to initiate the factory</p>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Active Nexus Jobs */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-4">
                                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Live Production Matrix</h3>
                                <div className="h-[1px] flex-1 bg-white/5" />
                                <span className="text-[10px] font-mono text-zinc-700">{nexusJobs.length} ACTIVE_NODES</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                                {nexusJobs.map((job) => (
                                    <motion.div
                                        key={job.id}
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        whileHover={{ y: -8, boxShadow: "0 25px 50px -12px rgba(var(--primary-rgb),0.25)" }}
                                        className="glass-card hover:border-primary/50 transition-all p-8 space-y-8 group/job relative overflow-hidden"
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover/job:opacity-100 transition-opacity duration-700" />

                                        <div className="flex items-center justify-between relative z-10">
                                            <div className="flex items-center gap-4">
                                                <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]">
                                                    <Zap className="h-6 w-6 text-primary group-hover/job:scale-110 group-hover/job:rotate-12 transition-transform duration-500" />
                                                </div>
                                                <div className="space-y-1">
                                                    <span className="text-xs font-black uppercase tracking-tight text-white group-hover/job:text-primary transition-colors">Node_{String(job.id).slice(0, 4)}</span>
                                                    <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-[0.3em]">{job.niche}</p>
                                                </div>
                                            </div>
                                            <div className={cn(
                                                "text-[9px] font-black uppercase tracking-[0.2em] px-3 py-1.5 rounded-full border flex items-center gap-2 transition-all duration-500",
                                                job.status === "COMPLETED"
                                                    ? "text-emerald-500 border-emerald-500/20 bg-emerald-500/5 shadow-[0_0_20px_rgba(16,185,129,0.1)]"
                                                    : "text-primary border-primary/20 bg-primary/5 shadow-[0_0_20px_rgba(var(--primary-rgb),0.1)]"
                                            )}>
                                                {job.status === "COMPLETED" && <CheckCircle2 className="h-2.5 w-2.5" />}
                                                {job.status}
                                            </div>
                                        </div>

                                        <div className="space-y-4 relative z-10">
                                            <div className="flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-zinc-500 italic">
                                                <span className="group-hover/job:text-zinc-300 transition-colors">Neural Synthesizing...</span>
                                                <span className="text-primary group-hover/job:scale-110 transition-transform">{job.progress}%</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-zinc-950/80 border border-white/5 rounded-full overflow-hidden shadow-inner">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${job.progress}%` }}
                                                    className="h-full bg-primary shadow-[0_0_25px_rgba(var(--primary-rgb),0.6)]"
                                                />
                                            </div>
                                        </div>

                                        {job.status === "COMPLETED" && (
                                            <button
                                                onClick={() => handleInspectResult(job)}
                                                className="w-full py-4 rounded-2xl bg-zinc-950 border border-white/5 text-[10px] font-black uppercase tracking-[0.4em] text-zinc-500 hover:text-white hover:border-primary/50 hover:bg-primary/5 transition-all relative overflow-hidden group/inspect"
                                            >
                                                <div className="absolute inset-x-0 bottom-0 h-px bg-primary scale-x-0 group-hover/inspect:scale-x-100 transition-transform duration-700" />
                                                Inspect Neural Stream
                                            </button>
                                        )}
                                    </motion.div>
                                ))}

                                {nexusJobs.length === 0 && (
                                    <div className="col-span-full py-20 text-center glass-card border-dashed opacity-20 group/empty hover:opacity-40 transition-opacity">
                                        <Loader2 className="h-10 w-10 text-zinc-800 mx-auto mb-4 animate-spin group-hover/empty:text-primary transition-colors" />
                                        <p className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-700 italic">No Active Neural Streams</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

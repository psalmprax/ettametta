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
    Loader2
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
    const [selectedNiche, setSelectedNiche] = useState("Technology");
    const [userTier, setUserTier] = useState<string>("free");
    const { data: jobUpdate } = useWebSocket<any>(`${WS_BASE}/ws/jobs`);

    // Fetch existing Nexus jobs
    useEffect(() => {
        const fetchNexusJobs = async () => {
            try {
                const token = localStorage.getItem("vf_token");
                const res = await fetch(`${API_BASE}/nexus/jobs`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setNexusJobs(data);
                }
            } catch (err) {
                console.error("Failed to fetch nexus jobs:", err);
            }
        };
        fetchNexusJobs();

        const fetchProfile = async () => {
            try {
                const token = localStorage.getItem("vf_token");
                const response = await fetch(`${API_BASE}/auth/me`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setUserTier(data.subscription || "free");
                }
            } catch (err) {
                console.error("Failed to fetch profile", err);
            }
        };
        fetchProfile();

        const fetchNiches = async () => {
            try {
                const token = localStorage.getItem("vf_token");
                const res = await fetch(`${API_BASE}/discovery/niches`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (res.ok) setNiches(await res.json());
            } catch (err) {
                console.error("Failed to fetch niches:", err);
            }
        };
        fetchNiches();
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

    const handleLaunch = async () => {
        if (!activeBlueprint) return;
        setIsLaunching(true);
        try {
            const token = localStorage.getItem("vf_token");
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
                            className="glass-card bg-zinc-950 border-white/10 rounded-xl px-4 py-4 text-[10px] font-black uppercase tracking-widest text-primary outline-none focus:ring-1 focus:ring-primary/40 transition-all hover:border-primary/30"
                        >
                            <option value="">Select Niche...</option>
                            {niches.map(n => <option key={n} value={n}>{n}</option>)}
                        </select>
                        <button className="glass-card px-6 py-4 rounded-2xl flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-white transition-all">
                            <Settings2 className="h-4 w-4" />
                            Cluster Settings
                        </button>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleLaunch}
                            disabled={!activeBlueprint || isLaunching}
                            className={cn(
                                "bg-primary text-white font-black py-4 px-10 rounded-2xl flex items-center gap-3 shadow-[0_0_50px_rgba(var(--primary-rgb),0.3)] transition-all uppercase text-xs tracking-widest",
                                (!activeBlueprint || isLaunching) && "opacity-50 cursor-not-allowed grayscale"
                            )}
                        >
                            {isLaunching ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5 fill-white" />}
                            {isLaunching ? "Spinning Up..." : "Initiate Nexus"}
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
                                        whileHover={!isGated ? { x: 5 } : {}}
                                        onClick={() => !isGated && setActiveBlueprint(bp)}
                                        className={cn(
                                            "p-6 rounded-[2rem] border transition-all duration-500 relative overflow-hidden group",
                                            activeBlueprint?.id === bp.id
                                                ? "bg-primary/5 border-primary/40 shadow-lg"
                                                : "bg-zinc-950/40 border-white/5",
                                            isGated ? "opacity-50 cursor-not-allowed grayscale" : "cursor-pointer hover:border-white/10"
                                        )}
                                    >
                                        <div className="flex items-center justify-between mb-3">
                                            <div className={cn(
                                                "h-10 w-10 rounded-xl flex items-center justify-center transition-all",
                                                activeBlueprint?.id === bp.id ? "bg-primary text-white" : "bg-zinc-900 text-zinc-600"
                                            )}>
                                                <Layers className="h-5 w-5" />
                                            </div>
                                            {activeBlueprint?.id === bp.id && (
                                                <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                                            )}
                                            {isGated && (
                                                <div className="px-2 py-1 rounded border border-amber-500/20 bg-amber-500/10 text-amber-500 text-[8px] font-black uppercase tracking-widest flex items-center gap-1">
                                                    Locked
                                                </div>
                                            )}
                                        </div>
                                        <h4 className="font-black text-sm uppercase tracking-tight text-white mb-2 italic flex items-center gap-2">
                                            {bp.name}
                                        </h4>
                                        <p className="text-[10px] font-medium text-zinc-500 leading-relaxed">
                                            {bp.description}
                                        </p>
                                    </motion.div>
                                )
                            })}

                            <button className="w-full p-6 rounded-[2rem] border border-dashed border-white/5 flex flex-col items-center justify-center gap-3 text-zinc-700 hover:text-zinc-500 hover:border-white/10 transition-all group">
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
                                            {activeBlueprint.nodes.map((node, idx) => (
                                                <React.Fragment key={idx}>
                                                    <NexusNode
                                                        type={node.type}
                                                        label={node.label}
                                                        description={node.desc}
                                                        status="pending"
                                                        active={idx === 0}
                                                        progress={idx === 0 ? 0 : undefined}
                                                        metrics={[
                                                            { label: "Stability", value: "99.9%" },
                                                            { label: "Sync", value: "Alpha" }
                                                        ]}
                                                    />
                                                    {idx < activeBlueprint.nodes.map.length - 1 && (
                                                        <div className="hidden xl:block h-[2px] w-12 bg-gradient-to-r from-white/10 to-transparent" />
                                                    )}
                                                </React.Fragment>
                                            ))}
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

                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                {nexusJobs.map((job) => (
                                    <motion.div
                                        key={job.id}
                                        className="glass-card hover:border-primary/30 transition-all p-6 space-y-6 group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
                                                    <Zap className="h-4 w-4 text-primary" />
                                                </div>
                                                <div className="space-y-0.5">
                                                    <span className="text-[10px] font-black uppercase tracking-tight text-white">Job_{job.id.slice(0, 4)}</span>
                                                    <p className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{job.niche}</p>
                                                </div>
                                            </div>
                                            <span className={cn(
                                                "text-[8px] font-black uppercase tracking-widest px-2 py-1 rounded-md border",
                                                job.status === "COMPLETED" ? "text-emerald-500 border-emerald-500/20" : "text-primary border-primary/20"
                                            )}>
                                                {job.status}
                                            </span>
                                        </div>

                                        <div className="space-y-3">
                                            <div className="flex justify-between text-[8px] font-black uppercase tracking-widest text-zinc-500">
                                                <span>Synthesizing...</span>
                                                <span className="text-primary">{job.progress}%</span>
                                            </div>
                                            <div className="h-1 w-full bg-zinc-900 border border-white/5 rounded-full overflow-hidden">
                                                <motion.div
                                                    animate={{ width: `${job.progress}%` }}
                                                    className="h-full bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]"
                                                />
                                            </div>
                                        </div>

                                        {job.status === "COMPLETED" && (
                                            <button className="w-full py-2 rounded-xl bg-zinc-950 border border-white/10 text-[8px] font-black uppercase tracking-widest text-zinc-400 hover:text-white hover:border-primary/50 transition-all">
                                                Inspect Result
                                            </button>
                                        )}
                                    </motion.div>
                                ))}

                                {nexusJobs.length === 0 && (
                                    <div className="col-span-full py-20 text-center glass-card border-dashed opacity-20">
                                        <Loader2 className="h-8 w-8 text-zinc-800 mx-auto mb-4 animate-spin" />
                                        <p className="text-[10px] font-black uppercase tracking-widest text-zinc-700 italic">No Active Neural Streams</p>
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

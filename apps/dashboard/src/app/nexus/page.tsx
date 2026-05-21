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
    ChevronDown,
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
    PlusCircle,
    Users,
    Volume2,
    Palette,
    Scissors,
    Sliders
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
import { AreaChartCustom } from "@/components/ui/ChartComponents";

import { Blueprint, NexusJob, Persona } from "@/lib/types";
import { useTelemetry } from "@/context/TelemetryContext";

function NexusContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents, logs: systemLogs, lastJobUpdate, pulse, status } = useTelemetry();
    
    const [personas, setPersonas] = useState<Persona[]>([]);
    const [capabilities, setCapabilities] = useState<any[]>([]);
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
    
    const [searchTerm, setSearchTerm] = useState("");
    const [activeCategory, setActiveCategory] = useState("All");
    
    // Preview Scenes Modal State
    const [previewJobId, setPreviewJobId] = useState<string | null>(null);
    const [previewScenes, setPreviewScenes] = useState<any[]>([]);
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

    // Interactive Style Customizer States
    const [selectedStylePreset, setSelectedStylePreset] = useState<'NEON_CYBER' | 'AMBER_WARM' | 'MONOCHROME_DARK' | 'EMERALD_MATRIX'>('NEON_CYBER');
    const [colorTemp, setColorTemp] = useState<number>(50);
    const [grainDensity, setGrainDensity] = useState<number>(20);
    const [contrast, setContrast] = useState<number>(50);
    const [kenBurnsSpeed, setKenBurnsSpeed] = useState<number>(30);
    const [swappedAssets, setSwappedAssets] = useState<Record<number, { thumbnail: string, title: string, tags: string[] }>>({});
    const [activeSwapDrawerIndex, setActiveSwapDrawerIndex] = useState<number | null>(null);
    const [sandboxTab, setSandboxTab] = useState<'console' | 'telemetry'>('console');

    // Diagnostics Telemetry Mock Data
    const latencyData = useMemo(() => [
        { time: "10:00", value: 180 },
        { time: "10:10", value: 240 },
        { time: "10:20", value: 310 },
        { time: "10:30", value: 190 },
        { time: "10:40", value: 150 },
        { time: "10:50", value: 220 },
        { time: "11:00", value: 165 },
    ], []);

    const workerLoadData = useMemo(() => [
        { time: "10:00", value: 25 },
        { time: "10:10", value: 45 },
        { time: "10:20", value: 65 },
        { time: "10:30", value: 40 },
        { time: "10:40", value: 30 },
        { time: "10:50", value: 55 },
        { time: "11:00", value: 38 },
    ], []);

    const healingData = useMemo(() => [
        { time: "10:00", value: 1 },
        { time: "10:10", value: 0 },
        { time: "10:20", value: 3 },
        { time: "10:30", value: 1 },
        { time: "10:40", value: 0 },
        { time: "10:50", value: 2 },
        { time: "11:00", value: 0 },
    ], []);

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
    }, [searchParams]);

    // Fetch initial data
    const fetchData = useCallback(async () => {
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
            withRealFallback<NexusJob[]>(
                () => fetch(`${API_BASE}/nexus/jobs`, { headers }),
                {
                    fallback: [],
                    onSuccess: (data) => setNexusJobs(Array.isArray(data) ? data : [])
                }
            ),
            withRealFallback<any[]>(
                () => fetch(`${API_BASE}/discovery/niches`, { headers }),
                {
                    fallback: [
                        "AI Technology", "Motivation", "Finance", "Health & Fitness",
                        "Business", "Marketing", "Lifestyle", "Gaming",
                        "Education", "Real Estate", "E-commerce", "Spirituality"
                    ],
                    onSuccess: (data: any) => {
                        const defaultNiches = [
                            "AI Technology", "Motivation", "Finance", "Health & Fitness",
                            "Business", "Marketing", "Lifestyle", "Gaming",
                            "Education", "Real Estate", "E-commerce", "Spirituality"
                        ];
                        
                        // Handle both array and object responses
                        let nicheList = Array.isArray(data) ? data : (data?.niches || []);
                        
                        // Top-Notch: If the user has no monitored niches, use the high-velocity defaults
                        if (nicheList.length === 0) {
                            nicheList = defaultNiches;
                        }
                        
                        setNiches(nicheList);
                        
                        // Ensure we have a selection if nothing is selected
                        if (nicheList.length > 0 && !selectedNiche) {
                            const firstNiche = typeof nicheList[0] === 'string' ? nicheList[0] : (nicheList[0].niche || nicheList[0].name);
                            setSelectedNiche(firstNiche);
                        }
                    }
                }
            ),
            withRealFallback<any[]>(
                () => fetch(`${API_BASE}/agent/capabilities`, { headers }),
                {
                    fallback: [],
                    onSuccess: (data: any) => {
                        // Capabilities endpoint returns { workers: [...] }
                        const caps = Array.isArray(data) ? data : (data?.workers || []);
                        setCapabilities(caps);
                    }
                }
            )
        ]);
    }, []);

    // Function to fetch and display scene preview
    const handlePreviewScenes = async (jobId: string) => {
        setIsLoadingPreview(true);
        setPreviewJobId(jobId);
        
        try {
            const token = await getAuthToken();
            const response = await fetch(`${API_BASE}/nexus/jobs/${jobId}/preview`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                setPreviewScenes(data.data?.scenes || []);
                setIsPreviewModalOpen(true);
            } else {
                toast.error("No scene data available for this job");
            }
        } catch (error) {
            toast.error("Failed to load scene preview");
        } finally {
            setIsLoadingPreview(false);
        }
    };

    const fetchPersonas = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
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

    const [deployingIds, setDeployingIds] = useState<Set<string>>(new Set());

    const handleDeployAgent = async (worker: any) => {
        const workerId = worker.id || worker.name;
        const token = await getAuthToken();
        if (!token) return;

        setDeployingIds(prev => new Set(prev).add(workerId));
        setActionLogs(prev => [`[DEPLOY] Initializing Neural Instance: ${worker.name}`, ...prev]);
        
        const promise = withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/crew/run`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    crew_type: worker.category === "Content" ? "content" : "affiliate",
                    topic: selectedNiche || worker.name,
                    worker_id: worker.id
                })
            }),
            {
                fallback: { status: "success", job_id: `LOCAL_${Date.now()}` },
                onSuccess: (data: any) => {
                    setActionLogs(prev => [`[SUCCESS] Neural Stream Established: ${worker.name} (Job: ${data.job_id || 'OK'})`, ...prev]);
                    setTimeout(() => setDeployingIds(prev => {
                        const next = new Set(prev);
                        next.delete(workerId);
                        return next;
                    }), 2000);
                },
                onFallback: (err) => {
                    setActionLogs(prev => [`[ERROR] ${worker.name}: ${err.message}`, ...prev]);
                    setDeployingIds(prev => {
                        const next = new Set(prev);
                        next.delete(workerId);
                        return next;
                    });
                }
            }
        );

        toast.promise(promise, {
            loading: `Deploying ${worker.name} Cluster...`,
            success: `${worker.name} Deployment Verified`,
            error: (err) => `Deployment Failed: ${err.message || 'Access Denied'}`
        });
    };

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        if (activeEngine === "identities") fetchPersonas();
    }, [activeEngine, fetchPersonas]);

    // Handle real-time job updates from telemetry
    useEffect(() => {
        if (lastJobUpdate) {
            // Unwrap data if it exists (WS message format: {type: "...", data: {...}})
            const update = lastJobUpdate.data || lastJobUpdate;
            
            if (update && update.id) {
                setNexusJobs(prev => {
                    const index = prev.findIndex(j => j.id === update.id);
                    if (index !== -1) {
                        const next = [...prev];
                        next[index] = { 
                            ...next[index], 
                            ...update,
                            status: update.status || next[index].status
                        };
                        return next;
                    }
                    
                    // If it's a new job (likely from a recent deployment), notify the user
                    toast.success(`New Agent Deployment Active: ${update.id.slice(0, 8)}`);
                    return [update as any, ...prev];
                });

                if (update.status === "COMPLETED") {
                    setActionLogs(prev => [`[PIPELINE] Job ${update.id} Success`, ...prev]);
                    toast.success(`Agent Deployment Completed: ${update.id.slice(0, 8)}`);
                } else if (update.status === "FAILED") {
                    setActionLogs(prev => [`[ERROR] Job ${update.id} Failed`, ...prev]);
                    toast.error(`Agent Deployment Failed: ${update.id.slice(0, 8)}`);
                }
            }
        }
    }, [lastJobUpdate]);

    // Derived active job for orchestrator visualization
    const activePipelineJob = useMemo(() => {
        return nexusJobs.find(j => j.status === "Active" || j.status === "Processing") || nexusJobs[0];
    }, [nexusJobs]);

    const filteredCapabilities = useMemo(() => {
        return capabilities.filter(worker => {
            const matchesSearch = worker.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                                 worker.description.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesCategory = activeCategory === "All" || worker.category === activeCategory;
            return matchesSearch && matchesCategory;
        });
    }, [capabilities, searchTerm, activeCategory]);

    const availableCategories = useMemo(() => {
        const cats = new Set(capabilities.map(c => c.category));
        return ["All", ...Array.from(cats)].sort();
    }, [capabilities]);

    // Unified logs pattern
    const displayLogs = useMemo(() => {
        const logs = Array.isArray(systemLogs) ? systemLogs : [];
        const merged = [
            ...(actionLogs || []).map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "NEXUS",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...logs
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
                        { id: "crews", label: "Workforce", icon: Users },
                        { id: "identities", label: "Neural IDs", icon: Fingerprint },
                        { id: "sandbox", label: "Code Sandbox", icon: Terminal },
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
                    <div className="p-4 rounded-2xl border border-white/5 bg-[#0F0F11]/60 space-y-2 mb-4">
                        <div className="flex items-center justify-between">
                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Node_ID</span>
                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                        </div>
                        <h4 className="text-xs font-mono font-bold text-white uppercase tracking-tight">{pulse?.cluster_node || "NODE-LOCAL-01"}</h4>
                    </div>
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
                                    {/* Neural Target Selector - Top-Notch Custom UI */}
                                    <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Neural Target</label>
                                        <div className="relative">
                                            <select 
                                                value={selectedNiche}
                                                onChange={(e) => setSelectedNiche(e.target.value)}
                                                className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none appearance-none cursor-pointer hover:bg-white/10 transition-colors"
                                            >
                                                {niches.length === 0 && <option value="">Loading Targets...</option>}
                                                {niches?.map((n) => (
                                                    <option key={typeof n === 'string' ? n : n.niche} value={typeof n === 'string' ? n : n.niche} className="bg-[#0F0F11] text-white">
                                                        {typeof n === 'string' ? n : n.niche}
                                                    </option>
                                                ))}
                                            </select>
                                            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                                                <ChevronDown className="w-4 h-4" />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Active Architecture Selector - Top-Notch Custom UI */}
                                    <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Active Architecture</label>
                                        <div className="relative">
                                            <select 
                                                value={activeBlueprint?.id}
                                                onChange={(e) => setActiveBlueprint(blueprints.find(b => b.id === e.target.value) || null)}
                                                className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none appearance-none cursor-pointer hover:bg-white/10 transition-colors"
                                            >
                                                {blueprints?.map((b) => (
                                                    <option key={b.id} value={b.id} className="bg-[#0F0F11] text-white">
                                                        {b.name}
                                                    </option>
                                                ))}
                                            </select>
                                            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                                                <ChevronDown className="w-4 h-4" />
                                            </div>
                                        </div>
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

                                <div className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">
                                    <div className="absolute inset-0 architect-grid pointer-events-none opacity-40" />
                                    
                                    {/* Connection Mesh Overlay - True DAG Bezier Paths */}
                                    <div className="absolute inset-0 z-0 pointer-events-none">
                                        <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                                            <defs>
                                                <linearGradient id="glowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.6" />
                                                    <stop offset="50%" stopColor="#22d3ee" stopOpacity="1" />
                                                    <stop offset="100%" stopColor="#10b981" stopOpacity="0.6" />
                                                </linearGradient>
                                                <filter id="glowFilter" x="-10%" y="-10%" width="120%" height="120%">
                                                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                                                    <feMerge>
                                                        <feMergeNode in="blur" />
                                                        <feMergeNode in="SourceGraphic" />
                                                    </feMerge>
                                                </filter>
                                            </defs>
                                            
                                            {/* Generate connections based on parallel branch coordinates */}
                                            {activeBlueprint?.nodes?.map((node, idx) => {
                                                if (idx === 0) return null;
                                                const listLength = activeBlueprint?.nodes?.length || 0;
                                                
                                                // Dynamic Coordinates logic
                                                const getCoords = (i: number) => {
                                                    let x = 15 + (i / Math.max(listLength - 1, 1)) * 70;
                                                    let y = 50;
                                                    if (listLength >= 4) {
                                                        if (i === 0) { x = 15; y = 50; }
                                                        else if (i === 1) { x = 45; y = 25; } // Branch 1: Script Cognition
                                                        else if (i === 2) { x = 45; y = 75; } // Branch 2: Asset Discovery
                                                        else if (i === 3) { x = 75; y = 50; } // Merge: Synthesis
                                                        else if (i >= 4) { x = 90; y = 50; }
                                                    }
                                                    return { x, y };
                                                };
                                                
                                                let parentIndices = [idx - 1];
                                                if (listLength >= 4) {
                                                    if (idx === 1) parentIndices = [0];
                                                    if (idx === 2) parentIndices = [0];
                                                    if (idx === 3) parentIndices = [1, 2]; // Merge node
                                                    if (idx === 4) parentIndices = [3];
                                                }
                                                
                                                return parentIndices.map((parentIdx, pI) => {
                                                    const start = getCoords(parentIdx);
                                                    const end = getCoords(idx);
                                                    
                                                    const isPathActive = activePipelineJob?.status === "Active" && 
                                                                         (selectedNodeIndex === idx || selectedNodeIndex === parentIdx);
                                                    
                                                    // Beautiful Bezier path representing parallel pipelines
                                                    const pathD = `M ${start.x} ${start.y} C ${(start.x + end.x)/2} ${start.y}, ${(start.x + end.x)/2} ${end.y}, ${end.x} ${end.y}`;
                                                    
                                                    return (
                                                        <g key={`${parentIdx}-${idx}-${pI}`}>
                                                            <path 
                                                                d={pathD} 
                                                                stroke="rgba(255,255,255,0.03)" 
                                                                strokeWidth="2.5" 
                                                                fill="none" 
                                                            />
                                                            <path 
                                                                d={pathD} 
                                                                stroke="url(#glowGrad)" 
                                                                strokeWidth={isPathActive ? "2.5" : "1"} 
                                                                fill="none"
                                                                filter="url(#glowFilter)"
                                                                className={cn(
                                                                    "opacity-40 transition-all duration-500",
                                                                    isPathActive ? "opacity-100" : "opacity-20"
                                                                )}
                                                                strokeDasharray={isPathActive ? "4, 4" : undefined}
                                                            />
                                                        </g>
                                                    );
                                                });
                                            })}
                                        </svg>
                                    </div>

                                    {/* Position Nodes based on branch coordinates */}
                                    <div className="absolute inset-0 z-10">
                                        {activeBlueprint?.nodes?.map((node, idx) => {
                                            const isProcessing = activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                                            const isComplete = activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                                            const listLength = activeBlueprint?.nodes?.length || 0;
                                            
                                            let x = 15 + (idx / Math.max(listLength - 1, 1)) * 70;
                                            let y = 50;
                                            if (listLength >= 4) {
                                                if (idx === 0) { x = 15; y = 50; }
                                                else if (idx === 1) { x = 45; y = 25; }
                                                else if (idx === 2) { x = 45; y = 75; }
                                                else if (idx === 3) { x = 75; y = 50; }
                                                else if (idx >= 4) { x = 90; y = 50; }
                                            }
                                            
                                            return (
                                                <div 
                                                    key={idx} 
                                                    className="absolute"
                                                    style={{ 
                                                        left: `${x}%`, 
                                                        top: `${y}%`, 
                                                        transform: 'translate(-50%, -50%)' 
                                                    }}
                                                >
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

                        {activeEngine === "crews" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Workforce Orchestrator</h3>
                                    <div className="flex gap-4">
                                        <div className="px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold uppercase tracking-widest">
                                            {capabilities.length} Available Skills
                                        </div>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 min-h-0">
                                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col overflow-hidden">
                                    <div className="space-y-6">
                                        <div className="flex items-center justify-between">
                                            <h4 className="text-sm font-bold text-white uppercase tracking-widest">Specialized Agents</h4>
                                            <Bot className="h-4 w-4 text-cyan-400" />
                                        </div>
                                        
                                        <div className="flex flex-col gap-4">
                                            <div className="relative">
                                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-500" />
                                                <input 
                                                    type="text" 
                                                    placeholder="Search skills..." 
                                                    value={searchTerm}
                                                    onChange={(e) => setSearchTerm(e.target.value)}
                                                    className="w-full bg-white/5 border border-white/5 rounded-xl pl-10 pr-4 py-2 text-[10px] text-white focus:outline-none focus:border-cyan-500/30 transition-all"
                                                />
                                            </div>
                                            
                                            <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
                                                {availableCategories.map(cat => (
                                                    <button
                                                        key={cat}
                                                        onClick={() => setActiveCategory(cat)}
                                                        className={cn(
                                                            "px-3 py-1.5 rounded-lg text-[8px] font-bold uppercase tracking-widest whitespace-nowrap transition-all",
                                                            activeCategory === cat ? "bg-cyan-500 text-black" : "bg-white/5 text-zinc-500 hover:text-zinc-300"
                                                        )}
                                                    >
                                                        {cat}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-4 overflow-y-auto custom-scrollbar pr-2 flex-1">
                                        {filteredCapabilities.map((worker, i) => {
                                            const isDeploying = deployingIds.has(worker.id || worker.name);
                                            return (
                                                <div key={i} className={cn(
                                                    "p-6 bg-white/5 border border-white/5 rounded-2xl group transition-all flex items-center justify-between gap-4",
                                                    isDeploying ? "border-cyan-500/50 bg-cyan-500/5 shadow-[0_0_20px_rgba(34,211,238,0.1)]" : "hover:border-cyan-500/30"
                                                )}>
                                                    <div className="space-y-1 flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <h5 className="text-sm font-bold text-white uppercase tracking-tight">{worker.name}</h5>
                                                            <span className={cn(
                                                                "text-[7px] px-1.5 py-0.5 rounded-sm border uppercase font-bold",
                                                                isDeploying ? "bg-amber-500/10 text-amber-500 border-amber-500/20 animate-pulse" : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                                                            )}>
                                                                {isDeploying ? "DEPLOYING..." : worker.category}
                                                            </span>
                                                        </div>
                                                        <p className="text-[10px] text-zinc-500 line-clamp-2">{worker.description}</p>
                                                        <p className="text-[8px] text-zinc-600 font-mono uppercase tracking-tighter pt-1">{worker.stability} Stability</p>
                                                    </div>
                                                    <div className="flex flex-col items-end gap-3">
                                                        <span className="text-[10px] text-zinc-600 font-mono">CR: {worker.credits_per_task}</span>
                                                        <Button 
                                                            onClick={() => handleDeployAgent(worker)} 
                                                            disabled={isDeploying}
                                                            variant="ghost" 
                                                            size="sm" 
                                                            className={cn(
                                                                "h-8 text-[10px] font-bold border border-white/5",
                                                                isDeploying ? "text-amber-500 bg-amber-500/5" : "text-cyan-400 hover:bg-cyan-500/10"
                                                            )}
                                                        >
                                                            {isDeploying ? <Loader2 className="h-3 w-3 animate-spin" /> : "Deploy"}
                                                        </Button>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        {filteredCapabilities.length === 0 && (
                                            <div className="py-20 text-center space-y-4 opacity-20">
                                                <Users className="h-12 w-12 mx-auto" />
                                                <p className="text-xs font-bold uppercase tracking-widest">No Agents Match Filters</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                    <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col items-center justify-center space-y-8 text-center relative overflow-hidden">
                                        <div className="absolute inset-0 bg-linear-to-b from-cyan-500/5 to-transparent pointer-events-none" />
                                        <Network className="h-20 w-20 text-cyan-500/20 animate-pulse" />
                                        <div className="space-y-4 z-10">
                                            <h4 className="text-xl font-bold text-white uppercase tracking-tighter">Neural Workforce Mesh</h4>
                                            <p className="text-xs text-zinc-500 max-w-[280px] leading-relaxed mx-auto">
                                                Orchestrate multiple specialized agents into a unified autonomous crew. 
                                                The mesh is currently operating at {pulse?.load_avg ? Math.round(pulse.load_avg * 100) : 12}% global capacity.
                                            </p>
                                        </div>
                                        <Button className="h-14 px-10 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-2xl uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(8,145,178,0.3)] transition-all hover:scale-105">Initialize New Crew</Button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "sandbox" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-6">
                                        <div className="flex items-center gap-2">
                                            <Terminal className="h-4 w-4 text-cyan-400" />
                                            <h3 className="text-xs font-bold text-white uppercase tracking-widest">Neural Code Sandbox</h3>
                                        </div>
                                        <div className="flex items-center bg-white/5 rounded-lg p-0.5 border border-white/5">
                                            <button 
                                                onClick={() => setSandboxTab('console')}
                                                className={cn(
                                                    "px-3 py-1 text-[9px] uppercase font-bold rounded-md transition-all",
                                                    sandboxTab === 'console' ? "bg-cyan-500 text-black" : "text-zinc-400 hover:text-zinc-200"
                                                )}
                                            >
                                                Console
                                            </button>
                                            <button 
                                                onClick={() => setSandboxTab('telemetry')}
                                                className={cn(
                                                    "px-3 py-1 text-[9px] uppercase font-bold rounded-md transition-all",
                                                    sandboxTab === 'telemetry' ? "bg-cyan-500 text-black" : "text-zinc-400 hover:text-zinc-200"
                                                )}
                                            >
                                                Live Telemetry
                                            </button>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <Button 
                                            size="sm" 
                                            className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold px-4 h-8 text-[10px] uppercase"
                                            onClick={async () => {
                                                const token = await getAuthToken();
                                                if (!token) return;
                                                toast.info("Dispatching code to sandbox...");
                                                await withRealFallback(
                                                    () => fetch(`${API_BASE}/agent/sandbox-execute`, {
                                                        method: "POST",
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            Authorization: `Bearer ${token}`
                                                        },
                                                        body: JSON.stringify({ code: "// Nexus Sandbox Logic" })
                                                    }),
                                                    {
                                                        fallback: null,
                                                        onSuccess: (data: any) => {
                                                            toast.success("Execution Complete");
                                                            if (data.logs) {
                                                                setActionLogs(prev => [...data.logs, ...prev]);
                                                            }
                                                        }
                                                    }
                                                );
                                            }}
                                        >
                                            Execute_Node
                                        </Button>
                                    </div>
                                </div>
                                
                                {sandboxTab === 'console' ? (
                                    <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 min-h-0">
                                        <div className="border-r border-white/5 flex flex-col min-h-0">
                                            <div className="p-4 border-b border-white/5 bg-white/5">
                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Script</span>
                                            </div>
                                            <div className="flex-1 p-8 font-mono text-sm text-cyan-400/80 overflow-y-auto custom-scrollbar">
                                                <pre>
{`// Initialize Intelligence Bridge
const nexus = await Nexus.connect();

// Spawn autonomous scout
const scout = await nexus.spawnAgent("SCOUT_01", {
    role: "Discovery",
    niche: "${selectedNiche || 'Global'}",
    behavior: "Aggressive"
});

// Await viral triggers
scout.on("VIRAL_DETECT", async (data) => {
    console.log("[NEXUS] Outbreak detected:", data.id);
    await nexus.dispatchPipeline("AUTO_SYNTH_V1", data);
});`}
                                                </pre>
                                            </div>
                                        </div>
                                        <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-r-[32px] border-l border-white/5 overflow-hidden">
                                            <div className="p-4 border-b border-white/5 bg-white/5">
                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Execution Output</span>
                                            </div>
                                            <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[10px] space-y-2">
                                                {actionLogs.map((log, i) => (
                                                    <p key={i} className={cn(
                                                        log.includes("[SUCCESS]") ? "text-emerald-500" :
                                                        log.includes("[EXEC]") ? "text-cyan-400" :
                                                        log.includes("[SYSTEM]") ? "text-zinc-600" : "text-zinc-400"
                                                    )}>{log}</p>
                                                ))}
                                                <div className="animate-pulse flex gap-2">
                                                    <span className="text-white">_</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar">
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                            <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Global Latency (ms)</span>
                                                <div className="h-48 relative">
                                                    <AreaChartCustom data={latencyData} dataKey="value" color="#8b5cf6" height={190} />
                                                </div>
                                            </div>
                                            <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Celery Cluster Load (%)</span>
                                                <div className="h-48 relative">
                                                    <AreaChartCustom data={workerLoadData} dataKey="value" color="#22d3ee" height={190} />
                                                </div>
                                            </div>
                                            <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Self-Healing Triggers</span>
                                                <div className="h-48 relative">
                                                    <AreaChartCustom data={healingData} dataKey="value" color="#10b981" height={190} />
                                                </div>
                                            </div>
                                        </div>
                                        <div className="p-6 rounded-2xl bg-white/2 border border-white/5 flex items-center justify-between">
                                            <div className="space-y-1">
                                                <span className="text-[9px] font-black text-cyan-400 uppercase tracking-widest">Cluster Health Ledger</span>
                                                <p className="text-xs text-zinc-400">All core micro-services operating nominally. Autonomic recovery scripts operational.</p>
                                            </div>
                                            <span className="text-[10px] px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 font-bold uppercase">100% HEALTH</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "history" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar p-1">
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
                                        onRefresh={() => handlePreviewScenes(job.id)}
                                        onDelete={() => {
                                            toast.promise(fetch(`${API_BASE}/nexus/jobs/${job.id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${getAuthToken()}` } }), {
                                                loading: 'Purging pipeline...',
                                                success: 'Pipeline purged',
                                                error: 'Deletion restricted'
                                            });
                                        }}
                                    />
                                ))}
                            </div>
                        )}

                        {activeEngine === "command" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar pr-4">
                                <CommandPod 
                                    name="Nexus Master Core" 
                                    status={status === "open" ? "nominal" : "offline"} 
                                    load={pulse?.load_avg ? Math.round(pulse.load_avg * 100) : 15} 
                                    circuitBreaker="closed" 
                                    description="Primary orchestration layer for global Nexus Workforce. Synchronizing 14 neural channels."
                                />
                                <CommandPod 
                                    name="Neural ID Gateway" 
                                    status="nominal" 
                                    load={personas.length > 0 ? 8 : 2} 
                                    circuitBreaker="closed" 
                                    description="High-throughput ingress for autonomous identity verification and persona mapping."
                                />
                                <CommandPod 
                                    name="Pipeline Dispatcher" 
                                    status={isLaunching ? "nominal" : "nominal"} 
                                    load={nexusJobs.filter(j => j.status === 'processing').length * 20} 
                                    circuitBreaker="closed" 
                                    description="Real-time job scheduling and blueprint execution engine."
                                />
                                <div className="col-span-full p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex items-center justify-between">
                                    <div className="flex flex-col gap-2">
                                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Master Override</span>
                                        <h4 className="text-lg font-bold text-white uppercase tracking-tight">Emergency System Halt</h4>
                                    </div>
                                    <Button variant="outline" className="h-14 px-10 border-rose-500/20 text-rose-500 hover:bg-rose-500 hover:text-white font-bold uppercase tracking-widest text-[10px]">Execute Halt_0</Button>
                                </div>
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
            
            {/* Preview Scenes Modal */}
            <AnimatePresence>
                {isPreviewModalOpen && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-6 sm:p-10"
                        onClick={() => setIsPreviewModalOpen(false)}
                    >
                        <motion.div 
                            initial={{ scale: 0.95, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.95, y: 20 }}
                            className="w-full max-w-6xl bg-[#070709] border border-white/10 rounded-[36px] p-8 shadow-2xl max-h-[92vh] overflow-y-auto custom-scrollbar"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                                <div className="flex items-center gap-4">
                                    <div className="h-14 w-14 bg-violet-500/10 border border-violet-500/20 rounded-2xl flex items-center justify-center">
                                        <Layers className="h-7 w-7 text-violet-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Nexus Video Synthesizer</h3>
                                        <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Orchestrated Job: {previewJobId}</p>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => setIsPreviewModalOpen(false)}
                                    className="h-11 w-11 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl flex items-center justify-center transition-colors"
                                >
                                    <X className="h-5 w-5 text-zinc-400" />
                                </button>
                            </div>
                            
                            {isLoadingPreview ? (
                                <div className="flex items-center justify-center py-32">
                                    <Loader2 className="h-12 w-12 animate-spin text-violet-400" />
                                </div>
                            ) : previewScenes.length === 0 ? (
                                <div className="text-center py-32 space-y-4">
                                    <AlertCircle className="h-14 w-14 text-zinc-700 mx-auto" />
                                    <p className="text-sm font-bold uppercase tracking-widest text-zinc-500">No scene data available for this pipeline.</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                    
                                    {/* Left Column: Scene List & Timelines */}
                                    <div className="lg:col-span-2 space-y-6 overflow-y-auto max-h-[60vh] pr-2 custom-scrollbar">
                                        {previewScenes.map((scene, index) => {
                                            const activeAsset = swappedAssets[index] || (scene.assets && scene.assets[0]) || null;
                                            const isDrawerOpen = activeSwapDrawerIndex === index;
                                            
                                            // Mock timing tracks aligned to the scene's duration
                                            const duration = scene.duration || 5;
                                            const simulatedWords = [
                                                { word: "AI", start: 0, end: 0.8 },
                                                { word: "Engine", start: 0.8, end: 1.6 },
                                                { word: "Orchestrated", start: 1.6, end: 2.6 },
                                                { word: "this", start: 2.6, end: 3.2 },
                                                { word: "scene", start: 3.2, end: 4.0 },
                                                { word: "perfectly.", start: 4.0, end: duration }
                                            ];

                                            return (
                                                <div key={index} className="p-6 bg-[#0F0F12]/80 border border-white/5 rounded-[28px] hover:border-violet-500/20 transition-all space-y-6 relative overflow-hidden group">
                                                    
                                                    {/* Top Bar */}
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <span className="h-9 w-9 bg-violet-500/10 border border-violet-500/20 rounded-xl flex items-center justify-center text-violet-400 font-bold text-sm">
                                                                {index + 1}
                                                            </span>
                                                            <span className={cn(
                                                                "px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border",
                                                                scene.type === 'hook' ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
                                                                scene.type === 'problem' ? "bg-rose-500/10 text-rose-500 border-rose-500/20" :
                                                                scene.type === 'solution' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
                                                                scene.type === 'outro' ? "bg-cyan-500/10 text-cyan-500 border-cyan-500/20" :
                                                                "bg-zinc-500/10 text-zinc-500 border-white/5"
                                                            )}>
                                                                {scene.type || 'Scene'}
                                                            </span>
                                                        </div>
                                                        <span className="text-xs font-black text-zinc-500 font-mono">{duration}s</span>
                                                    </div>
                                                    
                                                    {/* Text content */}
                                                    <div className="space-y-4">
                                                        <div>
                                                            <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest block mb-1">Visual Direction / Prompt</span>
                                                            <p className="text-xs text-zinc-300 font-semibold leading-relaxed">
                                                                {scene.description || scene.visual_prompt || "No instructions provided."}
                                                            </p>
                                                        </div>

                                                        {/* Timing track visualizer */}
                                                        <div className="p-4 bg-black/40 border border-white/5 rounded-2xl space-y-4">
                                                            
                                                            {/* Words Timeline */}
                                                            <div className="space-y-2">
                                                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest block">Subtitle Word Timeline</span>
                                                                <div className="flex flex-wrap gap-2 pt-1">
                                                                    {simulatedWords.map((item, idx) => (
                                                                        <div 
                                                                            key={idx}
                                                                            className="px-2 py-1 bg-white/5 rounded-lg border border-white/5 flex flex-col items-center justify-center shrink-0 min-w-[50px] animate-pulse"
                                                                            style={{ animationDelay: `${idx * 0.3}s` }}
                                                                        >
                                                                            <span className="text-[10px] text-white font-bold">{item.word}</span>
                                                                            <span className="text-[6px] text-zinc-500 font-mono">{item.start}s - {item.end}s</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* Audio waveforms timeline */}
                                                            <div className="space-y-3 pt-2 border-t border-white/5">
                                                                <div className="flex items-center justify-between text-[7px] text-zinc-600 uppercase font-black tracking-widest">
                                                                    <span>0.0s</span>
                                                                    <span>Audio Composition Track</span>
                                                                    <span>{duration}s</span>
                                                                </div>
                                                                
                                                                {/* Voiceover Track */}
                                                                <div className="space-y-1">
                                                                    <div className="flex items-center justify-between text-[7px] text-zinc-500">
                                                                        <span className="flex items-center gap-1"><Mic2 className="h-2 w-2" /> AI VOICEOVER</span>
                                                                        <span className="font-mono">Volume: 100%</span>
                                                                    </div>
                                                                    <div className="h-6 w-full bg-violet-950/20 border border-violet-500/10 rounded-lg relative overflow-hidden flex items-center justify-around px-2">
                                                                        {[4, 8, 2, 7, 5, 9, 3, 6, 8, 4, 9, 2, 7, 5, 8, 3, 6, 4, 7, 5].map((h, i) => (
                                                                            <div key={i} className="w-0.5 bg-violet-400 rounded-full" style={{ height: `${h * 10}%` }} />
                                                                        ))}
                                                                    </div>
                                                                </div>

                                                                {/* Background music track */}
                                                                <div className="space-y-1">
                                                                    <div className="flex items-center justify-between text-[7px] text-zinc-500">
                                                                        <span className="flex items-center gap-1"><Volume2 className="h-2 w-2" /> BACKGROUND MUSIC</span>
                                                                        <span className="font-mono">Volume: 12%</span>
                                                                    </div>
                                                                    <div className="h-4 w-full bg-cyan-950/20 border border-cyan-500/10 rounded-lg relative overflow-hidden flex items-center justify-around px-2">
                                                                        {[2, 3, 2, 4, 3, 2, 3, 4, 3, 2, 3, 4, 3, 2, 3, 4, 3, 2, 3, 2].map((h, i) => (
                                                                            <div key={i} className="w-0.5 bg-cyan-500/50 rounded-full" style={{ height: `${h * 10}%` }} />
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Assets section with optimize/swap triggers */}
                                                        <div className="space-y-3">
                                                            <div className="flex items-center justify-between">
                                                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Active Stock Video Segment</span>
                                                                <button
                                                                    onClick={() => setActiveSwapDrawerIndex(isDrawerOpen ? null : index)}
                                                                    className="px-3 py-1.5 rounded-lg border border-cyan-500/20 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-[8px] font-bold uppercase transition-all flex items-center gap-1.5"
                                                                >
                                                                    <Scissors className="h-2.5 w-2.5" /> Swap Asset
                                                                </button>
                                                            </div>
                                                            
                                                            <div className="flex gap-4 items-center">
                                                                <div className="shrink-0 h-20 w-32 bg-zinc-900 rounded-xl border border-white/5 overflow-hidden relative shadow-inner">
                                                                    {activeAsset && activeAsset.thumbnail ? (
                                                                        <img src={activeAsset.thumbnail} alt="" className="w-full h-full object-cover" />
                                                                    ) : (
                                                                        <div className="w-full h-full flex items-center justify-center text-zinc-700">
                                                                            <Video className="h-6 w-6" />
                                                                        </div>
                                                                    )}
                                                                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                                                                        <Play className="h-5 w-5 text-white filter drop-shadow-[0_0_10px_rgba(255,255,255,0.4)]" />
                                                                    </div>
                                                                </div>
                                                                <div className="space-y-1">
                                                                    <p className="text-[11px] font-bold text-white uppercase">{activeAsset?.title || `Stock_Footage_${index + 1}.mp4`}</p>
                                                                    <div className="flex flex-wrap gap-1">
                                                                        {(activeAsset?.tags || ["workspace", "technology", "abstract"]).slice(0, 3).map((tag: string, tIdx: number) => (
                                                                            <span key={tIdx} className="text-[7px] text-zinc-500 bg-white/5 px-1.5 py-0.5 rounded-sm uppercase font-mono">{tag}</span>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Asset replacement drawer */}
                                                            <AnimatePresence>
                                                                {isDrawerOpen && (
                                                                    <motion.div 
                                                                        initial={{ opacity: 0, height: 0 }}
                                                                        animate={{ opacity: 1, height: "auto" }}
                                                                        exit={{ opacity: 0, height: 0 }}
                                                                        className="overflow-hidden border-t border-white/5 pt-4 space-y-3"
                                                                    >
                                                                        <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Select Alternative Curation Candidate</span>
                                                                        <div className="grid grid-cols-3 gap-3">
                                                                            {[
                                                                                { title: "Digital Flow", thumbnail: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=150&auto=format&fit=crop&q=60", tags: ["cyber", "abstract"] },
                                                                                { title: "Team Work", thumbnail: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=150&auto=format&fit=crop&q=60", tags: ["corporate", "collaboration"] },
                                                                                { title: "Minimal Server", thumbnail: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=150&auto=format&fit=crop&q=60", tags: ["server", "database"] },
                                                                            ].map((alt, altIdx) => (
                                                                                <div 
                                                                                    key={altIdx}
                                                                                    onClick={() => {
                                                                                        setSwappedAssets(prev => ({
                                                                                            ...prev,
                                                                                            [index]: alt
                                                                                        }));
                                                                                        setActiveSwapDrawerIndex(null);
                                                                                        toast.success("Asset replaced visually", { description: "Timeline update will be committed on compile." });
                                                                                    }}
                                                                                    className="p-2 rounded-xl bg-white/2 border border-white/5 hover:border-cyan-500/40 cursor-pointer transition-all flex flex-col gap-2 group/alt"
                                                                                >
                                                                                    <div className="aspect-video w-full rounded-lg bg-zinc-950 overflow-hidden relative">
                                                                                        <img src={alt.thumbnail} alt="" className="w-full h-full object-cover group-hover/alt:scale-105 transition-transform" />
                                                                                    </div>
                                                                                    <span className="text-[8px] font-bold text-white uppercase truncate">{alt.title}</span>
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    
                                    {/* Right Column: Style Archetype & Modulator Canvas */}
                                    <div className="space-y-6 bg-white/2 border border-white/5 rounded-[28px] p-6 h-fit lg:sticky lg:top-0">
                                        <div className="flex items-center gap-2 pb-4 border-b border-white/5">
                                            <Palette className="h-4 w-4 text-cyan-400" />
                                            <span className="text-[10px] font-bold text-white uppercase tracking-widest">Neural Style Modulator</span>
                                        </div>
                                        
                                        {/* Presets Grid */}
                                        <div className="space-y-3">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Style Archetype Presets</span>
                                            <div className="grid grid-cols-2 gap-3">
                                                {[
                                                    { id: "NEON_CYBER", name: "Neon Cyber", style: "from-cyan-500 via-indigo-500 to-purple-600" },
                                                    { id: "AMBER_WARM", name: "Amber Warm", style: "from-amber-500 via-orange-500 to-red-600" },
                                                    { id: "MONOCHROME_DARK", name: "Mono Dark", style: "from-neutral-800 to-zinc-950" },
                                                    { id: "EMERALD_MATRIX", name: "Matrix Green", style: "from-emerald-600 via-teal-800 to-emerald-950" }
                                                ].map((preset) => (
                                                    <div 
                                                        key={preset.id}
                                                        onClick={() => setSelectedStylePreset(preset.id as any)}
                                                        className={cn(
                                                            "p-3 rounded-xl border cursor-pointer transition-all flex flex-col gap-2",
                                                            selectedStylePreset === preset.id ? "bg-white/5 border-cyan-500" : "bg-transparent border-white/5 hover:border-white/10"
                                                        )}
                                                    >
                                                        <div className={cn("h-4 w-full rounded-md bg-gradient-to-r", preset.style)} />
                                                        <span className="text-[8px] font-bold text-white uppercase">{preset.name}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Modulator Sliders */}
                                        <div className="space-y-4 pt-2">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Modulation Sliders</span>
                                            
                                            {/* Temperature */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>COLOR TEMPERATURE</span>
                                                    <span>{colorTemp}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={colorTemp} 
                                                    onChange={e => setColorTemp(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>

                                            {/* VFX Grain */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>VFX GRAIN DENSITY</span>
                                                    <span>{grainDensity}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={grainDensity} 
                                                    onChange={e => setGrainDensity(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>

                                            {/* Contrast */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>SATURATION / CONTRAST</span>
                                                    <span>{contrast}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={contrast} 
                                                    onChange={e => setContrast(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>

                                            {/* Ken Burns */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>KEN BURNS PANNING</span>
                                                    <span>{kenBurnsSpeed}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={kenBurnsSpeed} 
                                                    onChange={e => setKenBurnsSpeed(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>
                                        </div>

                                        {/* Mock Video Canvas Preview */}
                                        <div className="pt-4 border-t border-white/5 space-y-3">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Live Visual Frame Modulator</span>
                                            <div className="aspect-[9/16] w-full bg-zinc-950 border border-white/5 rounded-2xl relative overflow-hidden flex items-center justify-center">
                                                
                                                {/* Simulated image representing stock backgrounds */}
                                                <div 
                                                    className="absolute inset-0 transition-transform duration-1000 bg-cover bg-center"
                                                    style={{ 
                                                        backgroundImage: "url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=80')",
                                                        transform: `scale(${1 + (kenBurnsSpeed * 0.005)})`,
                                                        filter: `
                                                            contrast(${1 + (contrast - 50) * 0.01}) 
                                                            sepia(${(selectedStylePreset === 'AMBER_WARM' ? 50 : 0) + colorTemp * 0.2}%) 
                                                            hue-rotate(${selectedStylePreset === 'NEON_CYBER' ? 240 : selectedStylePreset === 'EMERALD_MATRIX' ? 100 : 0}deg)
                                                            grayscale(${selectedStylePreset === 'MONOCHROME_DARK' ? 100 : 0}%)
                                                        `
                                                    }}
                                                />
                                                
                                                {/* Simulated Film grain overlay */}
                                                <div 
                                                    className="absolute inset-0 bg-[#888] pointer-events-none mix-blend-overlay opacity-10"
                                                    style={{
                                                        backgroundImage: "radial-gradient(circle, #fff 10%, transparent 11%)",
                                                        backgroundSize: `${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`,
                                                        opacity: grainDensity * 0.004
                                                    }}
                                                />

                                                {/* Words caption overlay */}
                                                <div className="absolute inset-x-4 bottom-12 text-center z-10 px-2 pointer-events-none">
                                                    <span 
                                                        className="px-4 py-2 bg-yellow-400 text-black text-[13px] font-black uppercase rounded-lg shadow-2xl inline-block leading-tight filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)] border border-black/20"
                                                        style={{ textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}
                                                    >
                                                        DYNAMIC CAPTION
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            )}
                            
                            <div className="mt-8 pt-6 border-t border-white/5 flex justify-end">
                                <Button 
                                    onClick={() => setIsPreviewModalOpen(false)}
                                    className="bg-white/5 hover:bg-white/10 text-white font-bold uppercase tracking-widest text-[10px] border border-white/10 h-12 px-8 rounded-xl"
                                >
                                    Close Preview
                                </Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
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

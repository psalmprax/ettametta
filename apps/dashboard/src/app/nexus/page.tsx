"use client";

import React, { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/layout";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { NexusNode, NodeType } from "@/components/ui/NexusNode";
import { useWebSocket } from "@/hooks/useWebSocket";
import { toast } from "sonner";

interface Blueprint {
    id: string;
    name: string;
    description: string;
    nodes: { type: NodeType; label: string; desc: string }[];
}

export default function NexusPage() {
    const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
    const [activeBlueprint, setActiveBlueprint] = useState<Blueprint | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);
    const [nexusJobs, setNexusJobs] = useState<any[]>([]);
    const [niches, setNiches] = useState<string[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("");
    const [userTier, setUserTier] = useState<string>("free");
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
    const [logStream, setLogStream] = useState<string[]>([]);

    // AI Agent Chat state
    const [chatMessages, setChatMessages] = useState<{ role: "user" | "agent"; content: string }[]>([]);
    const [chatInput, setChatInput] = useState("");
    const [isChatting, setIsChatting] = useState(false);
    const [agentCapabilities, setAgentCapabilities] = useState<string[]>([]);

    const { data: jobUpdate } = useWebSocket<any>(`${WS_BASE}/jobs`);
    const { data: logUpdate } = useWebSocket<any>(`${WS_BASE}/logs`);

    // Persona Lab state
    const [personaName, setPersonaName] = useState("");
    const [personaImageUrl, setPersonaImageUrl] = useState("");
    const [isCreatingPersona, setIsCreatingPersona] = useState(false);
    const [createdPersona, setCreatedPersona] = useState<{ name: string; reference_image_url: string } | null>(null);
    const [videoTopic, setVideoTopic] = useState("");
    const [videoScript, setVideoScript] = useState("");
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [telemetry, setTelemetry] = useState<any>(null);

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

                // Fetch Blueprints
                const bpRes = await fetch(`${API_BASE}/nexus/blueprints`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (bpRes.ok) {
                    const bpData = await bpRes.json();
                    setBlueprints(bpData);
                    if (bpData.length > 0) setActiveBlueprint(bpData[0]);
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

                // Fetch Agent Capabilities
                const capRes = await fetch(`${API_BASE}/agent/capabilities`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (capRes.ok) {
                    const capData = await capRes.json();
                    setAgentCapabilities(capData.capabilities || capData || []);
                }
            } catch (err) {
                console.error("Failed to fetch Nexus data:", err);
                toast.error("Failed to load nexus jobs");
            }
        };

        fetchData();

        // Polling for telemetry
        const fetchTelemetry = async () => {
            const token = localStorage.getItem("et_token");
            if (!token) return;
            try {
                const res = await fetch(`${API_BASE}/nexus/telemetry`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (res.ok) setTelemetry(await res.json());
            } catch (e) { console.error("Telemetry fetch error:", e); }
        };

        fetchTelemetry();
        const interval = setInterval(fetchTelemetry, 10000); // 10s intervals for real-first dashboarding
        return () => clearInterval(interval);
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
            if (activeJobId === String(updatedJob.id) && updatedJob.current_node) {
                 // Auto-select or focus on the current active node
                 const nodeIdx = activeBlueprint?.nodes.findIndex(n => n.type === updatedJob.current_node);
                 if (nodeIdx !== undefined && nodeIdx !== -1) {
                     setSelectedNodeIndex(nodeIdx);
                 }
            }
        }
    }, [jobUpdate, activeJobId, activeBlueprint]);

    // Handle Live Logs
    useEffect(() => {
        if (logUpdate && logUpdate.type === "log" && (logUpdate.module === "NEXUS" || logUpdate.module === "SYSTEM")) {
            const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            setLogStream(prev => [`[${timestamp}] [${logUpdate.level}] ${logUpdate.message}`, ...prev.slice(0, 49)]);
        }
    }, [logUpdate]);

    // Button handlers
    const handleClusterSettings = () => {
        window.location.href = '/settings';
    };

    const handleCustomRecipe = () => {
        window.location.href = '/creation';
    };

    const handleInspectResult = (job: any) => {
        if (job.output_path) {
            window.open(`/api/${job.output_path}`, '_blank');
        } else {
            toast.message("Output Incomplete", {
                description: "The pipeline is still processing this segment.",
                icon: <Loader2 className="h-4 w-4 animate-spin" />
            });
        }
    };

    const handleLaunchPipeline = async () => {
        if (!selectedNiche || !activeBlueprint) return;
        setIsLaunching(true);
        const token = localStorage.getItem("et_token");

        try {
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
                toast.success("Pipeline Dispatched", {
                    description: `Job ID: ${data.job_id} is now active in the neural cluster.`
                });
                setSelectedNodeIndex(0);
            } else {
                const err = await res.json();
                toast.error("Launch Failed", {
                    description: err.detail || "Neural cluster rejected the composition request."
                });
            }
        } catch (err) {
            console.error("Error launching pipeline:", err);
            toast.error("Failed to compose video");
        } finally {
            setIsLaunching(false);
        }
    };

    const handleSendChat = async () => {
        const message = chatInput.trim();
        if (!message || isChatting) return;

        setChatMessages(prev => [...prev, { role: "user", content: message }]);
        setChatInput("");
        setIsChatting(true);

        const token = localStorage.getItem("et_token");
        try {
            const res = await fetch(`${API_BASE}/agent/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ message })
            });

            if (res.ok) {
                const data = await res.json();
                setChatMessages(prev => [...prev, { role: "agent", content: data.response || data.message || JSON.stringify(data) }]);
            } else {
                const err = await res.json();
                toast.error("Agent Error", {
                    description: err.detail || "The AI agent failed to process your request."
                });
            }
        } catch (err) {
            console.error("Chat error:", err);
            toast.error("Failed to reach AI agent");
        } finally {
            setIsChatting(false);
        }
    };

    const handleCreatePersona = async () => {
        if (!personaName || !personaImageUrl) return;
        setIsCreatingPersona(true);
        const token = localStorage.getItem("et_token");

        try {
            const res = await fetch(`${API_BASE}/persona/create`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: personaName,
                    reference_image_url: personaImageUrl
                })
            });

            if (res.ok) {
                const data = await res.json();
                setCreatedPersona({ name: personaName, reference_image_url: personaImageUrl });
                toast.success("Persona Created", {
                    description: `Persona "${personaName}" is ready for video generation.`
                });
            } else {
                const err = await res.json();
                toast.error("Creation Failed", {
                    description: err.detail || "Could not create the persona."
                });
            }
        } catch (err) {
            console.error("Error creating persona:", err);
            toast.error("Failed to create persona");
        } finally {
            setIsCreatingPersona(false);
        }
    };

    const handleGenerateVideo = async () => {
        if (!createdPersona || !videoTopic) return;
        setIsGeneratingVideo(true);
        const token = localStorage.getItem("et_token");

        try {
            const body: Record<string, string> = {
                reference_image_url: createdPersona.reference_image_url,
                topic: videoTopic,
            };
            if (videoScript) body.script = videoScript;

            const res = await fetch(`${API_BASE}/persona/generate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                const data = await res.json();
                toast.success("Video Generated", {
                    description: data.video_url || "Persona video has been generated successfully."
                });
            } else {
                const err = await res.json();
                toast.error("Generation Failed", {
                    description: err.detail || "Could not generate the persona video."
                });
            }
        } catch (err) {
            console.error("Error generating video:", err);
            toast.error("Failed to generate persona video");
        } finally {
            setIsGeneratingVideo(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="max-w-[1600px] mx-auto p-8 space-y-12">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 pt-4">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-12 bg-primary rounded-full" />
                            <span className="text-[10px] font-black tracking-[0.4em] text-primary uppercase italic">Neural Orchestration</span>
                        </div>
                        <h1 className="text-6xl md:text-7xl font-black italic tracking-tighter uppercase text-white leading-none">
                            Nexus <span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-emerald-400 text-hollow">Engine</span>
                        </h1>
                        <p className="text-zinc-500 max-w-xl text-sm font-medium leading-relaxed">
                            Deploy end-to-end autonomous media pipelines. Ettametta's Nexus translates niche signals into cinematic realities through a four-stage neural synthesis.
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex -space-x-3">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-10 w-10 rounded-full border-2 border-black bg-zinc-900 flex items-center justify-center overflow-hidden">
                                    <div className="h-full w-full bg-linear-to-br from-primary/20 to-zinc-900" />
                                </div>
                            ))}
                            <div className="h-10 w-10 rounded-full border-2 border-black bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-white">
                                +{niches.length}
                            </div>
                        </div>
                        <div className="h-12 w-px bg-white/10 mx-2" />
                        <div className="text-right">
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Tier Access</p>
                            <p className="text-white font-black uppercase tracking-tighter italic">{userTier} CLUSTER</p>
                        </div>
                    </div>
                </div>

                {/* Configuration Bar */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-5xl bg-zinc-950/40 border border-white/5 backdrop-blur-3xl shadow-2xl">
                    <div className="flex flex-col gap-2 p-4 rounded-3xl bg-white/3 border border-white/5 group hover:border-primary/20 transition-all">
                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 flex items-center gap-2">
                            <Layers className="h-3 w-3" /> Targeted Niche
                        </label>
                        <select 
                            value={selectedNiche}
                            onChange={(e) => setSelectedNiche(e.target.value)}
                            className="bg-transparent text-white font-black uppercase tracking-tight focus:outline-none cursor-pointer"
                        >
                            {niches.map(n => <option key={n} value={n} className="bg-zinc-900">{n}</option>)}
                        </select>
                    </div>

                    <div className="flex flex-col gap-2 p-4 rounded-3xl bg-white/3 border border-white/5 group hover:border-primary/20 transition-all">
                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 flex items-center gap-2">
                           <Cpu className="h-3 w-3" /> Pipeline Recipe
                        </label>
                        <select 
                           value={activeBlueprint?.id}
                           onChange={(e) => setActiveBlueprint(blueprints.find(b => b.id === e.target.value) || null)}
                           className="bg-transparent text-white font-black uppercase tracking-tight focus:outline-none cursor-pointer"
                        >
                            {blueprints.map(b => (
                                <option key={b.id} value={b.id} className="bg-zinc-900">{b.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex flex-col gap-2 p-4 rounded-3xl bg-white/3 border border-white/5 group hover:border-primary/20 transition-all">
                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 flex items-center gap-2">
                           <Database className="h-3 w-3" /> Storage Node
                        </label>
                        <p className="text-white font-black uppercase tracking-tight">Cloud-S3 Master</p>
                    </div>

                    <button 
                        onClick={handleLaunchPipeline}
                        disabled={isLaunching || !selectedNiche}
                        className={cn(
                        "h-full rounded-3xl bg-primary flex items-center justify-center gap-3 transition-all hover:scale-[1.02] active:scale-95 group relative overflow-hidden",
                        (isLaunching || !selectedNiche) && "opacity-50 cursor-not-allowed"
                    )}>
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                        {isLaunching ? <Loader2 className="h-6 w-6 text-black animate-spin" /> : <Play className="h-6 w-6 text-black" />}
                        <span className="text-black font-black uppercase tracking-widest text-sm relative">Launch Pipeline</span>
                    </button>
                </div>

                {/* Pipeline Mesh Visualization */}
                <div className="grid grid-cols-1 xl:grid-cols-4 gap-12">
                    <div className="xl:col-span-3 space-y-12">
                        <div className="relative aspect-21/9 rounded-6xl bg-zinc-950 border border-white/5 overflow-hidden shadow-inner group">
                            {/* Animated Background Mesh */}
                            <div className="absolute inset-0 opacity-20 pointer-events-none">
                                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,var(--primary)_0%,transparent_100%)] opacity-10 animate-pulse" />
                                <svg className="w-full h-full">
                                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" strokeOpacity="0.05"/>
                                    </pattern>
                                    <rect width="100%" height="100%" fill="url(#grid)" />
                                </svg>
                            </div>

                            {/* Node Connectors */}
                            <div className="absolute inset-0 flex items-center justify-around px-20">
                                <div className="absolute top-1/2 left-0 right-0 h-px bg-linear-to-r from-transparent via-white/10 to-transparent" />
                                
                                {activeBlueprint?.nodes.map((node, idx) => {
                                    const isActive = activeJobId && selectedNodeIndex === idx;
                                    const job = nexusJobs.find(j => String(j.id) === activeJobId);
                                    const nodeStatus = (job?.node_status && job.node_status[node.type]) || 'IDLE';

                                    return (
                                        <div key={idx} className="relative z-10">
                                            <NexusNode 
                                                type={node.type}
                                                label={node.label}
                                                description={node.desc}
                                                status={nodeStatus}
                                                active={selectedNodeIndex === idx}
                                                onClick={() => setSelectedNodeIndex(idx)}
                                            />
                                            {idx < activeBlueprint.nodes.length - 1 && (
                                                <div className="absolute top-1/2 -right-20 translate-x-1/2 -translate-y-1/2">
                                                    <ChevronRight className="h-6 w-6 text-white/10" />
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* HUD Overlays */}
                            <div className="absolute bottom-10 left-10 p-4 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-xl">
                                <div className="flex items-center gap-4">
                                    <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
                                        Stream: <span className="text-white italic">Neural_Cluster_#402</span>
                                    </p>
                                </div>
                            </div>

                            <div className="absolute top-10 right-10 p-4 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-xl group-hover:border-primary/30 transition-all">
                                 <div className="flex items-center gap-4">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Status:</p>
                                    <p className="text-primary font-black uppercase tracking-tight italic">
                                        {telemetry?.status || (activeJobId ? 'OPERATIONAL' : 'IDLE')}
                                    </p>
                                 </div>
                            </div>
                        </div>

                        {/* Node Detail Section */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="glass-card p-10 space-y-6">
                                <div className="flex items-center gap-4">
                                    <div className="h-12 w-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                                        <Settings2 className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-black text-white italic tracking-tighter uppercase">Node Settings</h3>
                                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Configuration Matrix</p>
                                    </div>
                                </div>
                                <div className="space-y-4 pt-4">
                                    <div className="flex items-center justify-between p-4 rounded-2xl bg-white/2 border border-white/5">
                                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Execution Priority</span>
                                        <span className="text-xs font-black text-white uppercase italic">Ultra_High</span>
                                    </div>
                                    <div className="flex items-center justify-between p-4 rounded-2xl bg-white/2 border border-white/5">
                                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Cluster Routing</span>
                                        <span className="text-xs font-black text-white uppercase italic">{telemetry?.cluster_node || "EU-Central-1"}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="glass-card p-10 bg-white/2 border-white/10 flex flex-col justify-center items-center text-center space-y-6 group cursor-pointer" onClick={handleCustomRecipe}>
                                <div className="h-16 w-16 rounded-full bg-zinc-900 border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                                    <Plus className="h-8 w-8 text-zinc-700" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-lg font-black text-zinc-500 group-hover:text-white transition-colors uppercase tracking-tight italic">Initialize Custom Recipe</h3>
                                    <p className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest leading-relaxed">Design your own neural pipeline for custom workflows.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Secondary Metrics / Stream */}
                    <div className="space-y-12">
                        {/* Live Log Stream */}
                        <div className="glass-card p-8 min-h-[500px] flex flex-col space-y-6 relative overflow-hidden bg-black shadow-2xl">
                             <div className="flex items-center justify-between">
                                <h3 className="text-xs font-black uppercase tracking-widest text-primary flex items-center gap-2 italic">
                                    <Activity className="h-3 w-3" /> Live Event Stream
                                </h3>
                                <div className="px-2 py-1 rounded-md bg-zinc-900 border border-white/5 text-[8px] font-bold text-zinc-500 font-mono">
                                    {telemetry?.latency_ms ? `${telemetry.latency_ms}ms OFFSET` : "--ms OFFSET"}
                                </div>
                             </div>

                             <div className="flex-1 font-mono text-[10px] text-zinc-600 space-y-3 overflow-hidden">
                                {logStream.length > 0 ? (
                                     <div className="space-y-2">
                                        {logStream.map((log, idx) => (
                                            <p key={idx} className={cn(
                                                "animate-in fade-in slide-in-from-left-2 duration-300",
                                                log.includes("ERROR") ? "text-red-500" : 
                                                log.includes("SUCCESS") ? "text-emerald-500" :
                                                "text-zinc-400"
                                            )}>
                                                {log}
                                            </p>
                                        ))}
                                     </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center opacity-30 space-y-4 grayscale">
                                        <Search className="h-8 w-8" />
                                        <p className="uppercase tracking-[0.3em] font-black text-[8px]">Waiting for signal...</p>
                                    </div>
                                )}
                             </div>

                             <div className="pt-4 border-t border-white/5">
                                 <button 
                                    onClick={handleClusterSettings}
                                    className="w-full py-4 rounded-2xl bg-zinc-900 border border-white/5 text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-white transition-all"
                                 >
                                    Cluster Topology
                                 </button>
                             </div>
                        </div>

                         {/* Global Pulse Indicator */}
                        <div className="p-8 rounded-5xl bg-linear-to-br from-zinc-900 to-black border border-white/5 space-y-4">
                            <h4 className="text-[10px] font-black uppercase tracking-widest text-zinc-500 italic">Network Health</h4>
                            <div className="flex gap-1 h-8 items-end">
                                {[...Array(24)].map((_, i) => (
                                    <motion.div 
                                        key={i}
                                        animate={{ height: [`${20 + Math.random() * 60}%`, `${40 + Math.random() * 40}%`, `${20 + Math.random() * 60}%`] }}
                                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.05 }}
                                        className="flex-1 bg-primary/20 rounded-t-sm"
                                    />
                                ))}
                            </div>
                            <div className="flex justify-between items-center text-[8px] font-black uppercase tracking-tighter text-zinc-700">
                                <span>Signal_01: {telemetry?.signals?.[0]?.status || (Math.random() > 0.5 ? 'Active' : 'Standby')}</span>
                                <span>Latency: {telemetry?.latency_ms ? `${telemetry.latency_ms}ms` : "---ms"}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Persona Lab Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="space-y-8"
                >
                    <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                        <div className="h-10 w-10 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                            <User className="h-5 w-5" />
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-white italic tracking-tighter uppercase">Persona Lab</h2>
                            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Create &amp; Generate Digital Personas</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Create Persona Card */}
                        <div className="p-8 rounded-4xl bg-zinc-900 border border-white/5 space-y-6">
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-xl bg-white/4 border border-white/5 flex items-center justify-center">
                                    <Plus className="h-5 w-5 text-zinc-400" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-black text-white uppercase tracking-tight">Create Persona</h3>
                                    <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Define a new digital identity</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <User className="h-3 w-3" /> Persona Name
                                    </label>
                                    <input
                                        type="text"
                                        value={personaName}
                                        onChange={(e) => setPersonaName(e.target.value)}
                                        placeholder="Enter persona name..."
                                        className="w-full px-4 py-3 rounded-xl bg-white/3 border border-white/5 text-white text-sm font-medium placeholder:text-zinc-700 focus:outline-none focus:border-primary/30 transition-colors"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <ImageIcon className="h-3 w-3" /> Reference Image URL
                                    </label>
                                    <input
                                        type="text"
                                        value={personaImageUrl}
                                        onChange={(e) => setPersonaImageUrl(e.target.value)}
                                        placeholder="https://example.com/image.png"
                                        className="w-full px-4 py-3 rounded-xl bg-white/3 border border-white/5 text-white text-sm font-medium placeholder:text-zinc-700 focus:outline-none focus:border-primary/30 transition-colors"
                                    />
                                </div>

                                <button
                                    onClick={handleCreatePersona}
                                    disabled={isCreatingPersona || !personaName || !personaImageUrl}
                                    className={cn(
                                        "w-full py-3 rounded-xl bg-primary text-black font-black uppercase tracking-widest text-xs transition-all hover:scale-[1.01] active:scale-95 flex items-center justify-center gap-2",
                                        (isCreatingPersona || !personaName || !personaImageUrl) && "opacity-50 cursor-not-allowed hover:scale-100"
                                    )}
                                >
                                    {isCreatingPersona ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                                    Create Persona
                                </button>
                            </div>

                            {createdPersona && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 flex items-center gap-3"
                                >
                                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                                    <div>
                                        <p className="text-xs font-black text-emerald-400 uppercase tracking-tight">{createdPersona.name}</p>
                                        <p className="text-[9px] text-zinc-500 truncate max-w-[280px]">{createdPersona.reference_image_url}</p>
                                    </div>
                                </motion.div>
                            )}
                        </div>

                        {/* Generate Video Card */}
                        <div className={cn(
                            "p-8 rounded-4xl bg-zinc-900 border border-white/5 space-y-6 transition-opacity",
                            !createdPersona && "opacity-40 pointer-events-none"
                        )}>
                            <div className="flex items-center gap-4">
                                <div className="h-10 w-10 rounded-xl bg-white/4 border border-white/5 flex items-center justify-center">
                                    <Video className="h-5 w-5 text-zinc-400" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-black text-white uppercase tracking-tight">Generate Video</h3>
                                    <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Produce persona-driven content</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <Sparkles className="h-3 w-3" /> Topic
                                    </label>
                                    <input
                                        type="text"
                                        value={videoTopic}
                                        onChange={(e) => setVideoTopic(e.target.value)}
                                        placeholder="Video topic or subject..."
                                        className="w-full px-4 py-3 rounded-xl bg-white/3 border border-white/5 text-white text-sm font-medium placeholder:text-zinc-700 focus:outline-none focus:border-primary/30 transition-colors"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
                                        <MessageSquare className="h-3 w-3" /> Script (Optional)
                                    </label>
                                    <textarea
                                        value={videoScript}
                                        onChange={(e) => setVideoScript(e.target.value)}
                                        placeholder="Enter custom script or leave blank for auto-generation..."
                                        rows={3}
                                        className="w-full px-4 py-3 rounded-xl bg-white/3 border border-white/5 text-white text-sm font-medium placeholder:text-zinc-700 focus:outline-none focus:border-primary/30 transition-colors resize-none"
                                    />
                                </div>

                                <button
                                    onClick={handleGenerateVideo}
                                    disabled={isGeneratingVideo || !videoTopic}
                                    className={cn(
                                        "w-full py-3 rounded-xl bg-primary text-black font-black uppercase tracking-widest text-xs transition-all hover:scale-[1.01] active:scale-95 flex items-center justify-center gap-2",
                                        (isGeneratingVideo || !videoTopic) && "opacity-50 cursor-not-allowed hover:scale-100"
                                    )}
                                >
                                    {isGeneratingVideo ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                                    Generate Persona Video
                                </button>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* 13. Activity History (Manual items + dynamic job items) */}
                <div className="space-y-8 pb-20">
                    <div className="flex items-center justify-between border-b border-white/5 pb-4">
                        <h3 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
                        <Zap className="h-5 w-5 text-primary" />
                        Activity Stream
                        </h3>
                        <button className="text-[10px] font-black uppercase tracking-widest text-primary/60 hover:text-primary transition-colors">Clear Stream</button>
                    </div>

                    <div className="space-y-4 max-h-[400px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent">
                        {nexusJobs.length > 0 ? (
                        nexusJobs.map((job) => (
                            <div key={job.id} className="flex gap-4 p-4 rounded-2xl bg-white/2 border border-white/5 hover:border-white/10 transition-colors group">
                                <div className="shrink-0 pt-1">
                                    {job.status === 'COMPLETED' ? <CheckCircle2 className="h-5 w-5 text-emerald-500" /> : 
                                    job.status === 'FAILED' ? <AlertCircle className="h-5 w-5 text-red-500" /> : 
                                    <RefreshCw className="h-5 w-5 text-primary animate-spin" />}
                                </div>
                                <div className="flex-1 space-y-1">
                                    <div className="flex justify-between items-start">
                                        <p className="text-xs font-black uppercase tracking-tight text-white">{job.niche} / {job.status}</p>
                                        <span className="text-[8px] font-bold text-zinc-600 font-mono italic">{new Date(job.created_at).toLocaleTimeString()}</span>
                                    </div>
                                    <p className="text-[10px] font-medium text-zinc-500">{job.blueprint_id} pipeline {job.status === 'COMPLETED' ? 'successfully finished' : 'is currently in ' + (job.node_status ? Object.entries(job.node_status).find(([_, s]) => s === 'PROCESSING')?.[0] : 'idle') + ' state'}.</p>
                                </div>
                                {job.output_path && (
                                    <button 
                                        onClick={() => handleInspectResult(job)}
                                        className="opacity-0 group-hover:opacity-100 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                                    >
                                        <ExternalLink className="h-3 w-3 text-white" />
                                    </button>
                                )}
                            </div>
                        ))
                        ) : (
                            <div className="py-12 text-center space-y-4">
                            <div className="h-12 w-12 rounded-full bg-white/5 border border-white/5 mx-auto flex items-center justify-center">
                                <Activity className="h-6 w-6 text-zinc-700" />
                            </div>
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-700">No active pipelines detected</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* AI Agent Chat Section */}
                <div className="space-y-8 pb-20">
                    <div className="flex items-center justify-between border-b border-white/5 pb-4">
                        <h3 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
                            <MessageSquare className="h-5 w-5 text-primary" />
                            AI Agent
                        </h3>
                        <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-black uppercase tracking-widest text-primary">
                            Neural Core
                        </div>
                    </div>

                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                        {/* Chat Interface */}
                        <div className="xl:col-span-2 glass-card p-0 flex flex-col bg-black border border-white/5 rounded-4xl overflow-hidden">
                            {/* Messages Area */}
                            <div className="flex-1 min-h-[400px] max-h-[500px] overflow-y-auto p-8 space-y-6 scrollbar-thin scrollbar-thumb-white/5 scrollbar-track-transparent">
                                {chatMessages.length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center opacity-30 space-y-4 py-16">
                                        <Bot className="h-12 w-12" />
                                        <div className="text-center space-y-1">
                                            <p className="uppercase tracking-[0.3em] font-black text-[10px]">No messages yet</p>
                                            <p className="text-[10px] font-medium text-zinc-600">Start a conversation with the AI agent</p>
                                        </div>
                                    </div>
                                ) : (
                                    <AnimatePresence>
                                        {chatMessages.map((msg, idx) => (
                                            <motion.div
                                                key={idx}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ duration: 0.3 }}
                                                className={cn(
                                                    "flex gap-4",
                                                    msg.role === "user" ? "justify-end" : "justify-start"
                                                )}
                                            >
                                                {msg.role === "agent" && (
                                                    <div className="shrink-0 h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                                                        <Bot className="h-4 w-4 text-primary" />
                                                    </div>
                                                )}
                                                <div className={cn(
                                                    "max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed",
                                                    msg.role === "user"
                                                        ? "bg-primary/10 border border-primary/20 text-white"
                                                        : "bg-white/3 border border-white/5 text-zinc-300"
                                                )}>
                                                    <p className="text-[10px] font-black uppercase tracking-widest mb-1 opacity-50">
                                                        {msg.role === "user" ? "You" : "Agent"}
                                                    </p>
                                                    <p className="font-medium">{msg.content}</p>
                                                </div>
                                                {msg.role === "user" && (
                                                    <div className="shrink-0 h-9 w-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                                                        <User className="h-4 w-4 text-zinc-400" />
                                                    </div>
                                                )}
                                            </motion.div>
                                        ))}
                                    </AnimatePresence>
                                )}
                                {isChatting && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="flex gap-4"
                                    >
                                        <div className="shrink-0 h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                                            <Bot className="h-4 w-4 text-primary" />
                                        </div>
                                        <div className="bg-white/3 border border-white/5 rounded-2xl p-4 flex items-center gap-2">
                                            <Loader2 className="h-4 w-4 text-primary animate-spin" />
                                            <span className="text-xs text-zinc-500 font-medium">Agent is thinking...</span>
                                        </div>
                                    </motion.div>
                                )}
                            </div>

                            {/* Input Area */}
                            <div className="p-6 border-t border-white/5">
                                <div className="flex gap-3">
                                    <input
                                        type="text"
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                                        placeholder="Ask the AI agent anything..."
                                        className="flex-1 bg-white/3 border border-white/5 rounded-2xl px-5 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary/30 transition-colors"
                                    />
                                    <button
                                        onClick={handleSendChat}
                                        disabled={!chatInput.trim() || isChatting}
                                        className={cn(
                                            "h-12 w-12 rounded-2xl bg-primary flex items-center justify-center transition-all hover:scale-105 active:scale-95",
                                            (!chatInput.trim() || isChatting) && "opacity-50 cursor-not-allowed hover:scale-100"
                                        )}
                                    >
                                        <Send className="h-5 w-5 text-black" />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Capabilities Display */}
                        <div className="space-y-6">
                            <div className="glass-card p-8 space-y-6 bg-black border border-white/5 rounded-4xl">
                                <div className="flex items-center gap-4">
                                    <div className="h-12 w-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                                        <ShieldCheck className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-black text-white italic tracking-tighter uppercase">Capabilities</h3>
                                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Agent Skill Matrix</p>
                                    </div>
                                </div>

                                <div className="space-y-3 pt-2">
                                    {agentCapabilities.length > 0 ? (
                                        agentCapabilities.map((cap, idx) => (
                                            <motion.div
                                                key={idx}
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: idx * 0.05 }}
                                                className="flex items-center gap-3 p-3 rounded-xl bg-white/2 border border-white/5 hover:border-primary/20 transition-all group"
                                            >
                                                <Sparkles className="h-4 w-4 text-primary/60 group-hover:text-primary transition-colors shrink-0" />
                                                <span className="text-xs font-medium text-zinc-400 group-hover:text-white transition-colors">{cap}</span>
                                            </motion.div>
                                        ))
                                    ) : (
                                        <div className="py-8 text-center space-y-3 opacity-40">
                                            <Cpu className="h-8 w-8 mx-auto text-zinc-600" />
                                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Loading capabilities...</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
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
    Trash2,
    X,
    Radio,
    Terminal,
    ArrowRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { NexusNode, NodeType } from "@/components/ui/NexusNode";
import { useWebSocket } from "@/hooks/useWebSocket";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { ClusterManager } from "@/components/ui/ClusterManager";
import { BlueprintBuilder } from "@/components/ui/BlueprintBuilder";
import { Blueprint, NexusJob, Persona } from "@/lib/types";
import { Canvas } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";

function NexusBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#d05bff" />
                    <Float speed={1.5} rotationIntensity={0.8} floatIntensity={0.8}>
                        <Sphere args={[1.2, 64, 64]} scale={2.2}>
                            <MeshDistortMaterial
                                color="#d05bff"
                                speed={3}
                                distort={0.3}
                                radius={1}
                                wireframe
                                transparent
                                opacity={0.1}
                            />
                        </Sphere>
                    </Float>
                </Suspense>
            </Canvas>
        </div>
    );
}

export default function NexusPage() {
    const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
    const [activeBlueprint, setActiveBlueprint] = useState<Blueprint | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);
    const [nexusJobs, setNexusJobs] = useState<NexusJob[]>([]);
    const [niches, setNiches] = useState<string[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("");
    const [userTier, setUserTier] = useState<string>("free");
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const [showClusterManager, setShowClusterManager] = useState(false);
    const [showBlueprintBuilder, setShowBlueprintBuilder] = useState(false);
    const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
    const [logStream, setLogStream] = useState<string[]>([]);

    const { data: jobUpdate } = useWebSocket<any>(`${WS_BASE}/jobs`);
    const { data: logUpdate } = useWebSocket<any>(`${WS_BASE}/logs`);

    const [personas, setPersonas] = useState<Persona[]>([]);
    const [telemetry, setTelemetry] = useState<any>(null);

    // Fetch initial data
    useEffect(() => {
        const fetchData = async () => {
            const token = getAuthToken();
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
                withRealFallback<Persona[]>(
                    () => fetch(`${API_BASE}/persona/list`, { headers }),
                    {
                        fallback: [],
                        onSuccess: (data) => setPersonas(data)
                    }
                ),
            ]);
        };

        fetchData();

        const fetchTelemetry = async () => {
            const token = getAuthToken();
            if (!token) return;
            await withRealFallback<any>(
                () => fetch(`${API_BASE}/nexus/telemetry`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                {
                    fallback: null,
                    onSuccess: (data) => setTelemetry(data)
                }
            );
        };

        fetchTelemetry();
        const interval = setInterval(fetchTelemetry, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleLaunchPipeline = async () => {
        if (!selectedNiche || !activeBlueprint) return;
        setIsLaunching(true);
        await withRealFallback(
            async () => {
                const token = getAuthToken();
                if (!token) throw new Error("Authentication required");
                return fetch(`${API_BASE}/nexus/compose`, {
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
            },
            {
                fallback: null,
                onSuccess: (data: any) => {
                    setActiveJobId(String(data.job_id));
                    toast.success("Pipeline Dispatched", {
                        description: `Job ID: ${data.job_id} is now active in the neural cluster.`
                    });
                    setSelectedNodeIndex(0);
                }
            }
        );
        setIsLaunching(false);
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-[#050507] relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <NexusBackground />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    
                    {/* NEXUS HEADER HUD */}
                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                        <div className="space-y-6">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 160 }}
                                className="h-1 bg-purple-500 shadow-[0_0_20px_#d05bff]"
                            />
                            <div className="space-y-2">
                                <h1 className="text-6xl md:text-8xl font-black text-white uppercase tracking-tighter leading-none glitch-text italic" data-text="NEXUS_CORE">
                                    Nexus Core
                                </h1>
                                <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                                    <Activity className="h-3 w-3 text-purple-400 animate-pulse" />
                                    CLUSTER_STATUS: OPERATIONAL
                                    <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                                    NODES_ACTIVE: {telemetry?.active_nodes || 12}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="surface-glass rim-light p-6 flex flex-col items-end">
                                <span className="font-data-mono text-[8px] text-zinc-600 mb-1">LATENCY_PULSE</span>
                                <span className="text-xl font-black text-white tabular-nums tracking-tighter">
                                    {telemetry?.latency_ms || 24}ms
                                </span>
                            </div>
                            <button 
                                onClick={handleLaunchPipeline}
                                disabled={isLaunching}
                                className="action-primary h-20 px-12 italic text-xs tracking-tighter flex items-center gap-4 group"
                            >
                                {isLaunching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current group-hover:scale-110 transition-transform" />}
                                COMPOSE_PIPELINE
                            </button>
                        </div>
                    </header>

                    {/* CONFIGURATION HUD */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 surface-glass rim-light mb-16 relative overflow-hidden group">
                        <div className="absolute inset-0 scanline opacity-5" />
                        <div className="flex flex-col gap-2 p-6 bg-white/2 border border-white/5 hover:border-purple-500/20 transition-all group/item">
                            <label className="text-[9px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2">
                                <Layers className="h-3 w-3" /> Target Niche
                            </label>
                            <select 
                                value={selectedNiche}
                                onChange={(e) => setSelectedNiche(e.target.value)}
                                className="bg-transparent text-white font-black uppercase tracking-tight focus:outline-none cursor-pointer appearance-none group-hover/item:text-purple-400 transition-colors"
                            >
                                {niches.map(n => <option key={n} value={n} className="bg-zinc-900">{n}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2 p-6 bg-white/2 border border-white/5 hover:border-purple-500/20 transition-all group/item">
                            <label className="text-[9px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2">
                                <Cpu className="h-3 w-3" /> Synthesis Recipe
                            </label>
                            <select 
                                value={activeBlueprint?.id}
                                onChange={(e) => setActiveBlueprint(blueprints.find(b => b.id === e.target.value) || null)}
                                className="bg-transparent text-white font-black uppercase tracking-tight focus:outline-none cursor-pointer appearance-none group-hover/item:text-purple-400 transition-colors"
                            >
                                {blueprints.map(b => (
                                    <option key={b.id} value={b.id} className="bg-zinc-900">{b.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2 p-6 bg-white/2 border border-white/5 hover:border-purple-500/20 transition-all">
                            <label className="text-[9px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2">
                                <Database className="h-3 w-3" /> Edge Node
                            </label>
                            <p className="text-white font-black uppercase tracking-tight italic">{telemetry?.hostname || "Local-Cluster-Alpha"}</p>
                        </div>

                        <div className="flex flex-col gap-2 p-6 bg-white/2 border border-white/5 hover:border-purple-500/20 transition-all">
                            <label className="text-[9px] font-black uppercase tracking-[0.3em] text-zinc-600 flex items-center gap-2">
                                <Activity className="h-3 w-3" /> Network Tier
                            </label>
                            <p className="text-white font-black uppercase tracking-tight italic">{userTier.toUpperCase()} // UNRESTRICTED</p>
                        </div>
                    </div>

                    {/* CORE PIPELINE VISUALIZER */}
                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12">
                        
                        <div className="xl:col-span-8 space-y-12">
                            {/* NEURAL MESH */}
                            <div className="relative aspect-21/9 surface-glass rim-light overflow-hidden group">
                                <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
                                    <svg className="w-full h-full">
                                        <pattern id="nexus-grid" width="60" height="60" patternUnits="userSpaceOnUse">
                                            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="white" strokeWidth="0.5" strokeOpacity="0.1"/>
                                        </pattern>
                                        <rect width="100%" height="100%" fill="url(#nexus-grid)" />
                                    </svg>
                                </div>

                                <div className="absolute inset-0 flex items-center justify-around px-20 z-10">
                                    <div className="absolute top-1/2 left-0 right-0 h-px bg-linear-to-r from-transparent via-purple-500/20 to-transparent" />
                                    
                                    {activeBlueprint?.nodes.map((node, idx) => (
                                        <div key={idx} className="relative">
                                            <NexusNode 
                                                type={node.type as any}
                                                label={node.label}
                                                description={node.desc}
                                                status={selectedNodeIndex === idx ? 'processing' : 'pending'}
                                                active={selectedNodeIndex === idx}
                                                onClick={() => setSelectedNodeIndex(idx)}
                                            />
                                            {idx < activeBlueprint.nodes.length - 1 && (
                                                <div className="absolute top-1/2 -right-20 translate-x-1/2 -translate-y-1/2">
                                                    <ChevronRight className="h-6 w-6 text-purple-500/20" />
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                <div className="absolute bottom-8 left-8 p-4 bg-black/60 border border-white/5 backdrop-blur-xl flex items-center gap-4">
                                    <div className="h-2 w-2 rounded-full bg-purple-500 animate-pulse shadow-[0_0_10px_#d05bff]" />
                                    <span className="font-data-mono text-[8px] text-zinc-400 uppercase tracking-widest">Neural_Mesh_Live</span>
                                </div>
                            </div>

                            {/* NODE DETAIL CLUSTER */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <section className="surface-glass rim-light p-10 space-y-6">
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                                            <Settings2 className="h-6 w-6" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-black text-white italic tracking-tighter uppercase">Processor Tuning</h3>
                                            <p className="font-data-mono text-[8px] text-zinc-600 uppercase tracking-widest">Manual_Override_Terminal</p>
                                        </div>
                                    </div>
                                    <div className="space-y-4 pt-4 border-t border-white/5">
                                        <div className="flex items-center justify-between p-5 bg-white/2 border border-white/5 group hover:border-purple-500/30 transition-all cursor-pointer">
                                            <span className="font-label-caps text-[9px] text-zinc-500 uppercase tracking-widest">Sampling Precision</span>
                                            <span className="text-xs font-black text-white italic uppercase">ULTRA_HD</span>
                                        </div>
                                        <div className="flex items-center justify-between p-5 bg-white/2 border border-white/5 group hover:border-purple-500/30 transition-all cursor-pointer">
                                            <span className="font-label-caps text-[9px] text-zinc-500 uppercase tracking-widest">Compute Priority</span>
                                            <span className="text-xs font-black text-white italic uppercase">CLUSTER_OVERRIDE</span>
                                        </div>
                                    </div>
                                </section>

                                <section 
                                    className="surface-glass rim-light p-10 flex flex-col items-center justify-center text-center space-y-6 group cursor-pointer border-dashed border-white/10 hover:border-purple-500/30 transition-all"
                                    onClick={() => setShowBlueprintBuilder(true)}
                                >
                                    <div className="h-16 w-16 rounded-full bg-zinc-900 border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform group-hover:rim-glow-purple">
                                        <Plus className="h-8 w-8 text-zinc-700 group-hover:text-purple-400" />
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-lg font-black text-zinc-500 group-hover:text-white transition-colors uppercase tracking-tight italic">Inject Custom Recipe</h3>
                                        <p className="font-data-mono text-[8px] text-zinc-700 uppercase tracking-widest">Protocol_Developer_Access</p>
                                    </div>
                                </section>
                            </div>
                        </div>

                        {/* STREAM SIDEBAR */}
                        <div className="xl:col-span-4 space-y-12">
                            <div className="surface-glass rim-light p-10 min-h-[500px] flex flex-col space-y-8 relative overflow-hidden">
                                <div className="absolute inset-0 scanline opacity-10" />
                                <div className="flex items-center justify-between border-b border-white/5 pb-6">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-purple-400 flex items-center gap-3">
                                        <Radio className="h-4 w-4 animate-pulse" /> Event Log Stream
                                    </h3>
                                    <div className="px-3 py-1 bg-zinc-900 border border-white/5 text-[7px] font-bold text-zinc-500 font-mono">
                                        SYSLOG_PULSE
                                    </div>
                                </div>

                                <div className="flex-1 font-mono text-[9px] space-y-3 overflow-hidden">
                                    {logStream.length > 0 ? (
                                        <div className="space-y-4">
                                            {logStream.slice(0, 15).map((log, idx) => (
                                                <p key={idx} className={cn(
                                                    "animate-in fade-in slide-in-from-left-4 duration-500 border-l-2 pl-4 py-1",
                                                    log.includes("ERROR") ? "border-red-500 text-red-500/80 bg-red-500/5" : 
                                                    log.includes("SUCCESS") ? "border-emerald-500 text-emerald-500/80 bg-emerald-500/5" :
                                                    "border-zinc-800 text-zinc-500 bg-white/2"
                                                )}>
                                                    {log}
                                                </p>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center opacity-20 space-y-6 grayscale">
                                            <Search className="h-12 w-12" />
                                            <p className="font-data-mono text-[8px] uppercase tracking-[0.5em] font-black">Awaiting_Telemetry_Broadcast</p>
                                        </div>
                                    )}
                                </div>

                                <button 
                                    className="action-primary w-full py-5 italic text-[10px] tracking-tighter"
                                    onClick={() => setShowClusterManager(true)}
                                >
                                    TOPOLOGY_INSPECTOR
                                </button>
                            </div>

                            <section className="surface-glass rim-light p-10 space-y-8 group overflow-hidden relative">
                                <div className="absolute inset-0 bg-purple-500/[0.02] group-hover:bg-purple-500/[0.05] transition-colors" />
                                <h4 className="font-label-caps text-[9px] text-zinc-500 uppercase tracking-widest flex items-center gap-3">
                                    <ShieldCheck className="h-4 w-4" /> Stability Index
                                </h4>
                                <div className="space-y-6">
                                    <div className="flex items-end justify-between">
                                        <span className="text-4xl font-black text-white italic tracking-tighter tabular-nums">99.8%</span>
                                        <span className="font-data-mono text-[8px] text-emerald-500">OPTIMAL</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-zinc-950 rounded-full overflow-hidden">
                                        <motion.div 
                                            initial={{ width: 0 }}
                                            animate={{ width: "99.8%" }}
                                            className="h-full bg-purple-500 shadow-[0_0_15px_#d05bff]"
                                        />
                                    </div>
                                </div>
                            </section>
                        </div>
                    </div>
                </div>
            </div>

            {/* Modals */}
            <AnimatePresence>
                {showClusterManager && (
                    <ClusterManager onClose={() => setShowClusterManager(false)} />
                )}
                {showBlueprintBuilder && (
                    <BlueprintBuilder 
                        isOpen={true}
                        onClose={() => setShowBlueprintBuilder(false)} 
                        onSuccess={handleBlueprintCreated as any}
                    />
                )}
            </AnimatePresence>
        </DashboardLayout>
    );
}

function handleBlueprintCreated(blueprint: any) {
    // Local state logic would go here if extracted
}

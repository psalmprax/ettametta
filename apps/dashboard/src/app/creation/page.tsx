"use client";

import React, { useState, useCallback, useEffect, useRef, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial, Sphere, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";
import { withRealFallback } from "@/lib/real_first_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { DesignCard } from "@/components/ui/DesignCard";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { Blueprint, ScriptOutput, HookAnalysis, ScriptSegment } from "@/lib/types";
import {
    Sparkles,
    Zap,
    Cpu,
    CheckCircle2,
    RefreshCw,
    Play,
    Edit3,
    ShieldAlert,
    Plus,
    Film,
    Wand2,
    Target,
    ChevronDown,
    Globe,
    Brain,
    Palette,
    Layers,
    Monitor,
    Database,
    ZapOff,
    Terminal,
    Dna,
    Network,
    ArrowRight,
    Command,
    Infinity as InfinityIcon,
    Radio,
    Clapperboard,
    Mic2,
    Loader2,
    Search
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useNiches } from "@/hooks/useNiches";
import { Button } from "@/components/ui/Button";
import { useWebSocket } from "@/hooks/useWebSocket";

// --- Three.js Background Components ---

function NeuralParticles() {
    const points = useRef<THREE.Points>(null!);
    const [particleCount] = useState(2000);
    const positions = React.useMemo(() => {
        const pos = new Float32Array(particleCount * 3);
        for (let i = 0; i < particleCount; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 15;
            pos[i * 3 + 1] = (Math.random() - 0.5) * 15;
            pos[i * 3 + 2] = (Math.random() - 0.5) * 15;
        }
        return pos;
    }, [particleCount]);

    useFrame((state) => {
        const time = state.clock.getElapsedTime();
        points.current.rotation.y = time * 0.05;
        points.current.rotation.x = time * 0.03;
    });

    return (
        <Points ref={points} positions={positions} stride={3}>
            <PointMaterial
                transparent
                color="#00fbfb"
                size={0.02}
                sizeAttenuation={true}
                depthWrite={false}
                blending={THREE.AdditiveBlending}
            />
        </Points>
    );
}

function NeuralCore() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-40">
            <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#00fbfb" />
                    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
                        <Sphere args={[1, 64, 64]} scale={1.5}>
                            <MeshDistortMaterial
                                color="#00fbfb"
                                speed={4}
                                distort={0.4}
                                radius={1}
                                wireframe
                                transparent
                                opacity={0.15}
                            />
                        </Sphere>
                    </Float>
                    <NeuralParticles />
                </Suspense>
            </Canvas>
        </div>
    );
}

// --- Main Page Component ---

export default function CreationPage() {
    const { niches, isLoading: isLoadingNiches } = useNiches();
    const [activeEngine, setActiveEngine] = useState("genesis");
    const [prompt, setPrompt] = useState("");
    const [niche, setNiche] = useState("Motivation");
    const [activeStack, setActiveStack] = useState<"cloud" | "os">("cloud");
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<ScriptOutput | null>(null);
    const [telemetry, setTelemetry] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>(["SYSTEM_INITIALIZED", "READY_FOR_NEURAL_SEED"]);
    const [isCinemaLaunching, setIsCinemaLaunching] = useState(false);

    // WebSocket for Real-time Telemetry
    const { data: telemetryUpdate } = useWebSocket<any>(`${WS_BASE}/nexus/telemetry`);

    useEffect(() => {
        if (telemetryUpdate) setTelemetry(telemetryUpdate);
    }, [telemetryUpdate]);

    // Initial Telemetry Fetch
    const fetchInitialTelemetry = async () => {
        const token = await getAuthToken();
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

    useEffect(() => {
        fetchInitialTelemetry();
    }, []);

    const handleGenerate = async () => {
        if (!prompt) {
            toast.error("Neural Seed Required");
            return;
        }
        setIsGenerating(true);
        setLogs((prev: string[]) => [`[SIGNAL] Initializing Generation: ${prompt.slice(0, 30)}...`, ...prev]);
        
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<ScriptOutput>(
            () => fetch(`${API_BASE}/no-face/script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic: prompt, niche, duration_seconds: 60, engine: activeStack })
            }),
            {
                fallback: {} as ScriptOutput,
                onSuccess: (data) => {
                    setScript(data);
                    setLogs((prev: string[]) => [`[SUCCESS] Neural Script Synthesized: ${data.title}`, ...prev]);
                    toast.success("Script Protocol Synthesized");
                },
                onFallback: (err) => {
                    setLogs((prev: string[]) => [`[ERROR] ${err.message}`, ...prev]);
                }
            }
        );
        setIsGenerating(false);
    };

    const handleLaunchCinema = async () => {
        if (!prompt) return;
        setIsCinemaLaunching(true);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/no-face/launch-cinema`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic: prompt, niche, duration_seconds: 60, engine: activeStack, script: script })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setLogs((prev: string[]) => [`[CINEMA] Sequence Initiated. JobID: ${data.job_id}`, ...prev]);
                    toast.success("Cinema Sequence Initiated");
                }
            }
        );
        setIsCinemaLaunching(false);
    };

    // Prepare Agent Data for Matrix
    const agents = [
        { id: "SYNTH_01", name: "Voice Forge", icon: Mic2, status: "ACTIVE" as any, latency: 12, load: 45, details: "Cloning: Operative_V4" },
        { id: "VISUAL_02", name: "Visual Core", icon: Clapperboard, status: telemetry?.status === "OPERATIONAL" ? "ACTIVE" : "IDLE" as any, latency: 45, load: telemetry?.load_avg * 10 || 0, details: "Rendering: Scene_08" },
        { id: "LOGIC_03", name: "Neural Logic", icon: Brain, status: "ACTIVE" as any, latency: 5, load: 22, details: "Optimizing Hook Patterns" },
    ];

    // Prepare Mock Assets (Should be wired to real jobs in next phase)
    const recentAssets = [
        { id: "ASSET_092", title: "Cyber Dream", type: "VIDEO" as any, timestamp: "3s AGO", tags: ["4K_READY"], size: "24.5 MB" },
        { id: "ASSET_012", title: "Logic Gate", type: "VIDEO" as any, timestamp: "12m AGO", tags: ["VOICE_SYNCED"], size: "18.2 MB" },
    ];

    return (
        <CommandCenterLayout
            title="NEURAL COMMAND"
            subtitle="CREATION_STUDIO_V4.2"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "genesis", label: "Command Center", icon: Command },
                        { id: "voice", label: "Voice Forge", icon: Mic2 },
                        { id: "script", label: "Script Engine", icon: Edit3 },
                        { id: "visual", label: "Visual Core", icon: Clapperboard },
                        { id: "logs", label: "System Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-violet-500/10 text-violet-400 border border-violet-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(167,139,250,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <AssetQuickview assets={recentAssets} />
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <NeuralCore />
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10 shrink-0">
                    {/* Neural Prompt Terminal */}
                    <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/60 backdrop-blur-xl p-8 space-y-6 flex flex-col">
                        <div className="flex items-center justify-between border-b border-white/5 pb-4">
                            <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Neural Prompt Terminal</h3>
                            <span className="text-[8px] font-mono text-zinc-600">READY_FOR_INPUT.EXE</span>
                        </div>
                        
                        <div className="flex-1 min-h-[160px] relative">
                            <div className="absolute left-0 top-0 text-violet-500 font-mono text-xs opacity-50">&gt;</div>
                            <textarea 
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder="ENTER INSTRUCTIONS FOR THE NEURAL NETWORK..."
                                className="w-full h-full bg-transparent border-none p-0 pl-6 text-sm font-mono text-white placeholder:text-zinc-700 focus:outline-none resize-none"
                            />
                            {isGenerating && (
                                <div className="absolute inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center rounded-xl">
                                    <div className="flex flex-col items-center gap-4">
                                        <Loader2 className="h-8 w-8 animate-spin text-violet-400" />
                                        <span className="text-[10px] font-bold text-violet-400 animate-pulse uppercase tracking-widest">Synthesizing Protocol...</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        <Button 
                            onClick={handleGenerate}
                            disabled={isGenerating || !prompt}
                            className="w-full h-16 bg-violet-500 hover:bg-violet-400 text-white font-bold text-lg rounded-2xl shadow-[0_0_30px_rgba(139,92,246,0.3)] transition-all uppercase tracking-widest"
                        >
                            {isGenerating ? "Synthesizing..." : "Initialize Generation"}
                        </Button>
                    </div>

                    {/* Active Processing Stream */}
                    <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/60 backdrop-blur-xl p-8 space-y-6 flex flex-col relative overflow-hidden">
                        <div className="flex items-center justify-between border-b border-white/5 pb-4">
                            <h3 className="text-[10px] font-bold text-emerald-400 tracking-[0.2em] uppercase">Active Processing Stream</h3>
                            <span className="text-[8px] font-mono text-zinc-600">LIVE DATA FEED_001</span>
                        </div>

                        <div className="flex-1 flex flex-col justify-center items-center relative py-10">
                            <div className="w-full h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent absolute top-1/2 -translate-y-1/2" />
                            <motion.div 
                                animate={{ scale: [1, 1.1, 1] }}
                                transition={{ duration: 2, repeat: Infinity }}
                                className="h-16 w-16 rounded-2xl border border-violet-500/50 flex items-center justify-center bg-violet-500/10 z-10"
                            >
                                <Brain className="h-8 w-8 text-violet-400" />
                            </motion.div>
                            <span className="text-[10px] font-bold text-violet-400 mt-4 tracking-widest uppercase opacity-80">Synapse Core</span>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center text-[8px] font-bold text-zinc-500 uppercase">
                                <span>Synthesis Progress</span>
                                <span>{isGenerating ? "Processing..." : "0.0%"}</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div 
                                    className="h-full bg-emerald-500"
                                    animate={isGenerating ? { x: ["-100%", "100%"] } : { width: 0 }}
                                    transition={isGenerating ? { duration: 1.5, repeat: Infinity, ease: "linear" } : {}}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* System Logs / Neural Script Preview */}
                <div className="flex-1 min-h-0 relative z-10 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                        <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">Neural Transcript Log</h3>
                        <div className="flex items-center gap-4">
                            <span className="text-[8px] font-mono text-zinc-600">LOG_LEVEL: VERBOSE</span>
                            <button onClick={() => setLogs(["SYSTEM_RESET", "READY"])} className="text-zinc-600 hover:text-white transition-colors">
                                <RefreshCw className="h-3 w-3" />
                            </button>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                        {logs.map((log, i) => (
                            <div key={i} className="flex gap-4">
                                <span className="text-zinc-700">[{new Date().toLocaleTimeString()}]</span>
                                <span className={cn(
                                    log.includes("[ERROR]") ? "text-rose-500" :
                                    log.includes("[SUCCESS]") ? "text-emerald-500" :
                                    log.includes("[SIGNAL]") ? "text-cyan-400" : "text-zinc-500"
                                )}>{log}</span>
                            </div>
                        ))}
                    </div>
                    {script && (
                        <div className="p-6 border-t border-white/5 bg-violet-500/5 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <span className="text-xs font-bold text-white uppercase">{script.title}</span>
                                <span className="text-[10px] text-zinc-500">{script.segments?.length} SEGMENTS DETECTED</span>
                            </div>
                            <Button 
                                onClick={handleLaunchCinema}
                                disabled={isCinemaLaunching}
                                className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs uppercase h-10 px-6 rounded-xl"
                            >
                                {isCinemaLaunching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Commit to Production"}
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </CommandCenterLayout>
    );
}

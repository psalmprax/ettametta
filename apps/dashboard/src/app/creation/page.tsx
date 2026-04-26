"use client";

import React, { useState, useCallback, useEffect, useRef, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial, Sphere, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";
import { withRealFallback } from "@/lib/real_first_utils";
import DashboardLayout from "@/components/layout";
import { BlueprintBuilder } from "@/components/ui/BlueprintBuilder";
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
    Radio
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useNiches } from "@/hooks/useNiches";

// --- TOP NOTCH 3D COMPONENTS ---

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

// --- MAIN PAGE ---

export default function CreationPage() {
    const { niches, styles: availableStyles, isLoading: isLoadingNiches } = useNiches();
    const [topic, setTopic] = useState("");
    const [niche, setNiche] = useState(() => niches && niches.length > 0 ? niches[0] : "Motivation");
    const [style, setStyle] = useState(() => availableStyles && availableStyles.length > 0 ? availableStyles[0] : "story");
    const [duration, setDuration] = useState(60);
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<ScriptOutput | null>(null);
    const [segmentAssets, setSegmentAssets] = useState<Record<number, { audio?: string, image?: string, videos?: any[] }>>({});
    const [loadingSegment, setLoadingSegment] = useState<string | null>(null);
    const [cinemaMode, setCinemaMode] = useState(false);
    const [isValidating, setIsValidating] = useState(false);
    const [isCinemaLaunching, setIsCinemaLaunching] = useState(false);
    const [hookAnalysis, setHookAnalysis] = useState<HookAnalysis | null>(null);

    const handleGenerateScript = async () => {
        if (!topic) {
            toast.error("Neural Seed Required");
            return;
        }
        setIsGenerating(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/video/script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic, niche, style, duration_seconds: duration })
            });
            if (!res.ok) throw new Error("Synthesis failure");
            const data = await res.json();
            setScript(data);
            toast.success("Script Protocol Synthesized");
        } catch (err) {
            console.error(err);
            toast.error("Neural Link Failed");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleLaunchCinema = async () => {
        if (!topic) {
            toast.error("Neural Seed Required");
            return;
        }
        setIsCinemaLaunching(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/video/launch-cinema`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic, niche, style, duration_seconds: duration })
            });
            if (!res.ok) throw new Error("Cinema launch failure");
            toast.success("Cinema Sequence Initiated");
        } catch (err) {
            console.error(err);
            toast.error("System Override Required");
        } finally {
            setIsCinemaLaunching(false);
        }
    };

    const handleValidateHook = async () => {
        if (!script?.segments?.[0]?.text) return;
        setIsValidating(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/video/validate-hook`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ hook: script.segments[0].text })
            });
            if (!res.ok) throw new Error("Validation failed");
            const data = await res.json();
            setHookAnalysis(data);
        } catch (err) {
            console.error(err);
            toast.error("Retention analysis offline");
        } finally {
            setIsValidating(false);
        }
    };

    const handleGlobalize = async (targetLang: string) => {
        if (!script) return;
        setIsGenerating(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/video/translate-script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ script, target_language: targetLang })
            });
            if (!res.ok) throw new Error("Translation failed");
            const data = await res.json();
            setScript(data);
            toast.success(`Localized to ${targetLang}`);
        } catch (err) {
            console.error(err);
            toast.error("Linguistic module error");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSynthesizeAudio = async (index: number, text: string) => {
        setLoadingSegment(`audio-${index}`);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/video/synthesize-audio`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ text, segment_index: index })
            });
            if (!res.ok) throw new Error("Audio synthesis failed");
            const data = await res.json();
            setSegmentAssets(prev => ({
                ...prev,
                [index]: { ...prev[index], audio: data.audio_url }
            }));
            toast.success("Vocal Pattern Captured");
        } catch (err) {
            console.error(err);
            toast.error("Audio Engine Stalled");
        } finally {
            setLoadingSegment(null);
        }
    };

    const handleSearchStock = async (index: number, query: string) => {
        setLoadingSegment(`stock-${index}`);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/video/search-stock`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ query, segment_index: index })
            });
            if (!res.ok) throw new Error("Stock search failed");
            const data = await res.json();
            setSegmentAssets(prev => ({
                ...prev,
                [index]: { ...prev[index], videos: data.videos }
            }));
            toast.success("Visual Assets Retained");
        } catch (err) {
            console.error(err);
            toast.error("Visual Link Terminated");
        } finally {
            setLoadingSegment(null);
        }
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-[#050507] relative flex flex-col font-sans">
                {/* ADVANCED UI LAYERS */}
                <div className="noise-overlay" />
                <NeuralCore />
                <div className="absolute inset-0 cyber-grid opacity-20 pointer-events-none" />
                <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    
                    {/* SYSTEM HUD */}
                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-10">
                        <div className="space-y-4">
                            <motion.div 
                                initial={{ opacity: 0, scaleX: 0 }}
                                animate={{ opacity: 1, scaleX: 1 }}
                                className="h-1 w-24 bg-cyan-400 origin-left"
                            />
                            <div className="relative">
                                <motion.h1 
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none glitch-text"
                                    data-text="CREATION SUITE"
                                >
                                    Creation Suite
                                </motion.h1>
                            </div>
                            <motion.div 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.4 }}
                                className="flex items-center gap-6 font-data-mono text-zinc-500"
                            >
                                <span className="flex items-center gap-2 text-cyan-400/80">
                                    <Radio className="h-3 w-3 animate-pulse" />
                                    CORE_ONLINE
                                </span>
                                <span className="w-px h-3 bg-zinc-800" />
                                <span>TERMINAL_ID: ET-4492</span>
                                <span className="w-px h-3 bg-zinc-800" />
                                <span className="flex items-center gap-2">
                                    <InfinityIcon className="h-3 w-3" />
                                    INFINITE_YIELD
                                </span>
                            </motion.div>
                        </div>

                        {/* MODE HUD */}
                        <motion.div 
                            initial={{ opacity: 0, x: 50 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-center gap-4"
                        >
                            <div className="surface-glass rim-light p-6 flex items-center gap-10">
                                <div className="space-y-1">
                                    <p className="font-label-caps text-[8px] text-zinc-600">Sync Status</p>
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full shadow-[0_0_10px_#10b981]" />
                                        <span className="font-data-mono text-white text-xs">ENCRYPTED</span>
                                    </div>
                                </div>
                                <div className="w-px h-10 bg-white/5" />
                                <div className="flex items-center gap-4">
                                    <div className="flex flex-col items-end">
                                        <span className="font-label-caps text-white text-[10px]">Cinema Mode</span>
                                        <span className="font-data-mono text-[8px] text-zinc-500">Auto-Cinematography</span>
                                    </div>
                                    <button 
                                        onClick={() => setCinemaMode(!cinemaMode)}
                                        className={cn(
                                            "w-16 h-8 rounded-none transition-all relative p-1 border",
                                            cinemaMode ? "border-cyan-400 bg-cyan-400/10" : "border-zinc-800 bg-zinc-900"
                                        )}
                                    >
                                        <motion.div 
                                            animate={{ x: cinemaMode ? 32 : 0 }}
                                            className={cn(
                                                "w-6 h-6 shadow-2xl transition-colors",
                                                cinemaMode ? "bg-cyan-400" : "bg-zinc-700"
                                            )}
                                        />
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </header>

                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12 items-start">
                        {/* LEFT: COMMAND CONSOLE */}
                        <div className="xl:col-span-4 space-y-10">
                            <section className="surface-glass rim-light p-10 space-y-10 relative overflow-hidden group">
                                <div className="absolute -right-10 -top-10 w-40 h-40 bg-cyan-400/5 blur-3xl rounded-full group-hover:bg-cyan-400/10 transition-all" />
                                
                                <div className="flex items-center justify-between">
                                    <h2 className="font-label-caps text-cyan-400 flex items-center gap-3 text-xs">
                                        <Command className="h-4 w-4" />
                                        CORE_CONFIGURATION
                                    </h2>
                                    <div className="flex gap-1">
                                        <div className="w-1 h-1 bg-zinc-800" />
                                        <div className="w-1 h-1 bg-zinc-800" />
                                        <div className="w-1 h-1 bg-zinc-800" />
                                    </div>
                                </div>

                                <div className="space-y-10">
                                    {/* Topic */}
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <label className="font-label-caps text-zinc-500">Neural Seed (Topic)</label>
                                            <span className="font-data-mono text-[8px] text-cyan-400/40">STRING_INPUT</span>
                                        </div>
                                        <div className="relative group/input">
                                            <input 
                                                value={topic}
                                                onChange={(e) => setTopic(e.target.value)}
                                                placeholder="Inject topic..."
                                                className="w-full bg-black/60 border border-white/5 p-6 text-white font-body-base focus:border-cyan-400 transition-all outline-none text-lg placeholder:text-zinc-800"
                                            />
                                            <div className="absolute bottom-0 left-0 h-[2px] bg-cyan-400 w-0 group-focus-within/input:w-full transition-all duration-500" />
                                            <Brain className="absolute right-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-800 group-focus-within/input:text-cyan-400 transition-colors" />
                                        </div>
                                    </div>

                                    {/* Selectors */}
                                    <div className="grid grid-cols-2 gap-6">
                                        <div className="space-y-3">
                                            <label className="font-label-caps text-zinc-500">Niche</label>
                                            <div className="relative">
                                                <select 
                                                    value={niche}
                                                    onChange={(e) => setNiche(e.target.value)}
                                                    className="w-full bg-black/60 border border-white/5 p-5 text-white font-label-caps outline-none appearance-none cursor-pointer focus:border-cyan-400/50 transition-all"
                                                >
                                                    {niches.map(n => <option key={n} value={n} className="bg-[#050507]">{n}</option>)}
                                                </select>
                                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600 pointer-events-none" />
                                            </div>
                                        </div>
                                        <div className="space-y-3">
                                            <label className="font-label-caps text-zinc-500">Style</label>
                                            <div className="relative">
                                                <select 
                                                    value={style}
                                                    onChange={(e) => setStyle(e.target.value)}
                                                    className="w-full bg-black/60 border border-white/5 p-5 text-white font-label-caps outline-none appearance-none cursor-pointer focus:border-cyan-400/50 transition-all"
                                                >
                                                    {availableStyles.map(s => <option key={s} value={s.toLowerCase()} className="bg-[#050507]">{s}</option>)}
                                                </select>
                                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600 pointer-events-none" />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Slider */}
                                    <div className="space-y-6 pt-4">
                                        <div className="flex justify-between items-center">
                                            <label className="font-label-caps text-zinc-500">Output Duration</label>
                                            <div className="px-3 py-1 bg-cyan-400/10 border border-cyan-400/20">
                                                <span className="font-data-mono text-cyan-400">{duration}S</span>
                                            </div>
                                        </div>
                                        <input 
                                            type="range"
                                            min="15"
                                            max="180"
                                            value={duration}
                                            onChange={(e) => setDuration(parseInt(e.target.value))}
                                            className="w-full h-8"
                                        />
                                        <div className="flex justify-between font-data-mono text-[8px] text-zinc-800">
                                            <span>MIN_15S</span>
                                            <span>MAX_180S</span>
                                        </div>
                                    </div>
                                </div>

                                <button 
                                    onClick={cinemaMode ? handleLaunchCinema : handleGenerateScript}
                                    disabled={isGenerating || isCinemaLaunching || !topic}
                                    className="w-full action-primary py-8 mt-4 flex items-center justify-center gap-6 group overflow-hidden"
                                >
                                    <span className="relative z-10 font-black tracking-widest uppercase text-lg italic">
                                        {isGenerating || isCinemaLaunching ? "PROCESSING..." : cinemaMode ? "INITIATE CINEMA" : "SYNTHESIZE SCRIPT"}
                                    </span>
                                    <div className="relative z-10">
                                        {isGenerating || isCinemaLaunching ? (
                                            <RefreshCw className="h-6 w-6 animate-spin" />
                                        ) : (
                                            <Zap className="h-6 w-6 group-hover:scale-150 transition-transform duration-500" />
                                        )}
                                    </div>
                                </button>
                            </section>

                            {/* LOGS HUD */}
                            <div className="surface-glass rim-light p-8 font-data-mono text-[9px] space-y-3 border-l-4 border-cyan-400/30">
                                <div className="flex items-center justify-between text-zinc-600">
                                    <span>SYSTEM_LOG</span>
                                    <span>v3.0.4-REV</span>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-emerald-500 flex items-center gap-2">
                                        <span className="w-1 h-1 bg-emerald-500" />
                                        &gt; [SUCCESS] NEURAL_CORE_LOADED
                                    </p>
                                    <p className="text-zinc-600 flex items-center gap-2">
                                        <span className="w-1 h-1 bg-zinc-800" />
                                        &gt; [INFO] WAITING_FOR_USER_INPUT
                                    </p>
                                    <p className="text-zinc-800 flex items-center gap-2">
                                        <span className="w-1 h-1 bg-zinc-900" />
                                        &gt; [DEBUG] NO_SEED_DETECTED
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* RIGHT: WORKSPACE CONSOLE */}
                        <div className="xl:col-span-8">
                            <div className="surface-glass rim-light min-h-[850px] flex flex-col relative group overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent" />
                                
                                {/* EMPTY STATE */}
                                {!script && (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center space-y-10 z-10">
                                        <div className="w-48 h-48 relative">
                                            <motion.div 
                                                animate={{ rotate: 360, scale: [1, 1.1, 1] }}
                                                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                                                className="absolute inset-0 border border-cyan-400/10 rounded-full border-t-cyan-400/40 border-l-cyan-400/20"
                                            />
                                            <div className="absolute inset-6 border border-zinc-900 rounded-full flex items-center justify-center bg-black/20">
                                                <Target className="h-16 w-16 text-zinc-900 animate-pulse" />
                                            </div>
                                        </div>
                                        <div className="text-center space-y-4">
                                            <h3 className="font-label-caps text-zinc-600 text-sm tracking-[0.5em]">SYSTEM_IDLE</h3>
                                            <p className="font-data-mono text-zinc-800 text-[10px]">INJECT TOPIC TO INITIALIZE WORKSPACE</p>
                                        </div>
                                    </div>
                                )}

                                {/* SCRIPT WORKSPACE */}
                                {script && (
                                    <div className="flex-1 flex flex-col">
                                        {/* Workspace Header */}
                                        <div className="p-10 border-b border-white/5 bg-black/40 flex items-center justify-between relative overflow-hidden">
                                            <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-cyan-400/40 to-transparent" />
                                            
                                            <div className="flex items-center gap-6">
                                                <div className="h-16 w-16 bg-cyan-400/5 flex items-center justify-center border border-cyan-400/10 shadow-[0_0_20px_rgba(0,251,251,0.05)]">
                                                    <Dna className="h-8 w-8 text-cyan-400" />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-3 mb-1">
                                                        <span className="font-data-mono text-[8px] text-cyan-400/60">FILE_STATUS: ACTIVE</span>
                                                        <div className="w-1 h-1 bg-emerald-500 rounded-full" />
                                                    </div>
                                                    <h3 className="font-label-caps text-2xl text-white tracking-tight italic">Neural_Blueprint_01.pen</h3>
                                                </div>
                                            </div>

                                            <button 
                                                onClick={handleValidateHook}
                                                disabled={isValidating}
                                                className="px-10 py-4 bg-white/5 border border-white/10 text-white font-label-caps text-[10px] hover:bg-cyan-400 hover:text-black transition-all flex items-center gap-4 group"
                                            >
                                                {isValidating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 group-hover:scale-125 transition-transform" />}
                                                ANALYZE_HOOK_RELIABILITY
                                            </button>
                                        </div>

                                        <div className="flex-1 p-12 space-y-16 overflow-y-auto max-h-[900px] custom-scrollbar relative">
                                            {/* Master Title */}
                                            <div className="space-y-6 relative">
                                                <div className="absolute -left-12 top-0 h-full w-1 bg-cyan-400" />
                                                <span className="font-label-caps text-cyan-400/60 flex items-center gap-3 text-[10px]">
                                                    <div className="w-4 h-px bg-cyan-400/40" />
                                                    MASTER_ASSET_TITLE
                                                </span>
                                                <h2 className="text-4xl font-bold text-white uppercase italic tracking-tighter leading-none">
                                                    {script.title}
                                                </h2>
                                            </div>

                                            {/* Analysis HUD */}
                                            {hookAnalysis && (
                                                <motion.div 
                                                    initial={{ opacity: 0, height: 0 }}
                                                    animate={{ opacity: 1, height: "auto" }}
                                                    className="p-8 bg-cyan-400/5 border border-cyan-400/20 space-y-6"
                                                >
                                                    <div className="flex justify-between items-center">
                                                        <span className="font-label-caps text-cyan-400 text-xs">RETENTION_AUDIT</span>
                                                        <div className="px-4 py-1 bg-cyan-400 text-black font-black text-[10px]">
                                                            SCORE: {hookAnalysis.score}%
                                                        </div>
                                                    </div>
                                                    <p className="text-sm text-cyan-200 leading-relaxed font-medium italic">
                                                        "{hookAnalysis.analysis}"
                                                    </p>
                                                </motion.div>
                                            )}

                                            {/* Segments Grid */}
                                            <div className="space-y-12">
                                                {script.segments?.map((seg, i) => (
                                                    <motion.div 
                                                        key={i}
                                                        initial={{ opacity: 0, x: -20 }}
                                                        whileInView={{ opacity: 1, x: 0 }}
                                                        viewport={{ once: true }}
                                                        className="group/segment relative p-10 bg-black/40 border border-white/5 hover:border-cyan-400/30 transition-all duration-500"
                                                    >
                                                        <div className="absolute -left-[1px] top-0 h-full w-1 bg-white/5 group-hover/segment:bg-cyan-400 transition-colors" />
                                                        
                                                        <div className="flex flex-col lg:flex-row gap-12">
                                                            <div className="flex-1 space-y-8">
                                                                <div className="flex items-center justify-between">
                                                                    <div className="flex items-center gap-6">
                                                                        <span className="font-data-mono text-[10px] text-cyan-400">0{i + 1}</span>
                                                                        <span className="font-label-caps text-[9px] bg-white/5 px-3 py-1 text-zinc-500 border border-white/5">
                                                                            {seg.type}
                                                                        </span>
                                                                    </div>
                                                                    <div className="font-data-mono text-zinc-700 text-[9px]">
                                                                        DURATION: {seg.duration}S
                                                                    </div>
                                                                </div>
                                                                
                                                                <div className="space-y-4">
                                                                    <p className="text-2xl font-bold text-white leading-tight tracking-tight">
                                                                        {seg.text}
                                                                    </p>
                                                                    <div className="flex items-center gap-4 text-zinc-500 font-data-mono text-[9px] italic bg-white/5 p-4 border-l-2 border-zinc-800">
                                                                        <Monitor className="h-4 w-4 opacity-50" />
                                                                        VISUAL_PROMPT: {seg.visual_cue}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            <div className="flex lg:flex-col gap-3 justify-end lg:justify-start">
                                                                <button 
                                                                    onClick={() => handleSynthesizeAudio(i, seg.text)}
                                                                    title="Synthesize Voiceover"
                                                                    className={cn(
                                                                        "w-16 h-16 flex items-center justify-center transition-all border",
                                                                        segmentAssets[i]?.audio 
                                                                            ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.1)]" 
                                                                            : "border-white/5 hover:border-cyan-400 hover:text-cyan-400 bg-black/40"
                                                                    )}
                                                                >
                                                                    {loadingSegment === `audio-${i}` ? <RefreshCw className="h-6 w-6 animate-spin" /> : <Play className="h-6 w-6" />}
                                                                </button>
                                                                <button 
                                                                    onClick={() => handleSearchStock(i, seg.visual_cue)}
                                                                    title="Retrieve Visual Stock"
                                                                    className={cn(
                                                                        "w-16 h-16 flex items-center justify-center transition-all border",
                                                                        segmentAssets[i]?.videos 
                                                                            ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.1)]" 
                                                                            : "border-white/5 hover:border-cyan-400 hover:text-cyan-400 bg-black/40"
                                                                    )}
                                                                >
                                                                    {loadingSegment === `stock-${i}` ? <RefreshCw className="h-6 w-6 animate-spin" /> : <Film className="h-6 w-6" />}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* GLOBAL HUD - FLOATING LOCALIZATION */}
                {script && (
                    <motion.div 
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="fixed right-10 top-1/2 -translate-y-1/2 flex flex-col gap-6 z-40 hidden 2xl:flex"
                    >
                        <div className="surface-glass rim-light p-3 flex flex-col gap-4 border-r-4 border-cyan-400/20">
                            {[
                                { code: "ES", name: "Spanish" },
                                { code: "DE", name: "German" },
                                { code: "FR", name: "French" },
                                { code: "IT", name: "Italian" },
                                { code: "PT", name: "Portuguese" },
                                { code: "JP", name: "Japanese" }
                            ].map(lang => (
                                <button
                                    key={lang.code}
                                    onClick={() => handleGlobalize(lang.name)}
                                    className="w-14 h-14 flex items-center justify-center font-label-caps text-xs text-zinc-600 hover:text-cyan-400 hover:bg-cyan-400/5 transition-all relative group"
                                >
                                    <span className="relative z-10">{lang.code}</span>
                                    <div className="absolute inset-0 border border-transparent group-hover:border-cyan-400/20 transition-all" />
                                </button>
                            ))}
                            <div className="h-[2px] bg-white/5 mx-2" />
                            <div className="w-14 h-14 flex items-center justify-center text-zinc-800">
                                <Globe className="h-5 w-5" />
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </DashboardLayout>
    );
}

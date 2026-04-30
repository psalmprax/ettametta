"use client";

import React, { useState, useEffect } from "react";
import { 
    Video, 
    Upload, 
    ChevronDown, 
    Sparkles, 
    Play, 
    Plus,
    ChevronLeft,
    ChevronRight,
    Image as ImageIcon,
    FileText,
    Zap,
    Mic2,
    Globe,
    Settings,
    Layers,
    Save,
    Cpu,
    CheckCircle2,
    Loader2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { HighVelocityTicker } from "@/components/ui/HighVelocityTicker";
import DashboardLayout from "@/components/layout";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { withRealFallback } from "@/lib/real_first_utils";

const STYLES = ["story", "motivation", "educational", "breaking_news", "cinematic_top10"];
const DURATIONS = [15, 30, 60, 90, 120];

export default function VideoEditorPage() {
    const router = useRouter();
    const [step, setStep] = useState(1); // 1: Topic, 2: Script Edit, 3: Rendering
    const [prompt, setPrompt] = useState("");
    const [niche, setNiche] = useState("Motivation");
    const [style, setStyle] = useState("story");
    const [duration, setDuration] = useState(60);
    const [engine, setEngine] = useState("cloud");
    
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<any>(null);
    const [activeSegment, setActiveSegment] = useState(0);

    const handleGenerateScript = async () => {
        if (!prompt) {
            toast.error("Please enter a topic first");
            return;
        }
        setIsGenerating(true);
        const token = await getAuthToken();
        
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/no-face/script`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ 
                    topic: prompt, 
                    niche, 
                    duration_seconds: duration, 
                    style 
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setScript(data);
                    setStep(2);
                    toast.success("Neural Script Synthesized");
                },
                onFallback: (err) => toast.error("Script Generation Failed", { description: err.message })
            }
        );
        setIsGenerating(false);
    };

    const handleCommitRender = async () => {
        if (!script) return;
        setIsGenerating(true);
        const token = await getAuthToken();
        
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/no-face/launch-cinema`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ 
                    topic: prompt, 
                    niche, 
                    duration_seconds: duration, 
                    style,
                    engine,
                    script 
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    toast.success("Cinema Sequence Initiated", { description: `Job ID: ${data.job_id}` });
                    router.push("/transformation");
                },
                onFallback: (err) => toast.error("Neural Render Failed", { description: err.message })
            }
        );
        setIsGenerating(false);
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                
                <div className="flex-1 section-container relative py-12 px-6 lg:px-16 max-w-screen-2xl mx-auto w-full z-10">
                    <HighVelocityTicker />

                    <header className="mb-12 flex flex-col xl:flex-row xl:items-end justify-between gap-8">
                        <div className="space-y-4">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 120 }}
                                className="h-1 bg-primary shadow-[0_0_20px_#00fbfb]"
                            />
                            <h1 className="text-4xl font-bold text-white uppercase tracking-tighter leading-none">
                                Elite <span className="text-hollow">Production</span> Workflow
                            </h1>
                            <div className="flex items-center gap-6">
                                <div className={cn("text-[9px] font-bold uppercase tracking-widest flex items-center gap-2", step >= 1 ? "text-primary" : "text-zinc-600")}>
                                    <span className="h-4 w-4 rounded-full border border-current flex items-center justify-center">1</span>
                                    Concept
                                </div>
                                <div className="h-px w-8 bg-zinc-900" />
                                <div className={cn("text-[9px] font-bold uppercase tracking-widest flex items-center gap-2", step >= 2 ? "text-primary" : "text-zinc-600")}>
                                    <span className="h-4 w-4 rounded-full border border-current flex items-center justify-center">2</span>
                                    Script_Logic
                                </div>
                                <div className="h-px w-8 bg-zinc-900" />
                                <div className={cn("text-[9px] font-bold uppercase tracking-widest flex items-center gap-2", step >= 3 ? "text-primary" : "text-zinc-600")}>
                                    <span className="h-4 w-4 rounded-full border border-current flex items-center justify-center">3</span>
                                    Neural_Render
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="surface-glass p-5 border border-white/5 text-right">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase block mb-1">Compute Cluster</span>
                                <span className="text-sm font-bold text-white uppercase">{engine.toUpperCase()}_ENGINE</span>
                            </div>
                        </div>
                    </header>

                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12 items-start h-full">
                        {/* Editor Controls */}
                        <div className="xl:col-span-4 space-y-8">
                            <AnimatePresence mode="wait">
                                {step === 1 ? (
                                    <motion.section 
                                        key="step1"
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 20 }}
                                        className="surface-glass rim-light p-8 space-y-8"
                                    >
                                        <div className="space-y-6">
                                            <div className="space-y-3">
                                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Viral Topic</label>
                                                <textarea 
                                                    value={prompt}
                                                    onChange={(e) => setPrompt(e.target.value)}
                                                    placeholder="Describe the core message..."
                                                    className="w-full h-32 bg-black/40 border border-white/5 p-6 text-sm text-white focus:outline-none focus:border-primary/30 transition-all resize-none"
                                                />
                                            </div>

                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-2">
                                                    <label className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Niche</label>
                                                    <select 
                                                        value={niche}
                                                        onChange={(e) => setNiche(e.target.value)}
                                                        className="w-full bg-black/40 border border-white/5 rounded-xl p-4 text-[10px] font-bold text-zinc-400 uppercase tracking-widest focus:outline-none"
                                                    >
                                                        <option>Motivation</option>
                                                        <option>AI Technology</option>
                                                        <option>Stoicism</option>
                                                        <option>Finance</option>
                                                    </select>
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Visual Style</label>
                                                    <select 
                                                        value={style}
                                                        onChange={(e) => setStyle(e.target.value)}
                                                        className="w-full bg-black/40 border border-white/5 rounded-xl p-4 text-[10px] font-bold text-zinc-400 uppercase tracking-widest focus:outline-none"
                                                    >
                                                        {STYLES.map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                                                    </select>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">Duration (Seconds)</label>
                                                <div className="grid grid-cols-5 gap-2">
                                                    {DURATIONS.map(d => (
                                                        <button 
                                                            key={d}
                                                            onClick={() => setDuration(d)}
                                                            className={cn(
                                                                "h-10 text-[9px] font-bold rounded-lg border transition-all",
                                                                duration === d ? "bg-primary text-black border-primary" : "bg-white/2 text-zinc-500 border-white/5"
                                                            )}
                                                        >
                                                            {d}S
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        <button 
                                            onClick={handleGenerateScript}
                                            disabled={isGenerating || !prompt}
                                            className="action-primary w-full py-5 text-[10px] tracking-widest flex items-center justify-center gap-3 font-bold"
                                        >
                                            {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Cpu className="h-4 w-4" />}
                                            SYNTHESIZE_SCRIPT
                                        </button>
                                    </motion.section>
                                ) : (
                                    <motion.section 
                                        key="step2"
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 20 }}
                                        className="surface-glass rim-light p-8 space-y-8"
                                    >
                                        <div className="flex items-center justify-between">
                                            <h3 className="text-sm font-bold text-white uppercase tracking-tighter">Script_Structure</h3>
                                            <button onClick={() => setStep(1)} className="text-[9px] font-bold text-zinc-600 hover:text-white uppercase">Back_to_Concept</button>
                                        </div>

                                        <div className="space-y-4 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                                            {script?.segments?.map((seg: any, i: number) => (
                                                <div 
                                                    key={i}
                                                    onClick={() => setActiveSegment(i)}
                                                    className={cn(
                                                        "p-5 border cursor-pointer transition-all relative overflow-hidden group",
                                                        activeSegment === i ? "bg-primary/5 border-primary/30" : "bg-white/2 border-white/5"
                                                    )}
                                                >
                                                    <div className="flex justify-between items-center mb-2">
                                                        <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">SEGMENT_{i+1}</span>
                                                        <span className="text-[8px] font-bold text-primary">{seg.duration}S</span>
                                                    </div>
                                                    <p className="text-[10px] text-zinc-400 leading-relaxed italic line-clamp-2">"{seg.text}"</p>
                                                    {activeSegment === i && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />}
                                                </div>
                                            ))}
                                        </div>

                                        <div className="space-y-4">
                                            <div className="flex gap-4">
                                                <button className="flex-1 h-12 bg-white/2 border border-white/5 flex items-center justify-center gap-2 text-[9px] font-bold text-zinc-400 hover:text-white transition-colors">
                                                    <Mic2 className="h-3 w-3" /> Voice_Clone
                                                </button>
                                                <button className="flex-1 h-12 bg-white/2 border border-white/5 flex items-center justify-center gap-2 text-[9px] font-bold text-zinc-400 hover:text-white transition-colors">
                                                    <Globe className="h-3 w-3" /> Localize
                                                </button>
                                            </div>
                                            <button 
                                                onClick={handleCommitRender}
                                                disabled={isGenerating}
                                                className="action-primary w-full py-6 text-[10px] tracking-[0.2em] font-bold flex items-center justify-center gap-3"
                                            >
                                                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4 fill-current" />}
                                                COMMIT_NEURAL_RENDER
                                            </button>
                                        </div>
                                    </motion.section>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Real-Time Preview Area */}
                        <div className="xl:col-span-8 space-y-8">
                            <section className="surface-glass p-6 rounded-[2.5rem] bg-black/40 border border-white/5 h-full min-h-[600px] flex flex-col">
                                <div className="flex items-center justify-between mb-6 px-4">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-2xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                                            <Play className="h-5 w-5 fill-current" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-white uppercase tracking-tight">Production_Monitor</h3>
                                            <p className="text-[9px] font-medium text-zinc-600 uppercase tracking-widest">Neural_Layer: {step === 1 ? "CONCEPTUAL" : "LOGICAL"}</p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <div className="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-[8px] font-bold uppercase">Ready</div>
                                    </div>
                                </div>

                                <div className="flex-1 relative bg-zinc-950 rounded-[2rem] overflow-hidden group">
                                    <div className="absolute inset-0 scanline opacity-10 pointer-events-none" />
                                    <img 
                                        src={step === 1 ? "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop" : "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&auto=format&fit=crop"} 
                                        className="w-full h-full object-cover opacity-40 group-hover:scale-105 transition-transform duration-[10s] ease-linear"
                                        alt="Neural Frame"
                                    />
                                    
                                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-12">
                                        {step === 2 && script?.segments?.[activeSegment] && (
                                            <motion.div 
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="space-y-6"
                                            >
                                                <p className="text-3xl md:text-5xl font-black text-white italic leading-tight tracking-tighter drop-shadow-2xl">
                                                    "{script.segments[activeSegment].text}"
                                                </p>
                                                <div className="flex items-center justify-center gap-4">
                                                    <span className="text-[10px] font-bold text-primary uppercase tracking-[0.3em]">Segment_{activeSegment + 1}</span>
                                                    <div className="h-px w-12 bg-primary/30" />
                                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.3em]">{script.segments[activeSegment].visual_prompt}</span>
                                                </div>
                                            </motion.div>
                                        )}

                                        {step === 1 && (
                                            <div className="text-center opacity-30">
                                                <Cpu className="h-16 w-16 text-zinc-700 mx-auto mb-6 animate-pulse" />
                                                <p className="text-[10px] font-bold text-zinc-700 uppercase tracking-[0.3em]">Awaiting Production Logic</p>
                                            </div>
                                        )}
                                    </div>

                                    {/* Overlay HUD */}
                                    <div className="absolute top-8 left-8 space-y-2">
                                        <div className="bg-black/60 backdrop-blur-md px-4 py-2 border border-white/10 rounded-lg">
                                            <p className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest mb-1">FPS</p>
                                            <p className="text-xs font-bold text-white">60.00</p>
                                        </div>
                                        <div className="bg-black/60 backdrop-blur-md px-4 py-2 border border-white/10 rounded-lg">
                                            <p className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Bitrate</p>
                                            <p className="text-xs font-bold text-white">12.4 Mbps</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-8 flex items-center justify-between px-4">
                                    <div className="flex gap-4">
                                        <button className="h-12 w-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all">
                                            <ChevronLeft className="h-5 w-5 text-zinc-600" />
                                        </button>
                                        <button className="h-12 w-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all text-primary">
                                            <Play className="h-5 w-5 fill-current" />
                                        </button>
                                        <button className="h-12 w-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all">
                                            <ChevronRight className="h-5 w-5 text-zinc-600" />
                                        </button>
                                    </div>
                                    <div className="font-data-mono text-[10px] text-zinc-600 uppercase tracking-widest">
                                        PRD_READY // SYNC_LOCK: TRUE
                                    </div>
                                </div>
                            </section>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

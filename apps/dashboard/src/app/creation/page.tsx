"use client";

import React, { useState, useCallback, useEffect } from "react";
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
    Network
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useNiches } from "@/hooks/useNiches";

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
            toast.error("Enter a topic first");
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
            toast.success("Script synthesized successfully");
        } catch (err) {
            console.error(err);
            toast.error("Neural link failed");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleLaunchCinema = async () => {
        if (!topic) {
            toast.error("Enter a topic first");
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
            toast.success("Cinema sequence initiated");
        } catch (err) {
            console.error(err);
            toast.error("System override required");
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
            toast.success("Vocal pattern synthesized");
        } catch (err) {
            console.error(err);
            toast.error("Audio engine failed");
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
            toast.success("Visual assets retrieved");
        } catch (err) {
            console.error(err);
            toast.error("Archive link failure");
        } finally {
            setLoadingSegment(null);
        }
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-[#08080a] relative overflow-hidden flex flex-col">
                {/* Background Cyber Grid */}
                <div className="absolute inset-0 cyber-grid opacity-20 pointer-events-none" />
                
                {/* Scanline Overlay */}
                <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

                <div className="flex-1 section-container relative py-12 px-6 lg:px-12 max-w-7xl mx-auto w-full">
                    {/* Header */}
                    <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
                        <div>
                            <motion.h1 
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="text-5xl md:text-7xl font-black text-white uppercase tracking-tighter mb-2 neon-text-cyan"
                            >
                                Creation Suite
                            </motion.h1>
                            <motion.p 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.2 }}
                                className="font-data-mono text-cyan-400/60 uppercase flex items-center gap-3"
                            >
                                <Terminal className="h-3 w-3" />
                                Neural Content Engineering Terminal v3.0.4
                            </motion.p>
                        </div>

                        {/* Cinema Mode Switch */}
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="surface-glass rim-light p-4 flex items-center gap-6"
                        >
                            <div className="flex items-center gap-3">
                                <Film className={cn("h-4 w-4 transition-colors", cinemaMode ? "text-cyan-400" : "text-zinc-600")} />
                                <span className="font-label-caps text-xs text-white">Cinema Mode</span>
                            </div>
                            <button 
                                onClick={() => setCinemaMode(!cinemaMode)}
                                className={cn(
                                    "w-12 h-6 rounded-full transition-all relative p-1",
                                    cinemaMode ? "bg-cyan-500/20" : "bg-zinc-800"
                                )}
                            >
                                <motion.div 
                                    animate={{ x: cinemaMode ? 24 : 0 }}
                                    className={cn(
                                        "w-4 h-4 rounded-full shadow-lg",
                                        cinemaMode ? "bg-cyan-400" : "bg-zinc-500"
                                    )}
                                />
                            </button>
                        </motion.div>
                    </header>

                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
                        {/* Control Panel */}
                        <div className="xl:col-span-4 space-y-8">
                            <section className="surface-glass rim-light p-8 space-y-8 relative group">
                                <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-100 transition-opacity">
                                    <Dna className="h-4 w-4 text-cyan-400" />
                                </div>
                                
                                <h2 className="font-label-caps text-cyan-400 mb-6 flex items-center gap-2">
                                    <Cpu className="h-4 w-4" />
                                    Input Parameters
                                </h2>

                                <div className="space-y-6">
                                    {/* Topic */}
                                    <div className="space-y-2">
                                        <label className="font-label-caps text-[10px] text-zinc-500">Target Objective</label>
                                        <div className="relative">
                                            <input 
                                                value={topic}
                                                onChange={(e) => setTopic(e.target.value)}
                                                placeholder="Enter neural seed..."
                                                className="w-full bg-black/40 border border-white/5 p-4 text-white font-body-base focus:border-cyan-400/50 transition-all outline-none"
                                            />
                                            <Brain className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-700" />
                                        </div>
                                    </div>

                                    {/* Niche & Style */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="font-label-caps text-[10px] text-zinc-500">Niche</label>
                                            <select 
                                                value={niche}
                                                onChange={(e) => setNiche(e.target.value)}
                                                className="w-full bg-black/40 border border-white/5 p-4 text-white font-label-caps text-[10px] outline-none"
                                            >
                                                {niches.map(n => <option key={n} value={n}>{n}</option>)}
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="font-label-caps text-[10px] text-zinc-500">Style</label>
                                            <select 
                                                value={style}
                                                onChange={(e) => setStyle(e.target.value)}
                                                className="w-full bg-black/40 border border-white/5 p-4 text-white font-label-caps text-[10px] outline-none"
                                            >
                                                {availableStyles.map(s => <option key={s} value={s.toLowerCase()}>{s}</option>)}
                                            </select>
                                        </div>
                                    </div>

                                    {/* Duration */}
                                    <div className="space-y-4 pt-4">
                                        <div className="flex justify-between items-center">
                                            <label className="font-label-caps text-[10px] text-zinc-500">Output Duration</label>
                                            <span className="font-data-mono text-cyan-400 text-sm">{duration}s</span>
                                        </div>
                                        <input 
                                            type="range"
                                            min="15"
                                            max="60"
                                            value={duration}
                                            onChange={(e) => setDuration(parseInt(e.target.value))}
                                            className="w-full"
                                        />
                                    </div>
                                </div>

                                <button 
                                    onClick={cinemaMode ? handleLaunchCinema : handleGenerateScript}
                                    disabled={isGenerating || isCinemaLaunching || !topic}
                                    className="w-full action-primary py-6 mt-8 flex items-center justify-center gap-4 group overflow-hidden relative"
                                >
                                    <span className="relative z-10 font-black tracking-widest uppercase">
                                        {isGenerating || isCinemaLaunching ? "Synthesizing..." : cinemaMode ? "Launch Cinema" : "Generate Script"}
                                    </span>
                                    {isGenerating || isCinemaLaunching ? (
                                        <RefreshCw className="h-5 w-5 animate-spin relative z-10" />
                                    ) : (
                                        <Zap className="h-5 w-5 relative z-10 group-hover:scale-125 transition-transform" />
                                    )}
                                    <motion.div 
                                        className="absolute inset-0 bg-white/20 translate-x-[-100%]"
                                        whileHover={{ translateX: "100%" }}
                                        transition={{ duration: 0.5 }}
                                    />
                                </button>
                            </section>

                            {/* Status Terminal */}
                            <div className="surface-glass rim-light p-6 font-data-mono text-[10px] space-y-2">
                                <p className="text-zinc-600 flex items-center gap-2">
                                    <span className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse" />
                                    AI Engine V4 ACTIVE
                                </p>
                                <p className="text-zinc-600 flex items-center gap-2">
                                    <span className="w-1 h-1 bg-cyan-500 rounded-full" />
                                    Neural Resolution: 4K Ultra
                                </p>
                                <p className="text-zinc-600 flex items-center gap-2">
                                    <span className={cn("w-1 h-1 rounded-full", topic ? "bg-emerald-500" : "bg-red-500")} />
                                    Neural Seed: {topic || "Waiting..."}
                                </p>
                            </div>
                        </div>

                        {/* Workspace */}
                        <div className="xl:col-span-8">
                            <div className="surface-glass rim-light min-h-[700px] flex flex-col relative group">
                                {/* Video Preview CRT Effect */}
                                {!script && (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center space-y-6 z-10">
                                        <div className="w-32 h-32 relative">
                                            <motion.div 
                                                animate={{ rotate: 360 }}
                                                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                                                className="absolute inset-0 border-2 border-cyan-400/20 rounded-full border-t-cyan-400"
                                            />
                                            <div className="absolute inset-4 border border-zinc-800 rounded-full flex items-center justify-center">
                                                <Network className="h-12 w-12 text-zinc-800" />
                                            </div>
                                        </div>
                                        <div className="text-center">
                                            <h3 className="font-label-caps text-zinc-500 mb-2">Neural Workspace Ready</h3>
                                            <p className="font-data-mono text-zinc-700 text-[10px]">Awaiting system initialization...</p>
                                        </div>
                                    </div>
                                )}

                                {/* Script Content */}
                                {script && (
                                    <div className="flex-1 flex flex-col">
                                        <div className="p-8 border-b border-white/5 bg-black/20 flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="h-12 w-12 bg-cyan-400/10 flex items-center justify-center border border-cyan-400/20">
                                                    <Dna className="h-6 w-6 text-cyan-400" />
                                                </div>
                                                <div>
                                                    <h3 className="font-label-caps text-xl text-white tracking-tight">Neural Blueprint</h3>
                                                    <p className="font-data-mono text-zinc-500">Retention Optimized Architecture</p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                <button 
                                                    onClick={handleValidateHook}
                                                    disabled={isValidating}
                                                    className="px-6 py-3 border border-cyan-400/20 text-cyan-400 font-label-caps text-[10px] hover:bg-cyan-400/10 transition-all flex items-center gap-2"
                                                >
                                                    {isValidating ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                                                    Analyze Hook
                                                </button>
                                            </div>
                                        </div>

                                        <div className="flex-1 p-10 space-y-12 overflow-y-auto max-h-[800px] custom-scrollbar">
                                            <div className="space-y-4">
                                                <span className="font-label-caps text-cyan-400">Project Master Title</span>
                                                <h2 className="text-4xl font-black text-white uppercase italic tracking-tighter border-l-4 border-cyan-400 pl-6">
                                                    {script.title}
                                                </h2>
                                            </div>

                                            <div className="grid gap-8">
                                                {script.segments?.map((seg, i) => (
                                                    <motion.div 
                                                        key={i}
                                                        initial={{ opacity: 0, y: 20 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        transition={{ delay: i * 0.1 }}
                                                        className="relative p-8 bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all"
                                                    >
                                                        <div className="absolute top-0 right-0 p-4 font-data-mono text-zinc-800">
                                                            #{i + 1}
                                                        </div>
                                                        
                                                        <div className="flex flex-col md:flex-row gap-8">
                                                            <div className="flex-1 space-y-6">
                                                                <div className="flex items-center gap-4">
                                                                    <span className="font-label-caps text-[10px] bg-cyan-400/10 text-cyan-400 px-2 py-1">
                                                                        {seg.type}
                                                                    </span>
                                                                    <span className="font-data-mono text-zinc-600">
                                                                        {seg.duration}s
                                                                    </span>
                                                                </div>
                                                                <p className="text-xl font-medium text-zinc-200 leading-relaxed italic">
                                                                    "{seg.text}"
                                                                </p>
                                                                <div className="flex items-center gap-3 text-zinc-500">
                                                                    <Monitor className="h-4 w-4" />
                                                                    <span className="font-data-mono text-[10px] uppercase tracking-widest">
                                                                        Visual: {seg.visual_cue}
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            <div className="flex md:flex-col gap-2">
                                                                <button 
                                                                    onClick={() => handleSynthesizeAudio(i, seg.text)}
                                                                    className={cn(
                                                                        "p-4 border transition-all",
                                                                        segmentAssets[i]?.audio ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400" : "border-white/5 hover:border-cyan-400/50 text-zinc-500 hover:text-cyan-400"
                                                                    )}
                                                                >
                                                                    {loadingSegment === `audio-${i}` ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5" />}
                                                                </button>
                                                                <button 
                                                                    onClick={() => handleSearchStock(i, seg.visual_cue)}
                                                                    className={cn(
                                                                        "p-4 border transition-all",
                                                                        segmentAssets[i]?.videos ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400" : "border-white/5 hover:border-cyan-400/50 text-zinc-500 hover:text-cyan-400"
                                                                    )}
                                                                >
                                                                    {loadingSegment === `stock-${i}` ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Film className="h-5 w-5" />}
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

                {/* Globalization Sidebar - Floating */}
                {script && (
                    <motion.div 
                        initial={{ opacity: 0, x: 100 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="fixed right-8 top-1/2 -translate-y-1/2 flex flex-col gap-4 z-40 hidden xl:flex"
                    >
                        <div className="surface-glass rim-light p-2 flex flex-col gap-2">
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
                                    title={`Localize to ${lang.name}`}
                                    className="w-12 h-12 flex items-center justify-center font-label-caps text-[10px] text-zinc-500 hover:text-cyan-400 hover:bg-white/5 transition-all border border-transparent hover:border-white/5"
                                >
                                    {lang.code}
                                </button>
                            ))}
                            <div className="h-px bg-white/5 mx-2" />
                            <div className="w-12 h-12 flex items-center justify-center text-zinc-700">
                                <Globe className="h-4 w-4" />
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </DashboardLayout>
    );
}

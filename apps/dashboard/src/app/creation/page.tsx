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
    Globe
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
    const [isCinemaLaunching, setIsCinemaLaunching] = useState(false);

    const [isValidating, setIsValidating] = useState(false);
    const [hookAnalysis, setHookAnalysis] = useState<HookAnalysis | null>(null);
    const [isExporting, setIsExporting] = useState(false);
    const [isLaunchingProduction, setIsLaunchingProduction] = useState(false);
    const [showBlueprintBuilder, setShowBlueprintBuilder] = useState(false);
    const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
    const [selectedBlueprint, setSelectedBlueprint] = useState<Blueprint | null>(null);

    useEffect(() => {
        if (niches && niches.length > 0 && niche === "Motivation") {
            setNiche(niches[0]);
        }
    }, [niches, niche]);

    useEffect(() => {
        const fetchBlueprints = async () => {
            const token = getAuthToken();
            if (!token) return;
            await withRealFallback<Blueprint[]>(
                () => fetch(`${API_BASE}/nexus/blueprints`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                {
                    fallback: [],
                    onSuccess: (data) => setBlueprints(Array.isArray(data) ? data : []),
                    errorMessage: "Failed to load neural recipes"
                }
            );
        };
        fetchBlueprints();
    }, []);

    const handleApplyAlternativeHook = useCallback((newHook: string) => {
        if (!script) return;
        const newSegments = script.segments.map(s => 
            s.type === "hook" ? { ...s, text: newHook } : s
        );
        setScript({ ...script, segments: newSegments });
        setHookAnalysis(null);
        toast.success("Hook Updated", { description: "Neural blueprint synchronized with new hook." });
    }, [script]);

    const handleGenerateScript = useCallback(async () => {
        if (!topic || !niche || !style) return;
        setIsGenerating(true);
        setHookAnalysis(null);
        const token = getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        await withRealFallback<ScriptOutput | null>(
            () => fetch(`${API_BASE}/no-face/generate-script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ topic, niche, style, duration })
            }),
            {
                fallback: null,
                onSuccess: (data) => setScript(data),
                errorMessage: "Neural script engine desynced. Market link unstable."
            }
        );
        setIsGenerating(false);
    }, [topic, niche, style, setHookAnalysis, setIsGenerating]);



    const handleValidateHook = useCallback(async () => {
        if (!script) return;
        const hookSegment = Array.isArray(script.segments) ? script.segments.find(s => s.type === "hook") : null;
        if (!hookSegment) return;

        setIsValidating(true);
        const token = getAuthToken();
        if (!token) {
            setIsValidating(false);
            return;
        }

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/no-face/validate-hook`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ hook: hookSegment.text })
            }),
            {
                fallback: null,
                onSuccess: (data) => setHookAnalysis(data)
            }
        );
        setIsValidating(false);
    }, [script]);

    const handleSynthesizeAudio = useCallback(async (index: number, text: string) => {
        setLoadingSegment(`audio-${index}`);
        const token = getAuthToken();
        if (!token) {
            setLoadingSegment(null);
            return;
        }

        const doRequest = async (): Promise<any> => {
            return await withRealFallback<any>(
                () => fetch(`${API_BASE}/no-face/generate-voiceover`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({ text })
                }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        setSegmentAssets(prev => ({
                            ...prev,
                            [index]: { ...prev[index], audio: data.audio_url || data.url }
                        }));
                    },
                    silent: true
                }
            );
        };

        let result = await doRequest();
        let retries = 0;
        const maxRetries = 2;
        while (!result && retries < maxRetries) {
            retries++;
            const delay = Math.pow(2, retries) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
            result = await doRequest();
        }
        setLoadingSegment(null);
        if (!result) {
            toast.error("Audio synthesis failed", {
                description: `Segment ${index + 1}: Voiceover generation failed after 3 attempts. Please try again or use a different voice.`
            });
        }
    }, [setLoadingSegment, setSegmentAssets]);

    const handleGenerateSegmentImage = useCallback(async (index: number, prompt: string) => {
        setLoadingSegment(`image-${index}`);
        const token = getAuthToken();
        if (!token) {
            setLoadingSegment(null);
            return;
        }

        const doRequest = async (): Promise<any> => {
            return await withRealFallback<any>(
                () => fetch(`${API_BASE}/no-face/generate-image`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({ prompt })
                }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        setSegmentAssets(prev => ({
                            ...prev,
                            [index]: { ...prev[index], image: data.image_url || data.url }
                        }));
                    },
                    silent: true
                }
            );
        };

        let result = await doRequest();
        let retries = 0;
        const maxRetries = 2;
        while (!result && retries < maxRetries) {
            retries++;
            const delay = Math.pow(2, retries) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
            result = await doRequest();
        }
        setLoadingSegment(null);
        if (!result) {
            toast.error("Image generation failed", {
                description: `Segment ${index + 1}: Image creation failed after 3 attempts. Please try again or adjust the prompt.`
            });
        }
    }, [setLoadingSegment, setSegmentAssets]);

    const handleSearchStock = useCallback(async (index: number, query: string) => {
        setLoadingSegment(`stock-${index}`);
        const token = getAuthToken();
        if (!token) {
            setLoadingSegment(null);
            return;
        }

        const doRequest = async (): Promise<any[]> => {
            return await withRealFallback<any[]>(
                () => fetch(`${API_BASE}/no-face/search-stock?query=${encodeURIComponent(query)}`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                {
                    fallback: [],
                    onSuccess: (data) => {
                        setSegmentAssets(prev => ({
                            ...prev,
                            [index]: { ...prev[index], videos: data }
                        }));
                    },
                    silent: true
                }
            );
        };

        let result = await doRequest();
        let retries = 0;
        const maxRetries = 2;
        while (!result || !result.length) {
            if (retries >= maxRetries) break;
            retries++;
            const delay = Math.pow(2, retries) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
            result = await doRequest();
        }
        setLoadingSegment(null);
        if (!result || !result.length) {
            toast.error("Stock video search failed", {
                description: `Segment ${index + 1}: Could not find stock videos after 3 attempts. Try a different query.`
            });
        }
    }, [setLoadingSegment, setSegmentAssets]);

    const handleGlobalize = useCallback(async (lang: string) => {
        if (!script) return;
        setIsGenerating(true);
        const token = getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        await withRealFallback<ScriptSegment[]>(
            () => fetch(`${API_BASE}/no-face/localize`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ segments: script.segments, target_lang: lang })
            }),
            {
                fallback: script.segments,
                onSuccess: (data) => setScript({ ...script, segments: data }),
                errorMessage: "Localization cluster busy. Reverting to primary language."
            }
        );
        setIsGenerating(false);
    }, [script]);

    const handleExportAssets = useCallback(() => {
        if (!script) return;
        setIsExporting(true);
        try {
            const exportData = {
                title: script.title,
                segments: script.segments.map((seg, i) => ({
                    ...seg,
                    audio_url: segmentAssets[i]?.audio || null,
                    image_url: segmentAssets[i]?.image || null,
                    stock_videos: segmentAssets[i]?.videos || []
                })),
                hashtags: script.hashtags,
                metadata: {
                    niche,
                    style,
                    duration,
                    exported_at: new Date().toISOString()
                }
            };
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${script.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_blueprint.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } finally {
            setIsExporting(false);
        }
    }, [script, segmentAssets, niche, style, duration]);

    const handleLaunchProduction = useCallback(async () => {
        if (!script) return;
        if (!selectedBlueprint) {
            toast.warning("No Recipe Selected", {
                description: "Please select a neural recipe or create a custom one."
            });
            return;
        }
        setIsLaunchingProduction(true);
        const token = getAuthToken();
        if (!token) {
            setIsLaunchingProduction(false);
            return;
        }

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/nexus/compose`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    niche,
                    topic,
                    blueprint_id: selectedBlueprint?.id || "story-factory",
                    cinema_mode: false,
                    script_data: {
                        title: script.title,
                        segments: script.segments,
                        hashtags: script.hashtags
                    }
                })
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Production pipeline activated.");
                    window.location.href = "/transformation";
                }
            }
        );
        setIsLaunchingProduction(false);
    }, [script, niche, topic, selectedBlueprint]);

    const handleLaunchCinema = useCallback(async () => {
        if (!topic) return;
        setIsCinemaLaunching(true);
        const token = getAuthToken();
        if (!token) {
            setIsCinemaLaunching(false);
            return;
        }

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/nexus/compose`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    niche,
                    topic,
                    cinema_mode: true
                })
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Cinema Mode: Autonomous production launched.");
                    window.location.href = "/transformation";
                }
            }
        );
        setIsCinemaLaunching(false);
    }, [topic, niche]);

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-end justify-between mb-12">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Intelligence Hub</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">Creation <span className="text-transparent bg-clip-text bg-linear-to-r from-violet-500 to-fuchsia-500 text-hollow">Suite</span></h1>
                        <p className="text-zinc-500 font-medium">Engineer high-velocity <span className="text-zinc-300 font-bold">faceless content</span> with neural script generation.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Input Controls */}
                    <div className="space-y-8">
                        <div className="glass-card space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity) pointer-events-none" />
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label htmlFor="topic" className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Objective / Topic</label>
                                    <div className="relative group">
                                        <Target className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-600 group-focus-within:text-primary transition-all" />
                                        <input
                                            id="topic"
                                            name="topic"
                                            value={topic}
                                            onChange={(e) => setTopic(e.target.value)}
                                            placeholder="The History of Quantum AI..."
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-5 pl-16 pr-6 focus:outline-none focus:ring-1 focus:ring-primary/40 text-base font-bold text-white placeholder:text-zinc-700 transition-all"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label htmlFor="niche" className="text-xs font-black uppercase tracking-widest text-zinc-500 ml-2">Niche</label>
                                        <div className="relative group">
                                            <select
                                                id="niche"
                                                name="niche"
                                                value={niche}
                                                onChange={(e) => setNiche(e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-5 pr-12 focus:outline-none focus:ring-1 focus:ring-primary/40 text-base font-bold uppercase tracking-wide text-zinc-300 appearance-none cursor-pointer hover:bg-zinc-900/50 transition-all"
                                            >
                                                {isLoadingNiches ? (
                                                    <option disabled>Loading...</option>
                                                ) : niches.length > 0 ? (
                                                    niches.map(n => <option key={n} value={n}>{n}</option>)
                                                ) : (
                                                    <option value="Motivation">Motivation</option>
                                                )}
                                            </select>
                                            <ChevronDown className="absolute right-5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600 group-hover:text-primary pointer-events-none transition-all" />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-xs font-black uppercase tracking-widest text-zinc-500 ml-2">Style</label>
                                        <div className="relative group">
                                            <select
                                                value={style}
                                                onChange={(e) => setStyle(e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-5 pr-12 focus:outline-none focus:ring-1 focus:ring-primary/40 text-base font-bold uppercase tracking-wide text-zinc-300 appearance-none cursor-pointer hover:bg-zinc-900/50 transition-all"
                                            >
                                                {availableStyles.map(s => <option key={s} value={s.toLowerCase()}>{s}</option>)}
                                            </select>
                                            <ChevronDown className="absolute right-5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600 group-hover:text-primary pointer-events-none transition-all" />
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label htmlFor="duration" className="text-xs font-black uppercase tracking-widest text-zinc-500 ml-2">Duration: {duration}s</label>
                                    <input
                                        id="duration"
                                        name="duration"
                                        type="range"
                                        min="15"
                                        max="60"
                                        step="1"
                                        value={duration}
                                        onChange={(e) => setDuration(parseInt(e.target.value))}
                                        className="w-full h-1.5 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-primary"
                                    />
                                </div>

                                <div className="p-4 rounded-xl border border-white/5 bg-zinc-950/20 flex items-center justify-between group hover:border-violet-500/30 transition-all cursor-pointer" onClick={() => setCinemaMode(!cinemaMode)}>
                                    <div className="flex items-center gap-3">
                                        <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center transition-all", cinemaMode ? "bg-violet-500/20 text-violet-500" : "bg-zinc-900 text-zinc-700")}>
                                            <Film className="h-4 w-4" />
                                        </div>
                                        <div className="space-y-0.5">
                                            <p className="text-xs font-black uppercase tracking-tight text-white group-hover:text-violet-400 transition-colors">Cinema Mode</p>
                                            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Fully Autonomous</p>
                                        </div>
                                    </div>
                                    <div className={cn("w-10 h-5 rounded-full relative transition-all duration-500", cinemaMode ? "bg-violet-600" : "bg-zinc-800")}>
                                        <motion.div
                                            animate={{ x: cinemaMode ? 20 : 2 }}
                                            className="absolute top-1 left-0 h-3 w-3 rounded-full bg-white shadow-sm"
                                        />
                                    </div>
                                </div>
                                </div>

                                {/* Blueprint Selection */}
                                <div className="glass-card p-6 rounded-2xl space-y-4 mb-8">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-violet-500/10 flex items-center justify-center border border-violet-500/20">
                                                <Cpu className="h-5 w-5 text-violet-500" />
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-black uppercase tracking-tight text-white">Neural Recipe</h3>
                                                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Select processing pipeline</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setShowBlueprintBuilder(true)}
                                            className="px-4 py-2 bg-violet-500/10 border border-violet-500/20 rounded-lg text-xs font-black text-violet-400 hover:bg-violet-500/20 transition-all"
                                        >
                                            Create Recipe
                                        </button>
                                    </div>
                                    
                                    <div className="grid grid-cols-2 gap-3">
                                        {blueprints.length === 0 ? (
                                            <p className="text-zinc-500 text-sm col-span-2">No recipes found. Create your first neural recipe.</p>
                                        ) : (
                                            blueprints.map((bp) => (
                                                <div
                                                    key={bp.id}
                                                    onClick={() => setSelectedBlueprint(bp)}
                                                    className={cn(
                                                        "p-4 rounded-xl border cursor-pointer transition-all",
                                                        selectedBlueprint?.id === bp.id
                                                            ? "bg-violet-500/10 border-violet-500/40"
                                                            : "bg-white/2 border-white/5 hover:border-white/10"
                                                    )}
                                                >
                                                    <p className="text-sm font-bold text-white">{bp.name}</p>
                                                    <p className="text-[10px] text-zinc-500 line-clamp-1">{bp.description}</p>
                                                    <p className="text-[9px] text-zinc-600 mt-2">Composition: {bp.composition_id}</p>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>

                            <motion.button
                                whileHover={{ scale: 1.02, y: -4 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={cinemaMode ? handleLaunchCinema : handleGenerateScript}
                                disabled={isGenerating || isCinemaLaunching || !topic}
                                className={cn(
                                    "w-full font-black py-5 rounded-xl transition-all flex items-center justify-center gap-3 uppercase text-sm tracking-widest",
                                    cinemaMode ? "bg-violet-600 hover:bg-violet-500 shadow-[0_0_40px_rgba(139,92,246,0.3)] text-white" : "bg-primary hover:bg-primary/90 shadow-[0_0_40px_rgba(var(--primary-rgb),0.3)] text-white"
                                )}
                            >
                                {isGenerating || isCinemaLaunching ? <RefreshCw className="h-5 w-5 animate-spin" /> : cinemaMode ? <Zap className="h-5 w-5" /> : <Wand2 className="h-5 w-5" />}
                                {isGenerating || isCinemaLaunching ? "Synthesizing..." : cinemaMode ? "Launch Cinema Production" : "Generate Script"}
                            </motion.button>
                        </div>

                        {/* Analysis Insights */}
                        <AnimatePresence>
                            {hookAnalysis && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "glass-card p-8 rounded-4xl space-y-6 relative overflow-hidden border",
                                        hookAnalysis.status === "KILL" ? "border-red-500/20 bg-red-500/5" : "border-emerald-500/20 bg-emerald-500/5"
                                    )}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            {hookAnalysis.status === "KILL" ? (
                                                <ShieldAlert className="h-5 w-5 text-red-500" />
                                            ) : (
                                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                            )}
                                            <span className={cn(
                                                "text-[10px] font-black uppercase tracking-[0.2em]",
                                                hookAnalysis.status === "KILL" ? "text-red-500" : "text-emerald-500"
                                            )}>
                                                {hookAnalysis.status === "KILL" ? "Neural Kill-Switch Activated" : "Hook Validated"}
                                            </span>
                                        </div>
                                        <span className="text-2xl font-black text-white">{hookAnalysis.score}%</span>
                                    </div>
                                    <p className="text-zinc-400 text-xs leading-relaxed font-medium">
                                        "{hookAnalysis.analysis}"
                                    </p>

                                    {hookAnalysis.status === "KILL" && (
                                        <div className="space-y-4 pt-2">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Suggested Pivots:</p>
                                            {hookAnalysis.alternatives?.map((alt: string, i: number) => (
                                                <div 
                                                    key={i} 
                                                    onClick={() => handleApplyAlternativeHook(alt)}
                                                    className="p-4 bg-zinc-950/80 rounded-xl border border-white/5 text-[11px] font-bold text-zinc-300 group hover:border-primary/40 transition-all cursor-pointer"
                                                >
                                                    {alt}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Script Workspace */}
                    <div className="lg:col-span-2 space-y-8">
                        <div className="glass-card overflow-hidden min-h-[600px] flex flex-col shadow-2xl relative">
                            <div className="absolute inset-0 scanline opacity-(--scanline-opacity) pointer-events-none" />
                            <div className="p-8 border-b border-white/5 bg-white/2 flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                        <Edit3 className="h-5 w-5 text-primary neon-glow" />
                                    </div>
                                    <div className="space-y-0.5">
                                        <h3 className="font-black uppercase tracking-tight text-white">Neural Blueprint</h3>
                                        <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Script & Retention Architecture</p>
                                    </div>
                                </div>
                                {script && (
                                    <div className="flex flex-wrap gap-2">
                                        {[
                                            { code: "ES", name: "Spanish" },
                                            { code: "DE", name: "German" },
                                            { code: "FR", name: "French" },
                                            { code: "IT", name: "Italian" },
                                            { code: "PT", name: "Portuguese" },
                                            { code: "JP", name: "Japanese" },
                                            { code: "ZH", name: "Chinese" }
                                        ].map(lang => (
                                            <button
                                                key={lang.code}
                                                onClick={() => handleGlobalize(lang.name)}
                                                className="px-3 py-2 rounded-lg bg-zinc-900 border border-white/5 text-[8px] font-black uppercase tracking-[0.2em] text-zinc-500 hover:text-white hover:border-primary/50 transition-all flex items-center gap-1.5"
                                            >
                                                <Globe className="h-2.5 w-2.5" />
                                                {lang.code}
                                            </button>
                                        ))}
                                        <button
                                            onClick={handleValidateHook}
                                            disabled={isValidating}
                                            className="glass-card hover:border-primary/50 text-zinc-400 hover:text-white text-[10px] font-black py-3 px-6 rounded-xl transition-all flex items-center gap-2 uppercase tracking-widest ml-auto"
                                        >
                                            {isValidating ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Sparkles className="h-3 w-3" />}
                                            Analyze Retention
                                        </button>
                                    </div>
                                )}
                            </div>

                            <div className="flex-1 p-10 space-y-10">
                                {script ? (
                                    <div className="space-y-12">
                                        <div className="space-y-2">
                                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Viral Title</span>
                                            <h2 className="text-3xl font-black text-white uppercase tracking-tighter">{script.title}</h2>
                                            {script.emotional_arc && (
                                                <div className="flex items-center gap-3 pt-2">
                                                    <Target className="h-3 w-3 text-zinc-600" />
                                                    <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-[0.2em]">{script.emotional_arc}</span>
                                                </div>
                                            )}
                                        </div>

                                        <div className="space-y-10">
                                            {Array.isArray(script.segments) && script.segments.map((seg, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    whileHover={{ x: 5 }}
                                                    transition={{
                                                        delay: i * 0.1,
                                                        x: { type: "spring", stiffness: 400, damping: 25 }
                                                    }}
                                                    className="relative pl-12 group"
                                                >
                                                    <div className="absolute left-0 top-0 bottom-0 w-px bg-white/5 group-hover:bg-primary/40 transition-all" />
                                                    <div className="absolute left-[-4px] top-0 h-2 w-2 rounded-full bg-zinc-800 group-hover:bg-primary transition-all" />

                                                    <div className="space-y-4">
                                                        <div className="flex items-center gap-4">
                                                            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">{seg.type}</span>
                                                            <span className="text-[10px] font-mono text-zinc-800 tracking-tighter">{seg.duration} SEC</span>
                                                        </div>
                                                        <p className="text-lg font-bold text-zinc-200 leading-relaxed">{seg.text}</p>

                                                        <div className="flex flex-wrap gap-3 items-center">
                                                            <div className="flex items-center gap-3 bg-zinc-950/40 p-3 rounded-xl border border-white/5 w-fit">
                                                                <Film className="h-3 w-3 text-zinc-500" />
                                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{seg.visual_cue}</span>
                                                            </div>
                                                            {seg.tone && (
                                                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/5 border border-primary/20">
                                                                    <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                                                                    <span className="text-[8px] font-black uppercase tracking-widest text-primary">{seg.tone}</span>
                                                                </div>
                                                            )}
                                                            {seg.visual_style && (
                                                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/5 border border-violet-500/20">
                                                                    <Zap className="h-2.5 w-2.5 text-violet-500" />
                                                                    <span className="text-[8px] font-black uppercase tracking-widest text-violet-400">{seg.visual_style}</span>
                                                                </div>
                                                            )}
                                                            {seg.pattern_interrupt && (
                                                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-500/5 border border-orange-500/20">
                                                                    <RefreshCw className="h-2.5 w-2.5 text-orange-500" />
                                                                    <span className="text-[8px] font-black uppercase tracking-widest text-orange-400">{seg.pattern_interrupt}</span>
                                                                </div>
                                                            )}
                                                        </div>

                                                        <div className="flex gap-2">
                                                             <button
                                                                 onClick={() => handleSynthesizeAudio(i, seg.text)}
                                                                 aria-label={`Generate audio for segment ${i + 1}`}
                                                                 className={cn(
                                                                     "p-2.5 rounded-lg border border-white/5 hover:border-primary/40 transition-all group/btn",
                                                                     segmentAssets[i]?.audio ? "bg-emerald-500/10 border-emerald-500/20" : "bg-zinc-900/50"
                                                                 )}
                                                             >
                                                                {loadingSegment === `audio-${i}` ? <RefreshCw className="h-4 w-4 animate-spin text-primary" /> : <Zap className={cn("h-4 w-4 transition-colors", segmentAssets[i]?.audio ? "text-emerald-500" : "text-zinc-600 group-hover/btn:text-primary")} />}
                                                            </button>
                                                            <button
                                                                onClick={() => handleSearchStock(i, seg.visual_cue)}
                                                                className={cn(
                                                                    "p-2.5 rounded-lg border border-white/5 hover:border-primary/40 transition-all group/btn",
                                                                    segmentAssets[i]?.videos ? "bg-emerald-500/10 border-emerald-500/20" : "bg-zinc-900/50"
                                                                )}
                                                            >
                                                                {loadingSegment === `stock-${i}` ? <RefreshCw className="h-4 w-4 animate-spin text-primary" /> : <Film className={cn("h-4 w-4 transition-colors", segmentAssets[i]?.videos ? "text-emerald-500" : "text-zinc-600 group-hover/btn:text-primary")} />}
                                                            </button>
                                                             <button
                                                                 onClick={() => handleGenerateSegmentImage(i, seg.visual_cue)}
                                                                 aria-label={`Generate image for segment ${i + 1}`}
                                                                 className={cn(
                                                                     "p-2.5 rounded-lg border border-white/5 hover:border-primary/40 transition-all group/btn",
                                                                     segmentAssets[i]?.image ? "bg-emerald-500/10 border-emerald-500/20" : "bg-zinc-900/50"
                                                                 )}
                                                             >
                                                                {loadingSegment === `image-${i}` ? <RefreshCw className="h-4 w-4 animate-spin text-primary" /> : <Wand2 className={cn("h-4 w-4 transition-colors", segmentAssets[i]?.image ? "text-emerald-500" : "text-zinc-600 group-hover/btn:text-primary")} />}
                                                            </button>
                                                        </div>

                                                        {/* Asset Previews */}
                                                        <div className="flex gap-4">
                                                            {segmentAssets[i]?.audio && (
                                                                <div className="flex items-center gap-3 p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
                                                                    <Play className="h-3 w-3 text-emerald-500" />
                                                                    <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">WAV Ready</span>
                                                                </div>
                                                            )}
                                                            {segmentAssets[i]?.image && (
                                                                <div className="h-16 w-16 rounded-xl border border-emerald-500/20 overflow-hidden shadow-lg">
                                                                    <img src={`${API_BASE}/static/${segmentAssets[i].image}`} className="w-full h-full object-cover" />
                                                                </div>
                                                            )}
                                                            {segmentAssets[i]?.videos && (
                                                                <div className="flex gap-2">
                                                                    {segmentAssets[i].videos.slice(0, 2).map((v: any, j: number) => (
                                                                        <div key={j} className="h-16 w-12 rounded-lg border border-emerald-500/20 overflow-hidden relative group/v">
                                                                            <img src={v.preview} className="w-full h-full object-cover" />
                                                                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/v:opacity-100 flex items-center justify-center transition-all">
                                                                                <Plus className="h-4 w-4 text-white" />
                                                                            </div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>

                                        <div className="flex flex-wrap gap-2 pt-8">
                                            {script.hashtags.map((tag, i) => (
                                                <span key={i} className="text-[10px] font-black tracking-widest text-primary uppercase py-2 px-4 rounded-lg bg-primary/5 border border-primary/10">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>

                                        <div className="pt-10 flex gap-4">
                                            <button
                                                onClick={handleExportAssets}
                                                disabled={isExporting}
                                                className="flex-1 bg-white/5 hover:bg-white/10 text-zinc-400 font-black py-5 rounded-2xl transition-all uppercase text-xs tracking-[0.2em] border border-white/5"
                                            >
                                                {isExporting ? "Exporting..." : "Export Assets"}
                                            </button>
                                            <motion.button
                                                whileHover={{ scale: 1.05, y: -2 }}
                                                whileTap={{ scale: 0.98 }}
                                                onClick={handleLaunchProduction}
                                                disabled={isLaunchingProduction}
                                                className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white font-black py-5 rounded-2xl transition-all shadow-[0_0_40px_rgba(16,185,129,0.2)] flex items-center justify-center gap-3 uppercase text-xs tracking-[0.2em]"
                                            >
                                                <Zap className="h-5 w-5" />
                                                {isLaunchingProduction ? "Launching..." : "Launch Production"}
                                            </motion.button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-30">
                                        <div className="relative">
                                            <Cpu className="h-24 w-24 text-zinc-800" />
                                            {isGenerating && <RefreshCw className="absolute inset-0 h-24 w-24 text-primary animate-spin opacity-40" />}
                                        </div>
                                        <p className="text-xs font-black uppercase tracking-[0.3em] text-zinc-700">Waiting for Neutral Input...</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Blueprint Builder Modal */}
            <BlueprintBuilder
                isOpen={showBlueprintBuilder}
                onClose={() => setShowBlueprintBuilder(false)}
                onSuccess={(newBlueprint) => {
                    setBlueprints(prev => [...prev, newBlueprint]);
                    setSelectedBlueprint(newBlueprint);
                    setShowBlueprintBuilder(false);
                    toast.success("Recipe Created", {
                        description: `'${newBlueprint.name}' is now available.`
                    });
                }}
            />
        </DashboardLayout>
    );
}

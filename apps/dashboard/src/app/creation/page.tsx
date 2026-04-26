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
        if (!topic || !niche || !style) {
            toast.error("Missing Information", {
                description: "Please provide an Objective/Topic to generate the script."
            });
            return;
        }
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
    }, [topic, niche, style, duration, setScript, setHookAnalysis, setIsGenerating]);



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
            setIsLaunchingProduction(false);
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
        if (!topic) {
            toast.error("Missing Topic", {
                description: "Please provide an Objective/Topic to launch Cinema Mode."
            });
            return;
        }
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
                <div className="mb-lg">
                    <h1 className="font-display-lg text-display-lg text-white mb-xs uppercase">Creation Suite</h1>
                    <p className="font-data-mono text-data-mono text-outline uppercase tracking-widest text-zinc-500">Engineer high-velocity faceless content</p>
                </div>

                {/* Cinema Mode Toggle */}
                <div className="flex items-center justify-between mb-lg p-md surface-glass rim-light">
                    <div className="flex items-center gap-sm">
                        <span className="material-symbols-outlined text-cyan-400">movie</span>
                        <span className="font-label-caps text-label-caps uppercase text-white">Cinema Mode</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input checked={cinemaMode} onChange={() => setCinemaMode(!cinemaMode)} className="sr-only peer" type="checkbox" />
                        <div className="w-11 h-6 bg-surface-container-highest peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-container"></div>
                    </label>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Input Controls */}
                    <div className="space-y-lg">
                        <div className="grid grid-cols-1 gap-md">
                            {/* Objective/Topic */}
                            <div className="flex flex-col gap-xs">
                                <label htmlFor="topic" className="font-label-caps text-label-caps text-outline-variant uppercase text-zinc-500">Objective / Topic</label>
                                <div className="surface-glass rim-light p-xs flex items-center">
                                    <span className="material-symbols-outlined px-sm text-cyan-400/50">psychology</span>
                                    <input
                                        id="topic"
                                        name="topic"
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        className="bg-transparent border-none w-full text-white placeholder-white/20 font-body-base py-sm focus:ring-0"
                                        placeholder="Quantum Computing Basics"
                                        type="text"
                                    />
                                </div>
                            </div>
                            
                            {/* Niche */}
                            <div className="flex flex-col gap-xs">
                                <label htmlFor="niche" className="font-label-caps text-label-caps text-outline-variant uppercase text-zinc-500">Niche</label>
                                <div className="surface-glass rim-light p-xs flex items-center">
                                    <span className="material-symbols-outlined px-sm text-cyan-400/50">category</span>
                                    <select
                                        id="niche"
                                        name="niche"
                                        value={niche}
                                        onChange={(e) => setNiche(e.target.value)}
                                        className="bg-transparent border-none w-full text-white font-body-base py-sm focus:ring-0 appearance-none [&>option]:bg-surface"
                                    >
                                        {isLoadingNiches ? (
                                            <option disabled>Loading...</option>
                                        ) : niches.length > 0 ? (
                                            niches.map(n => <option key={n} value={n}>{n}</option>)
                                        ) : (
                                            <option value="Motivation">Motivation</option>
                                        )}
                                    </select>
                                </div>
                            </div>

                            {/* Style */}
                            <div className="flex flex-col gap-xs">
                                <label className="font-label-caps text-label-caps text-outline-variant uppercase text-zinc-500">Style</label>
                                <div className="surface-glass rim-light p-xs flex items-center">
                                    <span className="material-symbols-outlined px-sm text-cyan-400/50">palette</span>
                                    <select
                                        value={style}
                                        onChange={(e) => setStyle(e.target.value)}
                                        className="bg-transparent border-none w-full text-white font-body-base py-sm focus:ring-0 appearance-none [&>option]:bg-surface"
                                    >
                                        {availableStyles.map(s => <option key={s} value={s.toLowerCase()}>{s}</option>)}
                                    </select>
                                </div>
                            </div>

                            {/* Duration Slider */}
                            <div className="flex flex-col gap-sm py-sm">
                                <div className="flex justify-between items-center">
                                    <label htmlFor="duration" className="font-label-caps text-label-caps text-outline-variant uppercase text-zinc-500">Duration</label>
                                    <span className="font-data-mono text-data-mono text-cyan-400">{duration}s</span>
                                </div>
                                <input
                                    id="duration"
                                    name="duration"
                                    type="range"
                                    min="15"
                                    max="60"
                                    step="1"
                                    value={duration}
                                    onChange={(e) => setDuration(parseInt(e.target.value))}
                                    className="w-full"
                                />
                            </div>
                        </div>

                        {/* Visualization / Preview Area (Bento Component) */}
                        <div className="grid grid-cols-2 gap-gutter">
                            <div className="surface-glass rim-light p-md col-span-2 aspect-video flex flex-col justify-end relative overflow-hidden">
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10"></div>
                                <img alt="Data stream" className="absolute inset-0 w-full h-full object-cover opacity-60" src="https://lh3.googleusercontent.com/aida-public/AB6AXuD-FrlreC3nNUT6-A3Bge55Oz0cI4Nxn_QrFNnVgfcw8f5YCqdiQ5YIrRTDGDl7Q7kDUVFnqffQ7bQyY9uhjHg5NYML-2InmRTMSOLCW1zfJq6NFYQ86YpMSrZHYEA-F2EV0lOa0Qu9uldAS4opInFC4r6i1BgiDpxBwSsaBvIQLzGLAdmPqg9AP4WXMftMdU4bZfhg9arjoka9lpquLB5zvNmxuInu-ieki0mORkz6Wu1BbmvJBRmdVy-_5fxuSFiWlHGClY3wuoPm" />
                                <div className="relative z-20">
                                    <div className="flex items-center gap-xs mb-xs">
                                        <span className="w-2 h-2 bg-cyan-400 shadow-[0_0_5px_#00fbfb]"></span>
                                        <span className="font-label-caps text-[10px] text-cyan-400 uppercase tracking-widest">System Ready</span>
                                    </div>
                                    <p className="font-data-mono text-xs text-white/70">Engine initialized for high-velocity output...</p>
                                </div>
                            </div>
                            <div className="surface-glass rim-light p-md flex flex-col items-center justify-center gap-xs">
                                <span className="font-display-lg text-headline-md text-white">4K</span>
                                <span className="font-label-caps text-[10px] text-outline-variant uppercase text-zinc-500">Resolution</span>
                            </div>
                            <div className="surface-glass rim-light p-md flex flex-col items-center justify-center gap-xs">
                                <span className="font-display-lg text-headline-md text-white">AI</span>
                                <span className="font-label-caps text-[10px] text-outline-variant uppercase text-zinc-500">Engine V4</span>
                            </div>
                        </div>

                        {/* Generate Button */}
                        <button
                            onClick={cinemaMode ? handleLaunchCinema : handleGenerateScript}
                            disabled={isGenerating || isCinemaLaunching || !topic}
                            className="w-full py-lg mt-md action-primary rounded-none flex items-center justify-center gap-sm active:scale-95 duration-200 group"
                        >
                            <span className="font-label-caps text-headline-md text-black uppercase tracking-tighter">
                                {isGenerating || isCinemaLaunching ? "SYNTHESIZING..." : cinemaMode ? "LAUNCH CINEMA" : "GENERATE SCRIPT"}
                            </span>
                            {isGenerating || isCinemaLaunching ? (
                                <RefreshCw className="h-6 w-6 text-black animate-spin" />
                            ) : (
                                <span className="material-symbols-outlined text-black group-hover:translate-x-1 transition-transform">bolt</span>
                            )}
                        </button>
                        
                        {/* Analysis Insights */}
                        <AnimatePresence>
                            {hookAnalysis && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "surface-glass p-8 rounded-4xl space-y-6 relative overflow-hidden border",
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
                                                    className="p-4 bg-zinc-950/80 rounded-xl border border-white/5 text-[11px] font-bold text-zinc-300 group hover:border-cyan-400/40 transition-all cursor-pointer"
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
                    <div className="lg:col-span-2 space-y-lg">
                        <div className="surface-glass rim-light overflow-hidden min-h-[600px] flex flex-col relative">
                            <div className="p-md border-b border-white/5 flex items-center justify-between">
                                <div className="flex items-center gap-md">
                                    <div className="h-10 w-10 bg-surface-container-high flex items-center justify-center border border-cyan-400/20">
                                        <span className="material-symbols-outlined text-cyan-400">edit_square</span>
                                    </div>
                                    <div className="space-y-0.5">
                                        <h3 className="font-label-caps text-headline-md uppercase tracking-tight text-white">Neural Blueprint</h3>
                                        <p className="font-label-caps text-[10px] text-outline-variant uppercase tracking-widest">Script & Retention Architecture</p>
                                    </div>
                                </div>
                                {script && (
                                    <div className="flex flex-wrap gap-sm">
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
                                                className="px-sm py-sm bg-surface-container-high border border-white/5 font-label-caps text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-white hover:border-cyan-400/50 transition-all flex items-center gap-xs"
                                            >
                                                <span className="material-symbols-outlined text-[12px]">language</span>
                                                {lang.code}
                                            </button>
                                        ))}
                                        <button
                                            onClick={handleValidateHook}
                                            disabled={isValidating}
                                            className="surface-glass rim-light hover:border-cyan-400/50 text-cyan-400 hover:text-cyan-300 font-label-caps text-[10px] py-sm px-md transition-all flex items-center gap-xs uppercase tracking-widest ml-auto"
                                        >
                                            {isValidating ? <RefreshCw className="h-3 w-3 animate-spin" /> : <span className="material-symbols-outlined text-[14px]">auto_awesome</span>}
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
                                                                aria-label={`Search stock videos for segment ${i + 1}`}
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
                                                                <div 
                                                                    className="h-16 w-16 rounded-xl border border-emerald-500/20 overflow-hidden shadow-lg bg-cover bg-center" 
                                                                    style={{ backgroundImage: `url(${API_BASE}/static/${segmentAssets[i].image})` }}
                                                                    role="img"
                                                                    aria-label="Segment Asset"
                                                                />
                                                            )}
                                                            {segmentAssets[i]?.videos && (
                                                                <div className="flex gap-2">
                                                                    {segmentAssets[i].videos.slice(0, 2).map((v: any, j: number) => (
                                                                        <div 
                                                                            key={j} 
                                                                            className="h-16 w-12 rounded-lg border border-emerald-500/20 overflow-hidden relative group/v bg-cover bg-center"
                                                                            style={{ backgroundImage: `url(${v.preview})` }}
                                                                            role="img"
                                                                            aria-label="Video Preview"
                                                                        >
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

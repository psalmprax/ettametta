"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import {
    RefreshCw,
    ShieldAlert,
    ChevronDown,
    ArrowRight,
    Coins,
    Loader2,
} from "lucide-react";
import { JobItem } from "./JobItem";

/** Module-internal — do not consume from outside. */
const AI_ENGINES = [
    // Always works — no API key needed
    { id: "lite4k", name: "Cinematic Parallax", free: true, needsKey: false, credits: 5, description: "FLUX image + motion — works out of the box" },
    // API key required — direct API implementations
    { id: "zsky", name: "ZSky AI", free: true, needsKey: true, credits: 0, description: "WAN 2.2 model, 50 free credits/day" },
    { id: "kling", name: "Kling AI", free: true, needsKey: true, credits: 0, description: "100 free credits/day, high quality" },
    { id: "pixverse", name: "PixVerse", free: true, needsKey: true, credits: 0, description: "20 free credits/day" },
    { id: "pika", name: "Pika", free: true, needsKey: true, credits: 10, description: "10 free credits/day" },
    { id: "runway", name: "Runway", free: true, needsKey: true, credits: 30, description: "10 free signup credits" },
    { id: "stability", name: "Stability AI", free: true, needsKey: true, credits: 0, description: "~25 calls/day, reliable API" },
    { id: "haiper", name: "Haiper", free: true, needsKey: true, credits: 0, description: "25 free credits/day + browser fallback" },
    { id: "luma", name: "Luma Dream Machine", free: true, needsKey: true, credits: 0, description: "15 free credits/day + browser fallback" },
    { id: "replicate", name: "Replicate (WAN/Seedance/Hailuo)", free: false, needsKey: true, credits: 5, description: "Pay-per-use, ~$0.02-0.40/video" },
    // GPU node required
    { id: "mochi", name: "Mochi", free: false, needsKey: false, credits: 15, description: "Requires GPU node (Genmo open model, 30GB VRAM)" },
    { id: "wan", name: "WAN 2.1", free: false, needsKey: false, credits: 15, description: "Requires GPU node (open weights, 16GB VRAM)" },
    { id: "wan2.2", name: "Wan 2.2", free: false, needsKey: false, credits: 15, description: "Requires GPU node or SiliconFlow key" },
    { id: "cogvideo", name: "CogVideoX", free: false, needsKey: false, credits: 20, description: "Requires GPU node (RTX 8000)" },
    { id: "zeroscope", name: "Zeroscope", free: false, needsKey: false, credits: 10, description: "Requires GPU node (lightweight text-to-video, 8GB VRAM)" },
    { id: "animatediff", name: "AnimateDiff", free: false, needsKey: false, credits: 15, description: "Requires GPU node (image-to-video animation, 12GB VRAM)" },
];

export function VisualCorePanel() {
    const { credits, refreshCredits } = useAuth();
    const [prompt, setPrompt] = useState("");
    const [style, setStyle] = useState("cinematic");
    const [mode, setMode] = useState<"generate" | "remix">("generate");
    const [provider, setProvider] = useState("lite4k");
    const [niche, setNiche] = useState("Auto-Detect");
    const [configKeys, setConfigKeys] = useState<Record<string, boolean>>({});
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [jobs, setJobs] = useState<any[]>([]);

    // Auto-refresh credit balance every 2 minutes
    const refreshRef = useRef(refreshCredits);
    useEffect(() => {
        refreshRef.current = refreshCredits;
    }, [refreshCredits]);

    useEffect(() => {
        refreshRef.current();
        const interval = setInterval(() => refreshRef.current(), 120_000);
        return () => clearInterval(interval);
    }, []);

    // Fetch settings to check which API keys are configured
    useEffect(() => {
        const abortController = new AbortController();
        
        const fetchConfig = async () => {
            const token = getAuthToken();
            if (!token) return;
            try {
                const response = await fetch(`${API_BASE}/settings/`, {
                    headers: { Authorization: `Bearer ${token}` },
                    signal: abortController.signal
                });
                if (response.ok) {
                    const data = await response.json();
                    const engineKeys = [
                        "runway_api_key", "pika_api_key", "luma_api_key", 
                        "zsky_api_key", "kling_api_key", "pixverse_api_key",
                        "replicate_api_key", "stability_api_key", "haiper_api_key"
                    ];
                    const keyMap: Record<string, boolean> = {};
                    for (const key of engineKeys) {
                        const settingsData = data?.data || data;
                        const val = settingsData?.[key];
                        keyMap[key] = !!val && val !== "" && val !== "********";
                    }
                    if (!abortController.signal.aborted) {
                        setConfigKeys(keyMap);
                    }
                }
            } catch (e: any) {
                if (e?.name === 'AbortError') return;
                console.error("Failed to fetch engine config:", e);
            }
        };
        fetchConfig();
        
        return () => abortController.abort();
    }, []);

    // Filter AI engines based on configured API keys
    const availableEngines = useMemo(() => {
        return AI_ENGINES.filter(engine => {
            if (!engine.needsKey) return true; // Always show free engines
            // Check if this engine's API key is configured
            const keyName = `${engine.id}_api_key`;
            return configKeys[keyName];
        });
    }, [configKeys]);

    // If current selected engine is no longer available, switch to first available
    useEffect(() => {
        const isAvailable = availableEngines.some(e => e.id === provider);
        if (!isAvailable && availableEngines.length > 0) {
            setProvider(availableEngines[0].id);
        }
    }, [availableEngines, provider]);

    // Derived state
    const selectedEngine = useMemo(() => AI_ENGINES.find(e => e.id === provider), [provider]);
    const engineCost = selectedEngine?.credits ?? 0;
    const insufficientCredits = credits !== null && engineCost > 0 && credits < engineCost;

    const pollJobStatus = async (jobId: string, token: string) => {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/video/autonomous/remix/${jobId}/status`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const status = data.data;
                    
                    // Update job in list with progress
                    setJobs(prev => prev.map(job => 
                        job.id === jobId ? { ...job, ...status, id: jobId } : job
                    ));
                    
                    // Stop polling when complete
                    if (status.status === 'completed' || status.status === 'failed') {
                        clearInterval(pollInterval);
                        setCurrentJobId(null);
                        setIsGenerating(false);
                        
                        if (status.status === 'completed') {
                            toast.success("Remix video created successfully!");
                        } else if (status.error) {
                            toast.error(`Remix failed: ${status.error}`);
                        }
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
                toast.error("Polling error — check console for details");
                clearInterval(pollInterval);
                setCurrentJobId(null);
                setIsGenerating(false);
            }
        }, 2000); // Poll every 2 seconds
        
        return () => clearInterval(pollInterval);
    };

    const handleGenerate = async () => {
        if (!prompt) {
            toast.error("Prompt required");
            return;
        }
        setIsGenerating(true);
        const token = getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        // Choose endpoint based on mode
        const endpoint = mode === "remix" 
            ? `${API_BASE}/video/autonomous/remix`
            : `${API_BASE}/video/generate`;

        const payload = mode === "remix"
            ? { topic: prompt, niche: niche === "Auto-Detect" ? null : niche, style, duration_seconds: 60 }
            : { prompt, style, engine: provider };

        if (mode === "remix") {
            // For remix mode, start job and poll for status
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) throw new Error("Request failed");
                
                const data = await response.json();
                if (data.data?.job_id) {
                    const jobId = data.data.job_id;
                    setCurrentJobId(jobId);
                    
                    // Add initial job to list
                    setJobs(prev => [{
                        id: jobId,
                        status: "processing",
                        progress: 0,
                        current_step: "Starting...",
                        created_at: new Date().toISOString(),
                    }, ...prev]);
                    
                    // Start polling
                    pollJobStatus(jobId, token);
                }
            } catch (error: any) {
                toast.error(`Remix failed: ${error.message}`);
                setIsGenerating(false);
            }
        } else {
            // For generate mode, use original logic
            await withRealFallback<any>((signal) => fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        toast.success("Video generation started");
                        if (data.job_id) {
                            setJobs(prev => [data, ...prev]);
                        }
                    },
                    onFallback: (err) => {
                        toast.error(`Generation failed: ${err.message}`);
                    }
                }
            );
            setIsGenerating(false);
        }
    };

    useEffect(() => {
        const fetchJobs = async () => {
            const token = getAuthToken();
            if (!token) return;
            
            try {
                const response = await fetch(`${API_BASE}/video/jobs`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.data && data.data.jobs) {
                        setJobs(data.data.jobs.slice(0, 10));
                    } else if (data.jobs) {
                        setJobs(data.jobs.slice(0, 10));
                    }
                }
            } catch (error) {
                console.error("Failed to fetch jobs:", error);
                toast.error("Failed to load job history");
            }
        };
        fetchJobs();
    }, []);

    return (
        <div className="h-full min-h-[400px] flex flex-col border border-white/5 bg-[#0F0F11]/60 rounded-[40px] p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Visual Synthesis Core</h3>
                <span className="text-[8px] font-mono text-zinc-600">FRAME_GENERATION_PIPELINE_ACTIVE</span>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Mode</label>
                    <select
                        value={mode}
                        onChange={(e) => setMode(e.target.value as "generate" | "remix")}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    >
                        <option value="generate">🎬 Generate from Scratch (AI Models)</option>
                        <option value="remix">✨ Remix Viral Content (Autonomous)</option>
                    </select>
                </div>

                <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Video Prompt / Topic</label>
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder={mode === "remix" ? "Enter topic for viral remix (e.g., 'AI productivity tips')..." : "Describe the video you want to generate..."}
                        className="w-full h-24 bg-black/20 border border-white/10 rounded-xl p-4 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 resize-none"
                    />
                </div>

                {mode === "remix" && (
                    <div>
                        <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Niche</label>
                        <select
                            value={niche}
                            onChange={(e) => setNiche(e.target.value)}
                            className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                        >
                            <option value="Auto-Detect">✨ Auto-Detect (Recommended)</option>
                            <option value="Motivation">Motivation</option>
                            <option value="Tech">Tech</option>
                            <option value="Finance">Finance</option>
                            <option value="Health">Health</option>
                            <option value="Gaming">Gaming</option>
                            <option value="Education">Education</option>
                            <option value="Social Commentary">Social Commentary</option>
                            <option value="Entertainment">Entertainment</option>
                            <option value="Lifestyle">Lifestyle</option>
                            <option value="Spirituality">Spirituality</option>
                        </select>
                    </div>
                )}

                <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Visual Style</label>
                    <select
                        value={style}
                        onChange={(e) => setStyle(e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    >
                        <option value="cinematic">Cinematic</option>
                        <option value="anime">Anime</option>
                        <option value="realistic">Realistic</option>
                        <option value="3d">3D Animation</option>
                        <option value="pixel">Pixel Art</option>
                    </select>
                </div>

                {mode === "generate" && (
                    <div>
                        <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block flex items-center justify-between">
                            <span>AI Engine <span className="text-zinc-600 font-normal">— generates from prompt</span></span>
                            <div className="flex items-center gap-2">
                                <span className="text-[8px] text-zinc-600">
                                    {availableEngines.length < AI_ENGINES.length 
                                        ? `${availableEngines.length} of ${AI_ENGINES.length} available` 
                                        : `${AI_ENGINES.length} engines`}
                                </span>
                                <button
                                    onClick={() => refreshCredits()}
                                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 transition-colors group"
                                    title="Refresh credit balance"
                                >
                                    <Coins className="h-3 w-3 text-amber-400" />
                                    <span className="text-[9px] font-bold text-amber-400 tabular-nums">{credits ?? '—'}</span>
                                    <RefreshCw className="h-2.5 w-2.5 text-amber-500/50 group-hover:text-amber-400 group-hover:rotate-180 transition-all" />
                                </button>
                            </div>
                        </label>
                        <div className="relative">
                            <select
                                value={provider}
                                onChange={(e) => setProvider(e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50 appearance-none"
                            >
                                <optgroup label="⚡ No API Key Needed">
                                    {availableEngines.filter(e => !e.needsKey && !e.description.includes('GPU')).map(eng => (
                                        <option key={eng.id} value={eng.id}>
                                            {eng.name} <span className="text-zinc-500">— {eng.credits > 0 ? `${eng.credits}¢` : 'Free'}</span>
                                        </option>
                                    ))}
                                </optgroup>
                                <optgroup label="🔑 API Keys Configured">
                                    {availableEngines.filter(e => e.needsKey && !e.description.includes('GPU')).map(eng => (
                                        <option key={eng.id} value={eng.id}>
                                            {eng.name} <span className="text-zinc-500">— {eng.credits > 0 ? `${eng.credits}¢` : 'Free'}</span>
                                        </option>
                                    ))}
                                </optgroup>
                                <optgroup label="🖥️ GPU Node Required">
                                    {availableEngines.filter(e => e.description.includes('GPU')).map(eng => (
                                        <option key={eng.id} value={eng.id}>
                                            {eng.name} <span className="text-zinc-500">— {eng.credits > 0 ? `${eng.credits}¢` : 'Free'}</span>
                                        </option>
                                    ))}
                                </optgroup>
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                                <ChevronDown className="h-4 w-4" />
                            </div>
                        </div>
                        <p className="text-[8px] text-zinc-600 mt-1.5 leading-relaxed">
                            {(() => {
                                const eng = AI_ENGINES.find(e => e.id === provider);
                                if (!eng) return '';
                                const costLabel = eng.credits > 0 ? `${eng.credits} credits per video` : 'Free to use';
                                return `${eng.description} — ${costLabel}`;
                            })()}
                        </p>
                        {configKeys && Object.keys(configKeys).length > 0 && (
                            <div className="mt-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
                                <p className="text-[8px] text-zinc-500 font-bold uppercase tracking-wider">
                                    Engines requiring API keys are hidden unless configured in Settings
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {insufficientCredits && (
                    <a
                        href="/credits"
                        className="flex items-start gap-2.5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-colors group"
                    >
                        <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                        <div className="space-y-0.5 flex-1">
                            <p className="text-[9px] font-bold text-rose-400 uppercase tracking-wider">
                                Insufficient Credits
                            </p>
                            <p className="text-[8px] text-rose-300/70 leading-relaxed">
                                {selectedEngine?.name} costs <span className="font-bold text-rose-300">{engineCost} credits</span> per video. You have <span className="font-bold text-rose-300">{credits} credits</span>.
                                <span className="ml-1 underline decoration-dotted underline-offset-2 group-hover:text-rose-200 transition-colors">Top up →</span>
                            </p>
                        </div>
                        <ArrowRight className="h-3.5 w-3.5 text-rose-400/50 group-hover:text-rose-300 group-hover:translate-x-0.5 transition-all shrink-0 mt-0.5" />
                    </a>
                )}

                <Button
                    onClick={handleGenerate}
                    disabled={isGenerating || !prompt || insufficientCredits}
                    className="w-full h-14 bg-violet-500 hover:bg-violet-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest"
                >
                    {isGenerating ? (
                        mode === "remix" && currentJobId ? (
                            <span className="flex items-center justify-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                {jobs.find(j => j.id === currentJobId)?.current_step || "Processing..."}
                            </span>
                        ) : (mode === "remix" ? "Discovering & Creating..." : "Initializing...")
                    ) : (mode === "remix" ? "Create Remix Video" : "Generate Video")}
                </Button>
            </div>

            {jobs.length > 0 && (
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-3">Recent Jobs</h4>
                    <div className="space-y-2">
                        {jobs.map((job) => (
                            <JobItem key={job.id} job={job} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

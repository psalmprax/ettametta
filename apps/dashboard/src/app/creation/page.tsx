"use client";

import React, { useState, useCallback, useEffect, useRef, Suspense, useMemo } from "react";
import dynamic from "next/dynamic";

const NeuralCore = dynamic(() => import("@/components/ui/NeuralCore"), { ssr: false });
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
    Search,
    PlaySquare,
    FileVideo
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useNiches } from "@/hooks/useNiches";
import { Button } from "@/components/ui/Button";
import { useRouter, useSearchParams } from "next/navigation";
import { useTelemetry } from "@/context/TelemetryContext";

// --- Sub-Panel Components ---

function VoiceForgePanel() {
    const [text, setText] = useState("");
    const [voice, setVoice] = useState("alloy");
    const [isGenerating, setIsGenerating] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!text) {
            toast.error("Text input required");
            return;
        }
        setIsGenerating(true);
        const token = await getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/tools/prompt/template`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ text, voice })
            });
            
            if (response.ok) {
                const data = await response.json();
                toast.success("Voice template generated");
            } else {
                toast.error("Failed to generate voice");
            }
        } catch (error) {
            toast.error("Voice generation error");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="h-full min-h-[400px] flex flex-col border border-white/5 bg-[#0F0F11]/60 rounded-[40px] p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Voice Forge Core</h3>
                <span className="text-[8px] font-mono text-zinc-600">NEURAL_AUDIO_SYNTHESIS_HUB_ACTIVE</span>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Input Text</label>
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Enter text to synthesize..."
                        className="w-full h-32 bg-black/20 border border-white/10 rounded-xl p-4 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 resize-none"
                    />
                </div>

                <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Voice Model</label>
                    <select
                        value={voice}
                        onChange={(e) => setVoice(e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    >
                        <option value="alloy">Alloy</option>
                        <option value="echo">Echo</option>
                        <option value="fable">Fable</option>
                        <option value="onyx">Onyx</option>
                        <option value="nova">Nova</option>
                        <option value="shimmer">Shimmer</option>
                    </select>
                </div>

                <Button
                    onClick={handleGenerate}
                    disabled={isGenerating || !text}
                    className="w-full h-14 bg-violet-500 hover:bg-violet-400 text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest"
                >
                    {isGenerating ? "Synthesizing..." : "Generate Voice"}
                </Button>

                {audioUrl && (
                    <div className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                        <audio controls src={audioUrl} className="w-full" />
                    </div>
                )}
            </div>
        </div>
    );
}

function ScriptEnginePanel() {
    const [topic, setTopic] = useState("");
    const [niche, setNiche] = useState("Auto-Detect");
    const [duration, setDuration] = useState(60);
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<ScriptOutput | null>(null);

    const handleGenerate = async () => {
        if (!topic) {
            toast.error("Topic required");
            return;
        }
        setIsGenerating(true);
        const token = await getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        // Send null for niche to trigger auto-detection
        const nichePayload = niche === "Auto-Detect" ? null : niche;

        await withRealFallback<ScriptOutput>((signal) => fetch(`${API_BASE}/no-face/script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic, niche: nichePayload, duration_seconds: duration })
            }),
            {
                fallback: {} as ScriptOutput,
                onSuccess: (data) => {
                    setScript(data);
                    toast.success("Script generated successfully");
                },
                onFallback: (err) => {
                    toast.error(`Script generation failed: ${err.message}`);
                }
            }
        );
        setIsGenerating(false);
    };

    return (
        <div className="h-full min-h-[400px] flex flex-col border border-white/5 bg-[#0F0F11]/60 rounded-[40px] p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Script Synthesis Engine</h3>
                <span className="text-[8px] font-mono text-zinc-600">LLM_ORCHESTRATION_LAYER_READY</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Topic</label>
                    <input
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="Enter video topic..."
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50"
                    />
                </div>

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

                <div>
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Duration (seconds)</label>
                    <input
                        type="number"
                        value={duration}
                        onChange={(e) => setDuration(Number(e.target.value))}
                        min={15}
                        max={300}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    />
                </div>
            </div>

            <Button
                onClick={handleGenerate}
                disabled={isGenerating || !topic}
                className="w-full h-14 bg-violet-500 hover:bg-violet-400 text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest"
            >
                {isGenerating ? "Synthesizing..." : "Generate Script"}
            </Button>

            {script && (
                <div className="flex-1 overflow-y-auto custom-scrollbar p-4 bg-black/20 rounded-xl border border-white/5">
                    <h4 className="text-sm font-bold text-white mb-2">{script.title}</h4>
                    <div className="space-y-2">
                        {script.segments?.map((segment, i) => (
                            <div key={i} className="p-3 bg-white/5 rounded-lg">
                                <p className="text-xs text-zinc-300">{segment.text}</p>
                                <span className="text-[8px] text-zinc-500 mt-1 block">{segment.duration}s</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function VisualCorePanel() {
    const [prompt, setPrompt] = useState("");
    const [style, setStyle] = useState("cinematic");
    const [mode, setMode] = useState<"generate" | "remix">("generate");
    const [niche, setNiche] = useState("Auto-Detect");
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [jobs, setJobs] = useState<any[]>([]);

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
        const token = await getAuthToken();
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
            : { prompt, style, provider: "pixverse" };

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
            const token = await getAuthToken();
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

                <Button
                    onClick={handleGenerate}
                    disabled={isGenerating || !prompt}
                    className="w-full h-14 bg-violet-500 hover:bg-violet-400 text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest"
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
                            <div key={job.id} className="p-3 bg-white/5 rounded-lg border border-white/5">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs text-white truncate flex-1">{job.title || job.prompt || "Remix Video"}</span>
                                    <span className={`text-[8px] px-2 py-1 rounded-full ml-2 ${
                                        job.status === 'completed' || job.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' :
                                        job.status === 'failed' || job.status === 'FAILED' ? 'bg-rose-500/20 text-rose-400' :
                                        'bg-yellow-500/20 text-yellow-400'
                                    }`}>
                                        {job.status === 'processing' ? 'PROCESSING' : job.status.toUpperCase()}
                                    </span>
                                </div>
                                
                                {/* Progress bar for processing jobs */}
                                {job.status === 'processing' && job.progress !== undefined && (
                                    <div className="mb-2">
                                        <div className="flex justify-between text-[8px] text-zinc-500 mb-1">
                                            <span>{job.current_step || 'Processing...'}</span>
                                            <span>{job.progress}%</span>
                                        </div>
                                        <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                                            <div 
                                                className="h-full bg-violet-500 transition-all duration-500"
                                                style={{ width: `${job.progress}%` }}
                                            />
                                        </div>
                                    </div>
                                )}
                                
                                <span className="text-[8px] text-zinc-500 block mb-2">
                                    {new Date(job.created_at).toLocaleString()}
                                </span>
                                
                                {/* Preview and Download buttons for completed videos */}
                                {(job.status === 'completed' || job.status === 'COMPLETED') && (job.output_path || job.result?.output_path) && (
                                    <div className="flex gap-2 mt-2">
                                        <button
                                            onClick={() => window.open(`/api/v1/video/preview/${job.id}`, '_blank')}
                                            className="flex-1 px-3 py-1.5 bg-violet-500/20 hover:bg-violet-500/30 text-violet-400 text-[9px] font-bold uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center gap-1"
                                        >
                                            <PlaySquare className="h-3 w-3" />
                                            Preview
                                        </button>
                                        <button
                                            onClick={() => {
                                                const link = document.createElement('a');
                                                link.href = `/api/v1/video/download/${job.id}`;
                                                link.download = `remix_${job.id}.mp4`;
                                                link.click();
                                            }}
                                            className="flex-1 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-[9px] font-bold uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center gap-1"
                                        >
                                            <FileVideo className="h-3 w-3" />
                                            Download
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// --- Main Page Component ---

function CreationContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { niches, isLoading: isLoadingNiches } = useNiches();
    
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "genesis");
    const [prompt, setPrompt] = useState(searchParams.get("seed") || "");
    const [niche, setNiche] = useState("Motivation");
    const [activeStack, setActiveStack] = useState<"cloud" | "os">("cloud");
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<ScriptOutput | null>(null);
    const [actionLogs, setActionLogs] = useState<string[]>(["CREATION_HUB_READY", "AWAITING_NEURAL_SEED"]);
    const [isCinemaLaunching, setIsCinemaLaunching] = useState(false);

    const { agents, logs: systemLogs, status, pulse } = useTelemetry();

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
        const seed = searchParams.get("seed");
        if (seed) setPrompt(seed);
    }, [searchParams]);

    const handleGenerate = async () => {
        if (!prompt) {
            toast.error("Neural Seed Required");
            return;
        }
        setIsGenerating(true);
        setActionLogs((prev: string[]) => [`[SIGNAL] Initializing Generation: ${prompt.slice(0, 30)}...`, ...prev]);
        
        const token = await getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        await withRealFallback<ScriptOutput>((signal) => fetch(`${API_BASE}/no-face/script`, {
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
                    setActionLogs((prev: string[]) => [`[SUCCESS] Neural Script Synthesized: ${data.title}`, ...prev]);
                    toast.success("Script Protocol Synthesized");
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[ERROR] ${err.message}`, ...prev]);
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

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/no-face/launch-cinema`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic: prompt, niche, duration_seconds: 60, engine: activeStack, script: script?.segments || script })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setActionLogs((prev: string[]) => [`[CINEMA] Sequence Initiated. JobID: ${data.job_id}`, ...prev]);
                    toast.success("Cinema Sequence Initiated");
                }
            }
        );
        setIsCinemaLaunching(false);
    };

    // Merge system logs and action logs for display
    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "CREATION",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...(Array.isArray(systemLogs) ? systemLogs : [])
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

    const [activityFeed, setActivityFeed] = useState<any[]>([]);

    useEffect(() => {
        const fetchHistory = async () => {
            const token = await getAuthToken();
            if (!token) return;
            await withRealFallback<any[]>((signal) => fetch(`${API_BASE}/publish/history`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                { fallback: [], onSuccess: (data) => setActivityFeed(data.slice(0, 5)) }
            );
        };
        fetchHistory();
    }, []);

    const recentAssets = useMemo(() => {
        return activityFeed.map(item => ({
            id: item.id,
            title: item.title,
            type: "VIDEO" as any,
            timestamp: new Date(item.published_at).toLocaleTimeString(),
            tags: ["PRODUCTION"],
            size: "---"
        }));
    }, [activityFeed]);

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
                            onClick={() => {
                                setActiveEngine(item.id);
                                router.replace(`/creation?engine=${item.id}`);
                            }}
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
                
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={cn("flex-1 relative z-10 flex flex-col gap-10", activeEngine !== "logs" && "overflow-y-auto custom-scrollbar pr-4")}
                    >
                        {activeEngine === "genesis" && (
                            <>
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 shrink-0">
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

                                    <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/60 backdrop-blur-xl p-8 space-y-6 flex flex-col relative overflow-hidden">
                                        <div className="flex items-center justify-between border-b border-white/5 pb-4">
                                            <h3 className="text-[10px] font-bold text-emerald-400 tracking-[0.2em] uppercase">Active Processing Stream</h3>
                                            <span className="text-[8px] font-mono text-zinc-600">LIVE DATA FEED_001</span>
                                        </div>

                                        <div className="flex-1 flex flex-col justify-center items-center relative py-10">
                                            <div className="w-full h-px bg-linear-to-r from-transparent via-violet-500/30 to-transparent absolute top-1/2 -translate-y-1/2" />
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
                                                <span>{isGenerating ? "Processing..." : (pulse?.load_avg ? `${Math.round(pulse.load_avg * 100)}%` : "0.0%")}</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                <motion.div 
                                                    className="h-full bg-emerald-500"
                                                    initial={{ width: 0 }}
                                                    animate={isGenerating ? { x: ["-100%", "100%"] } : { width: pulse?.load_avg ? `${pulse.load_avg * 100}%` : 0 }}
                                                    transition={isGenerating ? { duration: 1.5, repeat: Infinity, ease: "linear" } : { duration: 1 }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex-1 min-h-[300px] flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                        <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">Neural Transcript Log</h3>
                                        <div className="flex items-center gap-4">
                                            <span className="text-[8px] font-mono text-zinc-600">LOG_LEVEL: VERBOSE</span>
                                            <button onClick={() => setActionLogs([])} className="text-zinc-600 hover:text-white transition-colors">
                                                <RefreshCw className="h-3 w-3" />
                                            </button>
                                        </div>
                                    </div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                                        {displayLogs.map((log, i) => (
                                            <div key={i} className="flex gap-4">
                                                <span className="text-zinc-700">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                                <span className={cn(
                                                    log.level === "ACTION" ? "text-cyan-400" :
                                                    log.level === "ERROR" ? "text-rose-500" :
                                                    log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-500"
                                                )}>
                                                    {log.module ? `[${log.module}] ` : ""}{log.message}
                                                </span>
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
                            </>
                        )}

                        {activeEngine === "voice" && (
                            <VoiceForgePanel />
                        )}

                        {activeEngine === "script" && (
                            <ScriptEnginePanel />
                        )}

                        {activeEngine === "visual" && (
                            <VisualCorePanel />
                        )}

                        {activeEngine === "logs" && (
                            <div className="h-full flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                    <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">Global Creation Stream</h3>
                                    <div className="flex items-center gap-4">
                                        <span className="text-[8px] font-mono text-zinc-600">LOG_LEVEL: VERBOSE</span>
                                        <button onClick={() => setActionLogs([])} className="text-zinc-600 hover:text-white transition-colors">
                                            <RefreshCw className="h-3 w-3" />
                                        </button>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                                    {displayLogs.map((log, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-700">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-500"
                                            )}>
                                                {log.module ? `[${log.module}] ` : ""}{log.message}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function CreationPage() {
    return (
        <Suspense fallback={null}>
            <CreationContent />
        </Suspense>
    );
}

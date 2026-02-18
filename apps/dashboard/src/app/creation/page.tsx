"use client";

import React, { useState } from "react";
import DashboardLayout from "@/components/layout";
import {
    Sparkles,
    Zap,
    Cpu,
    CheckCircle2,
    RefreshCw,
    Play,
    Edit3,
    ShieldAlert,
    AlertTriangle,
    Plus,
    Film,
    Wand2,
    Clock,
    Target,
    Globe
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";

interface ScriptSegment {
    type: string;
    text: string;
    visual_cue: string;
    duration: number;
}

interface ScriptOutput {
    title: string;
    segments: ScriptSegment[];
    hashtags: string[];
}

export default function CreationPage() {
    const [topic, setTopic] = useState("");
    const [niche, setNiche] = useState("AI Technology");
    const [style, setStyle] = useState("story");
    const [duration, setDuration] = useState(60);
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<ScriptOutput | null>(null);
    const [segmentAssets, setSegmentAssets] = useState<Record<number, { audio?: string, image?: string, videos?: any[] }>>({});
    const [loadingSegment, setLoadingSegment] = useState<string | null>(null);

    const [isValidating, setIsValidating] = useState(false);
    const [hookAnalysis, setHookAnalysis] = useState<any>(null);

    const handleGenerateScript = async () => {
        if (!topic) return;
        setIsGenerating(true);
        setHookAnalysis(null);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/generate-script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ topic, niche, style, duration })
            });
            if (res.ok) {
                const data = await res.json();
                setScript(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleValidateHook = async () => {
        if (!script) return;
        const hookSegment = Array.isArray(script.segments) ? script.segments.find(s => s.type === "hook") : null;
        if (!hookSegment) return;

        setIsValidating(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/validate-hook`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ hook: hookSegment.text })
            });
            if (res.ok) {
                const data = await res.json();
                setHookAnalysis(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsValidating(false);
        }
    };

    const handleSynthesizeAudio = async (index: number, text: string) => {
        setLoadingSegment(`audio-${index}`);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/generate-voiceover`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ text })
            });
            if (res.ok) {
                const data = await res.json();
                setSegmentAssets(prev => ({
                    ...prev,
                    [index]: { ...prev[index], audio: data.audio_url }
                }));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingSegment(null);
        }
    };

    const handleGenerateSegmentImage = async (index: number, prompt: string) => {
        setLoadingSegment(`image-${index}`);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/generate-image`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ prompt })
            });
            if (res.ok) {
                const data = await res.json();
                setSegmentAssets(prev => ({
                    ...prev,
                    [index]: { ...prev[index], image: data.image_url }
                }));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingSegment(null);
        }
    };

    const handleSearchStock = async (index: number, query: string) => {
        setLoadingSegment(`stock-${index}`);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/search-stock?query=${encodeURIComponent(query)}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSegmentAssets(prev => ({
                    ...prev,
                    [index]: { ...prev[index], videos: data }
                }));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingSegment(null);
        }
    };

    const handleGlobalize = async (lang: string) => {
        if (!script) return;
        setIsGenerating(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/no-face/localize`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ segments: script.segments, target_lang: lang })
            });
            if (res.ok) {
                const data = await res.json();
                setScript({ ...script, segments: data });
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-end justify-between mb-12">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Intelligence Hub</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter italic uppercase text-white leading-none">Creation <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-500 to-fuchsia-500 text-hollow">Suite</span></h1>
                        <p className="text-zinc-500 font-medium">Engineer high-velocity <span className="text-zinc-300 font-bold">faceless content</span> with neural script generation.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    {/* Input Controls */}
                    <div className="space-y-8">
                        <div className="glass-card space-y-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Objective / Topic</label>
                                    <div className="relative group">
                                        <Target className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-600 group-focus-within:text-primary transition-all" />
                                        <input
                                            value={topic}
                                            onChange={(e) => setTopic(e.target.value)}
                                            placeholder="The History of Quantum AI..."
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-5 pl-16 pr-6 focus:outline-none focus:ring-1 focus:ring-primary/40 text-sm font-bold text-white placeholder:text-zinc-700 italic"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Niche</label>
                                        <select
                                            value={niche}
                                            onChange={(e) => setNiche(e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-5 focus:outline-none focus:ring-1 focus:ring-primary/40 text-xs font-black uppercase tracking-wider text-zinc-400 appearance-none cursor-pointer hover:bg-zinc-900/50"
                                        >
                                            <option>AI Technology</option>
                                            <option>Stoic Wisdom</option>
                                            <option>Market Trends</option>
                                            <option>History</option>
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Style</label>
                                        <select
                                            value={style}
                                            onChange={(e) => setStyle(e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-5 focus:outline-none focus:ring-1 focus:ring-primary/40 text-xs font-black uppercase tracking-wider text-zinc-400 appearance-none cursor-pointer hover:bg-zinc-900/50"
                                        >
                                            <option value="story">Storytelling</option>
                                            <option value="listicle">Listicle</option>
                                            <option value="educational">Educational</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-2">Duration: {duration}s</label>
                                    <input
                                        type="range"
                                        min="15"
                                        max="60"
                                        step="1"
                                        value={duration}
                                        onChange={(e) => setDuration(parseInt(e.target.value))}
                                        className="w-full h-1.5 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-primary"
                                    />
                                </div>
                            </div>

                            <motion.button
                                whileHover={{ scale: 1.02, y: -4 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={handleGenerateScript}
                                disabled={isGenerating || !topic}
                                className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-black py-5 rounded-xl transition-all shadow-[0_0_40px_rgba(var(--primary-rgb),0.3)] flex items-center justify-center gap-3 uppercase text-xs tracking-widest"
                            >
                                {isGenerating ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Wand2 className="h-5 w-5" />}
                                {isGenerating ? "Synthesizing..." : "Generate Script"}
                            </motion.button>
                        </div>

                        {/* Analysis Insights */}
                        <AnimatePresence>
                            {hookAnalysis && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={cn(
                                        "glass-card p-8 rounded-[2rem] space-y-6 relative overflow-hidden border",
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
                                        <span className="text-2xl font-black italic text-white">{hookAnalysis.score}%</span>
                                    </div>
                                    <p className="text-zinc-400 text-xs italic leading-relaxed font-medium">
                                        "{hookAnalysis.analysis}"
                                    </p>

                                    {hookAnalysis.status === "KILL" && (
                                        <div className="space-y-4 pt-2">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Suggested Pivots:</p>
                                            {hookAnalysis.alternatives.map((alt: string, i: number) => (
                                                <div key={i} className="p-4 bg-zinc-950/80 rounded-xl border border-white/5 text-[11px] font-bold text-zinc-300 italic group hover:border-primary/40 transition-all cursor-pointer">
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
                            <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                            <div className="p-8 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                        <Edit3 className="h-5 w-5 text-primary neon-glow" />
                                    </div>
                                    <div className="space-y-0.5">
                                        <h3 className="font-black italic uppercase tracking-tight text-white">Neural Blueprint</h3>
                                        <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Script & Retention Architecture</p>
                                    </div>
                                </div>
                                {script && (
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleGlobalize("Spanish")}
                                            className="px-4 py-2 rounded-lg bg-zinc-900 border border-white/5 text-[9px] font-black uppercase tracking-[0.2em] text-zinc-500 hover:text-white hover:border-primary/50 transition-all flex items-center gap-2"
                                        >
                                            <Globe className="h-3 w-3" />
                                            ES
                                        </button>
                                        <button
                                            onClick={() => handleGlobalize("German")}
                                            className="px-4 py-2 rounded-lg bg-zinc-900 border border-white/5 text-[9px] font-black uppercase tracking-[0.2em] text-zinc-500 hover:text-white hover:border-primary/50 transition-all flex items-center gap-2"
                                        >
                                            <Globe className="h-3 w-3" />
                                            DE
                                        </button>
                                        <button
                                            onClick={handleValidateHook}
                                            disabled={isValidating}
                                            className="glass-card hover:border-primary/50 text-zinc-400 hover:text-white text-[10px] font-black py-3 px-6 rounded-xl transition-all flex items-center gap-2 uppercase tracking-widest italic"
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
                                            <h2 className="text-3xl font-black italic text-white uppercase tracking-tighter">{script.title}</h2>
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
                                                    <div className="absolute left-0 top-0 bottom-0 w-[1px] bg-white/5 group-hover:bg-primary/40 transition-all" />
                                                    <div className="absolute left-[-4px] top-0 h-2 w-2 rounded-full bg-zinc-800 group-hover:bg-primary transition-all" />

                                                    <div className="space-y-4">
                                                        <div className="flex items-center gap-4">
                                                            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">{seg.type}</span>
                                                            <span className="text-[10px] font-mono text-zinc-800 tracking-tighter">{seg.duration} SEC</span>
                                                        </div>
                                                        <p className="text-lg font-bold text-zinc-200 leading-relaxed italic">{seg.text}</p>

                                                        <div className="flex gap-4 items-center">
                                                            <div className="flex items-center gap-3 bg-zinc-950/40 p-3 rounded-xl border border-white/5 w-fit">
                                                                <Film className="h-3 w-3 text-zinc-500" />
                                                                <span className="text-[10px] font-bold text-zinc-500 uppercase italic tracking-widest">{seg.visual_cue}</span>
                                                            </div>

                                                            <div className="flex gap-2">
                                                                <button
                                                                    onClick={() => handleSynthesizeAudio(i, seg.text)}
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
                                                                    className={cn(
                                                                        "p-2.5 rounded-lg border border-white/5 hover:border-primary/40 transition-all group/btn",
                                                                        segmentAssets[i]?.image ? "bg-emerald-500/10 border-emerald-500/20" : "bg-zinc-900/50"
                                                                    )}
                                                                >
                                                                    {loadingSegment === `image-${i}` ? <RefreshCw className="h-4 w-4 animate-spin text-primary" /> : <Wand2 className={cn("h-4 w-4 transition-colors", segmentAssets[i]?.image ? "text-emerald-500" : "text-zinc-600 group-hover/btn:text-primary")} />}
                                                                </button>
                                                            </div>
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
                                                className="flex-1 bg-white/5 hover:bg-white/10 text-zinc-400 font-black py-5 rounded-2xl transition-all uppercase text-xs tracking-[0.2em] italic border border-white/5"
                                            >
                                                Export Assets
                                            </button>
                                            <motion.button
                                                whileHover={{ scale: 1.05, y: -2 }}
                                                whileTap={{ scale: 0.98 }}
                                                className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white font-black py-5 rounded-2xl transition-all shadow-[0_0_40px_rgba(16,185,129,0.2)] flex items-center justify-center gap-3 uppercase text-xs tracking-[0.2em] italic"
                                            >
                                                <Zap className="h-5 w-5" />
                                                Launch Production
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
        </DashboardLayout>
    );
}

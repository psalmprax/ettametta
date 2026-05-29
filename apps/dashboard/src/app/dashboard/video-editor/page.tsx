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
    Loader2,
    Clapperboard,
    PenTool,
    Film
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import DashboardPageLayout from "@/components/DashboardPageLayout";
import { DesignCard } from "@/components/ui/DesignCard";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { withRealFallback } from "@/lib/real_first_utils";

const EDITOR_TABS = [
  { id: "concept", label: "Concept", icon: PenTool },
  { id: "logic", label: "Neural Logic", icon: Cpu },
  { id: "studio", label: "Final Studio", icon: Clapperboard },
];

const STYLES = ["story", "motivation", "educational", "breaking_news", "cinematic_top10"];
const DURATIONS = [15, 30, 60, 90, 120];

export default function VideoEditorPage() {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState("concept");
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
        
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/no-face/script`, {
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
                    setActiveTab("logic");
                    toast.success("Neural Script Synthesized");
                }
            }
        );
        setIsGenerating(false);
    };

    const handleCommitRender = async () => {
        if (!script) return;
        setIsGenerating(true);
        const token = await getAuthToken();
        
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/no-face/launch-cinema`, {
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
                    toast.success("Cinema Sequence Initiated");
                    router.push("/transformation");
                }
            }
        );
        setIsGenerating(false);
    };

    return (
        <DashboardPageLayout
            title="Video Studio"
            subtitle="Autonomous Short-Form Generation & Neural Scripting Engine"
            tabs={EDITOR_TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            actions={
                <div className="flex items-center gap-4">
                    <Button variant="outline" className="border-white/10 text-zinc-400 hover:text-white gap-2">
                        <Save className="h-4 w-4" />
                        Save Draft
                    </Button>
                </div>
            }
        >
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-12"
                >
                    {activeTab === "concept" && (
                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                            <div className="xl:col-span-1 p-10 rounded-[32px] bg-[#0F0F11] border border-white/5 space-y-8">
                                <h3 className="text-xl font-bold text-white uppercase tracking-tight">Viral Concept</h3>
                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Core Message</label>
                                        <textarea 
                                            value={prompt}
                                            onChange={(e) => setPrompt(e.target.value)}
                                            placeholder="Describe the neural footprint..."
                                            className="w-full h-40 bg-white/5 border border-white/5 rounded-2xl p-6 text-white font-bold focus:outline-none resize-none"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Niche</label>
                                            <select 
                                                value={niche}
                                                onChange={(e) => setNiche(e.target.value)}
                                                className="w-full bg-white/5 border border-white/5 rounded-2xl h-14 px-4 text-zinc-400 font-bold uppercase focus:outline-none"
                                            >
                                                <option>Motivation</option>
                                                <option>AI Technology</option>
                                                <option>Stoicism</option>
                                                <option>Finance</option>
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Duration</label>
                                            <select 
                                                value={duration}
                                                onChange={(e) => setDuration(Number(e.target.value))}
                                                className="w-full bg-white/5 border border-white/5 rounded-2xl h-14 px-4 text-zinc-400 font-bold uppercase focus:outline-none"
                                            >
                                                {DURATIONS.map(d => <option key={d} value={d}>{d} Seconds</option>)}
                                            </select>
                                        </div>
                                    </div>
                                    <Button 
                                        onClick={handleGenerateScript}
                                        disabled={isGenerating || !prompt}
                                        className="w-full bg-violet-500 hover:bg-violet-400 text-white font-bold h-16 rounded-2xl gap-3 text-lg"
                                    >
                                        {isGenerating ? <Loader2 className="h-6 w-6 animate-spin" /> : <Cpu className="h-6 w-6" />}
                                        Synthesize Script
                                    </Button>
                                </div>
                            </div>
                            <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                                <DesignCard 
                                    title="Aesthetic Style"
                                    status="Story"
                                    metrics={[
                                        { label: "Style Profile", value: style.toUpperCase(), color: "text-violet-400" },
                                        { label: "Engine", value: engine.toUpperCase(), color: "text-zinc-500" }
                                    ]}
                                    footerInfo="Neural style mapping is ready."
                                    toolsStatus="Optimal"
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === "logic" && (
                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                            <div className="xl:col-span-1 p-10 rounded-[32px] bg-[#0F0F11] border border-white/5 space-y-8">
                                <h3 className="text-xl font-bold text-white uppercase tracking-tight">Script Segments</h3>
                                <div className="space-y-4 max-h-[500px] overflow-y-auto custom-scrollbar pr-4">
                                    {script?.segments?.map((seg: any, i: number) => (
                                        <button 
                                            key={i}
                                            onClick={() => setActiveSegment(i)}
                                            className={cn(
                                                "w-full p-6 rounded-2xl border text-left transition-all",
                                                activeSegment === i ? "bg-violet-500/10 border-violet-500/30" : "bg-white/2 border-white/5"
                                            )}
                                        >
                                            <div className="flex justify-between items-center mb-3">
                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">#{i+1}</span>
                                                <span className="text-[10px] font-bold text-violet-400">{seg.duration}S</span>
                                            </div>
                                            <p className="text-xs text-white font-medium line-clamp-2 leading-relaxed italic">"{seg.text}"</p>
                                        </button>
                                    ))}
                                </div>
                                <Button 
                                    onClick={handleCommitRender}
                                    disabled={isGenerating}
                                    className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-16 rounded-2xl gap-3 text-lg"
                                >
                                    {isGenerating ? <Loader2 className="h-6 w-6 animate-spin" /> : <Zap className="h-6 w-6 fill-current" />}
                                    Launch Production
                                </Button>
                            </div>
                            <div className="xl:col-span-2 p-10 rounded-[40px] bg-black border border-white/5 relative overflow-hidden flex flex-col justify-center items-center text-center space-y-10">
                                <div className="absolute inset-0 opacity-20 grayscale pointer-events-none">
                                    <img src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop" className="w-full h-full object-cover" alt="Preview" />
                                </div>
                                {script?.segments?.[activeSegment] ? (
                                    <motion.div 
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className="relative z-10 space-y-8 max-w-2xl"
                                    >
                                        <p className="text-4xl font-black text-white italic leading-tight tracking-tighter drop-shadow-[0_10px_10px_rgba(0,0,0,0.5)]">
                                            "{script.segments[activeSegment].text}"
                                        </p>
                                        <div className="flex items-center justify-center gap-6">
                                            <div className="h-px w-12 bg-white/20" />
                                            <span className="text-[10px] font-bold text-violet-400 uppercase tracking-[0.3em]">{script.segments[activeSegment].visual_prompt}</span>
                                            <div className="h-px w-12 bg-white/20" />
                                        </div>
                                    </motion.div>
                                ) : (
                                    <div className="relative z-10 opacity-30 flex flex-col items-center space-y-6">
                                        <Film className="h-16 w-16" />
                                        <p className="text-[10px] font-bold uppercase tracking-[0.5em]">Awaiting Neural Logic Synthesis</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === "studio" && (
                        <div className="h-[600px] flex flex-col items-center justify-center space-y-8 opacity-30 grayscale">
                            <Clapperboard className="h-20 w-20" />
                            <div className="text-center space-y-4">
                                <h3 className="text-xl font-bold text-white uppercase tracking-[0.3em]">Studio_Standby</h3>
                                <p className="text-sm font-medium text-zinc-500 uppercase tracking-widest">Initialize script generation to unlock final studio controls</p>
                            </div>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </DashboardPageLayout>
    );
}

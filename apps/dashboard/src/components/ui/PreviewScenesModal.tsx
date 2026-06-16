"use client";

import React from "react";
import {
    X, Layers, Loader2, AlertCircle, RefreshCw,
    Mic2, Volume2, Play, Video, Scissors, Palette, Sliders
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { toast } from "sonner";

export interface PreviewScenesModalProps {
    isPreviewModalOpen: boolean;
    setIsPreviewModalOpen: (open: boolean) => void;
    previewJobId: string | null;
    previewScenes: any[];
    previewJobStatus: string;
    isLoadingPreview: boolean;
    handlePreviewScenes: (jobId: string) => void;
    swappedAssets: Record<number, any>;
    setSwappedAssets: React.Dispatch<React.SetStateAction<Record<number, any>>>;
    activeSwapDrawerIndex: number | null;
    setActiveSwapDrawerIndex: (index: number | null) => void;
    selectedStylePreset: string;
    setSelectedStylePreset: (preset: "NEON_CYBER" | "AMBER_WARM" | "MONOCHROME_DARK" | "EMERALD_MATRIX") => void;
    colorTemp: number;
    setColorTemp: (val: number) => void;
    grainDensity: number;
    setGrainDensity: (val: number) => void;
    contrast: number;
    setContrast: (val: number) => void;
    kenBurnsSpeed: number;
    setKenBurnsSpeed: (val: number) => void;
    availableCategories: string[];
    activeCategory: string;
    setActiveCategory: (cat: string) => void;
}

export default function PreviewScenesModal({
    isPreviewModalOpen,
    setIsPreviewModalOpen,
    previewJobId,
    previewScenes,
    previewJobStatus,
    isLoadingPreview,
    handlePreviewScenes,
    swappedAssets,
    setSwappedAssets,
    activeSwapDrawerIndex,
    setActiveSwapDrawerIndex,
    selectedStylePreset,
    setSelectedStylePreset,
    colorTemp,
    setColorTemp,
    grainDensity,
    setGrainDensity,
    contrast,
    setContrast,
    kenBurnsSpeed,
    setKenBurnsSpeed,
    availableCategories,
    activeCategory,
    setActiveCategory,
}: PreviewScenesModalProps) {
    return (
        <>
            {/* Preview Scenes Modal */}
            <AnimatePresence>
                {isPreviewModalOpen && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-6 sm:p-10"
                        onClick={() => setIsPreviewModalOpen(false)}
                    >
                        <motion.div 
                            initial={{ scale: 0.95, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.95, y: 20 }}
                            className="w-full max-w-6xl bg-[#070709] border border-white/10 rounded-[36px] p-8 shadow-2xl max-h-[92vh] overflow-y-auto custom-scrollbar"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                                <div className="flex items-center gap-4">
                                    <div className="h-14 w-14 bg-violet-500/10 border border-violet-500/20 rounded-2xl flex items-center justify-center">
                                        <Layers className="h-7 w-7 text-violet-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Nexus Video Synthesizer</h3>
                                        <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Orchestrated Job: {previewJobId}</p>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => setIsPreviewModalOpen(false)}
                                    className="h-11 w-11 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl flex items-center justify-center transition-colors"
                                >
                                    <X className="h-5 w-5 text-zinc-400" />
                                </button>
                            </div>
                            
                            {isLoadingPreview ? (
                                <div className="flex items-center justify-center py-32">
                                    <Loader2 className="h-12 w-12 animate-spin text-violet-400" />
                                </div>
                            ) : previewScenes.length === 0 ? (
                                <div className="text-center py-32 space-y-4">
                                    {["COMPLETED", "FAILED"].includes(previewJobStatus) ? (
                                        <AlertCircle className="h-14 w-14 text-zinc-700 mx-auto" />
                                    ) : (
                                        <Loader2 className="h-14 w-14 animate-spin text-violet-400 mx-auto" />
                                    )}
                                    <p className="text-sm font-bold uppercase tracking-widest text-zinc-500">
                                        {!["COMPLETED", "FAILED"].includes(previewJobStatus)
                                            ? `Narrative decomposition in progress (status: ${previewJobStatus}). Scenes will appear once the Cognition stage finishes.`
                                            : previewJobStatus === "FAILED"
                                            ? `This job failed with status: ${previewJobStatus}. No scene data is available.`
                                            : "No scene data available for this pipeline."}
                                    </p>
                                    <button
                                        onClick={() => handlePreviewScenes(previewJobId || "")}
                                        className="mt-4 px-6 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl border border-white/5 text-xs font-bold uppercase tracking-wider transition-colors inline-flex items-center gap-2 mx-auto"
                                    >
                                        <RefreshCw className="h-3 w-3" /> Refresh Preview
                                    </button>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                    
                                    {/* Left Column: Scene List & Timelines */}
                                    <div className="lg:col-span-2 space-y-6 overflow-y-auto max-h-[60vh] pr-2 custom-scrollbar">
                                        {previewScenes.map((scene, index) => {
                                            const activeAsset = swappedAssets[index] || (scene.assets && scene.assets[0]) || null;
                                            const isDrawerOpen = activeSwapDrawerIndex === index;
                                            
                                            // Mock timing tracks aligned to the scene's duration
                                            const duration = scene.duration || 5;
                                            const simulatedWords = [
                                                { word: "AI", start: 0, end: 0.8 },
                                                { word: "Engine", start: 0.8, end: 1.6 },
                                                { word: "Orchestrated", start: 1.6, end: 2.6 },
                                                { word: "this", start: 2.6, end: 3.2 },
                                                { word: "scene", start: 3.2, end: 4.0 },
                                                { word: "perfectly.", start: 4.0, end: duration }
                                            ];

                                            return (
                                                <div key={index} className="p-6 bg-[#0F0F12]/80 border border-white/5 rounded-[28px] hover:border-violet-500/20 transition-all space-y-6 relative overflow-hidden group">
                                                    
                                                    {/* Top Bar */}
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <span className="h-9 w-9 bg-violet-500/10 border border-violet-500/20 rounded-xl flex items-center justify-center text-violet-400 font-bold text-sm">
                                                                {index + 1}
                                                            </span>
                                                            <span className={cn(
                                                                "px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border",
                                                                scene.type === 'hook' ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
                                                                scene.type === 'problem' ? "bg-rose-500/10 text-rose-500 border-rose-500/20" :
                                                                scene.type === 'solution' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
                                                                scene.type === 'outro' ? "bg-cyan-500/10 text-cyan-500 border-cyan-500/20" :
                                                                "bg-zinc-500/10 text-zinc-500 border-white/5"
                                                            )}>
                                                                {scene.type || 'Scene'}
                                                            </span>
                                                        </div>
                                                        <span className="text-xs font-black text-zinc-500 font-mono">{duration}s</span>
                                                    </div>
                                                    
                                                    {/* Text content */}
                                                    <div className="space-y-4">
                                                        <div>
                                                            <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest block mb-1">Visual Direction / Prompt</span>
                                                            <p className="text-xs text-zinc-300 font-semibold leading-relaxed">
                                                                {scene.description || scene.visual_prompt || "No instructions provided."}
                                                            </p>
                                                        </div>

                                                        {/* Timing track visualizer */}
                                                        <div className="p-4 bg-black/40 border border-white/5 rounded-2xl space-y-4">
                                                            
                                                            {/* Words Timeline */}
                                                            <div className="space-y-2">
                                                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest block">Subtitle Word Timeline</span>
                                                                <div className="flex flex-wrap gap-2 pt-1">
                                                                    {simulatedWords.map((item, idx) => (
                                                                        <div 
                                                                            key={idx}
                                                                            className="px-2 py-1 bg-white/5 rounded-lg border border-white/5 flex flex-col items-center justify-center shrink-0 min-w-[50px] animate-pulse"
                                                                            style={{ animationDelay: `${idx * 0.3}s` }}
                                                                        >
                                                                            <span className="text-[10px] text-white font-bold">{item.word}</span>
                                                                            <span className="text-[6px] text-zinc-500 font-mono">{item.start}s - {item.end}s</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* Audio waveforms timeline */}
                                                            <div className="space-y-3 pt-2 border-t border-white/5">
                                                                <div className="flex items-center justify-between text-[7px] text-zinc-600 uppercase font-black tracking-widest">
                                                                    <span>0.0s</span>
                                                                    <span>Audio Composition Track</span>
                                                                    <span>{duration}s</span>
                                                                </div>
                                                                
                                                                {/* Voiceover Track */}
                                                                <div className="space-y-1">
                                                                    <div className="flex items-center justify-between text-[7px] text-zinc-500">
                                                                        <span className="flex items-center gap-1"><Mic2 className="h-2 w-2" /> AI VOICEOVER</span>
                                                                        <span className="font-mono">Volume: 100%</span>
                                                                    </div>
                                                                    <div className="h-6 w-full bg-violet-950/20 border border-violet-500/10 rounded-lg relative overflow-hidden flex items-center justify-around px-2">
                                                                        {[4, 8, 2, 7, 5, 9, 3, 6, 8, 4, 9, 2, 7, 5, 8, 3, 6, 4, 7, 5].map((h, i) => (
                                                                            <div key={i} className="w-0.5 bg-violet-400 rounded-full" style={{ height: `${h * 10}%` }} />
                                                                        ))}
                                                                    </div>
                                                                </div>

                                                                {/* Background music track */}
                                                                <div className="space-y-1">
                                                                    <div className="flex items-center justify-between text-[7px] text-zinc-500">
                                                                        <span className="flex items-center gap-1"><Volume2 className="h-2 w-2" /> BACKGROUND MUSIC</span>
                                                                        <span className="font-mono">Volume: 12%</span>
                                                                    </div>
                                                                    <div className="h-4 w-full bg-cyan-950/20 border border-cyan-500/10 rounded-lg relative overflow-hidden flex items-center justify-around px-2">
                                                                        {[2, 3, 2, 4, 3, 2, 3, 4, 3, 2, 3, 4, 3, 2, 3, 4, 3, 2, 3, 2].map((h, i) => (
                                                                            <div key={i} className="w-0.5 bg-cyan-500/50 rounded-full" style={{ height: `${h * 10}%` }} />
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Assets section with optimize/swap triggers */}
                                                        <div className="space-y-3">
                                                            <div className="flex items-center justify-between">
                                                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Active Stock Video Segment</span>
                                                                <button
                                                                    onClick={() => setActiveSwapDrawerIndex(isDrawerOpen ? null : index)}
                                                                    className="px-3 py-1.5 rounded-lg border border-cyan-500/20 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-[8px] font-bold uppercase transition-all flex items-center gap-1.5"
                                                                >
                                                                    <Scissors className="h-2.5 w-2.5" /> Swap Asset
                                                                </button>
                                                            </div>
                                                            
                                                            <div className="flex gap-4 items-center">
                                                                <div className="shrink-0 h-20 w-32 bg-zinc-900 rounded-xl border border-white/5 overflow-hidden relative shadow-inner">
                                                                    {activeAsset && activeAsset.thumbnail ? (
                                                                        <img src={activeAsset.thumbnail} alt="" className="w-full h-full object-cover" />
                                                                    ) : (
                                                                        <div className="w-full h-full flex items-center justify-center text-zinc-700">
                                                                            <Video className="h-6 w-6" />
                                                                        </div>
                                                                    )}
                                                                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                                                                        <Play className="h-5 w-5 text-white filter drop-shadow-[0_0_10px_rgba(255,255,255,0.4)]" />
                                                                    </div>
                                                                </div>
                                                                <div className="space-y-1">
                                                                    <p className="text-[11px] font-bold text-white uppercase">{activeAsset?.title || `Stock_Footage_${index + 1}.mp4`}</p>
                                                                    <div className="flex flex-wrap gap-1">
                                                                        {(activeAsset?.tags || ["workspace", "technology", "abstract"]).slice(0, 3).map((tag: string, tIdx: number) => (
                                                                            <span key={tIdx} className="text-[7px] text-zinc-500 bg-white/5 px-1.5 py-0.5 rounded-sm uppercase font-mono">{tag}</span>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Asset replacement drawer */}
                                                            <AnimatePresence>
                                                                {isDrawerOpen && (
                                                                    <motion.div 
                                                                        initial={{ opacity: 0, height: 0 }}
                                                                        animate={{ opacity: 1, height: "auto" }}
                                                                        exit={{ opacity: 0, height: 0 }}
                                                                        className="overflow-hidden border-t border-white/5 pt-4 space-y-3"
                                                                    >
                                                                        <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Select Alternative Curation Candidate</span>
                                                                        <div className="grid grid-cols-3 gap-3">
                                                                            {[
                                                                                { title: "Digital Flow", thumbnail: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=150&auto=format&fit=crop&q=60", tags: ["cyber", "abstract"] },
                                                                                { title: "Team Work", thumbnail: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=150&auto=format&fit=crop&q=60", tags: ["corporate", "collaboration"] },
                                                                                { title: "Minimal Server", thumbnail: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=150&auto=format&fit=crop&q=60", tags: ["server", "database"] },
                                                                            ].map((alt, altIdx) => (
                                                                                <div 
                                                                                    key={altIdx}
                                                                                    onClick={() => {
                                                                                        setSwappedAssets(prev => ({
                                                                                            ...prev,
                                                                                            [index]: alt
                                                                                        }));
                                                                                        setActiveSwapDrawerIndex(null);
                                                                                        toast.success("Asset replaced visually", { description: "Timeline update will be committed on compile." });
                                                                                    }}
                                                                                    className="p-2 rounded-xl bg-white/2 border border-white/5 hover:border-cyan-500/40 cursor-pointer transition-all flex flex-col gap-2 group/alt"
                                                                                >
                                                                                    <div className="aspect-video w-full rounded-lg bg-zinc-950 overflow-hidden relative">
                                                                                        <img src={alt.thumbnail} alt="" className="w-full h-full object-cover group-hover/alt:scale-105 transition-transform" />
                                                                                    </div>
                                                                                    <span className="text-[8px] font-bold text-white uppercase truncate">{alt.title}</span>
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    
                                    {/* Right Column: Style Archetype & Modulator Canvas */}
                                    <div className="space-y-6 bg-white/2 border border-white/5 rounded-[28px] p-6 h-fit lg:sticky lg:top-0">
                                        <div className="flex items-center gap-2 pb-4 border-b border-white/5">
                                            <Palette className="h-4 w-4 text-cyan-400" />
                                            <span className="text-[10px] font-bold text-white uppercase tracking-widest">Neural Style Modulator</span>
                                        </div>
                                        
                                        {/* Presets Grid */}
                                        <div className="space-y-3">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Style Archetype Presets</span>
                                            <div className="grid grid-cols-2 gap-3">
                                                {[
                                                    { id: "NEON_CYBER", name: "Neon Cyber", style: "from-cyan-500 via-indigo-500 to-purple-600" },
                                                    { id: "AMBER_WARM", name: "Amber Warm", style: "from-amber-500 via-orange-500 to-red-600" },
                                                    { id: "MONOCHROME_DARK", name: "Mono Dark", style: "from-neutral-800 to-zinc-950" },
                                                    { id: "EMERALD_MATRIX", name: "Matrix Green", style: "from-emerald-600 via-teal-800 to-emerald-950" }
                                                ].map((preset) => (
                                                    <div 
                                                        key={preset.id}
                                                        onClick={() => setSelectedStylePreset(preset.id as "NEON_CYBER" | "AMBER_WARM" | "MONOCHROME_DARK" | "EMERALD_MATRIX")}
                                                        className={cn(
                                                            "p-3 rounded-xl border cursor-pointer transition-all flex flex-col gap-2",
                                                            selectedStylePreset === preset.id ? "bg-white/5 border-cyan-500" : "bg-transparent border-white/5 hover:border-white/10"
                                                        )}
                                                    >
                                                        <div className={cn("h-4 w-full rounded-md bg-gradient-to-r", preset.style)} />
                                                        <span className="text-[8px] font-bold text-white uppercase">{preset.name}</span>
                                                    </div>
                                                ))}
                                            </div>                            </div>

                                        {/* Modulator Sliders */}
                                        <div className="space-y-4 pt-2">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Modulation Sliders</span>
                                            
                                            {/* Temperature */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>COLOR TEMPERATURE</span>
                                                    <span>{colorTemp}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={colorTemp} 
                                                    onChange={e => setColorTemp(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>

                                            {/* VFX Grain */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>VFX GRAIN DENSITY</span>
                                                    <span>{grainDensity}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={grainDensity} 
                                                    onChange={e => setGrainDensity(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>

                                            {/* Contrast */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>SATURATION / CONTRAST</span>
                                                    <span>{contrast}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={contrast} 
                                                    onChange={e => setContrast(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>

                                            {/* Ken Burns */}
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[8px] font-mono text-zinc-400">
                                                    <span>KEN BURNS PANNING</span>
                                                    <span>{kenBurnsSpeed}%</span>
                                                </div>
                                                <input 
                                                    type="range" min="0" max="100" value={kenBurnsSpeed} 
                                                    onChange={e => setKenBurnsSpeed(Number(e.target.value))}
                                                    className="w-full accent-cyan-400 h-1 bg-white/5 rounded-lg appearance-none cursor-pointer"
                                                />
                                            </div>
                                            
                                            <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
                                                {availableCategories.map(cat => (
                                                    <button
                                                        key={cat}
                                                        onClick={() => setActiveCategory(cat)}
                                                        className={cn(
                                                            "px-3 py-1.5 rounded-lg text-[8px] font-bold uppercase tracking-widest whitespace-nowrap transition-all",
                                                            activeCategory === cat ? "bg-cyan-500 text-black" : "bg-white/5 text-zinc-500 hover:text-zinc-300"
                                                        )}
                                                    >
                                                        {cat}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Mock Video Canvas Preview */}
                                        <div className="pt-4 border-t border-white/5 space-y-3">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest block">Live Visual Frame Modulator</span>
                                            <div className="aspect-[9/16] w-full bg-zinc-950 border border-white/5 rounded-2xl relative overflow-hidden flex items-center justify-center">
                                                
                                                {/* Simulated image representing stock backgrounds */}
                                                <div 
                                                    className="absolute inset-0 transition-transform duration-1000 bg-cover bg-center"
                                                    style={{ 
                                                        backgroundImage: "url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=80')",
                                                        transform: `scale(${1 + (kenBurnsSpeed * 0.005)})`,
                                                        filter: `
                                                            contrast(${1 + (contrast - 50) * 0.01}) 
                                                            sepia(${(selectedStylePreset === 'AMBER_WARM' ? 50 : 0) + colorTemp * 0.2}%) 
                                                            hue-rotate(${selectedStylePreset === 'NEON_CYBER' ? 240 : selectedStylePreset === 'EMERALD_MATRIX' ? 100 : 0}deg)
                                                            grayscale(${selectedStylePreset === 'MONOCHROME_DARK' ? 100 : 0}%)
                                                        `
                                                    }}
                                                />
                                                
                                                {/* Simulated Film grain overlay */}
                                                <div 
                                                    className="absolute inset-0 bg-[#888] pointer-events-none mix-blend-overlay opacity-10"
                                                    style={{
                                                        backgroundImage: "radial-gradient(circle, #fff 10%, transparent 11%)",
                                                        backgroundSize: `${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`,
                                                        opacity: grainDensity * 0.004
                                                    }}
                                                />

                                                {/* Words caption overlay */}
                                                <div className="absolute inset-x-4 bottom-12 text-center z-10 px-2 pointer-events-none">
                                                    <span 
                                                        className="px-4 py-2 bg-yellow-400 text-black text-[13px] font-black uppercase rounded-lg shadow-2xl inline-block leading-tight filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)] border border-black/20"
                                                        style={{ textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}
                                                    >
                                                        DYNAMIC CAPTION
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            <div className="mt-8 pt-6 border-t border-white/5 flex justify-end">
                                <Button 
                                    onClick={() => setIsPreviewModalOpen(false)}
                                    className="bg-white/5 hover:bg-white/10 text-white font-bold uppercase tracking-widest text-[10px] border border-white/10 h-12 px-8 rounded-xl"
                                >
                                    Close Preview
                                </Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}            </AnimatePresence>
        </>
    );
}

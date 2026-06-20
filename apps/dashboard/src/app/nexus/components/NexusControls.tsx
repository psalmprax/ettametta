"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
    ChevronDown,
    CheckCircle2,
    AlertCircle,
    Plus,
    Settings2,
    Video,
    Brain,
    Clapperboard,
    Play,
    Loader2,
} from "lucide-react";
import { Blueprint } from "@/lib/types";
import { Button } from "@/components/ui/Button";

/** Module-internal — do not consume from outside. */
interface NexusControlsProps {
    niches: any[];
    selectedNiche: string;
    onNicheChange: (value: string) => void;
    creationMode: "cinema" | "blueprint";
    onCreationModeChange: (mode: "cinema" | "blueprint") => void;
    blueprints: Blueprint[];
    activeBlueprint: Blueprint | null;
    onBlueprintChange: (bp: Blueprint | null) => void;
    isLaunching: boolean;
    onLaunch: () => void;
    onNewBlueprint: () => void;
    onEditBlueprint: () => void;
}

export default function NexusControls({
    niches,
    selectedNiche,
    onNicheChange,
    creationMode,
    onCreationModeChange,
    blueprints,
    activeBlueprint,
    onBlueprintChange,
    isLaunching,
    onLaunch,
    onNewBlueprint,
    onEditBlueprint,
}: NexusControlsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
            <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Neural Target</label>
                <div className="relative">
                    <select
                        value={selectedNiche}
                        onChange={(e) => onNicheChange(e.target.value)}
                        className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none appearance-none cursor-pointer hover:bg-white/10 transition-colors"
                    >
                        {niches.length === 0 && <option value="">Loading Targets...</option>}
                        {niches?.map((n) => (
                            <option key={typeof n === "string" ? n : n.niche} value={typeof n === "string" ? n : n.niche} className="bg-[#0F0F11] text-white">
                                {typeof n === "string" ? n : n.niche}
                            </option>
                        ))}
                    </select>
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                        <ChevronDown className="w-4 h-4" />
                    </div>
                </div>
                <div className="flex items-center gap-2 pt-1">
                    <div className="h-1 w-1 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[8px] text-emerald-500/80 font-mono uppercase tracking-tighter">Pexels Stock Ready</span>
                </div>
            </div>

            <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Creation Mode</label>
                <div className="flex gap-2">
                    <button
                        onClick={() => onCreationModeChange("cinema")}
                        className={cn(
                            "flex-1 px-4 py-3 rounded-xl text-[9px] font-bold uppercase tracking-widest transition-all border",
                            creationMode === "cinema"
                                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.1)]"
                                : "bg-white/5 border-white/5 text-zinc-500 hover:text-zinc-300 hover:bg-white/10"
                        )}
                    >
                        <div className="flex flex-col items-center gap-1">
                            <Video className="h-4 w-4" />
                            <span>Stock Video</span>
                            <span className="text-[6px] text-emerald-500/60 tracking-wider">Quick Create</span>
                        </div>
                    </button>
                    <button
                        onClick={() => onCreationModeChange("blueprint")}
                        className={cn(
                            "flex-1 px-4 py-3 rounded-xl text-[9px] font-bold uppercase tracking-widest transition-all border",
                            creationMode === "blueprint"
                                ? "bg-violet-500/10 border-violet-500/30 text-violet-400 shadow-[0_0_20px_rgba(139,92,246,0.1)]"
                                : "bg-white/5 border-white/5 text-zinc-500 hover:text-zinc-300 hover:bg-white/10"
                        )}
                    >
                        <div className="flex flex-col items-center gap-1">
                            <Brain className="h-4 w-4" />
                            <span>AI Blueprint</span>
                            <span className="text-[6px] text-violet-500/60 tracking-wider">Requires GPU</span>
                        </div>
                    </button>
                </div>
                {creationMode === "cinema" && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                        <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                        <span className="text-[7px] text-emerald-400/80 font-mono">Pexels Stock + Remotion Render — Working Now</span>
                    </div>
                )}
                {creationMode === "blueprint" && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/5 border border-amber-500/10">
                        <AlertCircle className="h-3 w-3 text-amber-500 shrink-0" />
                        <span className="text-[7px] text-amber-400/80 font-mono">Requires GPU Node — Configure RENDER_NODE_URL</span>
                    </div>
                )}
            </div>

            {creationMode === "blueprint" && (
                <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                    <div className="flex items-center justify-between">
                        <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Active Blueprint</label>
                        <div className="flex gap-1.5">
                            <button
                                onClick={onNewBlueprint}
                                className="px-2.5 py-1 rounded-lg bg-violet-500/10 border border-violet-500/20 text-[8px] font-bold text-violet-400 uppercase tracking-wider hover:bg-violet-500/20 transition-colors"
                                title="Create or edit blueprint settings"
                            >
                                <Plus className="h-3 w-3 inline mr-1" />
                                New
                            </button>
                            {activeBlueprint && (
                                <button
                                    onClick={onEditBlueprint}
                                    className="px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-[8px] font-bold text-cyan-400 uppercase tracking-wider hover:bg-cyan-500/20 transition-colors"
                                    title="Open visual node editor"
                                >
                                    <Settings2 className="h-3 w-3 inline mr-1" />
                                    Edit
                                </button>
                            )}
                        </div>
                    </div>
                    <div className="relative">
                        <select
                            value={activeBlueprint?.id}
                            onChange={(e) => onBlueprintChange(blueprints.find((b) => b.id === e.target.value) || null)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none appearance-none cursor-pointer hover:bg-white/10 transition-colors"
                        >
                            {blueprints?.map((b) => (
                                <option key={b.id} value={b.id} className="bg-[#0F0F11] text-white">
                                    {b.name}
                                </option>
                            ))}
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                            <ChevronDown className="w-4 h-4" />
                        </div>
                    </div>
                </div>
            )}

            <div className="flex flex-col justify-end">
                <Button
                    onClick={onLaunch}
                    disabled={isLaunching || !selectedNiche || (creationMode === "blueprint" && !activeBlueprint)}
                    className={cn(
                        "w-full h-16 text-black font-bold text-lg rounded-2xl transition-all uppercase tracking-widest",
                        creationMode === "cinema"
                            ? "bg-emerald-500 hover:bg-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.3)]"
                            : "bg-violet-500 hover:bg-violet-400 shadow-[0_0_30px_rgba(139,92,246,0.3)]"
                    )}
                >
                    {isLaunching ? (
                        <Loader2 className="h-6 w-6 animate-spin" />
                    ) : creationMode === "cinema" ? (
                        <><Clapperboard className="h-5 w-5 mr-2" /> Create Video</>
                    ) : (
                        <><Play className="h-5 w-5 mr-2" /> Dispatch Blueprint</>
                    )}
                </Button>
            </div>
        </div>
    );
}

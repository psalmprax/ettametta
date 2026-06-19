"use client";

import React from "react";
import {
    ChevronDown,
    Plus,
    Play,
    Settings2,
    Clapperboard,
    CheckCircle2,
    AlertCircle,
    Video,
    Brain,
    Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { NexusNode } from "@/components/ui/NexusNode";
import { Blueprint, NexusJob } from "@/lib/types";
import {
    CreationMode,
} from "@/hooks/useNexusData";

interface Props {
    niches: any[];
    selectedNiche: string;
    setSelectedNiche: (niche: string) => void;
    blueprints: Blueprint[];
    activeBlueprint: Blueprint | null;
    setActiveBlueprint: (bp: Blueprint | null) => void;
    creationMode: CreationMode;
    setCreationMode: (mode: CreationMode) => void;
    activePipelineJob: NexusJob | undefined;
    selectedNodeIndex: number;
    setSelectedNodeIndex: (idx: number) => void;
    isLaunching: boolean;
    handleLaunchPipeline: () => void;
    onOpenBlueprintBuilder: () => void;
    onOpenNeuralCanvas: () => void;
}

function getNodeCoords(idx: number, listLength: number): { x: number; y: number } {
    let x = 15 + (idx / Math.max(listLength - 1, 1)) * 70;
    let y = 50;
    if (listLength >= 4) {
        if (idx === 0) { x = 15; y = 50; }
        else if (idx === 1) { x = 45; y = 25; }
        else if (idx === 2) { x = 45; y = 75; }
        else if (idx === 3) { x = 75; y = 50; }
        else if (idx >= 4) { x = 90; y = 50; }
    }
    return { x, y };
}

function getNodeParents(idx: number, listLength: number): number[] {
    if (listLength < 4) return [idx - 1];
    if (idx === 1 || idx === 2) return [0];
    if (idx === 3) return [1, 2];
    if (idx === 4) return [3];
    return [idx - 1];
}

export default function OrchestratorTab({
    niches,
    selectedNiche,
    setSelectedNiche,
    blueprints,
    activeBlueprint,
    setActiveBlueprint,
    creationMode,
    setCreationMode,
    activePipelineJob,
    selectedNodeIndex,
    setSelectedNodeIndex,
    isLaunching,
    handleLaunchPipeline,
    onOpenBlueprintBuilder,
    onOpenNeuralCanvas,
}: Props) {
    const listLength = activeBlueprint?.nodes?.length || 0;

    return (
        <div className="space-y-8 h-full flex flex-col">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
                {/* Neural Target Selector */}
                <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                        Neural Target
                    </label>
                    <div className="relative">
                        <select
                            value={selectedNiche}
                            onChange={(e) => setSelectedNiche(e.target.value)}
                            className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-white font-bold uppercase tracking-tight focus:outline-none appearance-none cursor-pointer hover:bg-white/10 transition-colors"
                        >
                            {niches.length === 0 && <option value="">Loading Targets...</option>}
                            {niches?.map((n) => {
                                const val = typeof n === "string" ? n : n.niche;
                                return (
                                    <option key={val} value={val} className="bg-[#0F0F11] text-white">
                                        {val}
                                    </option>
                                );
                            })}
                        </select>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                            <ChevronDown className="w-4 h-4" />
                        </div>
                    </div>
                    <div className="flex items-center gap-2 pt-1">
                        <div className="h-1 w-1 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[8px] text-emerald-500/80 font-mono uppercase tracking-tighter">
                            Pexels Stock Ready
                        </span>
                    </div>
                </div>

                {/* Creation Mode Toggle */}
                <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                        Creation Mode
                    </label>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setCreationMode("cinema")}
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
                            onClick={() => setCreationMode("blueprint")}
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
                            <span className="text-[7px] text-emerald-400/80 font-mono">
                                Pexels Stock + Remotion Render — Working Now
                            </span>
                        </div>
                    )}
                    {creationMode === "blueprint" && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/5 border border-amber-500/10">
                            <AlertCircle className="h-3 w-3 text-amber-500 shrink-0" />
                            <span className="text-[7px] text-amber-400/80 font-mono">
                                Requires GPU Node — Configure RENDER_NODE_URL
                            </span>
                        </div>
                    )}
                </div>

                {/* Blueprint Selector (visible only in blueprint mode) */}
                {creationMode === "blueprint" && (
                    <div className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 space-y-4 backdrop-blur-xl relative">
                        <div className="flex items-center justify-between">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                Active Blueprint
                            </label>
                            <div className="flex gap-1.5">
                                <button
                                    onClick={onOpenBlueprintBuilder}
                                    className="px-2.5 py-1 rounded-lg bg-violet-500/10 border border-violet-500/20 text-[8px] font-bold text-violet-400 uppercase tracking-wider hover:bg-violet-500/20 transition-colors"
                                    title="Create or edit blueprint settings"
                                >
                                    <Plus className="h-3 w-3 inline mr-1" />
                                    New
                                </button>
                                {activeBlueprint && (
                                    <button
                                        onClick={onOpenNeuralCanvas}
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
                                onChange={(e) =>
                                    setActiveBlueprint(blueprints.find((b) => b.id === e.target.value) || null)
                                }
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
                        onClick={handleLaunchPipeline}
                        disabled={
                            isLaunching ||
                            !selectedNiche ||
                            (creationMode === "blueprint" && !activeBlueprint)
                        }
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
                            <>
                                <Clapperboard className="h-5 w-5 mr-2" /> Create Video
                            </>
                        ) : (
                            <>
                                <Play className="h-5 w-5 mr-2" /> Dispatch Blueprint
                            </>
                        )}
                    </Button>
                </div>
            </div>

            <div className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">
                <div className="absolute inset-0 architect-grid pointer-events-none opacity-40" />

                {/* Connection Mesh Overlay */}
                <div className="absolute inset-0 z-0 pointer-events-none">
                    <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                        <defs>
                            <linearGradient id="glowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.6" />
                                <stop offset="50%" stopColor="#22d3ee" stopOpacity="1" />
                                <stop offset="100%" stopColor="#10b981" stopOpacity="0.6" />
                            </linearGradient>
                            <filter id="glowFilter" x="-10%" y="-10%" width="120%" height="120%">
                                <feGaussianBlur stdDeviation="1.5" result="blur" />
                                <feMerge>
                                    <feMergeNode in="blur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                        </defs>

                        {activeBlueprint?.nodes?.map((node, idx) => {
                            if (idx === 0) return null;
                            const parents = getNodeParents(idx, listLength);

                            return parents.map((parentIdx, pI) => {
                                const start = getNodeCoords(parentIdx, listLength);
                                const end = getNodeCoords(idx, listLength);
                                const isPathActive =
                                    activePipelineJob?.status === "Active" &&
                                    (selectedNodeIndex === idx || selectedNodeIndex === parentIdx);
                                const pathD = `M ${start.x} ${start.y} C ${(start.x + end.x) / 2} ${start.y}, ${(start.x + end.x) / 2} ${end.y}, ${end.x} ${end.y}`;
                                return (
                                    <g key={`${parentIdx}-${idx}-${pI}`}>
                                        <path d={pathD} stroke="rgba(255,255,255,0.03)" strokeWidth="2.5" fill="none" />
                                        <path
                                            d={pathD}
                                            stroke="url(#glowGrad)"
                                            strokeWidth={isPathActive ? "2.5" : "1"}
                                            fill="none"
                                            filter="url(#glowFilter)"
                                            className={cn(
                                                "transition-all duration-500",
                                                isPathActive ? "opacity-100" : "opacity-20"
                                            )}
                                            strokeDasharray={isPathActive ? "4, 4" : undefined}
                                        />
                                    </g>
                                );
                            });
                        })}
                    </svg>
                </div>

                {/* Position Nodes */}
                <div className="absolute inset-0 z-10">
                    {activeBlueprint?.nodes?.map((node, idx) => {
                        const isProcessing =
                            activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                        const isComplete =
                            activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                        const { x, y } = getNodeCoords(idx, listLength);
                        return (
                            <div
                                key={idx}
                                className="absolute"
                                style={{ left: `${x}%`, top: `${y}%`, transform: "translate(-50%, -50%)" }}
                            >
                                <NexusNode
                                    type={node.type as any}
                                    label={node.label}
                                    description={node.desc}
                                    status={isComplete ? "complete" : isProcessing ? "processing" : "pending"}
                                    progress={isProcessing ? activePipelineJob.progress : undefined}
                                    active={selectedNodeIndex === idx}
                                    onClick={() => setSelectedNodeIndex(idx)}
                                />
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

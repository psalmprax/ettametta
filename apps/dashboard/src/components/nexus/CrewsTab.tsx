"use client";

import React from "react";
import {
    Bot,
    Search,
    Users,
    Network,
    Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface Props {
    capabilities: any[];
    searchTerm: string;
    setSearchTerm: (s: string) => void;
    activeCategory: string;
    setActiveCategory: (c: string) => void;
    filteredCapabilities: any[];
    availableCategories: string[];
    deployingIds: Set<string>;
    handleDeployAgent: (worker: any) => void;
    pulseLoadAvg: number | undefined;
}

export default function CrewsTab({
    capabilities,
    searchTerm,
    setSearchTerm,
    activeCategory,
    setActiveCategory,
    filteredCapabilities,
    availableCategories,
    deployingIds,
    handleDeployAgent,
    pulseLoadAvg,
}: Props) {
    return (
        <div className="space-y-8 h-full flex flex-col">
            <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">
                    Workforce Orchestrator
                </h3>
                <div className="flex gap-4">
                    <div className="px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold uppercase tracking-widest">
                        {capabilities.length} Available Skills
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 min-h-0">
                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col overflow-hidden">
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h4 className="text-sm font-bold text-white uppercase tracking-widest">
                                Specialized Agents
                            </h4>
                            <Bot className="h-4 w-4 text-cyan-400" />
                        </div>

                        <div className="flex flex-col gap-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-500" />
                                <input
                                    type="text"
                                    placeholder="Search skills..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full bg-white/5 border border-white/5 rounded-xl pl-10 pr-4 py-2 text-[10px] text-white focus:outline-none focus:border-cyan-500/30 transition-all"
                                />
                            </div>

                            <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
                                {availableCategories.map((cat) => (
                                    <button
                                        key={cat}
                                        onClick={() => setActiveCategory(cat)}
                                        className={cn(
                                            "px-3 py-1.5 rounded-lg text-[8px] font-bold uppercase tracking-widest whitespace-nowrap transition-all",
                                            activeCategory === cat
                                                ? "bg-cyan-500 text-black"
                                                : "bg-white/5 text-zinc-500 hover:text-zinc-300"
                                        )}
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4 overflow-y-auto custom-scrollbar pr-2 flex-1">
                        {filteredCapabilities.map((worker, i) => {
                            const isDeploying = deployingIds.has(worker.id || worker.name);
                            return (
                                <div
                                    key={i}
                                    className={cn(
                                        "p-6 bg-white/5 border border-white/5 rounded-2xl group transition-all flex items-center justify-between gap-4",
                                        isDeploying
                                            ? "border-cyan-500/50 bg-cyan-500/5 shadow-[0_0_20px_rgba(34,211,238,0.1)]"
                                            : "hover:border-cyan-500/30"
                                    )}
                                >
                                    <div className="space-y-1 flex-1">
                                        <div className="flex items-center gap-2">
                                            <h5 className="text-sm font-bold text-white uppercase tracking-tight">
                                                {worker.name}
                                            </h5>
                                            <span
                                                className={cn(
                                                    "text-[7px] px-1.5 py-0.5 rounded-sm border uppercase font-bold",
                                                    isDeploying
                                                        ? "bg-amber-500/10 text-amber-500 border-amber-500/20 animate-pulse"
                                                        : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                                                )}
                                            >
                                                {isDeploying ? "DEPLOYING..." : worker.category}
                                            </span>
                                        </div>
                                        <p className="text-[10px] text-zinc-500 line-clamp-2">
                                            {worker.description}
                                        </p>
                                        <p className="text-[8px] text-zinc-600 font-mono uppercase tracking-tighter pt-1">
                                            {worker.stability} Stability
                                        </p>
                                    </div>
                                    <div className="flex flex-col items-end gap-3">
                                        <span className="text-[10px] text-zinc-600 font-mono">
                                            CR: {worker.credits_per_task}
                                        </span>
                                        <Button
                                            onClick={() => handleDeployAgent(worker)}
                                            disabled={isDeploying}
                                            variant="ghost"
                                            size="sm"
                                            className={cn(
                                                "h-8 text-[10px] font-bold border border-white/5",
                                                isDeploying
                                                    ? "text-amber-500 bg-amber-500/5"
                                                    : "text-cyan-400 hover:bg-cyan-500/10"
                                            )}
                                        >
                                            {isDeploying ? (
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                            ) : (
                                                "Deploy"
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            );
                        })}
                        {filteredCapabilities.length === 0 && (
                            <div className="py-20 text-center space-y-4 opacity-20">
                                <Users className="h-12 w-12 mx-auto" />
                                <p className="text-xs font-bold uppercase tracking-widest">
                                    No Agents Match Filters
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col items-center justify-center space-y-8 text-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-linear-to-b from-cyan-500/5 to-transparent pointer-events-none" />
                    <Network className="h-20 w-20 text-cyan-500/20 animate-pulse" />
                    <div className="space-y-4 z-10">
                        <h4 className="text-xl font-bold text-white uppercase tracking-tighter">
                            Neural Workforce Mesh
                        </h4>
                        <p className="text-xs text-zinc-500 max-w-[280px] leading-relaxed mx-auto">
                            Orchestrate multiple specialized agents into a unified autonomous
                            crew. The mesh is currently operating at{" "}
                            {pulseLoadAvg ? Math.round(pulseLoadAvg * 100) : 12}% global capacity.
                        </p>
                    </div>
                    <Button className="h-14 px-10 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-2xl uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(8,145,178,0.3)] transition-all hover:scale-105">
                        Initialize New Crew
                    </Button>
                </div>
            </div>
        </div>
    );
}

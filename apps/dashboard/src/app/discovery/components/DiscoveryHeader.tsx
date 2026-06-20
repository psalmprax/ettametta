"use client";

import React from "react";
import { Search, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

/** Module-internal — do not consume from outside. */
interface AnalysisTask {
    task_id: string;
    status: string;
    result?: any;
    niche: string;
}

interface DiscoveryHeaderProps {
    activeNiche: string;
    onNicheChange: (value: string) => void;
    isKeywordSearch: boolean;
    onKeywordSearchChange: (value: boolean) => void;
    activeRegion: string;
    onRegionChange: (regionId: string) => void;
    isScanning: boolean;
    onScan: () => void;
    analysisTasks: Record<string, AnalysisTask>;
    onCreateFromAnalysis: (taskId: string, candidateId: string, niche: string) => void;
}

/** Module-internal — do not consume from outside. */
const REGIONS = [
    { id: "US", label: "USA", flag: "\u{1F1FA}\u{1F1F8}" },
    { id: "GB", label: "United Kingdom", flag: "\u{1F1EC}\u{1F1E7}" },
    { id: "DE", label: "Germany", flag: "\u{1F1E9}\u{1F1EA}" },
    { id: "CA", label: "Canada", flag: "\u{1F1E8}\u{1F1E6}" },
    { id: "FR", label: "France", flag: "\u{1F1EB}\u{1F1F7}" },
    { id: "AU", label: "Australia", flag: "\u{1F1E6}\u{1F1FA}" },
];

export function DiscoveryHeader({
    activeNiche,
    onNicheChange,
    isKeywordSearch,
    onKeywordSearchChange,
    activeRegion,
    onRegionChange,
    isScanning,
    onScan,
    analysisTasks,
    onCreateFromAnalysis,
}: DiscoveryHeaderProps) {
    return (
        <div className="space-y-8 h-full flex flex-col">
            <div className="flex items-center gap-6 shrink-0">
                <div className="relative flex-1">
                    <input
                        type="text"
                        placeholder={isKeywordSearch ? "SEARCH_KEYWORD_FOR_CANDIDATES..." : "SCAN_NICHE_FOR_VIRALITY..."}
                        value={activeNiche}
                        onChange={(e) => {
                            onNicheChange(e.target.value);
                            onKeywordSearchChange(false);
                        }}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                onScan();
                            }
                        }}
                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 pl-14 text-white font-mono text-lg focus:outline-none focus:border-primary/50"
                    />
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
                </div>
                <Button
                    onClick={onScan}
                    disabled={isScanning}
                    className="h-20 px-10 bg-primary text-black font-bold text-lg rounded-2xl uppercase tracking-widest flex items-center gap-3"
                >
                    {isScanning ? (
                        <>
                            <Loader2 className="h-6 w-6 animate-spin" />
                            {isKeywordSearch ? "Searching..." : "Scanning..."}
                        </>
                    ) : (
                        isKeywordSearch ? "Search" : "Initiate Scan"
                    )}
                </Button>
            </div>

            {Object.keys(analysisTasks).length > 0 && (
                <div className="shrink-0 rounded-2xl bg-[#0F0F11]/60 border border-white/5 p-4 space-y-2">
                    <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest">Active Analysis Tasks</span>
                    {Object.entries(analysisTasks).map(([id, task]) => (
                        <div key={id} className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3 text-[10px]">
                            <span className="text-zinc-300 font-mono truncate flex-1">{id}</span>
                            <div className="flex items-center gap-3">
                                <span className={cn("px-2 py-0.5 rounded text-[8px] font-bold uppercase",
                                    task.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-400" :
                                    task.status === "FAILED" ? "bg-rose-500/20 text-rose-400" :
                                    "bg-amber-500/20 text-amber-400"
                                )}>{task.status}</span>
                                {task.status === "COMPLETED" && (
                                    <button
                                        onClick={() => onCreateFromAnalysis(task.task_id, id, task.niche)}
                                        className="px-3 py-1.5 bg-violet-500 hover:bg-violet-400 text-black font-bold text-[8px] uppercase rounded-lg tracking-widest"
                                    >
                                        Create Video
                                    </button>
                                )}
                                {task.status === "FAILED" && (
                                    <XCircle className="h-3.5 w-3.5 text-rose-500" />
                                )}
                                {(task.status === "PENDING" || task.status === "QUEUED") && (
                                    <Loader2 className="h-3.5 w-3.5 text-amber-500 animate-spin" />
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="flex items-center gap-2 overflow-x-auto pb-2 shrink-0">
                {REGIONS.map((reg) => (
                    <button
                        key={reg.id}
                        onClick={() => onRegionChange(reg.id)}
                        disabled={isScanning}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-xl border transition-all shrink-0",
                            activeRegion === reg.id
                                ? "bg-primary/20 border-primary/50 text-white shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)]"
                                : "bg-white/5 border-white/10 text-zinc-500 hover:border-white/20",
                            isScanning && "opacity-50 cursor-not-allowed"
                        )}
                    >
                        <span className="text-sm">{reg.flag}</span>
                        <span className="text-[10px] font-bold uppercase tracking-tight">{reg.label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}

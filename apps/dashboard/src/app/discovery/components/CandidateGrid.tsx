"use client";

import React from "react";
import { Search } from "lucide-react";
import { CandidateCard } from "./CandidateCard";
import type { ContentCandidate } from "./DiscoveryContent";

interface CandidateGridProps {
    candidates: ContentCandidate[];
    isScanning: boolean;
    isKeywordSearch: boolean;
    activeNiche: string;
    credits: number;
    onAnalyze: (candidate: ContentCandidate) => void;
    onRemoveCandidate: (id: string) => void;
    onCreateVideo: (title: string) => void;
}

export function CandidateGrid({
    candidates,
    isScanning,
    isKeywordSearch,
    activeNiche,
    credits,
    onAnalyze,
    onRemoveCandidate,
    onCreateVideo,
}: CandidateGridProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 overflow-y-auto custom-scrollbar p-1">
            {candidates.length === 0 && !isScanning && (
                <div className="col-span-full flex flex-col items-center justify-center py-24 opacity-40 gap-4">
                    <Search className="h-16 w-16 text-zinc-600" />
                    <div className="text-center space-y-2">
                        <p className="text-lg font-bold text-white uppercase tracking-widest">
                            {isKeywordSearch ? `No results for "${activeNiche}"` : "Scan a niche to discover viral content"}
                        </p>
                        <p className="text-sm text-zinc-500 font-mono">
                            {isKeywordSearch
                                ? "Try a different keyword, or browse trending niches below."
                                : "Type a niche name above and press Enter or click Initiate Scan."}
                        </p>
                    </div>
                </div>
            )}
            {candidates.map((c) => (
                <CandidateCard
                    key={c.id}
                    candidate={c}
                    credits={credits}
                    onAnalyze={onAnalyze}
                    onRemove={onRemoveCandidate}
                    onCreateVideo={onCreateVideo}
                />
            ))}
        </div>
    );
}

"use client";

import React from "react";
import { copyToClipboard } from "@/lib/utils";
import { toast } from "sonner";
import { DesignCard } from "@/components/ui/DesignCard";
import type { ContentCandidate } from "./DiscoveryContent";

interface CandidateCardProps {
    candidate: ContentCandidate;
    credits: number;
    onAnalyze: (candidate: ContentCandidate) => void;
    onRemove: (id: string) => void;
    onCreateVideo: (title: string) => void;
}

export function CandidateCard({ candidate: c, credits, onAnalyze, onRemove, onCreateVideo }: CandidateCardProps) {
    return (
        <DesignCard
            title={c.title}
            status="Viral"
            metrics={[
                { label: "Viral Score", value: `${c.viral_score}%`, progress: c.viral_score, color: "text-emerald-400" },
                { label: "Views", value: `${(c.view_count / 1000).toFixed(1)}K`, color: "text-cyan-400" }
            ]}
            footerInfo={`${c.platform.toUpperCase()} • ${c.creator_name}`}
            toolsStatus="Live"
            credits={credits}
            onRefresh={() => onAnalyze(c)}
            onDelete={() => {
                onRemove(c.id);
                toast.error(`Purged Candidate: ${c.title.slice(0, 20)}...`);
            }}
            onShare={async () => {
                const success = await copyToClipboard(`https://ettametta.ai/discovery/candidate/${c.id}`);
                if (success) {
                    toast.success("Candidate Intelligence Link Copied");
                } else {
                    toast.error("Clipboard access not available");
                }
            }}
            onClick={() => onCreateVideo(c.title)}
        />
    );
}

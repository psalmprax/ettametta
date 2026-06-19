"use client";

import React from "react";
import { ShieldCheck, Target } from "lucide-react";
import { toast } from "sonner";
import { DesignCard } from "@/components/ui/DesignCard";

/** Module-internal — do not consume from outside. */
interface Props {
    sentinelStatus: any;
    pulse: any;
    onShareClipboard: (txt: string) => void;
    onRefresh: () => void;
}

/**
 * Sentinel tab — Algo Sentinel compliance card + Strategic Intelligence
 * recommendations list.
 */
export default function SentinelView({
    sentinelStatus,
    pulse,
    onShareClipboard,
    onRefresh,
}: Props) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <DesignCard
                title="Algorithm Sentinel"
                status={sentinelStatus?.status || "NOMINAL"}
                metrics={[
                    { label: "Sync Score", value: `${sentinelStatus?.score || 0}%`, progress: sentinelStatus?.score || 0, color: "text-violet-400" },
                    { label: "Platform Drift", value: "Minimal", color: "text-cyan-400" },
                ]}
                footerInfo="SCANNING: GLOBAL_ALGO_MATRIX"
                toolsStatus="Active"
                credits={pulse?.credits || 0}
                onRefresh={onRefresh}
                onMore={() => toast.success("Sentinel Diagnostics Fetched")}
                onShare={() => onShareClipboard("https://ettametta.ai/sentinel/status")}
                onDelete={() => toast.error("Security Protocol: System Core Protection Active. Deletion restricted.")}
            />
            <div className="lg:col-span-2 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                    <ShieldCheck className="h-5 w-5 text-violet-400" />
                    Strategic Intelligence
                </h3>
                <div className="grid grid-cols-1 gap-4">
                    {Array.isArray(sentinelStatus?.recommendations) && sentinelStatus.recommendations.map((rec: string, i: number) => (
                        <div key={i} className="p-5 bg-white/5 border border-white/5 rounded-2xl flex items-center gap-4 group hover:border-violet-500/30 transition-all">
                            <Target className="h-4 w-4 text-violet-400 shrink-0" />
                            <p className="text-xs text-zinc-400 font-medium leading-relaxed">{rec}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

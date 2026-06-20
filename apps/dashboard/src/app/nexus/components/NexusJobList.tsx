"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { RefreshCw, Coins } from "lucide-react";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { NexusJob } from "@/lib/types";

/** Module-internal — do not consume from outside. */
interface NexusJobListProps {
    nexusJobs: NexusJob[];
    credits: number | null;
    refreshCredits: () => void;
    pulse: any;
    agents: any[];
    onPreviewScenes: (jobId: string) => void;
    onDeleteJob: (jobId: string) => void;
}

export default function NexusJobList({
    nexusJobs,
    credits,
    refreshCredits,
    pulse,
    agents,
    onPreviewScenes,
    onDeleteJob,
}: NexusJobListProps) {
    return (
        <>
            <button
                onClick={() => refreshCredits()}
                className="w-full p-4 rounded-2xl border border-white/5 bg-[#0F0F11]/60 space-y-2 mb-4 hover:bg-white/5 transition-colors group text-left"
                title="Refresh credit balance"
            >
                <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Credits</span>
                    <RefreshCw className="h-2.5 w-2.5 text-amber-500/50 group-hover:text-amber-400 group-hover:rotate-180 transition-all" />
                </div>
                <div className="flex items-center gap-2">
                    <Coins className="h-4 w-4 text-amber-400" />
                    <span className="text-sm font-bold text-white tabular-nums">{credits ?? "—"}</span>
                </div>
            </button>
            <div className="p-4 rounded-2xl border border-white/5 bg-[#0F0F11]/60 space-y-2 mb-4">
                <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Node_ID</span>
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                </div>
                <h4 className="text-xs font-mono font-bold text-white uppercase tracking-tight">{pulse?.cluster_node || "NODE-LOCAL-01"}</h4>
            </div>
            <AgentMatrix agents={agents} />
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-[10px] font-bold text-zinc-500 tracking-[0.2em] uppercase">Pipeline Queue</h3>
                    <div className="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded text-[8px] font-bold text-cyan-400 uppercase">
                        Live_Status
                    </div>
                </div>
                <div className="space-y-2">
                    {nexusJobs?.slice(0, 3).map((job) => (
                        <div key={job.id} className="p-4 rounded-2xl border border-white/5 bg-white/5 flex items-center justify-between group hover:bg-white/8 transition-all">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] font-bold text-white uppercase tracking-tight">{job.niche}</span>
                                <div className="flex items-center gap-2">
                                    <div className={cn("h-1 w-1 rounded-full", job.status === "Active" ? "bg-emerald-500" : "bg-zinc-600")} />
                                    <span className="text-[8px] text-zinc-500 font-mono uppercase tracking-tighter">{job.status}</span>
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-1.5">
                                <span className="text-[10px] font-bold text-cyan-400">{job.progress || 0}%</span>
                                <div className="h-0.5 w-16 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-cyan-500" style={{ width: `${job.progress || 0}%` }} />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}

/** Module-internal — do not consume from outside. */
interface NexusJobHistoryProps {
    nexusJobs: NexusJob[];
    onPreviewScenes: (jobId: string) => void;
    onDeleteJob: (jobId: string) => void;
}

export function NexusJobHistory({ nexusJobs, onPreviewScenes, onDeleteJob }: NexusJobHistoryProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar p-1">
            {nexusJobs?.map((job) => (
                <DesignCard
                    key={job.id}
                    title={`PIPELINE_${job.id}`}
                    status={job.status}
                    metrics={[
                        { label: "Completion", value: `${job.progress || 0}%`, progress: job.progress, color: "text-cyan-400" },
                        { label: "Niche", value: job.niche, color: "text-zinc-500" },
                    ]}
                    footerInfo={new Date(job.created_at).toLocaleString()}
                    toolsStatus="Verified"
                    onRefresh={() => onPreviewScenes(job.id)}
                    onDelete={() => onDeleteJob(job.id)}
                />
            ))}
        </div>
    );
}

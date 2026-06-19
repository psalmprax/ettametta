"use client";

import React from "react";
import { Coins, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { NexusJob } from "@/lib/types";

interface Props {
    credits: number | null;
    onRefreshCredits: () => void;
    clusterNode: string | undefined;
    agents: any;
    nexusJobs: NexusJob[];
}

export default function NexusRightPanel({
    credits,
    onRefreshCredits,
    clusterNode,
    agents,
    nexusJobs,
}: Props) {
    return (
        <>
            <button
                onClick={onRefreshCredits}
                className="w-full p-4 rounded-2xl border border-white/5 bg-[#0F0F11]/60 space-y-2 mb-4 hover:bg-white/5 transition-colors group text-left"
                title="Refresh credit balance"
            >
                <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                        Credits
                    </span>
                    <RefreshCw className="h-2.5 w-2.5 text-amber-500/50 group-hover:text-amber-400 group-hover:rotate-180 transition-all" />
                </div>
                <div className="flex items-center gap-2">
                    <Coins className="h-4 w-4 text-amber-400" />
                    <span className="text-sm font-bold text-white tabular-nums">
                        {credits ?? "—"}
                    </span>
                </div>
            </button>

            <div className="p-4 rounded-2xl border border-white/5 bg-[#0F0F11]/60 space-y-2 mb-4">
                <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                        Node_ID
                    </span>
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                </div>
                <h4 className="text-xs font-mono font-bold text-white uppercase tracking-tight">
                    {clusterNode || "NODE-LOCAL-01"}
                </h4>
            </div>

            <AgentMatrix agents={agents} />

            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-[10px] font-bold text-zinc-500 tracking-[0.2em] uppercase">
                        Pipeline Queue
                    </h3>
                    <div className="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded text-[8px] font-bold text-cyan-400 uppercase">
                        Live_Status
                    </div>
                </div>
                <div className="space-y-2">
                    {nexusJobs?.slice(0, 3).map((job) => (
                        <div
                            key={job.id}
                            className="p-4 rounded-2xl border border-white/5 bg-white/5 flex items-center justify-between group hover:bg-white/8 transition-all"
                        >
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] font-bold text-white uppercase tracking-tight">
                                    {job.niche}
                                </span>
                                <div className="flex items-center gap-2">
                                    <div
                                        className={cn(
                                            "h-1 w-1 rounded-full",
                                            job.status === "Active"
                                                ? "bg-emerald-500"
                                                : "bg-zinc-600"
                                        )}
                                    />
                                    <span className="text-[8px] text-zinc-500 font-mono uppercase tracking-tighter">
                                        {job.status}
                                    </span>
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-1.5">
                                <span className="text-[10px] font-bold text-cyan-400">
                                    {job.progress || 0}%
                                </span>
                                <div className="h-0.5 w-16 bg-white/5 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-cyan-500"
                                        style={{ width: `${job.progress || 0}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}

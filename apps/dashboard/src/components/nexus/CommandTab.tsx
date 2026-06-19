"use client";

import React from "react";
import { CommandPod } from "@/components/ui/CommandPod";
import { Button } from "@/components/ui/Button";
import { NexusJob, Persona } from "@/lib/types";

interface Props {
    status: "open" | "closed" | string;
    clusterLoadAvg: number | undefined;
    personasLength: number;
    nexusJobs: NexusJob[];
    isLaunching: boolean;
}

export default function CommandTab({
    status,
    clusterLoadAvg,
    personasLength,
    nexusJobs,
    isLaunching,
}: Props) {
    const processingJobs = nexusJobs.filter(
        (j) => j.status === "processing"
    ).length;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar pr-4">
            <CommandPod
                name="Nexus Master Core"
                status={status === "open" ? "nominal" : "offline"}
                load={clusterLoadAvg ? Math.round(clusterLoadAvg * 100) : 15}
                circuitBreaker="closed"
                description="Primary orchestration layer for global Nexus Workforce. Synchronizing 14 neural channels."
            />
            <CommandPod
                name="Neural ID Gateway"
                status="nominal"
                load={personasLength > 0 ? 8 : 2}
                circuitBreaker="closed"
                description="High-throughput ingress for autonomous identity verification and persona mapping."
            />
            <CommandPod
                name="Pipeline Dispatcher"
                status={isLaunching ? "nominal" : "nominal"}
                load={processingJobs * 20}
                circuitBreaker="closed"
                description="Real-time job scheduling and blueprint execution engine."
            />
            <div className="col-span-full p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex items-center justify-between">
                <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                        Global Master Override
                    </span>
                    <h4 className="text-lg font-bold text-white uppercase tracking-tight">
                        Emergency System Halt
                    </h4>
                </div>
                <Button
                    variant="outline"
                    className="h-14 px-10 border-rose-500/20 text-rose-500 hover:bg-rose-500 hover:text-white font-bold uppercase tracking-widest text-[10px]"
                >
                    Execute Halt_0
                </Button>
            </div>
        </div>
    );
}

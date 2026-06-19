"use client";

import React from "react";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface Props {
    agents: any[];
    isRunning: boolean;
    isProcessing: boolean;
    /** Already-formatted iteration timestamp string, or "PENDING". */
    nextRunLabel: string;
    onToggle: () => void;
}

/**
 * Right-side context panel for the Autonomous page.
 *
 * Owns no data; the page derives `nextRunLabel` from `nextRun` epoch and
 * decides the running/standby state.
 */
export default function AutonomousRightPanel({
    agents,
    isRunning,
    isProcessing,
    nextRunLabel,
    onToggle,
}: Props) {
    return (
        <>
            <AgentMatrix agents={agents} />
            <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Loop Status</h4>
                <div className="flex flex-col">
                    <span className={cn("text-2xl font-bold uppercase tracking-tighter", isRunning ? "text-emerald-500" : "text-white")}>
                        {isRunning ? "Running" : "Standby"}
                    </span>
                    <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">
                        Iteration: {nextRunLabel}
                    </span>
                </div>
            </div>
            <Button
                onClick={onToggle}
                disabled={isProcessing}
                className={cn(
                    "w-full font-bold h-14 rounded-2xl transition-all",
                    isRunning ? "bg-zinc-950 border border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10" : "bg-emerald-500 text-black hover:bg-emerald-400"
                )}
            >
                {isProcessing ? "Transmitting..." : (isRunning ? "Halt Director" : "Launch Director")}
            </Button>
        </>
    );
}

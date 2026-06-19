"use client";

import React from "react";
import { Database, Zap, Network } from "lucide-react";
import { NexusEngine } from "@/hooks/useNexusData";

const PLACEHOLDER_CONFIG: Record<
    Exclude<NexusEngine, "orchestrator" | "crews" | "identities" | "sandbox" | "command" | "history" | "logs">,
    { title: string; subtitle: string; hash: string; Icon: React.ComponentType<{ className?: string }> }
> = {
    registry: {
        title: "Empire Registry",
        subtitle: "SECURE_STORAGE_ORCHESTRATION_ACTIVE",
        hash: "ENCRYPTED_VOXEL_HASH: 0x93F...A2",
        Icon: Database,
    },
    forge: {
        title: "Neural Forge",
        subtitle: "CREATIVE_SYNTHESIS_PIPELINE_READY",
        hash: "ACTIVE_TEMP: 4200K_NEURAL_BURN",
        Icon: Zap,
    },
    network: {
        title: "Global Network Mesh",
        subtitle: "SWARM_INTELLIGENCE_ROUTING_ACTIVE",
        hash: "NODES_CONNECTED: 4,092_DIRECT_LINKS",
        Icon: Network,
    },
};

interface Props {
    engine: NexusEngine;
}

export default function PlaceholderTab({ engine }: Props) {
    const config = PLACEHOLDER_CONFIG[engine as keyof typeof PLACEHOLDER_CONFIG];
    if (!config) return null;
    const { title, subtitle, hash, Icon } = config;

    return (
        <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
            <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
            <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                <div className="relative">
                    <Icon className="h-16 w-16 text-cyan-500 animate-pulse" />
                    <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                </div>
                <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">
                    {title}
                </h3>
                <div className="flex flex-col gap-1 items-center">
                    <span className="text-[10px] text-zinc-500 font-mono italic">{subtitle}</span>
                    <span className="text-[8px] text-cyan-500/50 font-mono">{hash}</span>
                </div>
            </div>
        </div>
    );
}

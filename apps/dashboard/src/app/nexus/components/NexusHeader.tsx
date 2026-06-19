"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    Cpu,
    Users,
    Fingerprint,
    Terminal,
    Layers,
} from "lucide-react";

const NAV_ITEMS = [
    { id: "orchestrator", label: "Orchestrator", icon: Cpu },
    { id: "crews", label: "Workforce", icon: Users },
    { id: "identities", label: "Neural IDs", icon: Fingerprint },
    { id: "sandbox", label: "Code Sandbox", icon: Terminal },
    { id: "command", label: "Command Pod", icon: Terminal },
    { id: "history", label: "Pipeline History", icon: Layers },
] as const;

interface NexusHeaderProps {
    activeEngine: string;
    onEngineChange: (id: string) => void;
}

export default function NexusHeader({ activeEngine, onEngineChange }: NexusHeaderProps) {
    const router = useRouter();

    return (
        <div className="space-y-1">
            {NAV_ITEMS.map((item) => (
                <button
                    key={item.id}
                    onClick={() => {
                        onEngineChange(item.id);
                        router.replace(`/nexus?engine=${item.id}`);
                    }}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                        activeEngine === item.id
                            ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                            : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                    )}
                >
                    <item.icon className="h-4 w-4" />
                    <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                    {activeEngine === item.id && (
                        <div className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
                    )}
                </button>
            ))}
        </div>
    );
}

"use client";

import React from "react";
import { Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { AreaChartCustom } from "@/components/ui/ChartComponents";
import { SandboxTab as SandboxTabKey } from "@/hooks/useNexusData";

interface Props {
    actionLogs: string[];
    sandboxTab: SandboxTabKey;
    setSandboxTab: (t: SandboxTabKey) => void;
    handleSandboxExecute: () => void;
    selectedNiche: string;
    mockTelemetry: {
        latency: { time: string; value: number }[];
        workerLoad: { time: string; value: number }[];
        healing: { time: string; value: number }[];
    };
}

export default function SandboxTab({
    actionLogs,
    sandboxTab,
    setSandboxTab,
    handleSandboxExecute,
    selectedNiche,
    mockTelemetry,
}: Props) {
    return (
        <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <Terminal className="h-4 w-4 text-cyan-400" />
                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">
                            Neural Code Sandbox
                        </h3>
                    </div>
                    <div className="flex items-center bg-white/5 rounded-lg p-0.5 border border-white/5">
                        <button
                            onClick={() => setSandboxTab("console")}
                            className={cn(
                                "px-3 py-1 text-[9px] uppercase font-bold rounded-md transition-all",
                                sandboxTab === "console"
                                    ? "bg-cyan-500 text-black"
                                    : "text-zinc-400 hover:text-zinc-200"
                            )}
                        >
                            Console
                        </button>
                        <button
                            onClick={() => setSandboxTab("telemetry")}
                            className={cn(
                                "px-3 py-1 text-[9px] uppercase font-bold rounded-md transition-all",
                                sandboxTab === "telemetry"
                                    ? "bg-cyan-500 text-black"
                                    : "text-zinc-400 hover:text-zinc-200"
                            )}
                        >
                            Live Telemetry
                        </button>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <Button
                        size="sm"
                        className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold px-4 h-8 text-[10px] uppercase"
                        onClick={handleSandboxExecute}
                    >
                        Execute_Node
                    </Button>
                </div>
            </div>

            {sandboxTab === "console" ? (
                <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 min-h-0">
                    <div className="border-r border-white/5 flex flex-col min-h-0">
                        <div className="p-4 border-b border-white/5 bg-white/5">
                            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                                Active Script
                            </span>
                        </div>
                        <div className="flex-1 p-8 font-mono text-sm text-cyan-400/80 overflow-y-auto custom-scrollbar">
                            <pre>{`// Initialize Intelligence Bridge
const nexus = await Nexus.connect();

// Spawn autonomous scout
const scout = await nexus.spawnAgent("SCOUT_01", {
    role: "Discovery",
    niche: "${selectedNiche || "Global"}",
    behavior: "Aggressive"
});

// Await viral triggers
scout.on("VIRAL_DETECT", async (data) => {
    console.log("[NEXUS] Outbreak detected:", data.id);
    await nexus.dispatchPipeline("AUTO_SYNTH_V1", data);
});`}</pre>
                        </div>
                    </div>

                    <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-r-[32px] border-l border-white/5 overflow-hidden">
                        <div className="p-4 border-b border-white/5 bg-white/5">
                            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                                Execution Output
                            </span>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[10px] space-y-2">
                            {actionLogs.map((log, i) => (
                                <p
                                    key={i}
                                    className={cn(
                                        log.includes("[SUCCESS]")
                                            ? "text-emerald-500"
                                            : log.includes("[EXEC]")
                                            ? "text-cyan-400"
                                            : log.includes("[SYSTEM]")
                                            ? "text-zinc-600"
                                            : "text-zinc-400"
                                    )}
                                >
                                    {log}
                                </p>
                            ))}
                            <div className="animate-pulse flex gap-2">
                                <span className="text-white">_</span>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                                Global Latency (ms)
                            </span>
                            <div className="h-48 relative">
                                <AreaChartCustom
                                    data={mockTelemetry.latency}
                                    dataKey="value"
                                    color="#8b5cf6"
                                    height={190}
                                />
                            </div>
                        </div>
                        <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                                Celery Cluster Load (%)
                            </span>
                            <div className="h-48 relative">
                                <AreaChartCustom
                                    data={mockTelemetry.workerLoad}
                                    dataKey="value"
                                    color="#22d3ee"
                                    height={190}
                                />
                            </div>
                        </div>
                        <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                                Self-Healing Triggers
                            </span>
                            <div className="h-48 relative">
                                <AreaChartCustom
                                    data={mockTelemetry.healing}
                                    dataKey="value"
                                    color="#10b981"
                                    height={190}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-white/2 border border-white/5 flex items-center justify-between">
                        <div className="space-y-1">
                            <span className="text-[9px] font-black text-cyan-400 uppercase tracking-widest">
                                Cluster Health Ledger
                            </span>
                            <p className="text-xs text-zinc-400">
                                All core micro-services operating nominally. Autonomic recovery
                                scripts operational.
                            </p>
                        </div>
                        <span className="text-[10px] px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 font-bold uppercase">
                            100% HEALTH
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}

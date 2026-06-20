"use client";

import React from "react";
import {
    ShieldAlert,
    Radar,
    Terminal,
    Globe,
    Loader2,
    XCircle,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import dynamic from "next/dynamic";

/** Module-internal — do not consume from outside. */
const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });
const Geomap = dynamic(() => import("@/components/ui/Geomap"), { ssr: false });

interface AnalysisTask {
    task_id: string;
    status: string;
    result?: any;
    niche: string;
}

/** Module-internal — do not consume from outside. */
interface IntelInsight {
    type: string;
    confidence: number;
    message: string;
}

interface IntelData {
    insights?: IntelInsight[];
}

/** Module-internal — do not consume from outside. */
interface LogEntry {
    type: string;
    level: string;
    module: string;
    message: string;
    timestamp: number;
}

/** Module-internal — do not consume from outside. */
interface MapPoint {
    id: string;
    lat: number;
    lng: number;
    intensity: number;
    label: string;
}

/** Module-internal — do not consume from outside. */
interface NetworkNode {
    id: string;
    group: number;
    label: string;
}

interface NetworkLink {
    source: string;
    target: string;
    value: number;
}

/** Module-internal — do not consume from outside. */
interface NetworkData {
    nodes: NetworkNode[];
    links: NetworkLink[];
}

interface Alert {
    timestamp: string;
    title: string;
    description: string;
    tags?: string[];
}

/** Module-internal — do not consume from outside. */
interface AnalysisPanelProps {
    activeEngine: string;
    intelData: IntelData | null;
    networkData: NetworkData;
    alerts: Alert[];
    displayLogs: LogEntry[];
    mapPoints: MapPoint[];
    activeNiche: string;
    onCreateFromAnalysis: (taskId: string, candidateId: string, niche: string) => void;
    analysisTasks: Record<string, AnalysisTask>;
}

export function AnalysisPanel({
    activeEngine,
    intelData,
    networkData,
    alerts,
    displayLogs,
    mapPoints,
    activeNiche,
    onCreateFromAnalysis,
    analysisTasks,
}: AnalysisPanelProps) {
    if (activeEngine === "intel") {
        return (
            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-12 flex flex-col gap-8">
                <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Niche Intelligence: {activeNiche}</h3>
                    <div className="px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-widest">Live Analysis Active</div>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 flex-1 min-h-0">
                    <div className="rounded-2xl bg-white/5 border border-white/5 p-8 overflow-hidden relative">
                        <NetworkMesh nodes={networkData.nodes} links={networkData.links} />
                        <div className="absolute inset-0 bg-linear-to-t from-[#0F0F11] via-transparent to-transparent" />
                        <div className="absolute bottom-8 left-8 right-8 space-y-4">
                            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Growth Vector Analysis</h4>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div initial={{ width: 0 }} animate={{ width: "75%" }} className="h-full bg-primary" />
                            </div>
                        </div>
                    </div>
                    <div className="space-y-6 overflow-y-auto custom-scrollbar pr-4">
                        {intelData?.insights?.map((insight: any, i: number) => (
                            <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-primary uppercase tracking-widest">{insight.type}</span>
                                    <span className="text-[10px] font-mono text-zinc-500">{insight.confidence}% CONF</span>
                                </div>
                                <p className="text-sm text-zinc-300 leading-relaxed">{insight.message}</p>
                            </div>
                        )) || (
                            <div className="h-full flex flex-col items-center justify-center opacity-20 gap-4">
                                <Radar className="h-12 w-12" />
                                <span className="text-xs font-bold uppercase tracking-[0.4em]">Scanning Neural Patterns...</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    if (activeEngine === "alerts") {
        return (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                {alerts.map((alert, i) => (
                    <div key={i} className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col justify-between group hover:border-primary/20 transition-all">
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <div className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                                    <ShieldAlert className="h-5 w-5 text-primary" />
                                </div>
                                <span className="text-[10px] font-mono text-zinc-600 uppercase">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-lg font-bold text-white uppercase tracking-tight">{alert.title}</h4>
                                <p className="text-xs text-zinc-500 leading-relaxed">{alert.description}</p>
                            </div>
                        </div>
                        <div className="mt-8 flex items-center justify-between">
                            <div className="flex gap-2">
                                {alert.tags?.map((tag: string) => (
                                    <span key={tag} className="px-3 py-1 rounded-full bg-white/5 text-[8px] font-bold text-zinc-400 uppercase">{tag}</span>
                                ))}
                            </div>
                            <Button variant="outline" className="h-10 border-white/10 text-white text-[10px] uppercase font-bold group-hover:bg-primary group-hover:text-black">Investigate</Button>
                        </div>
                    </div>
                ))}
                {alerts.length === 0 && (
                    <div className="col-span-2 h-full flex flex-col items-center justify-center opacity-10 gap-6">
                        <ShieldAlert className="h-24 w-24" />
                        <span className="text-xl font-black uppercase tracking-[1em]">Scanning for Outbreaks</span>
                    </div>
                )}
            </div>
        );
    }

    if (activeEngine === "hotspots") {
        return (
            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative">
                <Geomap points={mapPoints} />
                <div className="absolute top-8 right-8 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-xs space-y-2">
                    <h4 className="text-white font-bold uppercase tracking-widest text-xs">Live Geolocation Feed</h4>
                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">Mapping {mapPoints.length} active viral outbreaks across platform clusters.</p>
                </div>
            </div>
        );
    }

    if (activeEngine === "logs") {
        return (
            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                    <div className="flex items-center gap-4">
                        <Terminal className="h-4 w-4 text-zinc-500" />
                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Discovery Engine Logs</h3>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[9px] font-bold text-emerald-500 uppercase">Engine_Active</span>
                        </div>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                    {displayLogs.map((log, i) => (
                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                            <span className="text-zinc-700 shrink-0 select-none">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                            <span className={cn(
                                "shrink-0 font-bold tracking-widest uppercase text-[9px] px-2 py-0.5 rounded",
                                log.level === "ACTION" ? "bg-cyan-500/10 text-cyan-500" :
                                log.level === "ERROR" ? "bg-rose-500/10 text-rose-500" :
                                log.level === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" : "bg-white/5 text-zinc-500"
                            )}>
                                {log.level || "INFO"}
                            </span>
                            <span className={cn(
                                "leading-relaxed",
                                log.level === "ACTION" ? "text-cyan-400" :
                                log.level === "ERROR" ? "text-rose-500" :
                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-400"
                            )}>
                                <span className="text-zinc-600">[{log.module || "SYSTEM"}]</span> {log.message}
                            </span>
                        </div>
                    ))}
                    <div className="h-4" />
                </div>
            </div>
        );
    }

    return null;
}

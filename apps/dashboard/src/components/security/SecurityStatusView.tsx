"use client";

import React from "react";
import { ShieldCheck, ScanLine, AlertTriangle, Lock, Key, Database, Server, Clock, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { SeverityIcon, SeverityPill } from "./SeverityBadge";

/** Module-internal — do not consume from outside. */
interface Props {
    agents: any[];
    /** Already-derived health score (page-level chain fallback applied). */
    healthScore: number;
    /** Already-derived threat level (page-level chain fallback applied). */
    threatLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "NOMINAL";
    /** Already-derived recent-threats list (securityStatus OR securityEvents). */
    recentThreats: any[];
    /** Already-derived threat counts with safe defaults. */
    threatBreakdown: { low: number; medium: number; high: number; critical: number };
    isScanning: boolean;
    onScan: () => void;
    systemIntegrity?: string;
}

/**
 * Status tab — Health-Score ring + Run-Audit CTA + Recent-Threats list +
 * Threat breakdown + System-Integrity grid.
 *
 * View models are computed in `SecurityContent` so that the
 * pre-existing `securityStatus?.data?.X` chain (which produces TS2339
 * because `SecurityStatus` interface doesn't declare `data`) lives in
 * exactly one place.
 */
export default function SecurityStatusView({
    agents,
    healthScore,
    threatLevel,
    recentThreats,
    threatBreakdown,
    isScanning,
    onScan,
    systemIntegrity,
}: Props) {
    return (
        <div className="space-y-10 overflow-y-auto custom-scrollbar flex-1 p-1">
            {/* Health Score Ring + Scan CTA */}
            <div className="flex items-center gap-12 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5">
                <div className="relative h-32 w-32 shrink-0">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
                        <circle cx="64" cy="64" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                        <circle cx="64" cy="64" r="54" fill="none" stroke="currentColor" strokeWidth="8"
                            strokeDasharray={`${2 * Math.PI * 54}`}
                            strokeDashoffset={`${2 * Math.PI * 54 * (1 - healthScore / 100)}`}
                            className={cn(
                                healthScore >= 80 ? "text-emerald-500" :
                                healthScore >= 50 ? "text-amber-500" : "text-rose-500"
                            )}
                            strokeLinecap="round"
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-3xl font-black text-white">{healthScore}</span>
                    </div>
                </div>
                <div className="space-y-4 flex-1">
                    <div className="flex items-center gap-4">
                        <h3 className="text-xl font-bold text-white uppercase tracking-tight">System Integrity Status</h3>
                        <span className={cn(
                            "px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest",
                            healthScore >= 80 ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                            healthScore >= 50 ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                            "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        )}>
                            {healthScore >= 80 ? "SECURE" : healthScore >= 50 ? "DEGRADED" : "CRITICAL"}
                        </span>
                    </div>
                    <p className="text-xs text-zinc-500 leading-relaxed">
                        {healthScore >= 90 ? "All systems nominal. Security posture is strong." :
                         healthScore >= 70 ? "Minor issues detected. Review recommendations below." :
                         healthScore >= 50 ? "Multiple issues found. Immediate attention recommended." :
                         "Critical security vulnerabilities detected. Take action immediately."}
                    </p>
                    <Button onClick={onScan} disabled={isScanning} className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-12 px-8 rounded-2xl gap-2">
                        {isScanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanLine className="h-4 w-4" />}
                        {isScanning ? "Scanning..." : "Run Full Audit"}
                    </Button>
                </div>
            </div>

            {/* Recent Threats */}
            <div className="space-y-4">
                <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-widest px-2">Recent Security Events</h4>
                <div className="space-y-2">
                    {(Array.isArray(recentThreats) ? recentThreats : []).slice(0, 10).map((event: any, i) => (
                        <div key={i} className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5">
                            <SeverityIcon severity={event.severity} className={cn(
                                event.severity === "critical" && "text-rose-500",
                                event.severity === "high" && "text-orange-500",
                                event.severity === "medium" && "text-amber-500",
                                (!event.severity || event.severity === "info") && "text-zinc-500"
                            )} />
                            <div className="flex-1 min-w-0">
                                <span className="text-xs font-bold text-white uppercase tracking-tight block truncate">{event.type || event.event_type || "Unknown Event"}</span>
                                <span className="text-[9px] text-zinc-600 font-mono">{event.details?.ip || event.details?.endpoint || event.message || ""}</span>
                            </div>
                            <SeverityPill severity={event.severity} />
                        </div>
                    ))}
                    {(!recentThreats || recentThreats.length === 0) && (
                        <div className="flex flex-col items-center justify-center py-12 opacity-20">
                            <ShieldCheck className="h-12 w-12 mb-4 text-emerald-500" />
                            <span className="text-xs font-bold uppercase tracking-[0.4em]">No recent threats detected</span>
                        </div>
                    )}
                </div>

                {/* Threat breakdown summary */}
                <div className="space-y-2 pt-4 border-t border-white/5">
                    <h5 className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Threat breakdown</h5>
                    <div className="grid grid-cols-4 gap-4 text-[8px] font-bold">
                        <span className="text-rose-500">Critical: {threatBreakdown?.critical || 0}</span>
                        <span className="text-orange-500">High: {threatBreakdown?.high || 0}</span>
                        <span className="text-amber-500">Medium: {threatBreakdown?.medium || 0}</span>
                        <span className="text-zinc-400">Low: {threatBreakdown?.low || 0}</span>
                    </div>
                    <div className={cn(
                        "mt-2 text-[8px] font-bold uppercase tracking-widest",
                        threatLevel === "CRITICAL" ? "text-rose-500" :
                        threatLevel === "HIGH" ? "text-orange-500" :
                        threatLevel === "MEDIUM" ? "text-amber-500" : "text-emerald-500"
                    )}>Threat: {threatLevel}</div>
                </div>
            </div>

            {/* System Integrity Card */}
            <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5">
                <div className="flex items-center gap-4 mb-6">
                    <Lock className="h-6 w-6 text-emerald-500" />
                    <h4 className="text-sm font-bold text-white uppercase tracking-widest">System Integrity</h4>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {[
                        { icon: Key, label: "API Keys", value: systemIntegrity || "NOMINAL", color: "text-emerald-500" },
                        { icon: Database, label: "Database", value: "Connected", color: "text-emerald-500" },
                        { icon: Server, label: "Services", value: `${agents?.length || 0} Active`, color: "text-cyan-500" },
                        { icon: Clock, label: "Last Audit", value: "On demand", color: "text-zinc-500" },
                    ].map((stat, i) => (
                        <div key={i} className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-2">
                            <stat.icon className={cn("h-4 w-4", stat.color)} />
                            <div className="space-y-1">
                                <span className="block text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{stat.label}</span>
                                <span className={cn("block text-xs font-bold", stat.color)}>{stat.value}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

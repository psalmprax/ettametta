"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    ShieldCheck,
    ShieldAlert,
    Shield,
    Activity,
    Terminal,
    ScanLine,
    AlertTriangle,
    AlertOctagon,
    CheckCircle2,
    XCircle,
    RefreshCw,
    Lock,
    Key,
    Database,
    Server,
    Cpu,
    HardDrive,
    Globe,
    Clock,
    Loader2,
    Eye,
    EyeOff,
    AlertCircle,
    Search,
    ChevronRight,
    Zap,
    Target,
    Dna,
    Radar,
    Fingerprint
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";
import { useTelemetry } from "@/context/TelemetryContext";

function SecurityContent() {
    const { agents, logs: systemLogs, status, pulse } = useTelemetry();
    const [activeEngine, setActiveEngine] = useState("status");
    const [securityStatus, setSecurityStatus] = useState<any>(null);
    const [securityEvents, setSecurityEvents] = useState<any[]>([]);
    const [scanResults, setScanResults] = useState<any[]>([]);
    const [isScanning, setIsScanning] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [actionLogs, setActionLogs] = useState<string[]>(["SECURITY_SENTINEL_INITIALIZED"]);

    const fetchSecurityStatus = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/security/status`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => setSecurityStatus(data),
                onFallback: () => setActionLogs((prev: string[]) => ["[ERROR] Failed to fetch security status", ...prev])
            }
        );
        setIsLoading(false);
    }, []);

    const fetchSecurityEvents = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any[]>((signal) => fetch(`${API_BASE}/security/events`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (data) => setSecurityEvents(data)
            }
        );
    }, []);

    const handleScan = async () => {
        setIsScanning(true);
        setActionLogs((prev: string[]) => ["[SCAN] Initiating full system integrity audit...", ...prev]);
        const token = await getAuthToken();
        if (!token) { setIsScanning(false); return; }

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/security/scan`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const report = data?.report || {};
                    setScanResults(report?.findings || []);
                    setActionLogs((prev: string[]) => [
                        `[SCAN] Audit complete — Score: ${report?.score || 0}/100`,
                        ...(report?.findings || []).map((f: string) => `[FINDING] ${f}`),
                        ...prev
                    ]);
                    toast.success(`Audit complete — Score: ${report?.score || 0}/100`);
                    fetchSecurityStatus();
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[ERROR] Audit failed: ${err.message}`, ...prev]);
                    toast.error("Audit failed");
                }
            }
        );
        setIsScanning(false);
    };

    useEffect(() => {
        fetchSecurityStatus();
        fetchSecurityEvents();
    }, [fetchSecurityStatus, fetchSecurityEvents]);

    const healthScore = securityStatus?.health_score ?? securityStatus?.data?.health_score ?? 0;
    const threatLevel = securityStatus?.threat_level ?? securityStatus?.data?.threat_level ?? "NOMINAL";
    const recentThreats = securityStatus?.recent_threats ?? securityStatus?.data?.recent_threats ?? securityEvents;
    const threatBreakdown = securityStatus?.threat_breakdown ?? securityStatus?.data?.threat_breakdown ?? { low: 0, medium: 0, high: 0, critical: 0 };

    return (
        <CommandCenterLayout
            title="SECURITY SENTINEL"
            subtitle="THREAT_DETECTION_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "status", label: "Security Status", icon: ShieldCheck },
                        { id: "events", label: "Event Log", icon: Activity },
                        { id: "scan", label: "Vulnerability Scan", icon: ScanLine },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Health Overview</h4>
                        <div className="flex flex-col">
                            <span className="text-3xl font-bold text-white">{healthScore}%</span>
                            <span className={cn(
                                "text-[8px] font-bold uppercase tracking-widest",
                                threatLevel === "CRITICAL" ? "text-rose-500" :
                                threatLevel === "HIGH" ? "text-orange-500" :
                                threatLevel === "MEDIUM" ? "text-amber-500" :
                                "text-emerald-500"
                            )}>
                                Threat: {threatLevel}
                            </span>
                        </div>
                        <div className="space-y-2 pt-2 border-t border-white/5">
                            <div className="flex justify-between text-[8px] font-bold">
                                <span className="text-zinc-600">Critical</span>
                                <span className="text-rose-500">{threatBreakdown?.critical || 0}</span>
                            </div>
                            <div className="flex justify-between text-[8px] font-bold">
                                <span className="text-zinc-600">High</span>
                                <span className="text-orange-500">{threatBreakdown?.high || 0}</span>
                            </div>
                            <div className="flex justify-between text-[8px] font-bold">
                                <span className="text-zinc-600">Medium</span>
                                <span className="text-amber-500">{threatBreakdown?.medium || 0}</span>
                            </div>
                            <div className="flex justify-between text-[8px] font-bold">
                                <span className="text-zinc-600">Low</span>
                                <span className="text-zinc-400">{threatBreakdown?.low || 0}</span>
                            </div>
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "status" && (
                            <div className="space-y-10 overflow-y-auto custom-scrollbar flex-1 p-1">
                                {/* Health Score Ring */}
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
                                        <Button onClick={handleScan} disabled={isScanning} className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-12 px-8 rounded-2xl gap-2">
                                            {isScanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanLine className="h-4 w-4" />}
                                            {isScanning ? "Scanning..." : "Run Full Audit"}
                                        </Button>
                                    </div>
                                </div>

                                {/* Recent Threats */}
                                <div className="space-y-4">
                                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-widest px-2">Recent Security Events</h4>
                                    <div className="space-y-2">
                                        {(Array.isArray(recentThreats) ? recentThreats : []).slice(0, 10).map((event: any, i: number) => (
                                            <div key={i} className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5">
                                                {event.severity === "critical" ? <AlertOctagon className="h-5 w-5 text-rose-500" /> :
                                                 event.severity === "high" ? <AlertTriangle className="h-5 w-5 text-orange-500" /> :
                                                 event.severity === "medium" ? <AlertCircle className="h-5 w-5 text-amber-500" /> :
                                                 <Activity className="h-5 w-5 text-zinc-500" />}
                                                <div className="flex-1 min-w-0">
                                                    <span className="text-xs font-bold text-white uppercase tracking-tight block truncate">{event.type || event.event_type || "Unknown Event"}</span>
                                                    <span className="text-[9px] text-zinc-600 font-mono">{event.details?.ip || event.details?.endpoint || event.message || ""}</span>
                                                </div>
                                                <span className={cn(
                                                    "px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest",
                                                    event.severity === "critical" ? "bg-rose-500/20 text-rose-400" :
                                                    event.severity === "high" ? "bg-orange-500/20 text-orange-400" :
                                                    event.severity === "medium" ? "bg-amber-500/20 text-amber-400" :
                                                    "bg-zinc-500/20 text-zinc-400"
                                                )}>{event.severity || "info"}</span>
                                            </div>
                                        ))}
                                        {(!recentThreats || recentThreats.length === 0) && (
                                            <div className="flex flex-col items-center justify-center py-12 opacity-20">
                                                <ShieldCheck className="h-12 w-12 mb-4 text-emerald-500" />
                                                <span className="text-xs font-bold uppercase tracking-[0.4em]">No recent threats detected</span>
                                            </div>
                                        )}
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
                                            { icon: Key, label: "API Keys", value: securityStatus?.system_integrity || "NOMINAL", color: "text-emerald-500" },
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
                        )}

                        {activeEngine === "events" && (
                            <div className="overflow-y-auto custom-scrollbar flex-1 p-1">
                                <div className="space-y-2">
                                    {(Array.isArray(securityEvents) ? securityEvents : []).length === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-32 opacity-20">
                                            <Activity className="h-16 w-16 mb-4" />
                                            <span className="text-[10px] font-bold uppercase tracking-[0.5em]">No security events recorded</span>
                                        </div>
                                    ) : (
                                        (Array.isArray(securityEvents) ? securityEvents : []).map((event: any, i: number) => (
                                            <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/5 flex items-start gap-4 group hover:border-emerald-500/20 transition-all">
                                                <div className={cn(
                                                    "h-10 w-10 rounded-xl flex items-center justify-center shrink-0",
                                                    event.severity === "critical" ? "bg-rose-500/10" :
                                                    event.severity === "high" ? "bg-orange-500/10" :
                                                    "bg-zinc-500/10"
                                                )}>
                                                    {event.severity === "critical" ? <AlertOctagon className="h-5 w-5 text-rose-500" /> :
                                                     event.severity === "high" ? <AlertTriangle className="h-5 w-5 text-orange-500" /> :
                                                     <Activity className="h-5 w-5 text-zinc-500" />}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-3 mb-1">
                                                        <span className="text-xs font-bold text-white uppercase tracking-tight">{event.type || "Unknown"}</span>
                                                        <span className="text-[8px] font-mono text-zinc-600">{event.timestamp ? new Date(event.timestamp).toLocaleString() : ""}</span>
                                                    </div>
                                                    <p className="text-[10px] text-zinc-500 leading-relaxed">
                                                        {event.details ? JSON.stringify(event.details).slice(0, 200) : event.message || ""}
                                                    </p>
                                                </div>
                                                <span className={cn(
                                                    "px-3 py-1 rounded-full text-[8px] font-bold uppercase tracking-widest shrink-0",
                                                    event.severity === "critical" ? "bg-rose-500/20 text-rose-400" :
                                                    event.severity === "high" ? "bg-orange-500/20 text-orange-400" :
                                                    "bg-zinc-500/20 text-zinc-400"
                                                )}>{event.severity || "info"}</span>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}

                        {activeEngine === "scan" && (
                            <div className="space-y-8 overflow-y-auto custom-scrollbar flex-1 p-1">
                                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                                    <div className="flex items-center justify-between">
                                        <div className="space-y-2">
                                            <h3 className="text-xl font-bold text-white uppercase tracking-tight">Vulnerability Scanner</h3>
                                            <p className="text-xs text-zinc-500">Performs comprehensive system integrity checks including secret scanning, port analysis, and configuration validation.</p>
                                        </div>
                                        <Button onClick={handleScan} disabled={isScanning}
                                            className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-14 px-10 rounded-2xl gap-3 text-lg">
                                            {isScanning ? <Loader2 className="h-5 w-5 animate-spin" /> : <ScanLine className="h-5 w-5" />}
                                            {isScanning ? "Scanning..." : "Execute Scan"}
                                        </Button>
                                    </div>

                                    {scanResults.length > 0 && (
                                        <div className="space-y-4">
                                            <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Findings ({scanResults.length})</h4>
                                            {scanResults.map((finding: string, i: number) => (
                                                <div key={i} className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
                                                    <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                                                    <span className="text-xs text-zinc-300">{finding}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {scanResults.length === 0 && !isScanning && (
                                        <div className="flex flex-col items-center justify-center py-16 opacity-20">
                                            <Shield className="h-16 w-16 mb-4" />
                                            <span className="text-[10px] font-bold uppercase tracking-[0.5em]">No scan results yet — run a scan to check for vulnerabilities</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Security Engine Logs</h3>
                                    </div>
                                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                        <span className="text-[9px] font-bold text-emerald-500 uppercase">Sentinel_Active</span>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {actionLogs.map((log, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date().toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                log.startsWith("[SUCCESS]") ? "text-emerald-500" :
                                                log.startsWith("[ERROR]") ? "text-rose-500" :
                                                log.startsWith("[SCAN]") ? "text-cyan-400" :
                                                log.startsWith("[FINDING]") ? "text-orange-500" :
                                                "text-zinc-400"
                                            )}>{log}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function SecurityPage() {
    return (
        <Suspense fallback={null}>
            <SecurityContent />
        </Suspense>
    );
}

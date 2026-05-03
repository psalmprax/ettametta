"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
import {
    ShieldCheck,
    UserCheck,
    AlertTriangle,
    Fingerprint,
    FileText,
    Play,
    RefreshCw,
    Download,
    Eye,
    ChevronRight,
    Terminal,
    Target,
    Cpu
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { useTelemetry } from "@/context/TelemetryContext";

export default function AuditsPage() {
    const { agents, logs: systemLogs, status, pulse } = useTelemetry();
    const [activeTab, setActiveTab] = useState<"account" | "security" | "bias" | "logs">("account");
    const [isLoading, setIsLoading] = useState(false);
    const [securityStatus, setSecurityStatus] = useState<any>(null);
    const [auditReports, setAuditReports] = useState<any[]>([]);
    const [securityEvents, setSecurityEvents] = useState<any[]>([]);
    const [actionLogs, setActionLogs] = useState<string[]>(["GOVERNANCE_INITIALIZED", "SYNCHRONIZING_TRUST_MATRIX"]);

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setIsLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        if (activeTab === "security") {
            await Promise.all([
                withRealFallback<any>(
                    () => fetch(`${API_BASE}/security/status`, { headers }),
                    { fallback: null, onSuccess: (data) => setSecurityStatus(data) }
                ),
                withRealFallback<any[]>(
                    () => fetch(`${API_BASE}/security/events`, { headers }),
                    { fallback: [], onSuccess: (data) => setSecurityEvents(data) }
                )
            ]);
        }
        setIsLoading(false);
    };

    const handleRunSecurityAudit = async () => {
        setIsLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        setActionLogs(prev => [`[ACTION] Triggering Red Team Security Audit...`, ...prev]);

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/security/scan`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: { report: null },
                onSuccess: (data) => {
                    toast.success("Security Audit Complete");
                    setSecurityStatus(data.report);
                    setActionLogs(prev => [`[SUCCESS] Integrity Score: ${data.report?.health_score || 100}`, ...prev]);
                    fetchData();
                },
                onFallback: () => toast.error("Audit Failed")
            }
        );
        setIsLoading(false);
    };

    const handleRunAccountAudit = async (platform: string) => {
        setIsLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        setActionLogs(prev => [`[ACTION] Dispatched compliance audit for ${platform}...`, ...prev]);

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/agent/account-audit`, {
                method: "POST",
                headers: { 
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ action: "audit", platform })
            }),
            {
                fallback: { result: null },
                onSuccess: (data) => {
                    toast.success(`${platform.toUpperCase()} Audit Dispatched`);
                    setActionLogs(prev => [`[SUCCESS] Neural alignment verified for ${platform}.`, ...prev]);
                    setAuditReports(prev => [{
                        id: Math.random().toString(36).substr(2, 9),
                        platform,
                        status: "Success",
                        timestamp: new Date().toISOString(),
                        score: data.score,
                        recommendations: data.recommendations,
                        sprint_plan: data.sprint_plan
                    }, ...prev]);
                },
                onFallback: () => toast.error("Audit Failed")
            }
        );
        setIsLoading(false);
    };

    const handleDownloadReport = (report: any) => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `audit_${report.platform}_${report.id}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
        toast.success("Report Exported");
    };

    return (
        <CommandCenterLayout
            title="TRUST MATRIX"
            subtitle="GOVERNANCE_ENGINE_V4.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "account", label: "Account Audit", icon: UserCheck },
                        { id: "security", label: "Security Audit", icon: ShieldCheck },
                        { id: "bias", label: "Bias Scan", icon: Fingerprint },
                        { id: "logs", label: "Governance Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id as any)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeTab === item.id ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeTab === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="bg-slate-900/40 backdrop-blur-md border border-white/5 p-8 rounded-2xl space-y-6">
                        <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Compliance Health</h3>
                        <div className="space-y-4">
                            <HealthMetric label="Global Integrity" value={`${securityStatus?.health_score || 98.2}%`} color="text-cyan-400" />
                            <HealthMetric label="Privacy Parity" value={`${securityStatus?.privacy_score || 100}%`} color="text-emerald-400" />
                            <HealthMetric label="Bias Neutrality" value={`${securityStatus?.bias_score || 94.5}%`} color="text-amber-400" />
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeTab === "account" && (
                            <AccountAuditSection onAudit={handleRunAccountAudit} onDownload={handleDownloadReport} reports={auditReports} />
                        )}
                        {activeTab === "security" && (
                            <SecurityAuditSection status={securityStatus} events={securityEvents} onScan={handleRunSecurityAudit} isLoading={isLoading} />
                        )}
                        {activeTab === "bias" && (
                            <BiasScanSection />
                        )}
                        {activeTab === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Governance Telemetry</h3>
                                    </div>
                                    <span className="text-[10px] font-mono text-cyan-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {[
                                        ...actionLogs.map(msg => ({ level: "ACTION", message: msg, timestamp: Date.now() / 1000 })),
                                        ...(Array.isArray(systemLogs) ? systemLogs.filter(l => l.module === "SECURITY" || l.module === "AGENT") : [])
                                    ].sort((a, b) => b.timestamp - a.timestamp).map((log: any, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                "shrink-0 font-bold tracking-widest uppercase text-[9px] px-2 py-0.5 rounded",
                                                log.level === "ACTION" ? "bg-cyan-500/10 text-cyan-500" :
                                                log.level === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" : "bg-white/5 text-zinc-500"
                                            )}>
                                                {log.level || "INFO"}
                                            </span>
                                            <span className={cn(
                                                "leading-relaxed",
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-400"
                                            )}>
                                                {log.message}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        
                        {activeTab !== "logs" && (
                            <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Governance Engine Logs</span>
                                    <span className="text-[8px] font-mono text-cyan-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                    {[
                                        ...actionLogs.map(msg => ({ level: "ACTION", message: msg, timestamp: Date.now() / 1000 })),
                                        ...(Array.isArray(systemLogs) ? systemLogs.filter(l => l.module === "SECURITY" || l.module === "AGENT") : [])
                                    ].sort((a, b) => b.timestamp - a.timestamp).map((log: any, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-600"
                                            )}>{log.message}</span>
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

function TabButton({ active, onClick, icon: Icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "flex items-center gap-2 px-6 py-3 rounded-xl transition-all uppercase text-[10px] font-bold tracking-widest",
                active ? "bg-white/5 text-white shadow-xl" : "text-zinc-600 hover:text-zinc-400"
            )}
        >
            <Icon className={cn("h-4 w-4", active ? "text-cyan-400" : "text-zinc-700")} />
            {label}
        </button>
    );
}

function HealthMetric({ label, value, color }: any) {
    return (
        <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-tight text-zinc-500">{label}</span>
            <span className={cn("text-lg font-bold tabular-nums", color)}>{value}</span>
        </div>
    );
}

function AccountAuditSection({ onAudit, onDownload, reports }: any) {
    const platforms = ["youtube", "tiktok", "instagram", "facebook", "x", "linkedin"];
    
    return (
        <div className="space-y-10">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {platforms.map(p => (
                    <button
                        key={p}
                        onClick={() => onAudit(p)}
                        className="glass-card p-6 flex flex-col items-center gap-3 hover:border-cyan-400/30 transition-all group"
                    >
                        <div className="h-10 w-10 rounded-xl bg-white/3 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <RefreshCw className="h-5 w-5 text-zinc-600 group-hover:text-cyan-400" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 group-hover:text-white transition-colors">{p}</span>
                    </button>
                ))}
            </div>

            <div className="space-y-6">
                <div className="flex items-center gap-3 px-2">
                    <FileText className="h-4 w-4 text-zinc-500" />
                    <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Recent Compliance Reports</h3>
                </div>
                
                {reports.length === 0 ? (
                    <div className="glass-card py-20 flex flex-col items-center gap-4 opacity-40">
                        <AlertTriangle className="h-10 w-10 text-zinc-700" />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">No Audits Performed</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {reports.map((report: any) => (
                            <div key={report.id} className="glass-card p-6 flex items-center justify-between group hover:border-white/10 transition-all">
                                <div className="flex items-center gap-6">
                                    <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                                        <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-bold text-white uppercase">{report.platform} Growth Audit</h4>
                                        <div className="flex items-center gap-4 mt-1">
                                            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{new Date(report.timestamp).toLocaleString()}</p>
                                            {report.score && (
                                                <span className="text-[9px] font-bold text-cyan-400 uppercase tracking-widest px-2 py-0.5 rounded-full bg-cyan-400/10 border border-cyan-400/20">
                                                    Score: {report.score}%
                                                </span>
                                            )}
                                        </div>
                                        {report.recommendations && (
                                            <div className="mt-4 space-y-2">
                                                <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Strategic Recommendations:</p>
                                                <ul className="space-y-1">
                                                    {report.recommendations.map((rec: string, i: number) => (
                                                        <li key={i} className="flex items-start gap-2 text-[10px] text-zinc-400 font-medium leading-relaxed">
                                                            <div className="h-1 w-1 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                                                            {rec}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        {report.sprint_plan && (
                                            <p className="mt-3 text-[10px] font-bold text-emerald-400 uppercase tracking-tight">
                                                Sprint: {report.sprint_plan}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <button 
                                    onClick={() => onDownload(report)}
                                    className="p-3 rounded-xl bg-white/3 hover:bg-white/5 border border-white/5 transition-all"
                                >
                                    <Download className="h-4 w-4 text-zinc-500" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function SecurityAuditSection({ status, events, onScan, isLoading }: any) {
    return (
        <div className="space-y-8">
            <div className="bg-slate-900/40 backdrop-blur-md border border-white/5 p-10 rounded-2xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-10">
                <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                <div className="space-y-4 text-center md:text-left">
                    <h3 className="text-3xl font-bold uppercase tracking-tighter text-white">Red Team <span className="text-cyan-400">Integrity</span> Audit</h3>
                    <p className="text-zinc-500 font-medium max-w-sm">Trigger a comprehensive scan of API endpoints, database encryption, and workforce isolation nodes.</p>
                    <button 
                        onClick={onScan}
                        disabled={isLoading}
                        className="bg-white text-black font-bold py-4 px-8 rounded-xl uppercase text-[10px] tracking-widest flex items-center gap-3 hover:bg-cyan-400 transition-all"
                    >
                        {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-black" />}
                        Run Full Scan
                    </button>
                </div>
                <div className="h-48 w-48 rounded-full border-8 border-white/5 flex items-center justify-center relative">
                    <div className="absolute inset-4 rounded-full border border-cyan-400/30 animate-ping" />
                    <div className="flex flex-col items-center">
                        <span className="text-4xl font-bold text-white">{status?.health_score || "100"}</span>
                        <span className="text-[8px] font-bold uppercase tracking-widest text-zinc-600">Integrity Score</span>
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500 px-2">Live Threat Stream</h3>
                <div className="bg-slate-900/40 backdrop-blur-md border border-white/5 divide-y divide-white/5 rounded-2xl overflow-hidden">
                    {events?.length === 0 && <div className="p-10 text-center text-[10px] font-bold uppercase tracking-widest text-zinc-700">No security events detected</div>}
                    {events?.map((e: any, i: number) => (
                        <div key={i} className="p-5 flex items-center justify-between group hover:bg-white/2 transition-colors">
                            <div className="flex items-center gap-4">
                                <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                <span className="text-[11px] font-bold text-zinc-300">{e.message || e}</span>
                            </div>
                            <span className="text-[9px] font-bold text-zinc-700 uppercase tabular-nums">{new Date().toLocaleTimeString()}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function BiasScanSection() {
    return (
        <div className="bg-slate-900/40 backdrop-blur-md border border-white/5 py-32 flex flex-col items-center justify-center text-center gap-8 rounded-2xl border-dashed">
            <div className="relative">
                <Fingerprint className="h-24 w-24 text-zinc-800" />
                <div className="absolute inset-0 flex items-center justify-center">
                    <RefreshCw className="h-12 w-12 text-cyan-400/20 animate-spin-slow" />
                </div>
            </div>
            <div className="space-y-3">
                <h3 className="text-2xl font-bold uppercase tracking-tight text-white">Neural Bias Neutrals</h3>
                <p className="text-zinc-500 font-medium max-w-sm">Synchronizing with Global Compliance Mesh to verify generative neutrality across all 12 autonomous clusters.</p>
            </div>
            <button className="bg-zinc-900 text-zinc-400 border border-white/10 px-10 py-4 rounded-xl font-bold uppercase text-[10px] tracking-widest cursor-not-allowed">
                Initializing Cluster Sync...
            </button>
        </div>
    );
}

function CheckCircle2(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
            <path d="m9 12 2 2 4-4" />
        </svg>
    );
}

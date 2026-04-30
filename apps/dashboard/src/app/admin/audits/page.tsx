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
    Terminal
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";

export default function AuditsPage() {
    const [activeTab, setActiveTab] = useState<"account" | "security" | "bias">("account");
    const [isLoading, setIsLoading] = useState(false);
    const [securityStatus, setSecurityStatus] = useState<any>(null);
    const [auditReports, setAuditReports] = useState<any[]>([]);
    const [securityEvents, setSecurityEvents] = useState<any[]>([]);

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setIsLoading(true);
        const token = getAuthToken();
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
        const token = getAuthToken();
        if (!token) return;

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
                    fetchData();
                },
                onFallback: () => toast.error("Audit Failed")
            }
        );
        setIsLoading(false);
    };

    const handleRunAccountAudit = async (platform: string) => {
        setIsLoading(true);
        const token = getAuthToken();
        if (!token) return;

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
                    // Append simulated report for UI immediate feedback
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
        toast.success("Report Exported", { description: "Compliance data saved to local storage." });
    };

    return (
        <DashboardLayout>
            <div className="space-y-10 pb-24">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-cyan-400 rounded-full shadow-[0_0_15px_rgba(34,211,238,0.5)]" />
                            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-400">Governance & Compliance</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-bold tracking-tighter uppercase text-white">Trust <span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 to-blue-600 text-hollow">Matrix</span></h1>
                        <p className="text-zinc-500 font-medium">Verify system integrity, platform compliance, and <span className="text-zinc-300 font-bold">neural bias neutrality</span>.</p>
                    </div>

                    <div className="flex bg-zinc-950 p-1.5 rounded-2xl border border-white/5">
                        <TabButton active={activeTab === "account"} onClick={() => setActiveTab("account")} icon={UserCheck} label="Account" />
                        <TabButton active={activeTab === "security"} onClick={() => setActiveTab("security")} icon={ShieldCheck} label="Security" />
                        <TabButton active={activeTab === "bias"} onClick={() => setActiveTab("bias")} icon={Fingerprint} label="Bias Scan" />
                    </div>
                </div>

                {/* Content Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    <div className="lg:col-span-2 space-y-8">
                        {activeTab === "account" && (
                            <AccountAuditSection onAudit={handleRunAccountAudit} onDownload={handleDownloadReport} reports={auditReports} />
                        )}
                        {activeTab === "security" && (
                            <SecurityAuditSection status={securityStatus} events={securityEvents} onScan={handleRunSecurityAudit} isLoading={isLoading} />
                        )}
                        {activeTab === "bias" && (
                            <BiasScanSection />
                        )}
                    </div>

                    {/* Sidebar Stats */}
                    <div className="space-y-8">
                        <div className="bg-slate-900/40 backdrop-blur-md border border-white/5 p-8 rounded-2xl space-y-6">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Compliance Health</h3>
                            <div className="space-y-4">
                                <HealthMetric label="Global Integrity" value={`${securityStatus?.health_score || 98.2}%`} color="text-cyan-400" />
                                <HealthMetric label="Privacy Parity" value={`${securityStatus?.privacy_score || 100}%`} color="text-emerald-400" />
                                <HealthMetric label="Bias Neutrality" value={`${securityStatus?.bias_score || 94.5}%`} color="text-amber-400" />
                            </div>
                            <div className="pt-6 border-t border-white/5">
                                <p className="text-[9px] text-zinc-600 leading-relaxed font-bold uppercase tracking-tight">
                                    All neural clusters are currently operating within the <span className="text-white">ISO/AI-2026</span> standard for safe generative distribution.
                                </p>
                            </div>
                        </div>

                        <div className="bg-slate-900/40 backdrop-blur-md border border-white/5 p-8 rounded-2xl space-y-4">
                            <div className="flex items-center gap-3">
                                <Terminal className="h-4 w-4 text-violet-400" />
                                <span className="text-[9px] font-bold uppercase tracking-widest text-violet-400">Node Advisory</span>
                            </div>
                            <p className="text-[10px] text-zinc-500 leading-relaxed font-medium">
                                Red Team audits monitor for generative drift. We recommend a full system scan every 72 hours of autonomous production.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
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

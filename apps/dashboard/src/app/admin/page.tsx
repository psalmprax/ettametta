"use client";

import React, { useState, useEffect, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { useAuth } from "@/context/AuthContext";
import { useTelemetry } from "@/context/TelemetryContext";
import { useRouter } from "next/navigation";
import {
    Key,
    Database,
    Shield,
    Server,
    EyeOff,
    Eye,
    Wand2,
    Bot,
    Activity,
    Terminal,
    FileText,
    Monitor,
    Cpu,
    HardDrive,
    ShieldCheck,
    Webhook,
    DollarSign,
    Repeat,
    RotateCw,
    AlertCircle,
    ArrowUpRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import EnvManager from "@/components/admin/EnvManager";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";

export default function AdminSettingsPage() {
    const { user, isLoading: authLoading } = useAuth();
    const { agents, logs: _systemLogs, status: _status, pulse: _pulse } = useTelemetry();
    const router = useRouter();
    const [activeEngine, setActiveEngine] = useState("OAuth");
    const [settings, setSettings] = useState<any>({});
    const [_isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [securityStatus, setSecurityStatus] = useState<any>(null);
    const [securityEvents, setSecurityEvents] = useState<any[]>([]);
    const [auditResult, setAuditResult] = useState<any>(null);
    const [scanResult, setScanResult] = useState<any>(null);
    const [isAuditing, setIsAuditing] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [systemStatus, setSystemStatus] = useState<any>(null);
    const [_adminAudits, setAdminAudits] = useState<any[]>([]);
    const [webhookStats, setWebhookStats] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>(["ADMIN_INITIALIZED", "PROTOCOL_READY"]);

    // Security check
    useEffect(() => {
        if (!authLoading && (!user || (user.role !== "admin" && user.role !== "super_admin"))) {
            router.push("/");
        }
    }, [authLoading, user, router]);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        setIsLoading(true);
        await Promise.all([
            withRealFallback<any>((signal) => fetch(`${API_BASE}/settings/system`, { headers }),
                { fallback: {}, onSuccess: (data) => setSettings(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/security/status`, { headers }),
                { fallback: null, onSuccess: (data) => setSecurityStatus(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/admin/system/status`, { headers }),
                { fallback: null, onSuccess: (data) => setSystemStatus(data) }
            ),
            withRealFallback<any[]>((signal) => fetch(`${API_BASE}/admin/audits`, { headers }),
                { fallback: [], onSuccess: (data) => setAdminAudits(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/billing/webhook/stats`, { headers }),
                { fallback: null, onSuccess: (data) => setWebhookStats(data) }
            ),
            withRealFallback<any[]>((signal) => fetch(`${API_BASE}/security/events`, { headers }),
                { fallback: [], onSuccess: (data) => setSecurityEvents(data) }
            )
        ]);
        setIsLoading(false);
    }, []);

    const fetchWebhookStats = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/billing/webhook/stats`, { headers: { Authorization: `Bearer ${token}` } }),
            { fallback: null, onSuccess: (data) => setWebhookStats(data) }
        );
    }, []);

    useEffect(() => {
        if (user?.role === "admin" || user?.role === "super_admin") {
            fetchData();
        }
    }, [user, fetchData]);

    // Poll webhook stats every 30 seconds when the Webhooks tab is active
    useEffect(() => {
        if (user?.role !== "admin" && user?.role !== "super_admin") return;
        if (activeEngine !== "Webhooks") return;
        const interval = setInterval(() => { void fetchWebhookStats(); }, 30_000);
        return () => clearInterval(interval);
    }, [user, fetchWebhookStats, activeEngine]);

    // Poll security status every 30 seconds when the Security tab is active
    useEffect(() => {
        if (user?.role !== "admin" && user?.role !== "super_admin") return;
        if (activeEngine !== "Security") return;
        const interval = setInterval(() => { void fetchData(); }, 30_000);
        return () => clearInterval(interval);
    }, [user, fetchData, activeEngine]);

    const triggerAudit = async () => {
        setIsAuditing(true);
        setAuditResult(null);
        setLogs((prev: string[]) => [`[PROTOCOL] Initiating system integrity audit...`, ...prev]);
        const token = await getAuthToken();
        if (!token) { setIsAuditing(false); return; }

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/security/scan`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                signal,
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setAuditResult(data);
                    toast.success("Security scan complete");
                    setLogs((prev: string[]) => [`[SUCCESS] Integrity audit finished. Score: ${data?.report?.score ?? "?"}%`, ...prev]);
                    // Refresh status after audit
                    fetchData();
                },
                onFallback: (err: any) => {
                    setLogs((prev: string[]) => [`[FAILURE] Audit failed: ${err?.message || "Unknown error"}`, ...prev]);
                }
            }
        );
        setIsAuditing(false);
    };

    const triggerVulnerabilityScan = async () => {
        setIsScanning(true);
        setScanResult(null);
        setLogs((prev: string[]) => [`[PROTOCOL] Launching vulnerability scan...`, ...prev]);
        const token = await getAuthToken();
        if (!token) { setIsScanning(false); return; }

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/security/bias-scan`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                signal,
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setScanResult(data);
                    toast.success("Vulnerability scan complete");
                    const vulnCount = data?.scan_results?.length ?? 0;
                    setLogs((prev: string[]) => [`[SUCCESS] Vulnerability scan: bias ${data?.bias_score ?? "?"}%, ${vulnCount} findings`, ...prev]);
                },
                onFallback: (err: any) => {
                    setLogs((prev: string[]) => [`[FAILURE] Vulnerability scan failed: ${err?.message || "Unknown error"}`, ...prev]);
                }
            }
        );
        setIsScanning(false);
    };

    const saveSettings = async () => {
        setIsSaving(true);
        setLogs((prev: string[]) => [`[PROTOCOL] Committing global system changes...`, ...prev]);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback((signal) => fetch(`${API_BASE}/settings/system`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(settings)
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("System protocols updated");
                    setLogs((prev: string[]) => [`[SUCCESS] Nodes synchronized with new configuration.`, ...prev]);
                    fetchData();
                }
            }
        );
        setIsSaving(false);
    };

    // Using real agents from useTelemetry

    const tabs = [
        { id: "OAuth", label: "OAuth & Auth", icon: Key },
        { id: "API", label: "API Master", icon: Bot },
        { id: "Storage", label: "Cloud Vault", icon: Database },
        { id: "Engine", label: "Engine Params", icon: Wand2 },
        { id: "Infrastructure", label: "System Nodes", icon: Server },
        { id: "Security", label: "Security Hub", icon: Shield },
        { id: "Webhooks", label: "Webhooks", icon: Webhook },
        { id: "Audits", label: "Admin Audits", icon: FileText },
        { id: "Environment", label: "Master Protocol", icon: Terminal },
    ];

    if (authLoading || !user || (user.role !== "admin" && user.role !== "super_admin")) {
        return <div className="h-screen bg-black" />;
    }

    return (
        <CommandCenterLayout
          title="SYSTEM MASTER"
          subtitle="ADMIN_PROTOCOL_V4.0"
          leftPanel={
            <div className="space-y-1">
              {tabs.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveEngine(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                    activeEngine === item.id ? "bg-red-500/10 text-red-500 border border-red-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                  {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />}
                </button>
              ))}
            </div>
          }
          rightPanel={
            <>
              <AgentMatrix agents={agents} />
              <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Health Score</h4>
                <div className="flex flex-col">
                  <span className="text-2xl font-bold text-white">{securityStatus?.health_score || 0}%</span>
                  <span className={cn("text-[8px] font-bold uppercase tracking-widest", securityStatus?.threat_level === "LOW" ? "text-emerald-500" : "text-red-500")}>
                    Threat: {securityStatus?.threat_level || "NOMINAL"}
                  </span>
                </div>
              </div>
              <Button onClick={saveSettings} disabled={isSaving} className="w-full bg-red-500 hover:bg-red-400 text-white font-bold h-14 rounded-2xl">
                {isSaving ? "Synchronizing..." : "Commit Protocol"}
              </Button>
            </>
          }
        >
          <div className="p-10 space-y-10 relative h-full flex flex-col">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeEngine}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="flex-1 flex flex-col min-h-0"
              >
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-10">
                  {activeEngine === "OAuth" && (
                    <div className="space-y-8">
                       <h3 className="text-2xl font-bold text-white uppercase tracking-widest">OAuth Configuration</h3>
                       <div className="grid grid-cols-1 gap-6">
                         <SettingField label="Google Client ID" value={settings.google_client_id} onChange={(v) => setSettings({...settings, google_client_id: v})} />
                         <SettingField label="Google Secret" value={settings.google_client_secret} onChange={(v) => setSettings({...settings, google_client_secret: v})} isSecret />
                         <SettingField label="TikTok Key" value={settings.tiktok_client_key} onChange={(v) => setSettings({...settings, tiktok_client_key: v})} />
                         <SettingField label="TikTok Secret" value={settings.tiktok_client_secret} onChange={(v) => setSettings({...settings, tiktok_client_secret: v})} isSecret />
                       </div>
                    </div>
                  )}

                  {activeEngine === "Infrastructure" && (
                    <div className="space-y-10">
                      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Node Infrastructure</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                        <StatusCard icon={Cpu} label="CPU Load" value={systemStatus?.cpu_load || "0%"} color="text-cyan-400" />
                        <StatusCard icon={HardDrive} label="Memory" value={systemStatus?.memory_usage || "0%"} color="text-violet-400" />
                        <StatusCard icon={Activity} label="Latency" value={systemStatus?.latency || "0ms"} color="text-emerald-400" />
                        <StatusCard icon={Monitor} label="Uptime" value={systemStatus?.uptime || "0h"} color="text-amber-400" />
                      </div>
                      <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                        <SettingField label="Production Domain" value={settings.production_domain} onChange={(v) => setSettings({...settings, production_domain: v})} />
                        <SettingField label="Render Cluster URL" value={settings.render_node_url} onChange={(v) => setSettings({...settings, render_node_url: v})} />
                      </div>
                    </div>
                  )}

                  {activeEngine === "Webhooks" && (
                    <div className="space-y-10">
                      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Webhook Monitor</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                        <StatusCard icon={Webhook} label="Total Processed" value={String(webhookStats?.total_processed ?? "—")} color="text-cyan-400" />
                        <StatusCard icon={RotateCw} label="Renewals" value={String(webhookStats?.total_renewals ?? "—")} color="text-violet-400" />
                        <StatusCard icon={DollarSign} label="Credits Granted" value={String(webhookStats?.total_credits_granted ?? "—")} color="text-emerald-400" />
                        <StatusCard icon={Repeat} label="Duplicates Skipped" value={String(webhookStats?.total_skipped ?? "—")} color="text-amber-400" />
                      </div>

                      {/* Recent webhook events table */}
                      <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-white uppercase tracking-widest">Recent Purchase Events</h4>
                          <span className="text-[8px] font-mono text-cyan-500/50">STRIPE_WEBHOOK_LEDGER</span>
                        </div>
                        {webhookStats?.recent?.length > 0 ? (
                          <div className="overflow-x-auto">
                            <table className="w-full text-left">
                              <thead>
                                <tr className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest border-b border-white/5">
                                  <th className="pb-3 pr-4">User</th>
                                  <th className="pb-3 pr-4">Amount</th>
                                  <th className="pb-3 pr-4">Session ID</th>
                                  <th className="pb-3 pr-4">Description</th>
                                  <th className="pb-3">Time</th>
                                </tr>
                              </thead>
                              <tbody className="text-[10px]">
                                {webhookStats.recent.map((tx: any) => (
                                  <tr key={tx.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="py-3 pr-4 font-mono text-zinc-400">{tx.user_id}</td>
                                    <td className="py-3 pr-4 font-bold text-emerald-400">+{tx.amount}</td>
                                    <td className="py-3 pr-4 font-mono text-zinc-500">{tx.reference_id || "—"}</td>
                                    <td className="py-3 pr-4 text-zinc-400 max-w-[200px] truncate">{tx.description || "—"}</td>
                                    <td className="py-3 text-zinc-600 whitespace-nowrap">
                                      {tx.created_at ? new Date(tx.created_at).toLocaleString() : "—"}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className="py-8 text-center">
                            <Webhook className="h-8 w-8 text-zinc-800 mx-auto mb-2" />
                            <p className="text-xs font-bold text-zinc-600 uppercase tracking-wider">No webhook events recorded</p>
                            <p className="text-[9px] text-zinc-700 mt-1">Events appear after users purchase credits via Stripe</p>
                          </div>
                        )}
                      </div>

                      <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                        <h4 className="text-xs font-bold text-white uppercase tracking-widest">Idempotency Status</h4>
                        <div className="flex items-center gap-4 p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/10">
                          <ShieldCheck className="h-6 w-6 text-emerald-500 shrink-0" />
                          <div className="space-y-0.5">
                            <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Protection Active</p>
                            <p className="text-[9px] text-zinc-500">
                              Credit purchase webhooks check CreditTransactionDB for existing reference_id before granting credits.
                              Duplicate Stripe retries are automatically skipped.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeEngine === "Security" && (
                    <div className="space-y-10">
                       <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Security Sentinel</h3>

                       {/* Security Status Cards */}
                       <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                         <StatusCard icon={Shield} label="Health Score" value={`${securityStatus?.health_score ?? "—"}%`} color={securityStatus?.health_score && securityStatus.health_score >= 80 ? "text-emerald-400" : "text-red-500"} />
                         <StatusCard icon={Activity} label="Threat Level" value={securityStatus?.threat_level || "NOMINAL"} color={securityStatus?.threat_level === "CRITICAL" || securityStatus?.threat_level === "HIGH" ? "text-red-500" : securityStatus?.threat_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"} />
                         <StatusCard icon={ShieldCheck} label="System Integrity" value={securityStatus?.system_integrity || "NOMINAL"} color={securityStatus?.system_integrity === "CRITICAL" ? "text-red-500" : securityStatus?.system_integrity === "DEGRADED" ? "text-amber-400" : "text-emerald-400"} />
                         <StatusCard icon={FileText} label="Recent Threats" value={String(securityStatus?.recent_threats?.length ?? 0)} color="text-amber-400" />
                       </div>

                       {/* Threat Breakdown */}
                       {securityStatus?.threat_breakdown && (
                         <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                           <h4 className="text-xs font-bold text-white uppercase tracking-widest">Threat Breakdown (Last 100 Events)</h4>
                           <div className="grid grid-cols-4 gap-4">
                             <ThreatCounter label="Critical" count={securityStatus.threat_breakdown.critical ?? 0} color="bg-red-500" />
                             <ThreatCounter label="High" count={securityStatus.threat_breakdown.high ?? 0} color="bg-orange-500" />
                             <ThreatCounter label="Medium" count={securityStatus.threat_breakdown.medium ?? 0} color="bg-amber-500" />
                             <ThreatCounter label="Low" count={securityStatus.threat_breakdown.low ?? 0} color="bg-zinc-500" />
                           </div>
                         </div>
                       )}

                       {/* Actions */}
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                         <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                           <div className="flex items-center gap-3">
                             <ShieldCheck className="h-6 w-6 text-red-500" />
                             <div>
                               <h4 className="text-xs font-bold text-white uppercase tracking-widest">Integrity Audit</h4>
                               <p className="text-[9px] text-zinc-500 mt-0.5">Full system integrity check — SECRET_KEY, file permissions, open ports</p>
                             </div>
                           </div>
                           <Button
                             onClick={triggerAudit}
                             disabled={isAuditing}
                             className="w-full bg-red-500 hover:bg-red-400 text-white font-bold h-12 rounded-2xl"
                           >
                             {isAuditing ? "Auditing..." : "Run Audit"}
                           </Button>
                           {auditResult && (
                             <div className="space-y-2 pt-2">
                               <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                                 <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Score</span>
                                 <span className={cn("text-sm font-bold", (auditResult?.report?.score ?? 0) >= 80 ? "text-emerald-400" : "text-red-500")}>
                                   {auditResult?.report?.score ?? "?"}%
                                 </span>
                               </div>
                               {auditResult?.report?.findings?.length > 0 && (
                                 <div className="space-y-1 max-h-40 overflow-y-auto">
                                   {auditResult.report.findings.map((f: string, i: number) => (
                                     <div key={i} className="flex items-start gap-2 p-2 rounded-xl bg-red-500/5 border border-red-500/10">
                                       <AlertCircle className="h-3 w-3 text-red-500 shrink-0 mt-0.5" />
                                       <span className="text-[9px] text-zinc-400 leading-relaxed">{f}</span>
                                     </div>
                                   ))}
                                 </div>
                               )}
                               {(!auditResult?.report?.findings || auditResult.report.findings.length === 0) && (
                                 <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                                   <p className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider text-center">No findings — system is clean</p>
                                 </div>
                               )}
                             </div>
                           )}
                         </div>

                         <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                           <div className="flex items-center gap-3">
                             <Cpu className="h-6 w-6 text-violet-500" />
                             <div>
                               <h4 className="text-xs font-bold text-white uppercase tracking-widest">Vulnerability Scan</h4>
                               <p className="text-[9px] text-zinc-500 mt-0.5">Scans for debug mode, hardcoded secrets, and misconfigurations</p>
                             </div>
                           </div>
                           <Button
                             onClick={triggerVulnerabilityScan}
                             disabled={isScanning}
                             className="w-full bg-violet-500 hover:bg-violet-400 text-white font-bold h-12 rounded-2xl"
                           >
                             {isScanning ? "Scanning..." : "Run Vulnerability Scan"}
                           </Button>
                           {scanResult?.scan_results && scanResult.scan_results.length > 0 && (
                             <div className="space-y-1 max-h-40 overflow-y-auto pt-2">
                               {scanResult.scan_results.map((v: any, i: number) => (
                                 <div key={i} className="flex items-start gap-2 p-2 rounded-xl bg-red-500/5 border border-red-500/10">
                                   <AlertCircle className={cn("h-3 w-3 shrink-0 mt-0.5", v.severity === "critical" ? "text-red-500" : v.severity === "high" ? "text-orange-500" : "text-amber-500")} />
                                   <div>
                                     <div className="flex items-center gap-2">
                                       <span className="text-[8px] font-bold uppercase tracking-wider text-red-500">{v.severity}</span>
                                       <span className="text-[9px] text-zinc-300 font-bold">{v.type}</span>
                                     </div>
                                     <p className="text-[8px] text-zinc-500 leading-relaxed">{v.description}</p>
                                   </div>
                                 </div>
                               ))}
                             </div>
                           )}
                           {scanResult && (!scanResult.scan_results || scanResult.scan_results.length === 0) && (
                             <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                               <p className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider text-center">No vulnerabilities found — system is clean</p>
                             </div>
                           )}
                         </div>
                       </div>

                       {/* Security Events */}
                       <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                         <div className="flex items-center justify-between">
                           <h4 className="text-xs font-bold text-white uppercase tracking-widest">Recent Security Events</h4>
                           <span className="text-[8px] font-mono text-red-500/50">SENTINEL_LOG</span>
                         </div>
                         {securityEvents.length > 0 ? (
                           <div className="overflow-x-auto">
                             <table className="w-full text-left">
                               <thead>
                                 <tr className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest border-b border-white/5">
                                   <th className="pb-3 pr-4">Severity</th>
                                   <th className="pb-3 pr-4">Type</th>
                                   <th className="pb-3 pr-4">Details</th>
                                   <th className="pb-3">Timestamp</th>
                                 </tr>
                               </thead>
                               <tbody className="text-[10px]">
                                 {securityEvents.map((event: any, i: number) => (
                                   <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                     <td className="py-3 pr-4">
                                       <span className={cn(
                                         "px-2 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider",
                                         event.severity === "critical" ? "bg-red-500/20 text-red-500 border border-red-500/30" :
                                         event.severity === "high" ? "bg-orange-500/20 text-orange-500 border border-orange-500/30" :
                                         event.severity === "medium" ? "bg-amber-500/20 text-amber-500 border border-amber-500/30" :
                                         "bg-zinc-500/20 text-zinc-400 border border-zinc-500/30"
                                       )}>
                                         {event.severity || "low"}
                                       </span>
                                     </td>
                                     <td className="py-3 pr-4 font-mono text-zinc-300">{event.type || "—"}</td>
                                     <td className="py-3 pr-4 max-w-[250px] truncate text-zinc-500">
                                       {event.details ? (() => {
                                         const d = typeof event.details === "string" ? event.details : JSON.stringify(event.details);
                                         return d.length > 60 ? d.slice(0, 60) + "..." : d;
                                       })() : "—"}
                                     </td>
                                     <td className="py-3 text-zinc-600 whitespace-nowrap">
                                       {event.timestamp ? new Date(event.timestamp).toLocaleString() : "—"}
                                     </td>
                                   </tr>
                                 ))}
                               </tbody>
                             </table>
                           </div>
                         ) : (
                           <div className="py-8 text-center">
                             <Shield className="h-8 w-8 text-zinc-800 mx-auto mb-2" />
                             <p className="text-xs font-bold text-zinc-600 uppercase tracking-wider">No security events recorded</p>
                             <p className="text-[9px] text-zinc-700 mt-1">Events appear when sentinel detects anomalies or threats</p>
                           </div>
                         )}
                       </div>
                    </div>
                  )}

                  {activeEngine === "Audits" && (
                    <div className="space-y-10">
                      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Admin Audits</h3>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <a
                          href="/admin/audits"
                          className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6 hover:border-cyan-500/30 transition-all group"
                        >
                          <div className="h-16 w-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <FileText className="h-8 w-8 text-cyan-400" />
                          </div>
                          <div className="space-y-2">
                            <h4 className="text-lg font-bold text-white uppercase tracking-tight">Governance Engine</h4>
                            <p className="text-xs text-zinc-500 leading-relaxed">
                              Full compliance & security audit suite — account audits, red-team integrity scans,
                              bias neutrality checks, and governance telemetry logs.
                            </p>
                          </div>
                          <div className="flex items-center gap-2 text-cyan-400 text-[10px] font-bold uppercase tracking-widest group-hover:gap-3 transition-all">
                            Open Audit Console
                            <ArrowUpRight className="h-3 w-3" />
                          </div>
                        </a>

                        <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                          <div className="h-16 w-16 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                            <ShieldCheck className="h-8 w-8 text-violet-400" />
                          </div>
                          <div className="space-y-2">
                            <h4 className="text-lg font-bold text-white uppercase tracking-tight">Latest Scan Results</h4>
                            <div className="space-y-3 mt-4">
                              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">System Integrity</span>
                                <span className={cn("text-sm font-bold", (securityStatus?.health_score ?? 0) >= 80 ? "text-emerald-400" : "text-red-500")}>
                                  {securityStatus?.health_score ?? "—"}%
                                </span>
                              </div>
                              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Threat Level</span>
                                <span className={cn(
                                  "text-sm font-bold",
                                  securityStatus?.threat_level === "CRITICAL" || securityStatus?.threat_level === "HIGH" ? "text-red-500" :
                                  securityStatus?.threat_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"
                                )}>
                                  {securityStatus?.threat_level || "NOMINAL"}
                                </span>
                              </div>
                              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">System Integrity</span>
                                <span className={cn(
                                  "text-sm font-bold",
                                  securityStatus?.system_integrity === "CRITICAL" ? "text-red-500" :
                                  securityStatus?.system_integrity === "DEGRADED" ? "text-amber-400" : "text-emerald-400"
                                )}>
                                  {securityStatus?.system_integrity || "NOMINAL"}
                                </span>
                              </div>
                              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Security Events</span>
                                <span className="text-sm font-bold text-white">{securityEvents?.length ?? 0}</span>
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={triggerAudit}
                            disabled={isAuditing}
                            className="w-full bg-cyan-500 hover:bg-cyan-400 text-white font-bold h-12 rounded-2xl transition-all flex items-center justify-center gap-2"
                          >
                            {isAuditing ? "Auditing..." : "Run New Audit"}
                            <ArrowUpRight className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}


                  {activeEngine === "Environment" && (
                    <EnvManager />
                  )}
                </div>

                <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                  <div className="p-4 border-b border-white/5 flex items-center justify-between">
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Master Logs</span>
                    <span className="text-[8px] font-mono text-red-500/50">ADMIN_GATE_ACTIVE</span>
                  </div>
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                    {logs.map((log, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                        <span className={cn(
                          log.includes("[PROTOCOL]") ? "text-cyan-400" :
                          log.includes("[SUCCESS]") ? "text-emerald-500" : "text-zinc-600"
                        )}>{log}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </CommandCenterLayout>
    );
}

function SettingField({ label, value, onChange, isSecret = false }: { readonly label: string, readonly value: string, readonly onChange: (v: string) => void, readonly isSecret?: boolean }) {
  const [show, setShow] = useState(!isSecret);
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">{label}</label>
      <div className="relative">
        <input
          type={show ? "text" : "password"}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-[#0F0F11]/60 border border-white/5 rounded-2xl px-6 py-4 text-white font-mono text-xs focus:border-red-500/30 transition-all outline-none"
        />
        {isSecret && (
          <button onClick={() => setShow(!show)} className="absolute right-6 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-white transition-colors">
            {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );
}

function StatusCard({ icon: Icon, label, value, color }: { readonly icon: any, readonly label: string, readonly value: string, readonly color: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-3">
      <Icon className={cn("h-5 w-5", color)} />
      <div className="space-y-1">
        <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">{label}</span>
        <p className="text-xl font-bold text-white tracking-tight">{value}</p>
      </div>
    </div>
  );
}

function ThreatCounter({ label, count, color }: { readonly label: string, readonly count: number, readonly color: string }) {
  return (
    <div className="p-4 rounded-2xl bg-white/2 border border-white/5 text-center space-y-2">
      <div className={cn("h-2 w-full rounded-full", color)} style={{ opacity: count > 0 ? 1 : 0.15 }} />
      <p className="text-xl font-bold text-white">{count}</p>
      <p className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{label}</p>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import {
    Key,
    Database,
    Shield,
    Server,
    Wand2,
    Bot,
    Terminal,
    FileText,
    Webhook,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { ClusterManager } from "@/components/ui/ClusterManager";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import AdminSettingsPage, { InfrastructureSettings } from "./AdminSettingsPage";
import { InfrastructureStatus, WebhooksTab, SecurityHub, AuditsTab } from "./SystemConfig";
import EnvManager from "@/components/admin/EnvManager";

export default function AdminContent() {
    const { agents } = useTelemetry();
    const [activeEngine, setActiveEngine] = useState("OAuth");
    const [settings, setSettings] = useState<any>({});
    const [isSaving, setIsSaving] = useState(false);
    const [securityStatus, setSecurityStatus] = useState<any>(null);
    const [securityEvents, setSecurityEvents] = useState<any[]>([]);
    const [auditResult, setAuditResult] = useState<any>(null);
    const [scanResult, setScanResult] = useState<any>(null);
    const [isAuditing, setIsAuditing] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [systemStatus, setSystemStatus] = useState<any>(null);
    const [webhookStats, setWebhookStats] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>(["ADMIN_INITIALIZED", "PROTOCOL_READY"]);
    const [isClusterManagerOpen, setIsClusterManagerOpen] = useState(false);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

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
            withRealFallback<any>((signal) => fetch(`${API_BASE}/billing/webhook/stats`, { headers }),
                { fallback: null, onSuccess: (data) => setWebhookStats(data) }
            ),
            withRealFallback<any[]>((signal) => fetch(`${API_BASE}/security/events`, { headers }),
                { fallback: [], onSuccess: (data) => setSecurityEvents(data) }
            )
        ]);
    }, []);

    const fetchWebhookStats = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/billing/webhook/stats`, { headers: { Authorization: `Bearer ${token}` } }),
            { fallback: null, onSuccess: (data) => setWebhookStats(data) }
        );
    }, []);

    useEffect(() => { void fetchData(); }, [fetchData]);

    useEffect(() => {
        if (activeEngine !== "Webhooks") return;
        const interval = setInterval(() => { void fetchWebhookStats(); }, 30_000);
        return () => clearInterval(interval);
    }, [fetchWebhookStats, activeEngine]);

    useEffect(() => {
        if (activeEngine !== "Security") return;
        const interval = setInterval(() => { void fetchData(); }, 30_000);
        return () => clearInterval(interval);
    }, [fetchData, activeEngine]);

    const triggerAudit = async () => {
        setIsAuditing(true);
        setAuditResult(null);
        setLogs((prev) => [`[PROTOCOL] Initiating system integrity audit...`, ...prev]);
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
                    setLogs((prev) => [`[SUCCESS] Integrity audit finished. Score: ${data?.report?.score ?? "?"}%`, ...prev]);
                    fetchData();
                },
                onFallback: (err: any) => {
                    setLogs((prev) => [`[FAILURE] Audit failed: ${err?.message || "Unknown error"}`, ...prev]);
                }
            }
        );
        setIsAuditing(false);
    };

    const triggerVulnerabilityScan = async () => {
        setIsScanning(true);
        setScanResult(null);
        setLogs((prev) => [`[PROTOCOL] Launching vulnerability scan...`, ...prev]);
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
                    setLogs((prev) => [`[SUCCESS] Vulnerability scan: bias ${data?.bias_score ?? "?"}%, ${vulnCount} findings`, ...prev]);
                },
                onFallback: (err: any) => {
                    setLogs((prev) => [`[FAILURE] Vulnerability scan failed: ${err?.message || "Unknown error"}`, ...prev]);
                }
            }
        );
        setIsScanning(false);
    };

    const saveSettings = async () => {
        setIsSaving(true);
        setLogs((prev) => [`[PROTOCOL] Committing global system changes...`, ...prev]);
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
                    setLogs((prev) => [`[SUCCESS] Nodes synchronized with new configuration.`, ...prev]);
                    fetchData();
                }
            }
        );
        setIsSaving(false);
    };

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
                  {activeEngine === "OAuth" && <AdminSettingsPage settings={settings} setSettings={setSettings} />}

                  {activeEngine === "Infrastructure" && (
                    <div className="space-y-10">
                      <InfrastructureStatus systemStatus={systemStatus} setIsClusterManagerOpen={setIsClusterManagerOpen} />
                      <InfrastructureSettings settings={settings} setSettings={setSettings} />
                    </div>
                  )}

                  {activeEngine === "Webhooks" && <WebhooksTab webhookStats={webhookStats} />}

                  {activeEngine === "Security" && (
                    <SecurityHub
                      securityStatus={securityStatus}
                      securityEvents={securityEvents}
                      isAuditing={isAuditing}
                      isScanning={isScanning}
                      auditResult={auditResult}
                      scanResult={scanResult}
                      triggerAudit={triggerAudit}
                      triggerVulnerabilityScan={triggerVulnerabilityScan}
                    />
                  )}

                  {activeEngine === "Audits" && (
                    <AuditsTab
                      securityStatus={securityStatus}
                      securityEvents={securityEvents}
                      isAuditing={isAuditing}
                      triggerAudit={triggerAudit}
                    />
                  )}

                  {activeEngine === "Environment" && <EnvManager />}
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

          {isClusterManagerOpen && (
            <ClusterManager onClose={() => setIsClusterManagerOpen(false)} />
          )}
        </CommandCenterLayout>
    );
}

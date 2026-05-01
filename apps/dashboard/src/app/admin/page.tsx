"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import {
    Key,
    Database,
    Shield,
    Server,
    Save,
    EyeOff,
    Eye,
    CheckCircle2,
    Loader2,
    Layout,
    CreditCard,
    Wand2,
    Bot,
    Workflow,
    Code,
    ShoppingCart,
    TrendingUp,
    Lock,
    AlertTriangle,
    Activity,
    ScanLine,
    Clock,
    AlertOctagon,
    CheckCircle,
    XCircle,
    RefreshCw,
    Terminal,
    FileText,
    AlertCircle,
    Monitor,
    Cpu,
    HardDrive,
    Search,
    ChevronRight,
    Zap,
    Target,
    ShieldCheck,
    Dna,
    Radar
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import EnvManager from "@/components/admin/EnvManager";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";

export default function AdminSettingsPage() {
    const { user, isLoading: authLoading } = useAuth();
    const router = useRouter();
    const [activeEngine, setActiveEngine] = useState("OAuth");
    const [settings, setSettings] = useState<any>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [securityStatus, setSecurityStatus] = useState<any>(null);
    const [securityEvents, setSecurityEvents] = useState<any[]>([]);
    const [systemStatus, setSystemStatus] = useState<any>(null);
    const [adminAudits, setAdminAudits] = useState<any[]>([]);
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
            withRealFallback<any>(
                () => fetch(`${API_BASE}/settings/system`, { headers }),
                { fallback: {}, onSuccess: (data) => setSettings(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/security/status`, { headers }),
                { fallback: null, onSuccess: (data) => setSecurityStatus(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/admin/system/status`, { headers }),
                { fallback: null, onSuccess: (data) => setSystemStatus(data) }
            ),
            withRealFallback<any[]>(
                () => fetch(`${API_BASE}/admin/audits`, { headers }),
                { fallback: [], onSuccess: (data) => setAdminAudits(data) }
            )
        ]);
        setIsLoading(false);
    }, []);

    useEffect(() => {
        if (user?.role === "admin" || user?.role === "super_admin") {
            fetchData();
        }
    }, [user, fetchData]);

    const saveSettings = async () => {
        setIsSaving(true);
        setLogs((prev: string[]) => [`[PROTOCOL] Committing global system changes...`, ...prev]);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback(
            () => fetch(`${API_BASE}/settings/system`, {
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

    // Prepare Agent Data
    const agents = [
        { id: "SEC_01", name: "Firewall Guard", icon: ShieldCheck, status: "ACTIVE" as any, latency: 2, load: 1, details: "Monitoring Inbound" },
        { id: "SYS_01", name: "System Kernel", icon: Cpu, status: "ACTIVE" as any, latency: 4, load: 15, details: "Orchestrating Nodes" },
        { id: "AUDIT_01", name: "Audit Logger", icon: FileText, status: "IDLE" as any, latency: 1, load: 0, details: "Standby" },
    ];

    const tabs = [
        { id: "OAuth", label: "OAuth & Auth", icon: Key },
        { id: "API", label: "API Master", icon: Bot },
        { id: "Storage", label: "Cloud Vault", icon: Database },
        { id: "Engine", label: "Engine Params", icon: Wand2 },
        { id: "Infrastructure", label: "System Nodes", icon: Server },
        { id: "Security", label: "Security Hub", icon: Shield },
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

                  {activeEngine === "Security" && (
                    <div className="space-y-10">
                       <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Security Sentinel</h3>
                       <div className="p-10 rounded-[32px] bg-red-500/5 border border-red-500/10 flex items-center justify-between">
                         <div className="flex items-center gap-6">
                           <ShieldCheck className="h-10 w-10 text-red-500" />
                           <div className="space-y-1">
                             <h4 className="text-white font-bold uppercase tracking-widest text-sm">System Integrity</h4>
                             <p className="text-zinc-500 text-xs">Platform nodes are running verified code signatures.</p>
                           </div>
                         </div>
                         <Button className="bg-red-500 text-white font-bold h-12 px-8">Run Audit</Button>
                       </div>
                    </div>
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

function SettingField({ label, value, onChange, isSecret = false }: { label: string, value: string, onChange: (v: string) => void, isSecret?: boolean }) {
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

function StatusCard({ icon: Icon, label, value, color }: { icon: any, label: string, value: string, color: string }) {
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

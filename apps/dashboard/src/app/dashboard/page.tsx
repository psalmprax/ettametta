"use client";

import React, { useEffect, useState, useCallback, useMemo, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import Link from "next/link";
import {
  Zap,
  TrendingUp,
  Activity,
  Globe,
  CheckCircle2,
  LayoutDashboard,
  Cpu,
  History,
  Workflow,
  Terminal,
  Database,
  Radar,
  Target,
  ShieldCheck,
  LineChart,
  ArrowUpRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";
import { useRouter, useSearchParams } from "next/navigation";
import { useTelemetry } from "@/context/TelemetryContext";

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { agents, logs: systemLogs, pulse, status } = useTelemetry();
  
  const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "overview");
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [actionLogs, setActionLogs] = useState<string[]>([]);

  const fetchStats = useCallback(async () => {
    const token = await getAuthToken();
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };

    await withRealFallback<any[]>(
      () => fetch(`${API_BASE}/publish/history`, { headers }),
      { fallback: [], onSuccess: (data) => data && setActivityFeed(data.slice(0, 10)) }
    );
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const stats = useMemo(() => {
    const rs = (pulse as any)?.real_stats || {};
    const total_views = rs.total_views || 0;
    let reach_formatted = "0";
    if (total_views >= 1000000) reach_formatted = `${(total_views / 1000000).toFixed(1)}M`;
    else if (total_views >= 1000) reach_formatted = `${(total_views / 1000).toFixed(1)}K`;
    else reach_formatted = total_views.toString();

    const success_rate_val = total_views > 0 ? (rs.total_likes / total_views * 100) : 0;

    return {
      active_trends: rs.total_discovered || 0,
      videos_processed: rs.completed_jobs || 0,
      total_reach: reach_formatted,
      success_rate: `${success_rate_val.toFixed(1)}%`,
      velocity: "Nominal",
      engine_load: `${Math.min(100, Math.round((rs.active_jobs / 10) * 100))}%`
    };
  }, [pulse]);

  // Combined logs for display
  const displayLogs = useMemo(() => {
    const actionLogsFormatted = actionLogs.map(msg => ({
      level: "ACTION",
      module: "SYSTEM",
      message: msg,
      timestamp: Date.now() / 1000
    }));
    return [...actionLogsFormatted, ...systemLogs].sort((a, b) => b.timestamp - a.timestamp);
  }, [actionLogs, systemLogs]);

  return (
    <CommandCenterLayout
      title="SYSTEM DASHBOARD"
      subtitle="TELEMETRY_ENGINE_V2"
      leftPanel={
        <div className="space-y-1">
          {[
            { id: "overview", label: "Overview", icon: LayoutDashboard },
            { id: "egress", label: "Egress Stream", icon: Zap },
            { id: "engine", label: "Engine Pulse", icon: Cpu },
            { id: "history", label: "History", icon: History },
            { id: "logs", label: "Master Logs", icon: Terminal },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveEngine(item.id);
                router.replace(`/dashboard?engine=${item.id}`);
              }}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                activeEngine === item.id ? "bg-primary/10 text-primary border border-primary/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
              )}
            >
              <item.icon className="h-4 w-4" />
              <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
              {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(var(--primary),0.5)]" />}
            </button>
          ))}
        </div>
      }
      rightPanel={<AgentMatrix agents={agents} />}
    >
      <div className="p-10 space-y-10 relative h-full overflow-y-auto custom-scrollbar">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeEngine}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="flex-1"
          >
            {activeEngine === "overview" && (
              <div className="flex flex-col gap-10">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  <DesignCard 
                    title="Active Trends" 
                    status="ACTIVE" 
                    metrics={[
                      { label: "Discovered", value: stats.active_trends.toString(), color: "text-primary" },
                      { label: "Processed", value: stats.videos_processed.toString(), color: "text-zinc-400" }
                    ]}
                    footerInfo="SYSTEM_ARCH: NEURAL_LATTICE_V4"
                    toolsStatus="Online"
                    onRefresh={fetchStats}
                    onShare={() => toast.success("System Link Copied")}
                  />
                  <DesignCard 
                    title="Global Reach" 
                    status="ACTIVE" 
                    metrics={[
                      { label: "Est. Reach", value: stats.total_reach, color: "text-emerald-400" },
                      { label: "Viral Accuracy", value: stats.success_rate, color: "text-amber-500" }
                    ]}
                    footerInfo="REGION: GLOBAL_CLUSTER_01"
                    toolsStatus="Online"
                    onRefresh={fetchStats}
                    onShare={() => toast.success("Reach Stats Copied")}
                  />
                  <DesignCard 
                    title="Engine Load" 
                    status="ACTIVE" 
                    metrics={[
                      { label: "Processing", value: stats.engine_load, progress: parseInt(stats.engine_load), color: "text-rose-500" },
                      { label: "Velocity", value: stats.velocity, color: "text-cyan-400" }
                    ]}
                    footerInfo="CLUSTER: PRIMARY_REST_NODE"
                    toolsStatus="Online"
                    onRefresh={fetchStats}
                    onMore={() => setActiveEngine("engine")}
                  />
                </div>

                <div className="flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                  <div className="p-4 border-b border-white/5 flex items-center justify-between">
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">System Logs</span>
                    <span className="text-[8px] font-mono text-primary/50">DATA_HUB_ACTIVE</span>
                  </div>
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                    {displayLogs.slice(0, 15).map((log, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                        <span className={cn(
                          log.level === "ACTION" ? "text-cyan-400" :
                          log.level === "ERROR" ? "text-rose-500" : "text-zinc-600"
                        )}>{log.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeEngine === "egress" && (
              <div className="flex-1 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col space-y-8 min-h-0">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-white flex items-center gap-3">
                    <Zap className="h-5 w-5 text-emerald-400" />
                    Live Egress Stream
                  </h3>
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-bold text-emerald-500 uppercase">Observer_Active</span>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="p-5 bg-white/5 border border-white/5 rounded-2xl flex items-center justify-between group hover:border-emerald-500/30 transition-all">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                          <Globe className="h-5 w-5 text-emerald-400" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-white">Egress_Gate_Sequence_{i}</h4>
                          <p className="text-[10px] text-zinc-500">Destination: Neural_Buffer_US_01</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono text-emerald-500 font-bold uppercase tracking-widest">SECURED</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeEngine === "engine" && (
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-0">
                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col items-center justify-center space-y-6 text-center">
                  <Activity className="h-16 w-16 text-cyan-400 animate-pulse" />
                  <div className="space-y-2">
                    <h4 className="text-xl font-bold text-white uppercase tracking-tighter">Neural Throughput</h4>
                    <p className="text-xs text-zinc-500 max-w-[300px]">Live telemetry stream from global orchestration nodes. Monitoring {pulse?.active_segments?.length || 0} active neural channels.</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4 w-full max-w-sm">
                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                      <span className="block text-[10px] font-bold text-zinc-600 uppercase">Latency</span>
                      <span className="text-lg font-bold text-cyan-400">{pulse?.metrics?.latency?.toFixed(0) || pulse?.latency_ms?.toFixed(0) || "---"}ms</span>
                    </div>
                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                      <span className="block text-[10px] font-bold text-zinc-600 uppercase">Signal</span>
                      <span className="text-lg font-bold text-emerald-500">{(pulse?.metrics?.signal_strength || 1.0) * 100}%</span>
                    </div>
                  </div>
                </div>
                <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col space-y-6">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-white uppercase tracking-widest">Active Channels</h4>
                    <span className="text-[10px] font-mono text-cyan-400">{status === "open" ? "SYNCED" : "RECONNECTING..."}</span>
                  </div>
                  <div className="space-y-4">
                    {(pulse?.active_segments || []).slice(0, 5).map(node => (
                      <div key={node.label} className="flex items-center justify-between p-4 bg-white/2 border border-white/5 rounded-xl">
                        <span className="text-xs font-bold text-zinc-400">{node.label}</span>
                        <div className="h-1.5 w-24 bg-white/5 rounded-full overflow-hidden">
                          <motion.div 
                            animate={{ width: [`${node.load}%`, `${Math.min(100, node.load + 10)}%`, `${node.load}%`] }}
                            transition={{ duration: 3, repeat: Infinity }}
                            className="h-full bg-cyan-500" 
                          />
                        </div>
                      </div>
                    ))}
                    {(!pulse?.active_segments || pulse.active_segments.length === 0) && (
                      <div className="text-center py-10 text-zinc-600 text-[10px] uppercase font-bold tracking-widest">Awaiting Neural Link...</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeEngine === "history" && (
              <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-4">
                {activityFeed.map((activity, idx) => (
                  <div key={idx} className="p-6 rounded-2xl bg-[#0F0F11]/60 border border-white/5 flex items-center justify-between group hover:border-violet-500/30 transition-all">
                    <div className="flex items-center gap-6">
                      <div className="h-12 w-12 rounded-xl bg-violet-500/10 flex items-center justify-center">
                        <History className="h-6 w-6 text-violet-400" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-white uppercase">{activity.title || "NEURAL_SEQUENCE"}</span>
                        <span className="text-[10px] text-zinc-500">{new Date(activity.published_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-[8px] font-mono text-zinc-600">ID: {activity.id?.slice(0, 12)}</span>
                      <div className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-bold text-emerald-500 uppercase">SUCCESS</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeEngine === "logs" && (
              <div className="flex-1 flex flex-col bg-[#0F0F11]/80 rounded-[32px] border border-white/5 overflow-hidden">
                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/40">
                  <div className="flex items-center gap-3">
                    <Terminal className="h-4 w-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-widest">Master System Log Stream</h3>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                  {displayLogs.map((log, i) => (
                    <div key={i} className="flex gap-6 items-start border-b border-white/[0.02] pb-2">
                      <span className="text-zinc-800 shrink-0">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                      <span className={cn(
                        "break-all",
                        log.level === "ACTION" ? "text-cyan-400" :
                        log.level === "ERROR" ? "text-rose-500" : 
                        log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-500"
                      )}>{log.module ? `[${log.module}] ` : ""}{log.message}</span>
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

export default function Home() {
  return (
    <Suspense fallback={null}>
      <DashboardContent />
    </Suspense>
  );
}

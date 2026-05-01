"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
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
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE, WS_BASE } from "@/lib/config";
import { useWebSocket } from "@/hooks/useWebSocket";
import { getAuthToken } from "@/lib/auth_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

export default function Home() {
  const [activeEngine, setActiveEngine] = useState("overview");
  const [stats, setStats] = useState({
    active_trends: 0,
    videos_processed: 0,
    total_reach: "0",
    success_rate: "0%",
    velocity: "Nominal",
    engine_load: "0%"
  });
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>(["SYSTEM_INITIALIZED", "SYNCHRONIZING_GLOBAL_NODES"]);
  const { data: wsData } = useWebSocket<any>(`${WS_BASE}/telemetry`);

  const fetchStats = useCallback(async () => {
    const token = await getAuthToken();
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };

    await Promise.all([
      withRealFallback<any>(
        () => fetch(`${API_BASE}/analytics/stats/summary`, { headers }),
        { fallback: null, onSuccess: (data) => data && setStats(prev => ({ ...prev, ...data })) }
      ),
      withRealFallback<any[]>(
        () => fetch(`${API_BASE}/publish/history`, { headers }),
        { fallback: [], onSuccess: (data) => data && setActivityFeed(data.slice(0, 10)) }
      )
    ]);
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  useEffect(() => {
    if (wsData && wsData.type === "telemetry_pulse") {
      const { real_stats, metrics } = wsData;
      setStats(prev => {
        const total_views = real_stats.total_views || 0;
        let reach_formatted = "0";
        if (total_views >= 1000000) reach_formatted = `${(total_views / 1000000).toFixed(1)}M`;
        else if (total_views >= 1000) reach_formatted = `${(total_views / 1000).toFixed(1)}K`;
        else reach_formatted = total_views.toString();

        const success_rate_val = total_views > 0 ? (real_stats.total_likes / total_views * 100) : 0;
        
        return {
          ...prev,
          active_trends: real_stats.total_discovered || prev.active_trends,
          videos_processed: real_stats.completed_jobs || prev.videos_processed,
          total_reach: reach_formatted,
          success_rate: `${success_rate_val.toFixed(1)}%`,
          velocity: metrics.global_velocity > 3 ? "Critical" : metrics.global_velocity > 1.5 ? "High" : "Nominal",
          engine_load: `${Math.min(100, Math.round((real_stats.active_jobs / 10) * 100))}%`
        };
      });
      setLogs((prev: string[]) => [`[TELEMETRY] Pulse received. Velocity: ${metrics.global_velocity.toFixed(2)}x`, ...prev.slice(0, 50)]);
    }
  }, [wsData]);

  // Prepare Agent Data
  const agents = [
    { id: "CORE_01", name: "System Kernel", icon: Cpu, status: "ACTIVE" as any, latency: 4, load: 2, details: "Kernel Stable" },
    { id: "INTEL_01", name: "Trend Monitor", icon: Radar, status: "ACTIVE" as any, latency: 45, load: 12, details: "Polling Viral Clusters" },
    { id: "EGRESS_01", name: "Egress Gate", icon: Zap, status: "ACTIVE" as any, latency: 12, load: 5, details: "Nodes Verified" },
  ];

  return (
    <CommandCenterLayout
      title="SYSTEM DASHBOARD"
      subtitle="GLOBAL_INTELLIGENCE_OS_V4.0"
      leftPanel={
        <div className="space-y-1">
          {[
            { id: "overview", label: "Intelligence Overview", icon: LayoutDashboard },
            { id: "egress", label: "Live Egress Stream", icon: Zap },
            { id: "engine", label: "Engine Pulse", icon: Cpu },
            { id: "history", label: "Neural History", icon: History },
            { id: "logs", label: "System Logs", icon: Terminal },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveEngine(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                activeEngine === item.id ? "bg-primary/10 text-primary border border-primary/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
              )}
            >
              <item.icon className="h-4 w-4" />
              <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
              {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(var(--primary-rgb),0.5)]" />}
            </button>
          ))}
        </div>
      }
      rightPanel={
        <>
          <AgentMatrix agents={agents} />
          <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
            <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Reach</h4>
            <div className="flex flex-col">
              <span className="text-2xl font-bold text-white">{stats.total_reach}</span>
              <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-widest">{stats.success_rate} Accuracy</span>
            </div>
          </div>
        </>
      }
    >
      <div className="p-10 space-y-10 relative h-full flex flex-col">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeEngine}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex-1 flex flex-col min-h-0"
          >
            {activeEngine === "overview" && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                <DesignCard
                  title="Neural Core"
                  status="Current"
                  metrics={[
                    { label: "Active Trends", value: stats.active_trends, progress: 85, color: "text-cyan-400" },
                    { label: "Core Output", value: stats.videos_processed, progress: 62, color: "text-violet-400" }
                  ]}
                  footerInfo="SYSTEM_ARCH: NEURAL_LATTICE_V4"
                  toolsStatus="Online"
                />
                <DesignCard
                  title="Global Reach"
                  status="Active"
                  metrics={[
                    { label: "Est. Reach", value: stats.total_reach, progress: 45, color: "text-emerald-400" },
                    { label: "Viral Accuracy", value: stats.success_rate, progress: 92, color: "text-amber-400" }
                  ]}
                  footerInfo="REGION: GLOBAL_CLUSTER_01"
                  toolsStatus="Online"
                />
                <DesignCard
                  title="Engine Load"
                  status="Active"
                  metrics={[
                    { label: "Processing", value: stats.engine_load, progress: parseInt(stats.engine_load), color: "text-rose-400" },
                    { label: "Velocity", value: stats.velocity, progress: 50, color: "text-blue-400" }
                  ]}
                  footerInfo="CLUSTER: PRIMARY_REST_NODE"
                  toolsStatus="Online"
                />
              </div>
            )}

            {activeEngine === "egress" && (
              <div className="space-y-6 overflow-y-auto custom-scrollbar flex-1 p-1">
                {activityFeed.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center opacity-30 grayscale space-y-4 py-40">
                    <Zap className="h-16 w-16" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.5em]">No active egress activity</span>
                  </div>
                ) : (
                  activityFeed.map((activity, idx) => (
                    <div key={activity.id || idx} className="p-8 rounded-[32px] bg-[#0F0F11] border border-white/5 flex items-center justify-between group hover:border-cyan-500/20 transition-all">
                      <div className="flex items-center gap-8">
                        <div className="h-16 w-16 rounded-2xl bg-cyan-500/10 flex items-center justify-center">
                          <Zap className="h-8 w-8 text-cyan-500" />
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-lg font-bold text-white uppercase tracking-tight">{activity.title || "Untitled Sequence"}</span>
                          <span className="text-xs text-zinc-500 font-bold uppercase tracking-widest">{activity.platform} • {new Date(activity.published_at).toLocaleTimeString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">SEQ_ID: {activity.id?.slice(0, 8) || "..."}_NODE</span>
                        <ArrowUpRight className="h-4 w-4 text-zinc-800 group-hover:text-cyan-400 transition-colors" />
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">System Logs</span>
                <span className="text-[8px] font-mono text-primary/50">DATA_HUB_ACTIVE</span>
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className="flex gap-4">
                    <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                    <span className={cn(
                      log.includes("[TELEMETRY]") ? "text-cyan-400" :
                      log.includes("[SYSTEM]") ? "text-violet-500" : "text-zinc-600"
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

"use client";

import React, { useEffect, useState } from "react";
import DashboardLayout from "@/components/layout";
import Link from "next/link";
import {
  Zap,
  TrendingUp,
  Clock,
  PlusCircle,
  Play,
  CheckCircle2
} from "lucide-react";

import { motion, Variants } from "framer-motion";
import { API_BASE } from "@/lib/config";

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const itemVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] }
  }
};

interface DashboardStats {
  active_trends: number;
  videos_processed: number;
  total_reach: string;
  success_rate: string;
  storage?: {
    current_size_gb: number;
    threshold_gb: number;
    usage_percent: number;
    status: string;
    provider: string;
  };
}

export default function Home() {
  const [stats, setStats] = useState<DashboardStats>({
    active_trends: 0,
    videos_processed: 0,
    total_reach: "0",
    success_rate: "0%"
  });
  const [isLoading, setIsLoading] = useState(true);
  const [activityFeed, setActivityFeed] = useState<any[]>([]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem("et_token");
        const response = await fetch(`${API_BASE}/analytics/stats/summary`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();

          // Fetch storage stats
          const storageResponse = await fetch(`${API_BASE}/analytics/stats/storage`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (storageResponse.ok) {
            data.storage = await storageResponse.json();
          }

          setStats(data);

          // Fetch Egress history for activity feed
          const historyRes = await fetch(`${API_BASE}/publish/history`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (historyRes.ok) {
            const history = await historyRes.json();
            setActivityFeed(history.slice(0, 5));
          }
        }
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <DashboardLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-10"
      >
        <motion.div variants={itemVariants} className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="h-1 w-8 bg-primary rounded-full" />
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">System Command</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-black tracking-tighter italic uppercase text-white">Neural <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-500 text-hollow">Dashboard</span></h1>
          <p className="text-zinc-500 font-medium max-w-lg">
            Aggregated intelligence from Nigerian & Global social clusters.
            Engine status: <span className="text-emerald-500 font-bold uppercase">Nominal</span>
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <TelemetryTile
            title="Active Trends"
            value={stats.active_trends.toString()}
            icon={<TrendingUp className="h-5 w-5 text-emerald-400" />}
            label="Real-time scan"
            subtext={`+${(stats as any).recent_discovery_count || 0} discovered`}
          />
          <TelemetryTile
            title="Core Throughput"
            value={stats.videos_processed.toString()}
            icon={<Zap className="h-5 w-5 text-primary" />}
            label="Total Processed"
            subtext={`Load: ${(stats as any).engine_load || "0%"}`}
          />
          <TelemetryTile
            title="Global Reach"
            value={stats.total_reach}
            icon={<Play className="h-5 w-5 text-blue-400" />}
            label="Est. Impressions"
            subtext={`Velocity: ${(stats as any).velocity || "Nominal"}`}
          />
          <TelemetryTile
            title="Model Precision"
            value={stats.success_rate}
            icon={<CheckCircle2 className="h-5 w-5 text-zinc-400" />}
            label="Accuracy Index"
            subtext="Verified"
          />
        </motion.div>

        {/* Core Actions */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ActionCard
            title="Trend Discovery"
            description="Autonomous social mining for high-velocity niche opportunities."
            buttonText="Trigger Scan"
            href="/discovery"
          />
          <ActionCard
            title="Mirror Studio"
            description="Generative originality transforms with AI-driven face & voice synthesis."
            buttonText="Open Studio"
            href="/transformation"
          />
          <ActionCard
            title="Global Distribution"
            description="Manage multi-node publishing cycles for verified Social Assets."
            buttonText="Command Center"
            href="/publishing"
          />
        </motion.div>

        {/* Storage Monitoring Section */}
        {stats.storage && (
          <motion.div variants={itemVariants} className="glass-card p-8 rounded-[2rem] relative overflow-hidden group border border-white/5 hover:border-primary/30 transition-all">
            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
              <div className="space-y-4 text-center md:text-left">
                <div className="flex items-center gap-3 justify-center md:justify-start">
                  <div className={`h-2 w-2 rounded-full animate-pulse ${stats.storage.status === 'Healthy' ? 'bg-emerald-500' : stats.storage.status === 'Warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
                  <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Storage Lifecycle Manager</span>
                </div>
                <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">Autonomous <span className="text-primary">Archival</span> Status</h3>
                <p className="text-zinc-500 font-medium max-w-md">
                  Monitoring local video assets. Automatic migration to <span className="text-white font-bold">{stats.storage.provider}</span> triggers at {stats.storage.threshold_gb}GB.
                </p>
              </div>

              <div className="flex-1 w-full max-w-md space-y-4">
                <div className="flex justify-between items-end">
                  <span className="text-2xl font-black text-white">{stats.storage.current_size_gb} <span className="text-sm text-zinc-500 uppercase font-bold tracking-widest">GB Used</span></span>
                  <span className="text-sm font-black text-primary">{stats.storage.usage_percent}%</span>
                </div>
                <div className="h-4 w-full bg-white/5 rounded-full overflow-hidden border border-white/5 p-1">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${stats.storage.usage_percent}%` }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className={`h-full rounded-full ${stats.storage.status === 'Healthy' ? 'bg-emerald-500' : stats.storage.status === 'Warning' ? 'bg-amber-500' : 'bg-red-500'}`}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-zinc-600">
                  <span>0 GB</span>
                  <span>Threshold: {stats.storage.threshold_gb} GB</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Recent Activity Section */}
        <motion.div variants={itemVariants} className="space-y-6">
          <div className="flex items-center justify-between px-4">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-zinc-500" />
              <h3 className="text-xs font-black uppercase tracking-[0.25em] text-zinc-500">Global Egress Feed</h3>
            </div>
            <Link href="/publishing" className="text-[10px] font-black text-primary uppercase tracking-widest hover:underline transition-all">
              View Node Matrix →
            </Link>
          </div>

          {!activityFeed || activityFeed.length === 0 ? (
            <motion.div className="glass-card flex flex-col items-center justify-center text-center py-16 gap-6 relative overflow-hidden group">
              <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
              <div className="h-16 w-16 rounded-3xl bg-white/[0.03] border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                <Clock className="h-8 w-8 text-zinc-600" />
              </div>
              <div className="space-y-2 relative">
                <h3 className="text-2xl font-black tracking-tight text-white uppercase">Awaiting Telemetry</h3>
                <p className="text-zinc-500 max-w-sm mx-auto font-medium">Your command buffer is empty. Start a discovery cycle to find viral opportunities.</p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 items-center">
                <Link href="/discovery" className="bg-primary hover:bg-primary/90 text-white font-black py-4 px-10 rounded-2xl transition-all flex items-center gap-3 shadow-[0_0_30px_rgba(var(--primary-rgb),0.2)] group-hover:shadow-[0_0_50px_rgba(var(--primary-rgb),0.4)] relative">
                  <PlusCircle className="h-5 w-5" />
                  Initiate Discovery
                </Link>
              </div>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activityFeed.map((activity, idx) => (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="glass-card p-6 flex items-center gap-4 group hover:border-primary/30 transition-all border border-white/5"
                >
                  <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0">
                    <Zap className="h-6 w-6 text-primary neon-glow" />
                  </div>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">{activity.platform}</p>
                      <p className="text-[9px] font-bold text-zinc-600 tabular-nums uppercase">{new Date(activity.published_at).toLocaleTimeString()}</p>
                    </div>
                    <h4 className="text-sm font-black text-white truncate uppercase tracking-tight">{activity.title}</h4>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
}

function TelemetryTile({ title, value, icon, label, subtext }: { title: string, value: string, icon: React.ReactNode, label: string, subtext: string }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -5 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="glass-card p-6 rounded-3xl space-y-4 relative group overflow-hidden"
    >
      <div className="absolute inset-0 shimmer-elite opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">{title}</p>
          <h2 className="text-3xl font-black text-white tracking-tighter">{value}</h2>
        </div>
        <div className="p-3 rounded-2xl bg-white/[0.03] border border-white/5 group-hover:border-primary/30 transition-colors">
          {icon}
        </div>
      </div>
      <div className="pt-2 flex items-center justify-between border-t border-white/5">
        <span className="text-[10px] font-bold text-zinc-400">{label}</span>
        <span className="text-[10px] font-bold text-primary uppercase tracking-tighter">{subtext}</span>
      </div>
    </motion.div>
  );
}

function ActionCard({ title, description, buttonText, href }: { title: string, description: string, buttonText: string, href: string }) {
  return (
    <Link href={href}>
      <motion.div
        whileHover={{ scale: 1.02, y: -8 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 350, damping: 20 }}
        className="glass-card p-8 rounded-[2rem] h-full flex flex-col justify-between space-y-6 hover:border-primary/50 transition-all duration-300 group text-left relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-opacity">
          <Zap className="h-24 w-24 text-primary" />
        </div>
        <div className="space-y-3 relative">
          <h3 className="text-xl font-black text-white uppercase tracking-tight">{title}</h3>
          <p className="text-zinc-500 text-sm font-medium leading-relaxed">{description}</p>
        </div>
        <div className="w-full bg-zinc-900 border border-white/10 group-hover:border-primary/50 text-zinc-400 group-hover:text-white font-black py-4 px-6 rounded-xl transition-all duration-300 text-center uppercase text-xs tracking-widest relative">
          {buttonText}
        </div>
      </motion.div>
    </Link>
  );
}

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
}

export default function Home() {
  const [stats, setStats] = useState<DashboardStats>({
    active_trends: 0,
    videos_processed: 0,
    total_reach: "0",
    success_rate: "0%"
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem("vf_token");
        const response = await fetch(`${API_BASE}/analytics/stats/summary`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setStats(data);
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

        {/* Recent Activity Section */}
        <motion.div variants={itemVariants} className="glass-card flex flex-col items-center justify-center text-center gap-6 relative overflow-hidden group">
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
            <Link href="/publishing" className="text-zinc-500 hover:text-white font-bold text-sm transition-colors">
              Manage Node Links
            </Link>
          </div>
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

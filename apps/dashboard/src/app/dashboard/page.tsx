"use client";

import React, { useEffect, useState, Suspense } from "react";
import DashboardLayout from "@/components/layout";
import { withRealFallback } from "@/lib/real_first_utils";
import Link from "next/link";
import {
  Zap,
  TrendingUp,
  Clock,
  PlusCircle,
  Play,
  CheckCircle2,
  Activity,
  Cpu,
  Globe,
  Radio,
  ArrowRight,
  Database,
  Terminal,
  Infinity as InfinityIcon,
  Fingerprint
} from "lucide-react";
import { cn } from "@/lib/utils";

import { motion, Variants, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { API_BASE, WS_BASE } from "@/lib/config";
import { useNiches } from "@/hooks/useNiches";
import { useWebSocket } from "@/hooks/useWebSocket";
import { getAuthToken } from "@/lib/auth_utils";
import { Canvas } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";

function DashboardBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#00fbfb" />
                    <Float speed={1} rotationIntensity={0.5} floatIntensity={0.5}>
                        <Sphere args={[1.5, 64, 64]} scale={2}>
                            <MeshDistortMaterial
                                color="#00fbfb"
                                speed={2}
                                distort={0.2}
                                radius={1}
                                wireframe
                                transparent
                                opacity={0.1}
                            />
                        </Sphere>
                    </Float>
                </Suspense>
            </Canvas>
        </div>
    );
}

export default function Home() {
  const { niches } = useNiches();
  const [stats, setStats] = useState({
    active_trends: 0,
    videos_processed: 0,
    total_reach: "0",
    success_rate: "0%",
    velocity: "Nominal",
    engine_load: "0%"
  });
  const [isLoading, setIsLoading] = useState(true);
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const { data: wsData } = useWebSocket<any>(`${WS_BASE}/telemetry`);

  const fetchStats = async () => {
    const token = await getAuthToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    const headers = { Authorization: `Bearer ${token}` };

    await Promise.all([
      withRealFallback<any>(
        () => fetch(`${API_BASE}/v1/analytics/stats/summary`, { headers }),
        {
          fallback: null,
          onSuccess: (data) => data && setStats(prev => ({ ...prev, ...data }))
        }
      ),
      withRealFallback<any[]>(
        () => fetch(`${API_BASE}/v1/publish/history`, { headers }),
        {
          fallback: [],
          onSuccess: (data) => data && setActivityFeed(data.slice(0, 6))
        }
      )
    ]);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-[#050507] relative flex flex-col font-sans overflow-hidden">
        <div className="noise-overlay" />
        <DashboardBackground />
        <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
        <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

        <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
          
          {/* DASHBOARD HEADER */}
          <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
            <div className="space-y-6">
                <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: 140 }}
                    className="h-1 bg-cyan-400"
                />
                <div className="space-y-2">
                    <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none glitch-text italic" data-text="NEURAL_OS">
                        Neural OS
                    </h1>
                    <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                        <Terminal className="h-3 w-3 text-cyan-400" />
                        SYSTEM_ARCH: QUANTUM_LATTICE
                        <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                        UPTIME: 100.0%
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <div className="surface-glass rim-light p-6 flex flex-col items-end">
                    <span className="font-data-mono text-[8px] text-zinc-600 mb-1">ENGINE_LOAD</span>
                    <span className="text-xl font-black text-white tabular-nums tracking-tighter">
                        {stats.engine_load}
                    </span>
                </div>
                <Link href="/creation" className="action-primary h-20 px-12 flex items-center italic text-xs tracking-tighter">
                    INITIATE_CREATION
                </Link>
            </div>
          </header>

          {/* TELEMETRY TILES */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
            {[
              { label: "TREND_CLUSTERS", val: stats.active_trends, icon: TrendingUp, color: "text-cyan-400" },
              { label: "CORE_OUTPUT", val: stats.videos_processed, icon: Zap, color: "text-purple-400" },
              { label: "EST_REACH", val: stats.total_reach, icon: Globe, color: "text-emerald-400" },
              { label: "VIRAL_ACCURACY", val: stats.success_rate, icon: CheckCircle2, color: "text-amber-400" },
            ].map((stat, i) => (
              <motion.div 
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="surface-glass rim-light p-8 space-y-4 hover:rim-glow-cyan transition-all group"
              >
                <div className="flex items-center justify-between">
                    <stat.icon className={cn("h-5 w-5", stat.color)} />
                    <span className="font-data-mono text-[8px] text-zinc-700 tracking-[0.5em]">{stat.label}</span>
                </div>
                <h4 className="text-4xl font-black text-white tracking-tighter italic group-hover:text-cyan-400 transition-colors">{stat.val}</h4>
                <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                    <span className="font-label-caps text-[8px] text-zinc-600 tracking-widest">REAL_TIME_PULSE</span>
                    <Activity className="h-3 w-3 text-emerald-500 animate-pulse" />
                </div>
              </motion.div>
            ))}
          </div>

          {/* ACCESS TERMINALS */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-20">
            {[
              { title: "Discovery Console", desc: "Scan global clusters for high-velocity viral seeds.", href: "/discovery", icon: Database },
              { title: "Synthesis Hub", desc: "Transform seeds into premium social assets.", href: "/creation", icon: Cpu },
              { title: "Egress Matrix", desc: "Broadcast validated assets to the national grid.", href: "/publishing", icon: Radio },
            ].map((node, i) => (
              <Link 
                key={node.title}
                href={node.href}
                className="surface-glass rim-light p-10 space-y-6 group hover:rim-glow-cyan transition-all relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-10 transition-opacity">
                    <node.icon className="h-32 w-32 text-cyan-400" />
                </div>
                <div className="space-y-2 relative">
                    <h3 className="text-2xl font-black text-white uppercase tracking-tighter group-hover:text-cyan-400 transition-colors italic">{node.title}</h3>
                    <p className="text-zinc-500 text-sm font-medium leading-relaxed">{node.desc}</p>
                </div>
                <div className="pt-6 relative">
                    <div className="w-full bg-zinc-950 border border-white/5 group-hover:border-cyan-400/30 text-zinc-600 group-hover:text-cyan-400 py-4 font-label-caps text-[10px] text-center tracking-[0.4em] transition-all">
                        ENTER_TERMINAL
                    </div>
                </div>
              </Link>
            ))}
          </div>

          {/* EGRESS FEED */}
          <div className="space-y-10">
            <div className="flex items-center justify-between border-b border-white/5 pb-6">
                <div className="flex items-center gap-4">
                    <div className="h-3 w-3 bg-cyan-400 animate-ping rounded-full" />
                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter italic">Live Egress Stream</h2>
                </div>
                <Link href="/publishing" className="font-label-caps text-[9px] text-zinc-500 hover:text-cyan-400 transition-colors tracking-widest">
                    VIEW_FULL_HISTORY →
                </Link>
            </div>

            {activityFeed.length === 0 ? (
                <div className="surface-glass rim-light py-20 flex flex-col items-center justify-center text-center space-y-6">
                    <div className="h-16 w-16 bg-white/5 border border-white/10 flex items-center justify-center rounded-3xl">
                        <Radio className="h-8 w-8 text-zinc-700" />
                    </div>
                    <div className="space-y-1">
                        <h3 className="text-xl font-black text-white uppercase italic tracking-tighter">Awaiting Signal</h3>
                        <p className="text-zinc-500 font-medium text-sm">No recent egress detected in the local cluster.</p>
                    </div>
                    <Link href="/creation" className="action-primary py-4 px-10 italic text-[10px] tracking-tighter">
                        START_INITIAL_SEQUENCE
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {activityFeed.map((activity, idx) => (
                        <motion.div
                            key={activity.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="surface-glass rim-light p-6 flex items-center gap-5 group hover:rim-glow-cyan transition-all border border-white/5"
                        >
                            <div className="h-14 w-14 bg-cyan-400/5 border border-cyan-400/20 flex items-center justify-center group-hover:bg-cyan-400 group-hover:text-black transition-all">
                                <Play className="h-6 w-6 text-cyan-400 group-hover:text-black fill-current" />
                            </div>
                            <div className="flex-1 min-w-0 space-y-1">
                                <div className="flex items-center justify-between">
                                    <span className="font-data-mono text-[8px] text-cyan-400/60 uppercase">{activity.platform}</span>
                                    <span className="font-data-mono text-[7px] text-zinc-700">{new Date(activity.published_at).toLocaleTimeString()}</span>
                                </div>
                                <h4 className="text-sm font-black text-white truncate uppercase tracking-tight group-hover:text-cyan-400 transition-colors">{activity.title}</h4>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

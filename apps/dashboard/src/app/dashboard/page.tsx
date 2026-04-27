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
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

function DashboardBackground() {
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            setMousePos({ x: e.clientX / window.innerWidth - 0.5, y: e.clientY / window.innerHeight - 0.5 });
        };
        window.addEventListener("mousemove", handleMouseMove);
        return () => window.removeEventListener("mousemove", handleMouseMove);
    }, []);

    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
            <motion.div 
                animate={{ 
                    x: mousePos.x * 20, 
                    y: mousePos.y * 20,
                    rotateX: mousePos.y * 10,
                    rotateY: -mousePos.x * 10 
                }}
                className="absolute inset-0 cyber-grid opacity-30"
            />
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
      <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
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
                    <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tight leading-none" data-text="INTELLIGENCE_OS">
                        Intelligence OS
                    </h1>
                    <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                        <Terminal className="h-3 w-3 text-cyan-400" />
                        SYSTEM_ARCH: NEURAL_LATTICE_V4
                        <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                        UPTIME: 100.0%
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <Card variant="solid" className="p-6 flex flex-col items-end gap-1 rounded-2xl">
                    <span className="font-data-mono text-[8px] text-zinc-600 uppercase tracking-wider">Engine Load</span>
                    <span className="text-xl font-bold text-white tabular-nums tracking-tight">
                        {stats.engine_load}
                    </span>
                </Card>
                <Link href="/creation">
                    <Button variant="primary" size="xl" className="tracking-tight shadow-[0_0_30px_rgba(0,251,251,0.15)] rounded-full px-12">
                        INITIALIZE_CREATION
                    </Button>
                </Link>
            </div>
          </header>

          {/* TELEMETRY TILES */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
            {[
              { label: "Trend Clusters", val: stats.active_trends, icon: TrendingUp, color: "text-cyan-400" },
              { label: "Core Output", val: stats.videos_processed, icon: Zap, color: "text-violet-400" },
              { label: "Est. Reach", val: stats.total_reach, icon: Globe, color: "text-emerald-400" },
              { label: "Viral Accuracy", val: stats.success_rate, icon: CheckCircle2, color: "text-amber-400" },
            ].map((stat, i) => (
                <motion.div 
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="surface-glass p-8 rounded-3xl border border-white/5 hover:border-cyan-400/30 transition-all group relative overflow-hidden"
              >
                <div className="absolute inset-0 glass-refraction opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="flex items-center justify-between">
                    <stat.icon className={cn("h-5 w-5", stat.color)} />
                    <span className="font-data-mono text-[8px] text-zinc-500 uppercase tracking-widest">{stat.label}</span>
                </div>
                <h4 className="text-4xl font-bold text-white tracking-tight group-hover:text-cyan-400 transition-colors">{stat.val}</h4>
                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                    <span className="font-data-mono text-[7px] text-zinc-600 uppercase tracking-wider">Neural Pulse</span>
                    <Activity className="h-3 w-3 text-emerald-500 animate-pulse" />
                </div>
              </motion.div>
            ))}
          </div>

          {/* ACCESS TERMINALS */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-20">
            {[
              { title: "Discovery Console", desc: "Scan global clusters for high-velocity viral seeds.", href: "/discovery", icon: Database },
              { title: "Synthesis Hub", desc: "Transform seeds into premium social assets.", href: "/creation", icon: Cpu },
              { title: "Egress Matrix", desc: "Broadcast validated assets to the national grid.", href: "/publishing", icon: Radio },
            ].map((node, i) => (
              <Link 
                key={node.title}
                href={node.href}
                className="surface-glass p-10 rounded-[2.5rem] border border-white/5 group hover:border-cyan-400/30 transition-all relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-10 transition-opacity">
                    <node.icon className="h-24 w-24 text-cyan-400" />
                </div>
                <div className="space-y-3 relative">
                    <h3 className="text-2xl font-bold text-white uppercase tracking-tight group-hover:text-cyan-400 transition-colors">{node.title}</h3>
                    <p className="text-zinc-500 text-sm font-medium leading-relaxed">{node.desc}</p>
                </div>
                <div className="pt-6 relative">
                    <div className="w-full bg-white/2 border border-white/5 rounded-2xl group-hover:border-cyan-400/30 text-zinc-500 group-hover:text-white py-4 font-bold text-[10px] text-center tracking-[0.3em] transition-all uppercase">
                        Initialize Terminal
                    </div>
                </div>
              </Link>
            ))}
          </div>

          {/* EGRESS FEED */}
          <div className="space-y-8">
            <div className="flex items-center justify-between border-b border-white/5 pb-6">
                <div className="flex items-center gap-4">
                    <div className="h-2 w-2 bg-cyan-400 animate-ping rounded-full" />
                    <h2 className="text-2xl font-bold text-white uppercase tracking-tight">Live Egress Stream</h2>
                </div>
                <Link href="/publishing" className="font-data-mono text-[9px] text-zinc-500 hover:text-cyan-400 transition-colors uppercase tracking-widest">
                    SYSTEM_HISTORY →
                </Link>
            </div>

            {activityFeed.length === 0 ? (
                <Card variant="solid" className="py-20 flex flex-col items-center justify-center text-center space-y-8 rounded-[3rem]">
                    <div className="h-16 w-16 bg-white/5 border border-white/10 flex items-center justify-center rounded-3xl">
                        <Radio className="h-8 w-8 text-zinc-700" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-xl font-bold text-white uppercase tracking-tight">Awaiting Signal</h3>
                        <p className="text-zinc-500 font-medium text-sm">No recent egress detected in the local cluster.</p>
                    </div>
                    <Link href="/creation">
                        <Button variant="primary" size="lg" className="rounded-full px-12">
                            START_INITIAL_SEQUENCE
                        </Button>
                    </Link>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {activityFeed.map((activity, idx) => (
                        <motion.div
                            key={activity.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="surface-glass p-6 rounded-3xl flex items-center gap-5 group hover:border-cyan-400/30 transition-all border border-white/5"
                        >
                            <div className="h-12 w-12 bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center rounded-2xl group-hover:bg-cyan-400 group-hover:text-black transition-all">
                                <Play className="h-5 w-5 text-cyan-400 group-hover:text-black fill-current" />
                            </div>
                            <div className="flex-1 min-w-0 space-y-1">
                                <div className="flex items-center justify-between">
                                    <span className="font-data-mono text-[8px] text-cyan-400/60 uppercase">{activity.platform}</span>
                                    <span className="font-data-mono text-[7px] text-zinc-600">{new Date(activity.published_at).toLocaleTimeString()}</span>
                                </div>
                                <h4 className="text-sm font-bold text-white truncate uppercase tracking-tight group-hover:text-cyan-400 transition-colors">{activity.title}</h4>
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

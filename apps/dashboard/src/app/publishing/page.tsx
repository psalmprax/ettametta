"use client";

import React, { useState, useEffect, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import DashboardLayout from "@/components/layout";
import {
    Youtube,
    Share2,
    Settings,
    CheckCircle2,
    AlertCircle,
    Plus,
    ArrowUpRight,
    ShieldCheck,
    Globe,
    RefreshCw,
    Layout,
    Instagram,
    Twitter,
    Play,
    ExternalLink,
    X,
    Lock,
    Zap,
    Radio,
    Terminal,
    Activity,
    Database,
    ArrowRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { motion, AnimatePresence } from "framer-motion";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { Canvas } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";

function PublishingBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#3b82f6" />
                    <Float speed={1.5} rotationIntensity={0.8} floatIntensity={0.8}>
                        <Sphere args={[1.3, 64, 64]} scale={2.4}>
                            <MeshDistortMaterial
                                color="#3b82f6"
                                speed={3}
                                distort={0.25}
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

const getPlatformIcon = (platform: string) => {
    if (platform?.toLowerCase().includes("youtube")) return Youtube;
    if (platform?.toLowerCase().includes("instagram")) return Instagram;
    if (platform?.toLowerCase().includes("twitter") || platform?.toLowerCase().includes("x")) return Twitter;
    return Share2;
};

export default function PublishingPage() {
    const [accounts, setAccounts] = useState<any[]>([]);
    const [history, setHistory] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isPlatformModalOpen, setIsPlatformModalOpen] = useState(false);
    const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
    const [selectedJobForDeploy, setSelectedJobForDeploy] = useState<any>(null);
    const [jobs, setJobs] = useState<any[]>([]);
    const [isDeploying, setIsDeploying] = useState(false);
    const [telemetry, setTelemetry] = useState<any>(null);

    const fetchData = async () => {
        const token = getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };
        
        await Promise.all([
            withRealFallback<any>(
                () => fetch(`${API_BASE}/v1/publish/accounts`, { headers }),
                { fallback: [], onSuccess: (data) => setAccounts(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/v1/publish/history`, { headers }),
                { fallback: [], onSuccess: (data) => setHistory(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/v1/video/jobs`, { headers }),
                { fallback: [], onSuccess: (data) => setJobs(data) }
            )
        ]);
        setIsLoading(false);
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <PublishingBackground />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    
                    {/* PUBLISHING HEADER */}
                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                        <div className="space-y-6">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 150 }}
                                className="h-1 bg-blue-500 shadow-[0_0_20px_#3b82f6]"
                            />
                            <div className="space-y-2">
                                <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none  " data-text="EGRESS_HUB">
                                    Egress Hub
                                </h1>
                                <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                                    <Radio className="h-3 w-3 text-blue-400 animate-pulse" />
                                    BROADCAST_STATUS: BROADCASTING
                                    <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                                    TARGET_NODES: {accounts.length}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="surface-glass rim-light p-6 flex flex-col items-end">
                                <span className="font-data-mono text-[8px] text-zinc-600 mb-1">TOTAL_EGRESS</span>
                                <span className="text-xl font-bold text-white tabular-nums tracking-tighter">
                                    {history.length} ASSETS
                                </span>
                            </div>
                            <button 
                                onClick={() => setIsDeployModalOpen(true)}
                                className="action-primary h-20 px-12  text-xs tracking-tighter flex items-center gap-4"
                            >
                                <ArrowUpRight className="h-4 w-4" />
                                MANUAL_BROADCAST
                            </button>
                        </div>
                    </header>

                    {/* ACCOUNTS CLUSTER */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
                        <motion.button 
                            onClick={() => setIsPlatformModalOpen(true)}
                            className="surface-glass rim-light p-8 flex flex-col items-center justify-center gap-4 group hover:rim-glow-blue transition-all border-dashed border-white/10"
                        >
                            <div className="h-14 w-14 rounded-full bg-zinc-900 border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                                <Plus className="h-8 w-8 text-zinc-700 group-hover:text-blue-400" />
                            </div>
                            <span className="font-label-caps text-[9px] text-zinc-600 uppercase tracking-[0.4em] group-hover:text-white transition-colors">LINK_NEW_NODE</span>
                        </motion.button>

                        {accounts.map((acc, i) => {
                            const Icon = getPlatformIcon(acc.platform);
                            return (
                                <motion.div 
                                    key={acc.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="surface-glass rim-light p-8 space-y-6 hover:rim-glow-blue transition-all group"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="h-10 w-10 bg-blue-500/10 border border-blue-500/20 flex items-center justify-center rounded-xl group-hover:bg-blue-500 group-hover:text-black transition-all">
                                            <Icon className="h-5 w-5" />
                                        </div>
                                        <span className="font-data-mono text-[8px] text-zinc-700 tracking-widest">STABLE_LINK</span>
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-bold text-white  tracking-tighter uppercase group-hover:text-blue-400 transition-colors">{acc.username}</h3>
                                        <p className="font-data-mono text-[7px] text-zinc-600 uppercase">{acc.platform}</p>
                                    </div>
                                    <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                                        <span className="font-label-caps text-[8px] text-zinc-600">ID: {acc.id}</span>
                                        <Activity className="h-3 w-3 text-blue-500 animate-pulse" />
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>

                    {/* LIVE TRANSMISSION GRID */}
                    <div className="space-y-10">
                        <div className="flex items-center justify-between border-b border-white/5 pb-8">
                            <div className="space-y-2">
                                <h2 className="text-3xl font-bold text-white uppercase  tracking-tighter">Transmission Matrix</h2>
                                <p className="font-data-mono text-zinc-500 text-[9px]">LIVE_GLOBAL_DISTRIBUTION_LOG</p>
                            </div>
                            <div className="flex gap-4">
                                <div className="surface-glass px-6 py-3 flex items-center gap-3">
                                    <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]" />
                                    <span className="font-label-caps text-[8px] text-emerald-500 uppercase tracking-widest">99.4% DELIVERY</span>
                                </div>
                            </div>
                        </div>

                        {history.length === 0 ? (
                            <div className="surface-glass rim-light py-24 flex flex-col items-center justify-center text-center space-y-8">
                                <div className="h-20 w-20 bg-white/2 border border-white/5 flex items-center justify-center rounded-[2rem] opacity-20">
                                    <Globe className="h-10 w-10 text-white" />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-2xl font-bold text-white uppercase  tracking-tighter">No Active Egress</h3>
                                    <p className="text-zinc-500 font-medium text-sm max-w-sm">Initiate a manual broadcast or check the autonomous pipeline.</p>
                                </div>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                                {history.map((post, idx) => (
                                    <motion.div
                                        key={post.id}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        className="surface-glass rim-light p-10 flex items-start gap-8 group hover:rim-glow-blue transition-all relative overflow-hidden"
                                    >
                                        <div className="absolute inset-0 scanline opacity-5" />
                                        <div className="h-20 w-20 bg-blue-500/5 border border-blue-500/10 flex items-center justify-center group-hover:bg-blue-500 group-hover:text-black transition-all shrink-0">
                                            <Play className="h-8 w-8 text-blue-400 group-hover:text-black fill-current" />
                                        </div>
                                        <div className="flex-1 space-y-4 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <span className="font-data-mono text-[9px] text-blue-400 uppercase tracking-widest font-bold">{post.platform}</span>
                                                <span className="font-data-mono text-[8px] text-zinc-600 uppercase tabular-nums">{new Date(post.published_at).toLocaleDateString()}</span>
                                            </div>
                                            <div className="space-y-2">
                                                <h4 className="text-xl font-bold text-white uppercase  tracking-tight truncate group-hover:text-blue-400 transition-colors">{post.title}</h4>
                                                <div className="flex gap-4">
                                                    <div className="flex items-center gap-2">
                                                        <Activity className="h-3 w-3 text-emerald-500" />
                                                        <span className="font-data-mono text-[10px] text-zinc-500">{post.view_count || "---"} VIEWS</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Share2 className="h-3 w-3 text-blue-500" />
                                                        <span className="font-data-mono text-[10px] text-zinc-500">{post.shares || "---"} SHARES</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="pt-6 flex gap-4">
                                                <button className="bg-white/2 border border-white/5 hover:border-blue-500/30 text-zinc-600 hover:text-white px-6 py-3 font-label-caps text-[8px] uppercase tracking-widest transition-all">
                                                    SYNC_TELEMETRY
                                                </button>
                                                <a href={post.url} target="_blank" className="bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-500 hover:text-black px-6 py-3 font-label-caps text-[8px] uppercase tracking-widest transition-all">
                                                    OPEN_LINK
                                                </a>
                                            </div>
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

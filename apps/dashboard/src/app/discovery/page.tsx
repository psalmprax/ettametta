"use client";

import { withRealFallback } from "@/lib/real_first_utils";
import { getAuthToken } from "@/lib/auth_utils";
import React, { useState, useEffect, useCallback, Suspense, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";
import DashboardLayout from "@/components/layout";
import {
    Search,
    TrendingUp,
    Filter,
    RefreshCw,
    Play,
    Loader2,
    Globe,
    Zap,
    BarChart3,
    Clock,
    CheckCircle2,
    X,
    ChevronDown,
    Sparkles,
    Flame,
    MessageSquare,
    Heart,
    UserPlus,
    Wand2,
    Target,
    Terminal,
    Database,
    Network,
    Shield,
    Activity,
    ArrowRight,
    Monitor
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import dynamic from "next/dynamic";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useRouter, useSearchParams } from "next/navigation";
import { VideoPreviewModal } from "@/components/ui/VideoPreviewModal";
import { toast } from "sonner";

const Geomap = dynamic(() => import("@/components/ui/Geomap"), { ssr: false });
const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });

// --- REDESIGN COMPONENTS ---

function DiscoveryBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-30">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#00fbfb" />
                    <Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.5}>
                        <Sphere args={[1, 64, 64]} scale={2}>
                            <MeshDistortMaterial
                                color="#00fbfb"
                                speed={3}
                                distort={0.3}
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

interface ContentCandidate {
    id: string;
    platform: string;
    category: string;
    description: string;
    thumbnail_url: string;
    view_count: number;
    engagement_score: number;
    viral_score: number;
    published_at: string;
    creator_name: string;
    source_url: string;
    duration_seconds: number;
    title: string;
}

function DiscoveryContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [candidates, setCandidates] = useState<ContentCandidate[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeNiche, setActiveNiche] = useState(searchParams.get("q") || "Motivation");
    const [filter, setFilter] = useState("all");
    const [activeCategory, setActiveCategory] = useState("all");
    const [mode, setMode] = useState<"discovery" | "generative">("discovery");
    const [timeHorizon, setTimeHorizon] = useState("30d");
    const [niches, setNiches] = useState<string[]>([]);
    const [userTier, setUserTier] = useState<string>("free");
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);

    // Fetch Initial Data
    useEffect(() => {
        const load = async () => {
            const token = await getAuthToken();
            // Niche clusters
            const nicheRes = await fetch(`${API_BASE}/v1/discovery/niches`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (nicheRes.ok) setNiches(await nicheRes.json());
        };
        load();
    }, []);

    const fetchTrends = useCallback(async () => {
        setIsLoading(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/discovery/trends?niche=${activeNiche}&horizon=${timeHorizon}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setCandidates(data.trends || []);
            }
        } catch (err) {
            console.error(err);
            toast.error("Discovery module unstable");
        } finally {
            setIsLoading(false);
        }
    }, [activeNiche, timeHorizon]);

    useEffect(() => {
        fetchTrends();
    }, [fetchTrends]);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        setIsSearching(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/v1/discovery/search?q=${encodeURIComponent(searchQuery)}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setCandidates(data.results || []);
                setActiveNiche(searchQuery);
            }
        } finally {
            setIsSearching(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#050507] relative flex flex-col font-sans overflow-hidden">
            <div className="noise-overlay" />
            <DiscoveryBackground />
            <div className="absolute inset-0 cyber-grid opacity-20 pointer-events-none" />
            <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

            <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                
                {/* DISCOVERY HEADER HUD */}
                <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                    <div className="space-y-6">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: 100 }}
                            className="h-1 bg-cyan-400"
                        />
                        <div className="space-y-2">
                            <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none glitch-text italic" data-text="GLOBAL SCAN">
                                Global Scan
                            </h1>
                            <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                                <Activity className="h-3 w-3 text-cyan-400 animate-pulse" />
                                TRACKING_VELOCITY: 14.2K_PPS
                                <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                                STATUS: SCANNING_ACTIVE
                            </p>
                        </div>
                    </div>

                    {/* SEARCH CONSOLE */}
                    <form onSubmit={handleSearch} className="flex-1 max-w-2xl group">
                        <div className="relative surface-glass rim-light flex items-center">
                            <div className="pl-6 text-zinc-600 group-focus-within:text-cyan-400 transition-colors">
                                <Search className="h-5 w-5" />
                            </div>
                            <input 
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="INITIATE NICHE SEARCH..."
                                className="w-full bg-transparent p-6 text-white font-label-caps text-xs tracking-widest outline-none placeholder:text-zinc-800"
                            />
                            <button 
                                type="submit"
                                className="h-full px-10 action-primary border-l border-white/5 font-black italic text-xs tracking-tighter"
                            >
                                {isSearching ? <RefreshCw className="h-4 w-4 animate-spin" /> : "SEARCH"}
                            </button>
                        </div>
                    </form>
                </header>

                {/* CONTROL HUD */}
                <div className="flex flex-wrap items-center gap-6 mb-16">
                    <div className="surface-glass rim-light p-2 flex gap-1">
                        {["YouTube", "TikTok", "Instagram", "X"].map(plat => (
                            <button 
                                key={plat}
                                onClick={() => setFilter(plat.toLowerCase())}
                                className={cn(
                                    "px-6 py-3 font-label-caps text-[9px] transition-all",
                                    filter === plat.toLowerCase() ? "bg-cyan-400 text-black shadow-[0_0_15px_rgba(0,251,251,0.3)]" : "text-zinc-600 hover:text-zinc-300"
                                )}
                            >
                                {plat}
                            </button>
                        ))}
                    </div>

                    <div className="surface-glass rim-light p-2 flex gap-1">
                        {["24H", "7D", "30D"].map(h => (
                            <button 
                                key={h}
                                onClick={() => setTimeHorizon(h.toLowerCase())}
                                className={cn(
                                    "px-6 py-3 font-label-caps text-[9px] transition-all",
                                    timeHorizon === h.toLowerCase() ? "bg-white text-black" : "text-zinc-600 hover:text-zinc-300"
                                )}
                            >
                                {h}
                            </button>
                        ))}
                    </div>

                    <div className="ml-auto flex items-center gap-6">
                        <span className="font-data-mono text-[9px] text-zinc-700">TARGET_NICHE:</span>
                        <span className="px-4 py-2 bg-cyan-400/5 border border-cyan-400/20 text-cyan-400 font-label-caps text-[10px] italic">
                            {activeNiche || "GLOBAL_FEED"}
                        </span>
                    </div>
                </div>

                {/* MAIN CONTENT GRID */}
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-12">
                    
                    {/* LEFT: TREND CLUSTERS */}
                    <div className="xl:col-span-3 space-y-10">
                        <section className="surface-glass rim-light p-8 space-y-8">
                            <h2 className="font-label-caps text-xs text-zinc-500 flex items-center gap-3">
                                <Network className="h-4 w-4" />
                                NEURAL_CLUSTERS
                            </h2>
                            <div className="space-y-2">
                                {niches.slice(0, 10).map(n => (
                                    <button 
                                        key={n}
                                        onClick={() => setActiveNiche(n)}
                                        className={cn(
                                            "w-full text-left p-4 font-data-mono text-[9px] transition-all flex items-center justify-between group",
                                            activeNiche === n ? "text-cyan-400 bg-cyan-400/5 border-l-2 border-cyan-400" : "text-zinc-600 hover:text-zinc-300 hover:bg-white/5"
                                        )}
                                    >
                                        {n}
                                        <ArrowRight className={cn("h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity", activeNiche === n && "opacity-100")} />
                                    </button>
                                ))}
                            </div>
                            <button className="w-full py-4 border border-dashed border-white/10 font-label-caps text-[8px] text-zinc-700 hover:border-cyan-400/30 hover:text-cyan-400 transition-all">
                                + ADD_NEW_CLUSTER
                            </button>
                        </section>

                        <div className="surface-glass rim-light p-6 h-64 overflow-hidden relative group">
                            <div className="absolute inset-0 bg-black/40 z-10 flex items-center justify-center backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="font-label-caps text-[9px] text-cyan-400 tracking-[0.5em]">LIVE_MAP_SYNC</span>
                            </div>
                            <Geomap />
                        </div>
                    </div>

                    {/* RIGHT: CANDIDATE GRID */}
                    <div className="xl:col-span-9">
                        {isLoading ? (
                            <div className="h-[600px] flex flex-col items-center justify-center space-y-6">
                                <RefreshCw className="h-12 w-12 text-cyan-400 animate-spin" />
                                <span className="font-data-mono text-[10px] text-zinc-600 tracking-[0.5em]">SYNCHRONIZING_STREAM</span>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {candidates.map((c, i) => (
                                    <motion.div 
                                        key={c.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="surface-glass rim-light group/card overflow-hidden flex flex-col h-full hover:rim-glow-cyan transition-all duration-500"
                                    >
                                        {/* Thumbnail Section */}
                                        <div className="relative aspect-video overflow-hidden">
                                            <img 
                                                src={c.thumbnail_url || "https://api.dicebear.com/7.x/shapes/svg?seed=" + c.id} 
                                                alt={c.title}
                                                className="w-full h-full object-cover group-hover/card:scale-110 transition-transform duration-700"
                                            />
                                            <div className="absolute inset-0 bg-linear-to-t from-black/80 via-transparent to-transparent opacity-60" />
                                            
                                            <div className="absolute top-4 left-4 flex gap-2">
                                                <span className="bg-black/80 border border-white/10 px-2 py-1 font-data-mono text-[8px] text-cyan-400">
                                                    {c.platform}
                                                </span>
                                            </div>

                                            <div className="absolute bottom-4 left-4 flex gap-3">
                                                <div className="flex items-center gap-2 px-2 py-1 bg-emerald-500/20 border border-emerald-500/40 rounded-sm">
                                                    <Activity className="h-3 w-3 text-emerald-400" />
                                                    <span className="font-data-mono text-[9px] text-emerald-400">{c.viral_score}%</span>
                                                </div>
                                            </div>

                                            <button className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/card:opacity-100 transition-opacity bg-black/40 backdrop-blur-sm">
                                                <div className="w-16 h-16 rounded-full bg-cyan-400 flex items-center justify-center shadow-[0_0_30px_rgba(0,251,251,0.5)] transform scale-50 group-hover/card:scale-100 transition-transform duration-500">
                                                    <Play className="h-6 w-6 text-black fill-black ml-1" />
                                                </div>
                                            </button>
                                        </div>

                                        {/* Info Section */}
                                        <div className="p-6 flex-1 flex flex-col space-y-4">
                                            <h3 className="text-sm font-bold text-white line-clamp-2 leading-snug group-hover/card:text-cyan-400 transition-colors">
                                                {c.title}
                                            </h3>
                                            
                                            <div className="flex items-center justify-between text-zinc-600 font-data-mono text-[8px]">
                                                <span className="flex items-center gap-2 italic">
                                                    <UserPlus className="h-3 w-3" />
                                                    {c.creator_name}
                                                </span>
                                                <span>{Math.floor(c.view_count / 1000)}K VIEWS</span>
                                            </div>

                                            <div className="pt-4 mt-auto border-t border-white/5 flex gap-2">
                                                <button 
                                                    onClick={() => router.push(`/creation?seed=${encodeURIComponent(c.title)}`)}
                                                    className="flex-1 action-primary py-4 font-black italic text-[9px] tracking-tighter"
                                                >
                                                    REPLICATE
                                                </button>
                                                <button className="px-4 bg-white/5 border border-white/10 text-zinc-500 hover:text-white hover:bg-white/10 transition-all">
                                                    <BarChart3 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function DiscoveryPage() {
    return (
        <DashboardLayout>
            <Suspense fallback={
                <div className="min-h-screen bg-[#050507] flex flex-col items-center justify-center">
                    <RefreshCw className="h-12 w-12 text-cyan-400 animate-spin" />
                </div>
            }>
                <DiscoveryContent />
            </Suspense>
        </DashboardLayout>
    );
}

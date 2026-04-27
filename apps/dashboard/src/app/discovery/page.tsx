"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import dynamic from "next/dynamic";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";
import DashboardLayout from "@/components/layout";
import {
    Search,
    Play,
    RefreshCw,
    Activity,
    ArrowRight,
    BarChart3
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { toast } from "sonner";

const Geomap = dynamic(() => import("@/components/ui/Geomap"), { ssr: false });

// --- CLEAN DESIGN COMPONENTS ---

function DiscoveryBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/50 via-white to-amber-50/50" />
            <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(251, 191, 36, 0.05) 0%, transparent 50%)' }} />
            <Canvas camera={{ position: [0, 0, 5] }} className="opacity-40">
                <Float speed={2} rotationIntensity={0.3} floatIntensity={0.5}>
                    <Sphere args={[1, 64, 64]} scale={1.5}>
                        <MeshDistortMaterial
                            color="#c7d2fe"
                            speed={2}
                            distort={0.2}
                            radius={1}
                            transparent
                            opacity={0.3}
                        />
                    </Sphere>
                </Float>
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
    const [timeHorizon, setTimeHorizon] = useState("30d");
    const [niches, setNiches] = useState<string[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);

    // Fetch Initial Data
    useEffect(() => {
        const load = async () => {
            const token = await getAuthToken();
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
        <div className="min-h-screen bg-slate-50 relative flex flex-col font-sans overflow-hidden">
            <DiscoveryBackground />

            <div className="flex-1 section-container relative py-12 px-6 lg:px-16 max-w-screen-2xl mx-auto w-full z-10">
                
                {/* DISCOVERY HEADER */}
                <header className="mb-16 flex flex-col xl:flex-row xl:items-end justify-between gap-8">
                    <div className="space-y-4">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: 60 }}
                            className="h-1.5 bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full"
                        />
                        <div className="space-y-2">
                            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight leading-tight">
                                Global Content Scan
                            </h1>
                            <p className="text-slate-500 text-sm flex items-center gap-2">
                                <span className="flex items-center gap-1.5">
                                    <div className="h-1.5 w-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
                                    Scanning Active
                                </span>
                                <span className="text-slate-300">•</span>
                                <span className="font-mono text-xs text-slate-400">14.2K trends tracked</span>
                            </p>
                        </div>
                    </div>

                    <form onSubmit={handleSearch} className="flex-1 max-w-xl">
                        <div className="relative">
                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                                <Search className="h-5 w-5" />
                            </div>
                            <input 
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search content trends..."
                                className="w-full bg-white border border-slate-200 rounded-full pl-12 pr-4 py-3 text-slate-900 text-sm font-medium placeholder:text-slate-400 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/10 shadow-sm transition-all"
                            />
                            <Button 
                                type="submit"
                                variant="primary"
                                size="sm"
                                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full px-5 py-2 text-xs"
                                isLoading={isSearching}
                            >
                                Search
                            </Button>
                        </div>
                    </form>
                </header>

                {/* CONTROL PANEL */}
                <div className="flex flex-wrap items-center gap-4 mb-12">
                    <div className="flex gap-1 p-1 bg-white rounded-xl border border-slate-200 shadow-sm">
                        {["YouTube", "TikTok", "Instagram", "X"].map(plat => (
                            <button 
                                key={plat}
                                onClick={() => setFilter(plat.toLowerCase())}
                                className={cn(
                                    "px-4 py-2 rounded-lg text-xs font-semibold transition-all",
                                    filter === plat.toLowerCase() 
                                        ? "bg-indigo-600 text-white shadow-md" 
                                        : "text-slate-600 hover:bg-slate-50"
                                )}
                            >
                                {plat}
                            </button>
                        ))}
                    </div>

                    <div className="flex gap-1 p-1 bg-white rounded-xl border border-slate-200 shadow-sm">
                        {["24H", "7D", "30D"].map(h => (
                            <button 
                                key={h}
                                onClick={() => setTimeHorizon(h.toLowerCase())}
                                className={cn(
                                    "px-4 py-2 rounded-lg text-xs font-semibold transition-all",
                                    timeHorizon === h.toLowerCase()
                                        ? "bg-slate-900 text-white"
                                        : "text-slate-600 hover:bg-slate-50"
                                )}
                            >
                                {h}
                            </button>
                        ))}
                    </div>

                    <div className="ml-auto flex items-center gap-3">
                        <span className="text-xs text-slate-500 font-medium">Target Niche:</span>
                        <span className="px-4 py-1.5 bg-indigo-50 border border-indigo-100 text-indigo-700 font-semibold text-xs rounded-full">
                            {activeNiche || ""}
                        </span>
                    </div>
                </div>

                {/* CONTENT GRID */}
                <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                    
                    {/* SIDEBAR: NICHE CLUSTERS */}
                    <div className="xl:col-span-1 space-y-6">
                        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                            <h2 className="text-xs font-bold text-slate-500 flex items-center gap-2 mb-4 uppercase tracking-wide">
                                <ArrowRight className="h-4 w-4 text-indigo-500" />
                                Trend Clusters
                            </h2>
                            <div className="space-y-1">
                                {niches.slice(0, 10).map(n => (
                                    <button 
                                        key={n}
                                        onClick={() => setActiveNiche(n)}
                                        className={cn(
                                            "w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center justify-between",
                                            activeNiche === n 
                                                ? "bg-indigo-50 text-indigo-700 border border-indigo-100" 
                                                : "text-slate-600 hover:bg-slate-50"
                                        )}
                                    >
                                        {n}
                                        <ArrowRight className={cn("h-3.5 w-3.5 opacity-0 transition-opacity", activeNiche === n && "opacity-100")} />
                                    </button>
                                ))}
                            </div>
                            <button className="w-full mt-4 py-2.5 border border-dashed border-slate-200 rounded-xl text-slate-400 text-[10px] font-semibold hover:border-slate-300 hover:text-slate-600 transition-all uppercase tracking-wider">
                                + New Cluster
                            </button>
                        </div>

                        <div className="bg-white rounded-2xl border border-slate-200 p-4 h-64 overflow-hidden group relative">
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 flex items-center justify-center">
                                <span className="text-white text-xs font-medium tracking-wider">Map View</span>
                            </div>
                            <Geomap />
                        </div>
                    </div>

                    {/* MAIN: CANDIDATES */}
                    <div className="xl:col-span-3">
                        {isLoading ? (
                            <div className="h-[500px] flex flex-col items-center justify-center space-y-4">
                                <RefreshCw className="h-10 w-10 text-indigo-500 animate-spin" />
                                <span className="text-slate-400 text-sm font-medium">Loading trends...</span>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {candidates.map((c, i) => (
                                    <motion.div 
                                        key={c.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col hover:shadow-lg hover:border-slate-300 transition-all duration-300"
                                    >
                                        {/* Thumbnail */}
                                        <div className="relative aspect-video overflow-hidden bg-slate-100">
                                            <img 
                                                src={c.thumbnail_url || "https://api.dicebear.com/7.x/shapes/svg?seed=" + c.id} 
                                                alt={c.title}
                                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end">
                                                <div className="p-4 w-full">
                                                    <div className="flex gap-2">
                                                        <span className="bg-white/90 text-indigo-700 text-[10px] font-bold px-2.5 py-1 rounded-full">
                                                            {c.platform}
                                                        </span>
                                                        <span className="bg-emerald-500/90 text-white text-[10px] font-bold px-2.5 py-1 rounded-full flex items-center gap-1">
                                                            <Activity className="h-3 w-3" />
                                                            {c.viral_score}%
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                            <button className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 bg-black/30">
                                                <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all transform hover:scale-105">
                                                    <Play className="h-5 w-5 text-indigo-600 ml-0.5" />
                                                </div>
                                            </button>
                                        </div>

                                        {/* Info */}
                                        <div className="p-5 flex flex-col flex-1">
                                            <h3 className="text-sm font-bold text-slate-900 line-clamp-2 leading-snug mb-3 hover:text-indigo-600 transition-colors">
                                                {c.title}
                                            </h3>
                                            
                                            <div className="flex items-center justify-between text-slate-500 text-xs mb-4">
                                                <span className="flex items-center gap-1.5">
                                                    <BarChart3 className="h-3.5 w-3.5" />
                                                    {c.creator_name}
                                                </span>
                                                <span className="font-semibold text-slate-700">{Math.floor(c.view_count / 1000)}K views</span>
                                            </div>

                                            <div className="flex gap-2 mt-auto pt-3 border-t border-slate-100">
                                                <Button 
                                                    onClick={() => router.push(`/creation?seed=${encodeURIComponent(c.title)}`)}
                                                    variant="primary"
                                                    size="sm"
                                                    className="flex-1 rounded-lg text-xs"
                                                >
                                                    Create Similar
                                                </Button>
                                                <Button variant="outline" size="sm" className="rounded-lg p-2">
                                                    <BarChart3 className="h-4 w-4" />
                                                </Button>
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
            <Suspense fallback={<div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center"><div className="h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>}>
                <DiscoveryContent />
            </Suspense>
        </DashboardLayout>
    );
}

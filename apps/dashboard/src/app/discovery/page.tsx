"use client";

import React, { useState, useEffect } from "react";
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
    Flame
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import dynamic from "next/dynamic";
import * as d3 from "d3";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useRouter } from "next/navigation";

const Geomap = dynamic(() => import("@/components/ui/Geomap"), { ssr: false });
const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });

// Types
interface ContentCandidate {
    id: string;
    platform: string;
    description: string;
    thumbnail_url: string;
    views: number;
    engagement_score: number;
    viral_score: number;
    published_at: string;
    author: string;
    url: string;
    duration_seconds: number;
}

interface NicheTrend {
    niche: string;
    top_keywords: string[];
    avg_engagement: number;
}

export default function DiscoveryPage() {
    const router = useRouter();
    const [candidates, setCandidates] = useState<ContentCandidate[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeNiche, setActiveNiche] = useState("Motivation");
    const [filter, setFilter] = useState("all"); // all, youtube, tiktok
    const [showConfig, setShowConfig] = useState(false);
    const [timeHorizon, setTimeHorizon] = useState("30d"); // 24h, 7d, 30d

    // New State for "Neural Config"
    const [minViralScore, setMinViralScore] = useState(75);
    const [excludeShorts, setExcludeShorts] = useState(false);

    const niches = ["Motivation", "AI Technology", "Finance", "Health", "Gaming", "Crypto", "Relationships"];

    useEffect(() => {
        fetchTrends();
    }, [activeNiche, timeHorizon]);

    const fetchTrends = useCallback(async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/discovery/trends?niche=${activeNiche}&horizon=${timeHorizon}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setCandidates(data);
            } else {
                console.error("Failed to fetch trends", res.status);
                setCandidates([]);
            }
        } catch (err) {
            console.error(err);
            setCandidates([]);
        } finally {
            setIsLoading(false);
        }
    }, [activeNiche, timeHorizon]);

    useEffect(() => {
        fetchTrends();
    }, [fetchTrends]);

    const handleAnalyze = useCallback(async (candidate: ContentCandidate) => {
        alert(`Analysing viral DNA for: ${candidate.description.substring(0, 30)}...`);
    }, []);

    const handleAddToQueue = useCallback(async (candidate: ContentCandidate) => {
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/video/transform`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    input_url: candidate.url,
                    niche: activeNiche,
                    platform: "YouTube Shorts"
                })
            });
            if (res.ok) {
                router.push("/transformation");
            }
        } catch (err) {
            console.error(err);
        }
    }, [activeNiche, router]);

    const filteredCandidates = React.useMemo(() => {
        if (!Array.isArray(candidates)) return [];
        return candidates.filter(c => {
            if (filter === 'all') return true;
            return c.platform.toLowerCase() === filter.toLowerCase();
        });
    }, [candidates, filter]);

    const handleSearch = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) {
            fetchTrends();
            return;
        }

        setIsSearching(true);
        setIsLoading(true);
        try {
            const token = localStorage.getItem("vf_token");
            const res = await fetch(`${API_BASE}/discovery/search?q=${encodeURIComponent(searchQuery)}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setCandidates(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
            setIsSearching(false);
        }
    }, [searchQuery, fetchTrends]);

    const [mapPoints, setMapPoints] = useState<any[]>([
        { lat: 40.7128, lng: -74.006, intensity: 0.8, label: "NY Cluster" },
        { lat: 51.5074, lng: -0.1278, intensity: 0.6, label: "LDN Node" },
        { lat: 35.6762, lng: 139.6503, intensity: 0.9, label: "TKO Hub" },
        { lat: -33.8688, lng: 151.2093, intensity: 0.4, label: "SYD Point" },
        { lat: 6.5244, lng: 3.3792, intensity: 0.7, label: "LOS Gateway" }
    ]);

    const { data: telemetryData } = useWebSocket(`${WS_BASE}/ws/telemetry`);

    useEffect(() => {
        if (telemetryData) {
            try {
                // telemetryData is already parsed by the hook
                const data = telemetryData as any;
                if (data.type === "telemetry_pulse" && data.geo_activity) {
                    // Merge new points with existing ones, keeping the list size manageable
                    setMapPoints(prev => {
                        const newPoints = [...prev, ...data.geo_activity];
                        return newPoints.slice(-15); // Keep last 15 active pulses
                    });
                }
            } catch (e) {
                console.error("Error processing telemetry for map:", e);
            }
        }
    }, [telemetryData]);

    const topKeywords = ["Success", "Grind", "AI Automation", "Discipline", "Growth", "Wealth", "Stoicism"];

    return (
        <DashboardLayout>
            <div className="space-y-8 relative">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="h-1 w-8 bg-primary rounded-full" />
                            <span className="text-[10px] font-black tracking-[0.3em] text-primary uppercase">Global Intelligence</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black italic tracking-tighter uppercase text-white leading-none">
                            Viral <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-emerald-400 text-hollow">Discovery</span>
                        </h1>
                        <p className="text-zinc-500 mt-2 max-w-lg text-sm font-medium leading-relaxed">
                            Scanning <span className="text-zinc-300 font-bold">14,000+</span> data points per second to identify high-velocity content opportunities before they peak.
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <form onSubmit={handleSearch} className="relative group">
                            <input
                                type="text"
                                placeholder="Neural Search..."
                                aria-label="Search for viral content"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="bg-zinc-950/50 backdrop-blur-md border border-white/10 rounded-2xl py-3 pl-12 pr-6 text-sm font-bold text-white focus:outline-none focus:border-primary/50 transition-all w-80 group-hover:border-white/20"
                            />
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 group-hover:text-primary transition-colors" />
                        </form>
                        <button
                            onClick={fetchTrends}
                            className="p-3 rounded-2xl bg-zinc-900 border border-white/5 text-zinc-400 hover:text-white transition-all"
                        >
                            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                        </button>
                    </div>
                </div>

                {/* Viral Intelligence Map */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 mb-12">
                    <div className="lg:col-span-2">
                        <Geomap points={mapPoints} />
                    </div>
                    <div className="glass-card p-10 flex flex-col justify-center space-y-8 bg-primary/[0.02] border-primary/20 relative overflow-hidden">
                        <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                        <div className="space-y-1">
                            <h3 className="text-xl font-black text-white uppercase tracking-tighter italic">Keyword <span className="text-primary">Neural Cloud</span></h3>
                            <p className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">Semantic Density Analysis</p>
                        </div>
                        <div className="flex flex-wrap gap-3">
                            {topKeywords.map((word: string, i: number) => (
                                <motion.span
                                    key={i}
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                    className={cn(
                                        "px-4 py-2 rounded-xl font-black uppercase text-[10px] tracking-widest border transition-all",
                                        i === 0 ? "bg-primary text-black border-white/20 shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]" :
                                            "bg-zinc-950/50 text-zinc-500 border-white/5 hover:border-primary/30 hover:text-white"
                                    )}
                                >
                                    {word}
                                </motion.span>
                            ))}
                        </div>
                        <div className="pt-6 border-t border-white/5">
                            <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-4">
                                <span>Signal Clarity</span>
                                <span className="text-primary">92%</span>
                            </div>
                            <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "92%" }}
                                    className="h-full bg-primary"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Live Search Status Banner */}
                <AnimatePresence>
                    {isLoading && searchQuery && (
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="mb-8 p-4 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-between"
                        >
                            <div className="flex items-center gap-4">
                                <div className="h-2 w-2 bg-primary rounded-full animate-ping" />
                                <p className="text-xs font-black uppercase tracking-widest text-primary italic">
                                    Sourcing Intelligence: <span className="text-white">"{searchQuery}"</span>
                                </p>
                            </div>
                            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">Fast-Scanning YouTube & TikTok Clusters...</p>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Niche Selector & Neural Config */}
                <div className="flex flex-wrap items-center gap-3">
                    {niches.map((n) => (
                        <button
                            key={n}
                            onClick={() => { setActiveNiche(n); setSearchQuery(""); }}
                            className={cn(
                                "px-6 py-3 rounded-xl border text-xs font-black uppercase tracking-widest transition-all",
                                activeNiche === n && !searchQuery
                                    ? "bg-white text-black border-white shadow-[0_0_20px_rgba(255,255,255,0.2)] scale-105"
                                    : "bg-black/40 border-white/10 text-zinc-500 hover:border-white/30 hover:text-zinc-300"
                            )}
                        >
                            {n}
                        </button>
                    ))}
                    <button
                        onClick={() => setShowConfig(!showConfig)}
                        className={cn(
                            "px-4 py-3 rounded-xl border border-dashed border-zinc-700 text-xs font-bold uppercase tracking-widest transition-all flex items-center gap-2",
                            showConfig ? "bg-zinc-800 text-white" : "text-zinc-600 hover:text-zinc-400"
                        )}
                    >
                        <Sparkles className="h-4 w-4" />
                        Neural Config
                    </button>
                </div>

                {/* Neural Config Drawer (Animate Height) */}
                <AnimatePresence>
                    {showConfig && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="p-6 rounded-3xl bg-zinc-900/50 border border-white/5 grid grid-cols-1 md:grid-cols-3 gap-8">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Min Viral Score Threshold</label>
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={minViralScore}
                                            onChange={(e) => setMinViralScore(parseInt(e.target.value))}
                                            className="flex-1 accent-primary h-2 bg-zinc-800 rounded-full appearance-none"
                                        />
                                        <span className="text-xl font-black text-primary">{minViralScore}</span>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Format Filters</label>
                                    <div className="flex items-center gap-4">
                                        <button
                                            onClick={() => setExcludeShorts(!excludeShorts)}
                                            className={cn(
                                                "px-4 py-2 rounded-lg text-xs font-bold transition-all border",
                                                excludeShorts ? "bg-red-500/20 border-red-500 text-red-500" : "bg-zinc-950 border-zinc-800 text-zinc-500"
                                            )}
                                        >
                                            Exclude Shorts
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Content Grid */}
                <div className="space-y-6">
                    <div className="glass-card !p-0 overflow-hidden shadow-[0_32px_128px_rgba(0,0,0,0.5)] border-white/5">
                        <div className="px-10 py-12 border-b border-white/5 bg-white/[0.01] flex flex-col md:flex-row md:items-center justify-between gap-8 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-10 pointer-events-none" />
                            <div className="flex items-center gap-8 relative z-10">
                                <div className="relative">
                                    <Flame className={cn("h-10 w-10 neon-glow animate-pulse", searchQuery ? "text-primary" : "text-orange-500")} />
                                    <div className={cn("absolute -inset-2 blur-xl rounded-full opacity-50 animate-pulse", searchQuery ? "bg-primary/20" : "bg-orange-500/20")} />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-black text-4xl uppercase tracking-tighter text-white leading-none">
                                        {searchQuery ? "Neural" : "Trending"} <span className="text-hollow opacity-50">{searchQuery ? "Search" : "Signals"}</span>
                                    </h3>
                                    <div className="flex items-center gap-3">
                                        <p className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.4em]">
                                            {searchQuery ? `Analyzing Cluster: "${searchQuery}"` : "Global High-Velocity Content Feed"}
                                        </p>
                                        <div className="flex gap-0.5">
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="h-1 w-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: `${i * 0.2}s` }} />
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-6 relative z-10">
                                <div className="flex items-center bg-black/60 backdrop-blur-md rounded-2xl p-1.5 border border-white/5 shadow-2xl">
                                    {["24h", "7d", "30d"].map((t) => (
                                        <button
                                            key={t}
                                            onClick={() => setTimeHorizon(t)}
                                            className={cn(
                                                "px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                                                timeHorizon === t ? "bg-primary text-white shadow-[0_0_20px_rgba(var(--primary-rgb),0.4)]" : "text-zinc-600 hover:text-zinc-400"
                                            )}
                                        >
                                            {t}
                                        </button>
                                    ))}
                                </div>
                                <div className="h-10 w-[1px] bg-white/10 hidden md:block" />
                                <button
                                    onClick={() => setFilter(filter === 'all' ? 'youtube' : filter === 'youtube' ? 'tiktok' : 'all')}
                                    className="flex items-center gap-3 bg-zinc-950/80 backdrop-blur-md px-6 py-3 rounded-2xl border border-white/5 shadow-2xl group transition-all hover:border-primary/50"
                                >
                                    <Filter className="h-4 w-4 text-zinc-500 group-hover:text-primary transition-colors" />
                                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
                                        Filter: <span className="text-primary italic">{filter}</span>
                                    </span>
                                </button>
                            </div>
                        </div>

                        <div className="divide-y divide-white/5 relative">
                            {isLoading && (
                                <div className="absolute inset-0 z-40 flex flex-col items-center justify-center bg-black/60 backdrop-blur-md animate-in fade-in duration-500">
                                    <div className="absolute inset-0 scanline opacity-10 pointer-events-none" />
                                    <Loader2 className="h-16 w-16 text-primary animate-spin mb-6" />
                                    <p className="text-sm font-black uppercase tracking-[0.4em] text-primary neon-glow animate-pulse">Syncing Neural Nodes</p>
                                </div>
                            )}

                            <AnimatePresence mode="popLayout">
                                {Array.isArray(filteredCandidates) && filteredCandidates.length > 0 ? (
                                    filteredCandidates.map((candidate, idx) => {
                                        // Generate stable mock telemetry based on ID
                                        const hash = candidate.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                                        const velocity = 85 + (hash % 15);
                                        const growth = 20 + (hash % 80);

                                        return (
                                            <motion.div
                                                key={candidate.id}
                                                initial={{ opacity: 0, x: -30, filter: "blur(10px)" }}
                                                animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                                                transition={{ delay: idx * 0.08, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                                                layout
                                                className="p-10 px-12 flex flex-col lg:flex-row lg:items-center justify-between hover:bg-white/[0.03] transition-all group relative overflow-hidden"
                                            >
                                                <div className="absolute inset-x-0 top-0 h-full bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                                                <div className="absolute inset-0 shimmer opacity-0 group-hover:opacity-[var(--shimmer-opacity)] pointer-events-none" />

                                                {/* Left: Thumbnail & Core Info */}
                                                <div className="flex items-center gap-10 relative z-10">
                                                    <div className="h-28 w-44 rounded-[2rem] bg-zinc-950 border border-white/5 flex-shrink-0 relative overflow-hidden group-hover:border-primary/50 transition-all duration-700 shadow-2xl">
                                                        {candidate.thumbnail_url ? (
                                                            <img src={candidate.thumbnail_url} alt="" className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700" />
                                                        ) : (
                                                            <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
                                                                <TrendingUp className="h-10 w-10 text-zinc-800" />
                                                            </div>
                                                        )}
                                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60" />
                                                        <div className="absolute bottom-4 left-4 flex items-center gap-2">
                                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                                                            <span className="text-[8px] font-black text-white uppercase tracking-widest italic opacity-0 group-hover:opacity-100 transition-opacity">Live Alpha</span>
                                                        </div>
                                                    </div>

                                                    <div className="space-y-4">
                                                        <div className="flex items-center gap-3">
                                                            <div className="h-1 w-8 bg-primary/40 rounded-full" />
                                                            <span className="text-[10px] font-black text-primary uppercase tracking-[0.3em] italic">
                                                                {candidate.platform} <span className="text-zinc-600 mx-2">/</span> <span className="text-zinc-500 uppercase">Opportunity Node</span>
                                                            </span>
                                                        </div>
                                                        <h4 className="font-black text-2xl tracking-tighter text-white uppercase italic line-clamp-1 group-hover:text-primary transition-colors duration-300 max-w-xl">
                                                            {candidate.description?.split('\n')[0] || "UNTITLED_INTEL_STREAM"}
                                                        </h4>
                                                        <div className="flex items-center gap-6">
                                                            <div className="flex items-center gap-2">
                                                                <Globe className="h-3.5 w-3.5 text-zinc-600" />
                                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{candidate.author}</span>
                                                            </div>
                                                            <div className="h-1 w-1 rounded-full bg-zinc-800" />
                                                            <div className="flex items-center gap-2">
                                                                <BarChart3 className="h-3.5 w-3.5 text-zinc-600" />
                                                                <span className="text-[10px] font-bold text-zinc-500 tabular-nums">{(candidate.views || 0).toLocaleString()} Views</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Center: Telemetry Grid */}
                                                <div className="hidden xl:grid grid-cols-2 gap-x-12 gap-y-4 px-12 border-x border-white/5 relative z-10">
                                                    <div className="space-y-1">
                                                        <p className="text-[8px] font-black text-zinc-600 uppercase tracking-[0.2em] text-hollow">Viral_Velocity</p>
                                                        <p className="text-xs font-black text-white">{velocity}.4%</p>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-[8px] font-black text-zinc-600 uppercase tracking-[0.2em] text-hollow">Growth_Curve</p>
                                                        <p className="text-xs font-black text-emerald-500">+{growth}%</p>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-[8px] font-black text-zinc-600 uppercase tracking-[0.2em] text-hollow">Est_Revenue</p>
                                                        <p className="text-xs font-black text-primary">${((candidate.views || 0) * 0.002).toFixed(2)}</p>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-[8px] font-black text-zinc-600 uppercase tracking-[0.2em] text-hollow">Signal_Node</p>
                                                        <p className="text-xs font-black text-zinc-400">CLUSTER_{candidate.id.slice(0, 4).toUpperCase()}</p>
                                                    </div>
                                                </div>

                                                {/* Right: Neural Action Node */}
                                                <div className="flex items-center gap-10 mt-6 lg:mt-0 relative z-10">
                                                    <div className="text-right flex flex-col items-end gap-2">
                                                        <div className="text-[9px] font-black text-zinc-600 uppercase tracking-[0.3em] italic">Viral Score</div>
                                                        <div className="text-2xl font-black text-white tabular-nums drop-shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]">
                                                            {candidate.viral_score}<span className="text-primary text-sm">/100</span>
                                                        </div>
                                                    </div>

                                                    <div className="flex flex-col items-center gap-2">
                                                        <motion.button
                                                            whileHover={{ scale: 1.1, rotate: 5 }}
                                                            whileTap={{ scale: 0.95 }}
                                                            onClick={() => handleAddToQueue(candidate)}
                                                            className="h-16 w-16 rounded-[1.5rem] bg-primary text-black flex items-center justify-center shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)] hover:shadow-[0_0_50px_rgba(var(--primary-rgb),0.5)] transition-all group/btn"
                                                        >
                                                            <Zap className="h-8 w-8 fill-black group-hover/btn:scale-125 transition-transform duration-500" />
                                                        </motion.button>
                                                        <span className="text-[8px] font-black text-zinc-500 uppercase tracking-[0.3em]">Transform</span>
                                                    </div>
                                                </div>

                                                {/* Hover Scanline Effect */}
                                                <motion.div
                                                    className="absolute inset-y-0 w-[2px] bg-primary/20 shadow-[0_0_20px_rgba(var(--primary-rgb),0.5)] opacity-0 group-hover:opacity-100 pointer-events-none z-20"
                                                    initial={{ left: "-10%" }}
                                                    whileHover={{ left: "110%" }}
                                                    transition={{ duration: 1.5, ease: "linear", repeat: Infinity }}
                                                />
                                            </motion.div>
                                        );
                                    })
                                ) : (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="py-40 flex flex-col items-center justify-center gap-10 text-center relative overflow-hidden"
                                    >
                                        <div className="absolute inset-0 bg-gradient-radial from-primary/5 to-transparent opacity-30" />
                                        <div className="h-24 w-24 rounded-full bg-zinc-950 border border-white/5 flex items-center justify-center shadow-2xl relative">
                                            <Search className="h-10 w-10 text-zinc-800" />
                                            <div className="absolute inset-0 border-2 border-dashed border-zinc-800 rounded-full animate-spin-slow" />
                                        </div>
                                        <div className="space-y-3 relative z-10">
                                            <p className="text-sm font-black uppercase tracking-[0.6em] text-zinc-700">No Viral Signals Detected</p>
                                            <p className="text-[10px] font-bold text-zinc-800 uppercase tracking-widest italic">Scanning Inter-Social Cluster High-Velocity Nodes</p>
                                            <button onClick={fetchTrends} className="mt-6 text-xs font-black uppercase tracking-[0.4em] text-primary hover:neon-glow transition-all">Re-Initialize Scan</button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

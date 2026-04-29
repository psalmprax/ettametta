"use client";

import React, { useState, useEffect, useCallback, useRef, Suspense } from "react";
import dynamic from "next/dynamic";
import { Canvas } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";
import DashboardLayout from "@/components/layout";
import {
    Search,
    Play,
    RefreshCw,
    Activity,
    ArrowRight,
    BarChart3,
    Zap
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

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
    thumbnail_uri: string;
    view_count: number;
    engagement_score: number;
    viral_score: number;
    published_at: string;
    creator_name: string;
    source_uri: string;
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
    const [alerts, setAlerts] = useState<any[]>([]);
    const [monitoredNiches, setMonitoredNiches] = useState<string[]>([]);
    
    const [selectedCandidate, setSelectedCandidate] = useState<ContentCandidate | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [analysisTask, setAnalysisTask] = useState<string | null>(null);

    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        return () => {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
        };
    }, []);

    // Fetch Initial Data
    const loadInitialData = useCallback(async () => {
        try {
            const token = await getAuthToken();
            const headers = { Authorization: `Bearer ${token}` };
            
            const [nicheRes, monitoredRes, alertsRes] = await Promise.all([
                fetch(`${API_BASE}/discovery/niches`, { headers }),
                fetch(`${API_BASE}/discovery/niches`, { headers }), // This is just listing, I need to check which ones are watched
                fetch(`${API_BASE}/discovery/alerts`, { headers })
            ]);

            if (nicheRes.ok) setNiches(await nicheRes.json());
            if (alertsRes.ok) {
                const alertData = await alertsRes.json();
                setAlerts(alertData.alerts || []);
                setMonitoredNiches(alertData.alerts?.map((a: any) => a.niche) || []);
            }
        } catch (err) {
            console.error("Failed to load discovery data:", err);
        }
    }, []);

    useEffect(() => {
        loadInitialData();
    }, [loadInitialData]);

    const fetchTrends = useCallback(async () => {
        setIsLoading(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/discovery/trends?niche=${activeNiche}&horizon=${timeHorizon}`, {
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
            const res = await fetch(`${API_BASE}/discovery/search?q=${encodeURIComponent(searchQuery)}`, {
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

    const handleWatchNiche = async (niche: string) => {
        const isWatching = monitoredNiches.includes(niche);
        const token = await getAuthToken();
        try {
            if (isWatching) {
                // Find alert ID and delete
                const alert = alerts.find(a => a.niche === niche);
                if (alert) {
                    await fetch(`${API_BASE}/discovery/alerts/${alert.id}`, {
                        method: "DELETE",
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    toast.success(`Stopped watching ${niche}`);
                }
            } else {
                await fetch(`${API_BASE}/discovery/alerts`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({ niche, threshold: 7, enabled: true })
                });
                toast.success(`Watching ${niche} for viral breakouts`);
            }
            loadInitialData();
        } catch (err) {
            toast.error("Failed to update watch status");
        }
    };

    const handleOpenAnalysis = async (candidate: ContentCandidate) => {
        setSelectedCandidate(candidate);
        setAnalysisResult(null);
        setIsAnalyzing(true);

        const token = await getAuthToken();
        if (!token) return;

        try {
            const res = await fetch(`${API_BASE}/discovery/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ 
                    url: candidate.source_uri || candidate.id,
                    niche: activeNiche 
                })
            });
            
            if (res.ok) {
                const data = await res.json();
                const taskId = data.task_id;
                setAnalysisTask(taskId);

                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                
                pollIntervalRef.current = setInterval(async () => {
                    try {
                        const statusRes = await fetch(`${API_BASE}/discovery/analyze/${taskId}`, {
                            headers: { Authorization: `Bearer ${token}` }
                        });
                        if (statusRes.ok) {
                            const statusData = await statusRes.json();
                            if (statusData.status === "SUCCESS" || statusData.status === "COMPLETED") {
                                setAnalysisResult(statusData.result);
                                setIsAnalyzing(false);
                                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                            } else if (statusData.status === "FAILURE" || statusData.status === "REVOKED") {
                                toast.error("Deep analysis failed");
                                setIsAnalyzing(false);
                                if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                            }
                        }
                    } catch (e) {
                        console.error("Polling error:", e);
                        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
                    }
                }, 3000);
            }
        } catch (err) {
            console.error("Analysis initiation failed:", err);
            setIsAnalyzing(false);
        }
    };

    const handleCloseAnalysis = () => {
        setSelectedCandidate(null);
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
        }
    };

    return (
        <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
            <DiscoveryBackground />

            <div className="flex-1 section-container relative py-12 px-6 lg:px-16 max-w-screen-2xl mx-auto w-full z-10">
                
                {/* DISCOVERY HEADER */}
                <header className="mb-16 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                    <div className="space-y-6">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: 80 }}
                            className="h-1 bg-primary shadow-glow-primary/20"
                        />
                        <div className="space-y-2">
                            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight leading-tight uppercase">
                                Viral Intelligence
                            </h1>
                            <p className="text-zinc-500 text-xs font-bold uppercase tracking-widest flex items-center gap-3">
                                <span className="flex items-center gap-2 text-emerald-400">
                                    <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]"></div>
                                    Network_Online
                                </span>
                                <span className="text-zinc-800">•</span>
                                <span>Scanning 14.2K Global Trends</span>
                            </p>
                        </div>
                    </div>

                    <form onSubmit={handleSearch} className="flex-1 max-w-2xl relative">
                        <Input
                            variant="default"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Inject Search Query..."
                            className="pr-32"
                            data-testid="discovery-search-input"
                            icon={<Search className="h-4 w-4" />}
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2">
                            <Button 
                                type="submit"
                                variant="primary"
                                size="sm"
                                isLoading={isSearching}
                                className="px-8"
                            >
                                Scan
                            </Button>
                        </div>
                    </form>
                </header>

                {/* CONTROL PANEL */}
                <div className="flex flex-wrap items-center gap-6 mb-12">
                    <div className="flex gap-2 p-1.5 bg-white/5 rounded-2xl border border-white/5 shadow-inner">
                        {["YouTube", "TikTok", "Instagram", "X"].map(plat => (
                            <button 
                                key={plat}
                                onClick={() => setFilter(plat.toLowerCase())}
                                className={cn(
                                    "px-6 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all",
                                    filter === plat.toLowerCase() 
                                        ? "bg-primary text-black shadow-glow-primary/20" 
                                        : "text-zinc-500 hover:text-white hover:bg-white/5"
                                )}
                            >
                                {plat}
                            </button>
                        ))}
                    </div>

                    <div className="flex gap-2 p-1.5 bg-white/5 rounded-2xl border border-white/5 shadow-inner">
                        {["24H", "7D", "30D"].map(h => (
                            <button 
                                key={h}
                                onClick={() => setTimeHorizon(h.toLowerCase())}
                                className={cn(
                                    "px-6 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all",
                                    timeHorizon === h.toLowerCase()
                                        ? "bg-zinc-800 text-white"
                                        : "text-zinc-500 hover:text-white hover:bg-white/5"
                                )}
                            >
                                {h}
                            </button>
                        ))}
                    </div>

                    <div className="ml-auto flex items-center gap-4">
                        <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">Active_Cluster:</span>
                        <div className="px-6 py-2 bg-primary/10 border border-primary/20 text-primary font-bold text-[10px] rounded-full uppercase tracking-widest">
                            {activeNiche || "General"}
                        </div>
                    </div>
                </div>

                {/* CONTENT GRID */}
                <div className="grid grid-cols-1 xl:grid-cols-12 gap-12">
                    
                    {/* SIDEBAR: NICHE CLUSTERS */}
                    <div className="xl:col-span-3 space-y-8">
                        <Card variant="solid" className="p-8 space-y-8 rounded-4xl border-white/5">
                            <div className="flex items-center justify-between">
                                <h2 className="text-[10px] font-bold text-zinc-500 flex items-center gap-3 uppercase tracking-[0.2em]">
                                    <Activity className="h-4 w-4 text-primary" />
                                    Trend Clusters
                                </h2>
                            </div>
                            <div className="space-y-2">
                                {niches.slice(0, 10).map(n => (
                                    <div key={n} className="group relative">
                                        <button 
                                            onClick={() => setActiveNiche(n)}
                                            className={cn(
                                                "w-full text-left px-5 py-4 rounded-xl text-[11px] font-bold uppercase tracking-widest transition-all flex items-center justify-between group",
                                                activeNiche === n 
                                                    ? "bg-primary/10 text-primary border border-primary/20" 
                                                    : "text-zinc-500 hover:text-white hover:bg-white/5 border border-transparent"
                                            )}
                                        >
                                            {n}
                                            <ArrowRight className={cn("h-4 w-4 opacity-0 transition-all -translate-x-2", activeNiche === n && "opacity-100 translate-x-0")} />
                                        </button>
                                        <button 
                                            onClick={(e) => { e.stopPropagation(); handleWatchNiche(n); }}
                                            className={cn(
                                                "absolute right-12 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-all",
                                                monitoredNiches.includes(n) ? "text-emerald-500" : "text-zinc-700 opacity-0 group-hover:opacity-100"
                                            )}
                                            title={monitoredNiches.includes(n) ? "Watching" : "Watch Niche"}
                                        >
                                            <Activity className="h-3 w-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <Button variant="outline" size="sm" className="w-full py-6 border-dashed opacity-50 hover:opacity-100 rounded-2xl text-[10px] tracking-widest uppercase">
                                + Define Cluster
                            </Button>
                        </Card>

                        {/* ALERTS SECTION */}
                        <Card variant="solid" className="p-8 space-y-6 rounded-4xl border-white/5 bg-slate-900/40">
                            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-3">
                                <Zap className="h-4 w-4 text-amber-500" />
                                Neural Alerts
                            </h3>
                            <div className="space-y-4 max-h-64 overflow-y-auto custom-scrollbar pr-2">
                                {alerts.length > 0 ? alerts.map((alert, i) => (
                                    <div key={i} className="p-4 rounded-2xl bg-white/2 border border-white/5 space-y-1">
                                        <p className="text-[10px] font-bold text-white uppercase">{alert.niche}</p>
                                        <p className="text-[8px] text-zinc-600 font-medium">Monitoring for score &gt; {alert.threshold}</p>
                                    </div>
                                )) : (
                                    <div className="py-8 text-center opacity-30">
                                        <p className="text-[9px] font-bold uppercase text-zinc-700">No active alerts</p>
                                    </div>
                                )}
                            </div>
                        </Card>

                        <div className="surface-glass rounded-4xl border border-white/5 h-80 overflow-hidden relative group">
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10 flex flex-col justify-end p-8">
                                <span className="text-white text-[10px] font-bold uppercase tracking-widest mb-1">Global Hotspots</span>
                                <p className="text-zinc-500 text-[8px] uppercase tracking-widest">Live Geographic Feed</p>
                            </div>
                            <Geomap />
                        </div>
                    </div>

                    {/* MAIN: CANDIDATES */}
                    <div className="xl:col-span-9">
                        {isLoading ? (
                            <div className="h-[600px] flex flex-col items-center justify-center space-y-6">
                                <div className="h-16 w-16 border-2 border-primary border-t-transparent rounded-full animate-spin shadow-glow-primary/20" />
                                <span className="text-zinc-600 text-[10px] font-bold uppercase tracking-[0.3em] animate-pulse">Syncing Viral Data...</span>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {candidates.map((c, i) => (
                                    <motion.div 
                                        key={c.id}
                                        initial={{ opacity: 0, y: 30 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="group relative"
                                        data-testid="candidate-card"
                                    >
                                        <Card variant="solid" className="h-full overflow-hidden flex flex-col border-white/5 hover:border-primary/30 transition-all duration-500 rounded-4xl">
                                            {/* Thumbnail */}
                                            <div className="relative aspect-video overflow-hidden bg-zinc-900">
                                                <img 
                                                    src={c.thumbnail_uri || "https://api.dicebear.com/7.x/shapes/svg?seed=" + c.id} 
                                                    alt={c.title}
                                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-80 group-hover:opacity-100"
                                                />
                                                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60" />
                                                
                                                <div className="absolute top-4 left-4 flex gap-2">
                                                    <div className="px-3 py-1 bg-black/60 backdrop-blur-md border border-white/10 rounded-full text-[8px] font-bold text-white uppercase tracking-widest">
                                                        {c.platform}
                                                    </div>
                                                </div>

                                                <div className="absolute bottom-4 right-4">
                                                    <div className="px-4 py-1.5 bg-emerald-500 rounded-full text-black font-black text-[9px] flex items-center gap-2 shadow-glow-emerald/20">
                                                        <Activity className="h-3 w-3" />
                                                        {c.viral_score}% VIRAL
                                                    </div>
                                                </div>

                                                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500">
                                                    <div 
                                                        onClick={() => handleOpenAnalysis(c)}
                                                        className="h-16 w-16 bg-primary rounded-full flex items-center justify-center shadow-glow-primary/40 transform scale-75 group-hover:scale-100 transition-transform duration-500 cursor-pointer"
                                                    >
                                                        <Play className="h-6 w-6 text-black ml-1" />
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Info */}
                                            <div className="p-8 flex flex-col flex-1 space-y-6">
                                                <h3 className="text-lg font-bold text-white line-clamp-2 leading-tight uppercase tracking-tight group-hover:text-primary transition-colors">
                                                    {c.title}
                                                </h3>
                                                
                                                <div className="flex items-center justify-between text-zinc-500 font-bold text-[9px] uppercase tracking-widest">
                                                    <span className="flex items-center gap-2">
                                                        <div className="h-1.5 w-1.5 bg-zinc-700 rounded-full" />
                                                        {c.creator_name}
                                                    </span>
                                                    <span className="text-zinc-400">{(c.view_count / 1000).toFixed(1)}K VIEWS</span>
                                                </div>

                                                <div className="flex gap-4 pt-6 border-t border-white/5">
                                                    <Button 
                                                        onClick={() => handleOpenAnalysis(c)}
                                                        variant="primary"
                                                        size="sm"
                                                        className="flex-1 py-6 rounded-2xl text-[10px] tracking-[0.2em]"
                                                    >
                                                        Deep Scan
                                                    </Button>
                                                    <Button variant="secondary" size="sm" className="rounded-2xl w-14 p-0">
                                                        <BarChart3 className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </Card>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Analysis Modal (Playwright Expects this) */}
            <AnimatePresence>
                {selectedCandidate && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={handleCloseAnalysis}
                            className="absolute inset-0 bg-black/80 backdrop-blur-md"
                        />
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            className="relative w-full max-w-2xl bg-zinc-900 border border-white/10 rounded-4xl p-10 overflow-hidden shadow-2xl"
                            data-testid="analysis-modal"
                        >
                            <div className="absolute top-0 right-0 p-6">
                                <button onClick={handleCloseAnalysis} className="text-zinc-500 hover:text-white transition-colors">
                                    <Activity className="h-5 w-5 rotate-45" />
                                </button>
                            </div>

                            <div className="space-y-8">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-glow-primary/10">
                                        <BarChart3 className="h-10 w-10" />
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-white uppercase tracking-tight">Neural Analysis</h2>
                                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Candidate ID: {selectedCandidate.id}</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-6">
                                    <div className="p-6 rounded-3xl bg-white/2 border border-white/5 space-y-2">
                                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Viral Potential</p>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-4xl font-black text-white" data-testid="viral-score">{selectedCandidate.viral_score}%</span>
                                            <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">High Probability</span>
                                        </div>
                                    </div>
                                    <div className="p-6 rounded-3xl bg-white/2 border border-white/5 space-y-2">
                                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Engagement Rate</p>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-4xl font-black text-white">{(selectedCandidate.engagement_score * 10).toFixed(1)}%</span>
                                            <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Top 5%</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Synthesized Intelligence</h4>
                                    {isAnalyzing ? (
                                        <div className="flex items-center gap-4 py-4">
                                            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                                            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] animate-pulse">Running Neural Simulation...</p>
                                        </div>
                                    ) : analysisResult ? (
                                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                                            <p className="text-sm text-zinc-300 leading-relaxed font-medium">
                                                {analysisResult.analysis?.optimization_hook || "Analysis complete. Optimization patterns identified."}
                                            </p>
                                            <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10">
                                                <p className="text-[9px] font-bold text-primary uppercase tracking-wider mb-2">Strategy Recommendation</p>
                                                <p className="text-[11px] text-zinc-400 font-medium">{analysisResult.analysis?.strategy || "Deploying automated variations via Creation engine."}</p>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="text-sm text-zinc-300 leading-relaxed font-medium">
                                            This content cluster shows high resonance in the {selectedCandidate.category} niche. 
                                            The visual hooks used by {selectedCandidate.creator_name} correlate with current viral peaks 
                                            in the {activeNiche} sector. Recommendation: Trigger automated variation engine.
                                        </p>
                                    )}
                                </div>

                                <div className="flex gap-4 pt-4">
                                    <Button 
                                        onClick={() => router.push(`/creation?seed=${encodeURIComponent(selectedCandidate.title)}`)}
                                        variant="primary" 
                                        className="flex-1 py-8 rounded-2xl text-xs tracking-[0.2em]"
                                    >
                                        Transform to Video
                                    </Button>
                                    <Button 
                                        variant="outline" 
                                        onClick={handleCloseAnalysis}
                                        className="px-10 rounded-2xl border-white/5 text-zinc-500 hover:text-white"
                                    >
                                        Dismiss
                                    </Button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default function DiscoveryPage() {
    return (
        <DashboardLayout>
            <Suspense fallback={
                <div className="min-h-screen bg-bg-base flex flex-col items-center justify-center space-y-4">
                    <div className="h-12 w-12 border-2 border-primary border-t-transparent rounded-full animate-spin shadow-glow-primary/20" />
                    <span className="text-zinc-600 text-[10px] font-bold uppercase tracking-[0.3em] animate-pulse">Initializing Neural Link...</span>
                </div>
            }>
                <DiscoveryContent />
            </Suspense>
        </DashboardLayout>
    );
}

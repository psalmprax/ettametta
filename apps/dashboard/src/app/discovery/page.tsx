"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef, Suspense } from "react";
import dynamic from "next/dynamic";
import {
    Search, 
    TrendingUp, 
    Globe, 
    ShieldAlert, 
    Cpu,
    Radar,
    Loader2,
    Terminal,
    XCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn, copyToClipboard } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import { useWebSocket } from "@/hooks/useWebSocket";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";
import { AnalysisResultsCard, AnalysisReportData } from "@/components/discovery/AnalysisResultsCard";

const Geomap = dynamic(() => import("@/components/ui/Geomap"), { ssr: false });
const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });

interface ContentCandidate {
    id: string;
    platform: string;
    category: string;
    title: string;
    viral_score: number;
    view_count: number;
    creator_name: string;
}

function DiscoveryContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents, logs: systemLogs, pulse } = useTelemetry();
    
    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "trends");
    const [candidates, setCandidates] = useState<ContentCandidate[]>([]);
    const [activeNiche, setActiveNiche] = useState(searchParams.get("q") || "Motivation");
    const [activeRegion, setActiveRegion] = useState(searchParams.get("region") || "US");
    const [isScanning, setIsScanning] = useState(false);
    // Track whether current query is a keyword search (from ?q= URL param) vs niche scan
    const [isKeywordSearch, setIsKeywordSearch] = useState(!!searchParams.get("q"));
    const [actionLogs, setActionLogs] = useState<string[]>([]);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [intelData, setIntelData] = useState<any>(null);
    const [analysisTasks, setAnalysisTasks] = useState<Record<string, { task_id: string; status: string; result?: any; niche: string; candidate_id?: string }>>({});
    const [analysisReports, setAnalysisReports] = useState<Record<string, AnalysisReportData>>({});
    const pollingRefs = useRef<Record<string, NodeJS.Timeout>>({});

    // ── 10-05: WebSocket for analysis_complete events (replaces 3s polling) ──
    const { data: wsMessage, status: wsStatus, reconnectAttempts: wsReconnectAttempts } = useWebSocket<any>(`${WS_BASE}/jobs`);
    // ── 10-05: Fetch full AnalysisReport from DB read endpoint ────────────────
    const fetchAnalysisReport = useCallback(async (candidateId: string) => {
        const token = await getAuthToken();
        if (!token) return;
        try {
            const response = await fetch(
                `${API_BASE}/discovery/analysis/${candidateId}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            if (response.ok) {
                const result = await response.json();
                const report = result?.data?.analysis;
                if (report) {
                    setAnalysisReports(prev => ({ ...prev, [candidateId]: report }));
                    setActionLogs((prev: string[]) => [
                        `[ANALYSIS] ✅ Full report loaded (viral=${report.viral_score}, style=${report.style?.recommended_style})`,
                        ...prev
                    ]);
                    toast.success("AI Analysis complete!");
                }
            }
        } catch (error) {
            console.error("Failed to fetch analysis report:", error);
            toast.error("Failed to load analysis report");
        }
    }, []);
    const handleAnalyze = async (candidate: ContentCandidate) => {
        // Switch to niche scan mode for analysis (don't stay in keyword search mode)
        setIsKeywordSearch(false);

        const token = await getAuthToken();
        if (!token) return;
        
        setActionLogs((prev: string[]) => [`[ANALYSIS] Initiating deep analysis: ${candidate.title.slice(0, 30)}...`, ...prev]);
        
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/discovery/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    url: `https://ettametta.ai/discovery/${candidate.id}`,
                    niche: activeNiche,
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const taskId = data?.task_id;
                    if (taskId) {
                        setAnalysisTasks(prev => ({ ...prev, [candidate.id]: { task_id: taskId, status: "QUEUED", niche: activeNiche, candidate_id: candidate.id } }));
                        setActionLogs((prev: string[]) => [`[ANALYSIS] Task ${taskId} queued. Waiting for AI analysis...`, ...prev]);
                        toast.success(`Analysis queued for ${candidate.title.slice(0, 20)}...`);
                        
                        // Start polling (fallback if WebSocket is unavailable)
                        pollAnalysisTask(candidate.id, taskId);
                    }
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[ANALYSIS] Failed: ${err.message}`, ...prev]);
                    toast.error(`Analysis failed: ${err.message}`);
                }
            }
        );
    };

    const pollAnalysisTask = async (candidateId: string, taskId: string) => {
        const token = await getAuthToken();
        if (!token) return;
        
        const poll = async () => {
            try {
                const response = await fetch(`${API_BASE}/discovery/analyze/${taskId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const status = data?.data?.status || data?.status;
                    
                    if (status === "COMPLETED") {
                        setAnalysisTasks(prev => ({ ...prev, [candidateId]: { ...prev[candidateId], status: "COMPLETED", result: data?.data?.result || data?.result } }));
                        setActionLogs((prev: string[]) => [`[ANALYSIS] ✅ Analysis complete for task ${taskId}`, ...prev]);
                        // ── 10-05: Also try fetching the DB-persisted report ──
                        fetchAnalysisReport(candidateId);
                        if (pollingRefs.current[candidateId]) {
                            clearInterval(pollingRefs.current[candidateId]);
                            delete pollingRefs.current[candidateId];
                        }
                    } else if (status === "FAILED") {
                        setAnalysisTasks(prev => ({ ...prev, [candidateId]: { ...prev[candidateId], status: "FAILED" } }));
                        setActionLogs((prev: string[]) => [`[ANALYSIS] ❌ Analysis failed for task ${taskId}`, ...prev]);
                        toast.error("Analysis failed");
                        if (pollingRefs.current[candidateId]) {
                            clearInterval(pollingRefs.current[candidateId]);
                            delete pollingRefs.current[candidateId];
                        }
                    } else {
                        // Still pending - update status
                        setAnalysisTasks(prev => ({ ...prev, [candidateId]: { ...prev[candidateId], status: status || "PENDING" } }));
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
                toast.error("Analysis polling error — check console for details");
            }
        };
        
        // Poll every 3 seconds
        pollingRefs.current[candidateId] = setInterval(poll, 3000);
        // Initial poll
        await poll();
    };

    const handleCreateFromAnalysis = async (taskId: string, candidateId: string, niche: string) => {
        const token = await getAuthToken();
        if (!token) return;
        
        setActionLogs((prev: string[]) => [`[CREATE] Creating video from analysis task ${taskId}...`, ...prev]);
        
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/discovery/analyze/${taskId}/create-video`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    task_id: taskId,
                    niche: niche,
                    platform: "YouTube Shorts",
                    // ── 10-05: Pass content_id so backend can thread AnalysisReport ──
                    content_id: candidateId,
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const videoTaskId = data?.data?.task_id || data?.task_id;
                    setActionLogs((prev: string[]) => [`[CREATE] ✅ Video transformation started. Task: ${videoTaskId}`, ...prev]);
                    toast.success("Video creation started!");
                    // Navigate to creation page to track progress
                    router.push(`/creation?job=${videoTaskId}`);
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[CREATE] Failed: ${err.message}`, ...prev]);
                    toast.error(`Video creation failed: ${err.message}`);
                }
            }
        );
    };

    // ── 10-05: WebSocket listener for analysis_complete events ────────────────
    // When the Celery task persists the AnalysisReport, it publishes to Redis
    // job_updates. We catch it here and fetch the full report from the DB endpoint.
    useEffect(() => {
        if (!wsMessage) return;
        // Check for analysis_complete wrapped in job_update envelope
        if (
            wsMessage.type === "job_update" &&
            wsMessage.data?.type === "analysis_complete"
        ) {
            const { candidate_id } = wsMessage.data;
            if (candidate_id) {
                setActionLogs((prev: string[]) => [
                    `[WS] Analysis complete for ${candidate_id.slice(0, 12)}... (WebSocket)`, 
                    ...prev
                ]);
                // Update task status and fetch the full report
                setAnalysisTasks(prev => {
                    const updated = { ...prev };
                    for (const key of Object.keys(updated)) {
                        if (updated[key].candidate_id === candidate_id) {
                            updated[key] = { ...updated[key], status: "COMPLETED" };
                            // Clear any active polling for this candidate
                            if (pollingRefs.current[key]) {
                                clearInterval(pollingRefs.current[key]);
                                delete pollingRefs.current[key];
                            }
                        }
                    }
                    return updated;
                });
                fetchAnalysisReport(candidate_id);
            }
        }
    }, [wsMessage]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            Object.values(pollingRefs.current).forEach(clearInterval);
        };
    }, []);

    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine) setActiveEngine(engine);
        const qParam = searchParams.get("q");
        if (qParam) {
            setIsKeywordSearch(true);
            setActiveNiche(qParam);
        }
    }, [searchParams]);

    // Keyword search via /discovery/search (used when user types in SearchBar and lands on ?q=)
    const fetchSearch = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        if (!activeNiche.trim()) return;

        setIsScanning(true);
        setCandidates([]);
        setActionLogs((prev: string[]) => [
            `[SEARCH] Searching for: "${activeNiche}"`,
            `[SEARCH] Target Region: ${activeRegion}`,
            `[SEARCH] Querying database index...`,
            ...prev
        ]);

        await withRealFallback<any>(
            async (signal) => {
                setActionLogs((prev: string[]) => [`[SEARCH] Fetching live results for "${activeNiche}"...`, ...prev]);
                return fetch(
                    `${API_BASE}/discovery/search?query=${encodeURIComponent(activeNiche)}&region=${activeRegion}&limit=50`,
                    { headers: { Authorization: `Bearer ${token}` }, signal }
                );
            },
            {
                fallback: [],
                onSuccess: (data) => {
                    const results = Array.isArray(data) ? data : (data?.results || data?.items || []);
                    setCandidates(results);
                    if (results.length === 0) {
                        setActionLogs((prev: string[]) => [
                            `[SEARCH] No results found for "${activeNiche}" in ${activeRegion}.`,
                            `[SEARCH] Try a different keyword or browse trending content.`,
                            ...prev
                        ]);
                    } else {
                        setActionLogs((prev: string[]) => [
                            `[SUCCESS] Search complete: ${results.length} candidates found for "${activeNiche}" in ${activeRegion}.`,
                            `[DATA] Results indexed from database and live scanners.`,
                            ...prev
                        ]);
                    }
                    setIsScanning(false);
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[ERROR] Search failed: ${err.message}`, ...prev]);
                    setIsScanning(false);
                }
            }
        );
    }, [activeNiche, activeRegion]);

    // Niche scanning via /discovery/trends (used for browsing specific niches)
    const fetchTrends = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        setIsScanning(true);
        setCandidates([]);
        setActionLogs((prev: string[]) => [
            `[SCAN] Initiating Trend Analysis: ${activeNiche}`,
            `[SCAN] Target Region: ${activeRegion}`,
            `[SCAN] Checking regional cache silos...`,
            ...prev
        ]);

        await withRealFallback<any>(
            async (signal) => {
                setActionLogs((prev: string[]) => [`[SCAN] Dispatching live scanners for ${activeRegion}...`, ...prev]);
                return fetch(`${API_BASE}/discovery/trends?niche=${encodeURIComponent(activeNiche)}&region=${activeRegion}`, {
                    headers: { Authorization: `Bearer ${token}` },
                    signal,
                });
            },
            {
                fallback: [],
                onSuccess: (data) => {
                    const trends = Array.isArray(data) ? data : (data?.trends || []);
                    setCandidates(trends);
                    setActionLogs((prev: string[]) => [
                        `[SUCCESS] Analysis Complete: ${trends.length} viral candidates found in ${activeRegion}.`,
                        `[DATA] Persistence synchronized for regional segment.`,
                        ...prev
                    ]);
                    setIsScanning(false);
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[ERROR] Regional scan failed: ${err.message}`, ...prev]);
                    setIsScanning(false);
                }
            }
        );
    }, [activeNiche, activeRegion]);

    const fetchAlerts = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/discovery/alerts`, {
                headers: { Authorization: `Bearer ${token}` },
                signal,
            }),
            {
                fallback: [],
                onSuccess: (data) => {
                    const alertList = Array.isArray(data) ? data : (data?.alerts || []);
                    setAlerts(alertList);
                }
            }
        );
    }, []);

    const fetchIntel = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/discovery/insights/${encodeURIComponent(activeNiche)}`, {
                headers: { Authorization: `Bearer ${token}` },
                signal,
            }),
            {
                fallback: null,
                onSuccess: (data) => setIntelData(data)
            }
        );
    }, [activeNiche]);

    useEffect(() => {
        if (isKeywordSearch) {
            fetchSearch();
        } else {
            fetchTrends();
        }
    }, [fetchSearch, fetchTrends, isKeywordSearch, activeNiche, activeRegion]);

    useEffect(() => {
        if (activeEngine === "alerts") fetchAlerts();
        if (activeEngine === "intel") fetchIntel();
    }, [activeEngine, fetchAlerts, fetchIntel]);

    // Merge system logs and action logs for display
    const displayLogs = useMemo(() => {
        const merged = [
            ...actionLogs.map(msg => ({ 
                type: "log", 
                level: "ACTION", 
                module: "DISCOVERY",
                message: msg, 
                timestamp: Date.now() / 1000 
            })),
            ...(Array.isArray(systemLogs) ? systemLogs : [])
        ].sort((a, b) => b.timestamp - a.timestamp);
        return merged;
    }, [actionLogs, systemLogs]);

    // Derive map points from candidates
    const mapPoints = useMemo(() => {
        return candidates.map(c => {
            // Deterministic coords based on ID hash
            const hash = Array.from(c.id || "").reduce((acc, char) => acc + char.charCodeAt(0), 0);
            return {
                id: c.id,
                lat: ((hash % 180) - 90) * 0.8,
                lng: ((hash % 360) - 180) * 0.8,
                intensity: (c.viral_score || 50) / 100,
                label: c.title
            };
        });
    }, [candidates]);

    // Derive network graph data from real candidates for intel view
    const networkData = useMemo(() => ({
        nodes: [
            { id: "root", group: 1, label: activeNiche },
            ...candidates.slice(0, 5).map(c => ({ id: c.id, group: 2, label: c.title }))
        ],
        links: candidates.slice(0, 5).map(c => ({ source: "root", target: c.id, value: 1 }))
    }), [activeNiche, candidates]);

    return (
        <CommandCenterLayout
            title="VIRAL INTELLIGENCE"
            subtitle="GLOBAL_DISCOVERY_V3.0"
            additionalWsConnections={[{ name: "Discovery", status: wsStatus, reconnectAttempts: wsReconnectAttempts }]}
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "trends", label: "Viral Trends", icon: TrendingUp },
                        { id: "intel", label: "Niche Intel", icon: Cpu },
                        { id: "alerts", label: "Neural Alerts", icon: ShieldAlert },
                        { id: "hotspots", label: "Hotspots", icon: Globe },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => {
                                setActiveEngine(item.id);
                                // Sync URL for sidebar consistency
                                router.replace(`/discovery?engine=${item.id}`);
                            }}
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
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Scanner Metrics</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Candidates</span>
                                <span className="text-xl font-bold text-white">{pulse?.real_stats?.total_discovered || candidates.length}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Active Jobs</span>
                                <span className="text-xl font-bold text-rose-500">{pulse?.real_stats?.active_jobs || 0}</span>
                            </div>
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "trends" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex items-center gap-6 shrink-0">
                                    <div className="relative flex-1">
                                        <input
                                            type="text"
                                            placeholder={isKeywordSearch ? "SEARCH_KEYWORD_FOR_CANDIDATES..." : "SCAN_NICHE_FOR_VIRALITY..."}
                                            value={activeNiche}
                                            onChange={(e) => {
                                                setActiveNiche(e.target.value);
                                                setIsKeywordSearch(false); // User typed manually = niche scan mode
                                            }}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") {
                                                    if (isKeywordSearch && activeNiche.trim()) {
                                                        router.replace(`/discovery?q=${encodeURIComponent(activeNiche.trim())}`);
                                                        fetchSearch();
                                                    } else {
                                                        fetchTrends();
                                                    }
                                                }
                                            }}
                                            className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 pl-14 text-white font-mono text-lg focus:outline-none focus:border-primary/50"
                                        />
                                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
                                    </div>
                                    <Button 
                                        onClick={() => {
                                            if (isKeywordSearch && activeNiche.trim()) {
                                                router.replace(`/discovery?q=${encodeURIComponent(activeNiche.trim())}`);
                                                fetchSearch();
                                            } else {
                                                fetchTrends();
                                            }
                                        }} 
                                        disabled={isScanning}
                                        className="h-20 px-10 bg-primary text-black font-bold text-lg rounded-2xl uppercase tracking-widest flex items-center gap-3"
                                    >
                                        {isScanning ? (
                                            <>
                                                <Loader2 className="h-6 w-6 animate-spin" />
                                                {isKeywordSearch ? "Searching..." : "Scanning..."}
                                            </>
                                        ) : (
                                            isKeywordSearch ? "Search" : "Initiate Scan"
                                        )}
                                    </Button>
                                </div>

                                {/* 10-05: Analysis status bar with AnalysisResultsCard */}
                                {Object.keys(analysisTasks).length > 0 && (
                                    <div className="shrink-0 rounded-2xl bg-[#0F0F11]/60 border border-white/5 p-4 space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest">
                                                Active Analysis Tasks
                                            </span>
                                            <span className={cn(
                                                "text-[8px] font-mono uppercase",
                                                wsStatus === "open" ? "text-emerald-500" : "text-amber-500"
                                            )}>
                                                {wsStatus === "open" ? "WS LIVE" : "WS RECONNECTING"}
                                            </span>
                                        </div>
                                        {Object.entries(analysisTasks).map(([id, task]) => {
                                            const report = analysisReports[id];
                                            if (report && task.status === "COMPLETED") {
                                                // Show the full AnalysisResultsCard
                                                return (
                                                    <div key={id} className="space-y-2">
                                                        <AnalysisResultsCard
                                                            report={report}
                                                            onCreateVideo={(contentId) =>
                                                                handleCreateFromAnalysis(task.task_id, contentId, task.niche)
                                                            }
                                                        />
                                                    </div>
                                                );
                                            }
                                            // Show compact status row (pending/failed)
                                            return (
                                                <div key={id} className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3 text-[10px]">
                                                    <span className="text-zinc-300 font-mono truncate flex-1">{id}</span>
                                                    <div className="flex items-center gap-3">
                                                        <span className={cn("px-2 py-0.5 rounded text-[8px] font-bold uppercase",
                                                            task.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-400" :
                                                            task.status === "FAILED" ? "bg-rose-500/20 text-rose-400" :
                                                        "bg-amber-500/20 text-amber-400"
                                                    )}>{task.status}</span>
                                                        {task.status === "COMPLETED" && !report && (
                                                            <button
                                                                onClick={() => handleCreateFromAnalysis(task.task_id, id, task.niche)}
                                                                className="px-3 py-1.5 bg-violet-500 hover:bg-violet-400 text-black font-bold text-[8px] uppercase rounded-lg tracking-widest"
                                                            >
                                                                Create Video
                                                            </button>
                                                        )}
                                                        {task.status === "FAILED" && (
                                                            <XCircle className="h-3.5 w-3.5 text-rose-500" />
                                                        )}
                                                        {(task.status === "PENDING" || task.status === "QUEUED") && (
                                                            <Loader2 className="h-3.5 w-3.5 text-amber-500 animate-spin" />
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}

                                <div className="flex items-center gap-2 overflow-x-auto pb-2 shrink-0">
                                    {[
                                        { id: "US", label: "USA", flag: "🇺🇸" },
                                        { id: "GB", label: "United Kingdom", flag: "🇬🇧" },
                                        { id: "DE", label: "Germany", flag: "🇩🇪" },
                                        { id: "CA", label: "Canada", flag: "🇨🇦" },
                                        { id: "FR", label: "France", flag: "🇫🇷" },
                                        { id: "AU", label: "Australia", flag: "🇦🇺" },
                                    ].map((reg) => (
                                        <button
                                            key={reg.id}                    onClick={() => {
                        setActiveRegion(reg.id);
                        // Trigger re-fetch immediately on region change
                        setTimeout(() => {
                            if (isKeywordSearch) {
                                fetchSearch();
                            } else {
                                fetchTrends();
                            }
                        }, 100);
                    }}
                                            disabled={isScanning}
                                            className={cn(
                                                "flex items-center gap-2 px-4 py-2 rounded-xl border transition-all shrink-0",
                                                activeRegion === reg.id 
                                                    ? "bg-primary/20 border-primary/50 text-white shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)]" 
                                                    : "bg-white/5 border-white/10 text-zinc-500 hover:border-white/20",
                                                isScanning && "opacity-50 cursor-not-allowed"
                                            )}
                                        >
                                            <span className="text-sm">{reg.flag}</span>
                                            <span className="text-[10px] font-bold uppercase tracking-tight">{reg.label}</span>
                                        </button>
                                    ))}
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 overflow-y-auto custom-scrollbar p-1">
                                    {candidates.length === 0 && !isScanning && (
                                        <div className="col-span-full flex flex-col items-center justify-center py-24 opacity-40 gap-4">
                                            <Search className="h-16 w-16 text-zinc-600" />
                                            <div className="text-center space-y-2">
                                                <p className="text-lg font-bold text-white uppercase tracking-widest">
                                                    {isKeywordSearch ? `No results for "${activeNiche}"` : "Scan a niche to discover viral content"}
                                                </p>
                                                <p className="text-sm text-zinc-500 font-mono">
                                                    {isKeywordSearch
                                                        ? "Try a different keyword, or browse trending niches below."
                                                        : "Type a niche name above and press Enter or click Initiate Scan."}
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                    {candidates.map((c, i) => (
                                        <DesignCard
                                            key={c.id}
                                            title={c.title}
                                            status="Viral"
                                            metrics={[
                                                { label: "Viral Score", value: `${c.viral_score}%`, progress: c.viral_score, color: "text-emerald-400" },
                                                { label: "Views", value: `${(c.view_count / 1000).toFixed(1)}K`, color: "text-cyan-400" }
                                            ]}
                                            footerInfo={`${c.platform.toUpperCase()} • ${c.creator_name}`}
                                            toolsStatus="Live"
                                            credits={pulse?.credits || 0}
                                            onRefresh={() => {
                                                handleAnalyze(c);
                                            }}
                                            onDelete={() => {
                                                setCandidates(prev => prev.filter(cand => cand.id !== c.id));
                                                toast.error(`Purged Candidate: ${c.title.slice(0, 20)}...`);
                                            }}
                                            onShare={async () => {
                                                const success = await copyToClipboard(`https://ettametta.ai/discovery/candidate/${c.id}`);
                                                if (success) {
                                                    toast.success("Candidate Intelligence Link Copied");
                                                } else {
                                                    toast.error("Clipboard access not available");
                                                }
                                            }}
                                            onClick={() => router.push(`/creation?seed=${encodeURIComponent(c.title)}`)}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {activeEngine === "intel" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-12 flex flex-col gap-8">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Niche Intelligence: {activeNiche}</h3>
                                    <div className="px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-widest">Live Analysis Active</div>
                                </div>
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 flex-1 min-h-0">
                                    <div className="rounded-2xl bg-white/5 border border-white/5 p-8 overflow-hidden relative">
                                        <NetworkMesh nodes={networkData.nodes} links={networkData.links} />
                                        <div className="absolute inset-0 bg-linear-to-t from-[#0F0F11] via-transparent to-transparent" />
                                        <div className="absolute bottom-8 left-8 right-8 space-y-4">
                                            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Growth Vector Analysis</h4>
                                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                <motion.div initial={{ width: 0 }} animate={{ width: "75%" }} className="h-full bg-primary" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-6 overflow-y-auto custom-scrollbar pr-4">
                                        {intelData?.insights?.map((insight: any, i: number) => (
                                            <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] font-bold text-primary uppercase tracking-widest">{insight.type}</span>
                                                    <span className="text-[10px] font-mono text-zinc-500">{insight.confidence}% CONF</span>
                                                </div>
                                                <p className="text-sm text-zinc-300 leading-relaxed">{insight.message}</p>
                                            </div>
                                        )) || (
                                            <div className="h-full flex flex-col items-center justify-center opacity-20 gap-4">
                                                <Radar className="h-12 w-12" />
                                                <span className="text-xs font-bold uppercase tracking-[0.4em]">Scanning Neural Patterns...</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "alerts" && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                                {alerts.map((alert, i) => (
                                    <div key={i} className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col justify-between group hover:border-primary/20 transition-all">
                                        <div className="space-y-6">
                                            <div className="flex items-center justify-between">
                                                <div className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                                                    <ShieldAlert className="h-5 w-5 text-primary" />
                                                </div>
                                                <span className="text-[10px] font-mono text-zinc-600 uppercase">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                                            </div>
                                            <div className="space-y-2">
                                                <h4 className="text-lg font-bold text-white uppercase tracking-tight">{alert.title}</h4>
                                                <p className="text-xs text-zinc-500 leading-relaxed">{alert.description}</p>
                                            </div>
                                        </div>
                                        <div className="mt-8 flex items-center justify-between">
                                            <div className="flex gap-2">
                                                {alert.tags?.map((tag: string) => (
                                                    <span key={tag} className="px-3 py-1 rounded-full bg-white/5 text-[8px] font-bold text-zinc-400 uppercase">{tag}</span>
                                                ))}
                                            </div>
                                            <Button variant="outline" className="h-10 border-white/10 text-white text-[10px] uppercase font-bold group-hover:bg-primary group-hover:text-black">Investigate</Button>
                                        </div>
                                    </div>
                                ))}
                                {alerts.length === 0 && (
                                    <div className="col-span-2 h-full flex flex-col items-center justify-center opacity-10 gap-6">
                                        <ShieldAlert className="h-24 w-24" />
                                        <span className="text-xl font-black uppercase tracking-[1em]">Scanning for Outbreaks</span>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "hotspots" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 overflow-hidden relative">
                                <Geomap points={mapPoints} />
                                <div className="absolute top-8 right-8 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-xs space-y-2">
                                    <h4 className="text-white font-bold uppercase tracking-widest text-xs">Live Geolocation Feed</h4>
                                    <p className="text-zinc-500 text-[10px] leading-relaxed italic">Mapping {mapPoints.length} active viral outbreaks across platform clusters.</p>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Discovery Engine Logs</h3>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-[9px] font-bold text-emerald-500 uppercase">Engine_Active</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {displayLogs.map((log, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                "shrink-0 font-bold tracking-widest uppercase text-[9px] px-2 py-0.5 rounded",
                                                log.level === "ACTION" ? "bg-cyan-500/10 text-cyan-500" :
                                                log.level === "ERROR" ? "bg-rose-500/10 text-rose-500" :
                                                log.level === "SUCCESS" ? "bg-emerald-500/10 text-emerald-500" : "bg-white/5 text-zinc-500"
                                            )}>
                                                {log.level || "INFO"}
                                            </span>
                                            <span className={cn(
                                                "leading-relaxed",
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-400"
                                            )}>
                                                <span className="text-zinc-600">[{log.module || "SYSTEM"}]</span> {log.message}
                                            </span>
                                        </div>
                                    ))}
                                    <div className="h-4" />
                                </div>
                            </div>
                        )}

                        {activeEngine !== "logs" && (
                            <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Scanner Logs</span>
                                    <span className="text-[8px] font-mono text-primary/50">{status === "open" ? "LIVE_SYNC" : "OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                    {displayLogs.map((log, i) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-600"
                                            )}>
                                                {log.module ? `[${log.module}] ` : ""}{log.message}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function DiscoveryPage() {
    return (
        <Suspense fallback={null}>
            <DiscoveryContent />
        </Suspense>
    );
}

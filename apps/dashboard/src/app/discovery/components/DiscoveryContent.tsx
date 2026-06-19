"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
    TrendingUp,
    Cpu,
    ShieldAlert,
    Globe,
    Terminal,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { CandidateList } from "@/components/discovery/CandidateList";
import { NeuralConfig } from "@/components/discovery/NeuralConfig";
import { DiscoveryHeader } from "./DiscoveryHeader";
import { CandidateGrid } from "./CandidateGrid";
import { AnalysisPanel } from "./AnalysisPanel";

export interface ContentCandidate {
    id: string;
    platform: string;
    category: string;
    title: string;
    viral_score: number;
    view_count: number;
    creator_name: string;
    description: string;
    thumbnail_uri: string;
    engagement_score: number;
    published_at: string;
    source_uri: string;
    duration_seconds: number;
}

export function DiscoveryContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { agents, logs: systemLogs, pulse } = useTelemetry();

    const [activeEngine, setActiveEngine] = useState(searchParams.get("engine") || "trends");
    const [candidates, setCandidates] = useState<ContentCandidate[]>([]);
    const [activeNiche, setActiveNiche] = useState(searchParams.get("q") || "Motivation");
    const [activeRegion, setActiveRegion] = useState(searchParams.get("region") || "US");
    const [isScanning, setIsScanning] = useState(false);
    const [isKeywordSearch, setIsKeywordSearch] = useState(!!searchParams.get("q"));
    const [actionLogs, setActionLogs] = useState<string[]>([]);
    const [minViralScore, setMinViralScore] = useState(50);
    const [excludeShorts, setExcludeShorts] = useState(false);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [intelData, setIntelData] = useState<any>(null);
    const [analysisTasks, setAnalysisTasks] = useState<Record<string, { task_id: string; status: string; result?: any; niche: string }>>({});
    const pollingRefs = useRef<Record<string, NodeJS.Timeout>>({});

    const handleAnalyze = async (candidate: ContentCandidate) => {
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
                        setAnalysisTasks(prev => ({ ...prev, [candidate.id]: { task_id: taskId, status: "QUEUED", niche: activeNiche } }));
                        setActionLogs((prev: string[]) => [`[ANALYSIS] Task ${taskId} queued. Polling for results...`, ...prev]);
                        toast.success(`Analysis queued for ${candidate.title.slice(0, 20)}...`);

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
                        setActionLogs((prev: string[]) => [`[ANALYSIS] \u2705 Analysis complete for task ${taskId}`, ...prev]);
                        toast.success("AI Deconstruction complete!");
                        if (pollingRefs.current[candidateId]) {
                            clearInterval(pollingRefs.current[candidateId]);
                            delete pollingRefs.current[candidateId];
                        }
                    } else if (status === "FAILED") {
                        setAnalysisTasks(prev => ({ ...prev, [candidateId]: { ...prev[candidateId], status: "FAILED" } }));
                        setActionLogs((prev: string[]) => [`[ANALYSIS] \u274C Analysis failed for task ${taskId}`, ...prev]);
                        toast.error("Analysis failed");
                        if (pollingRefs.current[candidateId]) {
                            clearInterval(pollingRefs.current[candidateId]);
                            delete pollingRefs.current[candidateId];
                        }
                    } else {
                        setAnalysisTasks(prev => ({ ...prev, [candidateId]: { ...prev[candidateId], status: status || "PENDING" } }));
                    }
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        };

        pollingRefs.current[candidateId] = setInterval(poll, 3000);
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
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const videoTaskId = data?.data?.task_id || data?.task_id;
                    setActionLogs((prev: string[]) => [`[CREATE] \u2705 Video transformation started. Task: ${videoTaskId}`, ...prev]);
                    toast.success("Video creation started!");
                    router.push(`/creation?job=${videoTaskId}`);
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[CREATE] Failed: ${err.message}`, ...prev]);
                    toast.error(`Video creation failed: ${err.message}`);
                }
            }
        );
    };

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

    const mapPoints = useMemo(() => {
        return candidates.map(c => {
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

    const networkData = useMemo(() => ({
        nodes: [
            { id: "root", group: 1, label: activeNiche },
            ...candidates.slice(0, 5).map(c => ({ id: c.id, group: 2, label: c.title }))
        ],
        links: candidates.slice(0, 5).map(c => ({ source: "root", target: c.id, value: 1 }))
    }), [activeNiche, candidates]);

    const handleScan = useCallback(() => {
        if (isKeywordSearch && activeNiche.trim()) {
            router.replace(`/discovery?q=${encodeURIComponent(activeNiche.trim())}`);
            fetchSearch();
        } else {
            fetchTrends();
        }
    }, [isKeywordSearch, activeNiche, router, fetchSearch, fetchTrends]);

    const handleRegionChange = useCallback((regionId: string) => {
        setActiveRegion(regionId);
        setTimeout(() => {
            if (isKeywordSearch) {
                fetchSearch();
            } else {
                fetchTrends();
            }
        }, 100);
    }, [isKeywordSearch, fetchSearch, fetchTrends]);

    return (
        <CommandCenterLayout
            title="VIRAL INTELLIGENCE"
            subtitle="GLOBAL_DISCOVERY_V3.0"
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
                    <NeuralConfig
                        minViralScore={minViralScore}
                        excludeShorts={excludeShorts}
                        onMinViralScoreChange={setMinViralScore}
                        onExcludeShortsChange={setExcludeShorts}
                    />
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
                                <DiscoveryHeader
                                    activeNiche={activeNiche}
                                    onNicheChange={setActiveNiche}
                                    isKeywordSearch={isKeywordSearch}
                                    onKeywordSearchChange={setIsKeywordSearch}
                                    activeRegion={activeRegion}
                                    onRegionChange={handleRegionChange}
                                    isScanning={isScanning}
                                    onScan={handleScan}
                                    analysisTasks={analysisTasks}
                                    onCreateFromAnalysis={handleCreateFromAnalysis}
                                />

                                {candidates.length > 0 && (
                                    <CandidateList
                                        candidates={candidates}
                                        isLoading={isScanning}
                                        onSelectCandidate={handleAnalyze}
                                        onRefresh={() => isKeywordSearch ? fetchSearch() : fetchTrends()}
                                    />
                                )}

                                <CandidateGrid
                                    candidates={candidates}
                                    isScanning={isScanning}
                                    isKeywordSearch={isKeywordSearch}
                                    activeNiche={activeNiche}
                                    credits={pulse?.credits || 0}
                                    onAnalyze={handleAnalyze}
                                    onRemoveCandidate={(id: string) => setCandidates(prev => prev.filter(cand => cand.id !== id))}
                                    onCreateVideo={(title: string) => router.push(`/creation?seed=${encodeURIComponent(title)}`)}
                                />
                            </div>
                        )}

                        <AnalysisPanel
                            activeEngine={activeEngine}
                            intelData={intelData}
                            networkData={networkData}
                            alerts={alerts}
                            displayLogs={displayLogs}
                            mapPoints={mapPoints}
                            activeNiche={activeNiche}
                            onCreateFromAnalysis={handleCreateFromAnalysis}
                            analysisTasks={analysisTasks}
                        />

                        {activeEngine !== "logs" && (
                            <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                                <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Scanner Logs</span>
                                    <span className="text-[8px] font-mono text-primary/50">LIVE_SYNC</span>
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

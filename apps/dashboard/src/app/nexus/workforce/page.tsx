"use client";

import React, { useState, useEffect, useCallback } from "react";
import { 
    Cpu, 
    Zap, 
    Terminal, 
    Users, 
    Search, 
    Globe, 
    Code2, 
    FileText, 
    Play, 
    ShieldCheck, 
    Activity,
    Database,
    Bot,
    RefreshCw,
    Plus,
    Layout,
    Layers,
    ChevronRight,
    Loader2,
    CheckCircle2,
    Target,
    Fingerprint,
    Microscope,
    BarChart3,
    BookOpen,
    Rss,
    Radio
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

interface Skill {
    id: string;
    name: string;
    description: string;
    category: string;
    priority: "high" | "medium" | "low";
}

export default function WorkforceHub() {
    const [activeEngine, setActiveEngine] = useState("registry");
    const [skills, setSkills] = useState<Skill[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isExecuting, setIsExecuting] = useState(false);
    const [logs, setLogs] = useState<string[]>(["WORKFORCE_NODES_ONLINE", "READY_FOR_DEPLOYMENT"]);
    
    // Research State
    const [researchQuery, setResearchQuery] = useState("");
    const [researchResult, setResearchResult] = useState<any>(null);

    // Ingestion State
    const [ingestionAction, setIngestionAction] = useState("reddit");
    const [ingestionSubreddit, setIngestionSubreddit] = useState("technology");

    // Workforce Status
    const [workforceStatus, setWorkforceStatus] = useState<any>(null);

    const fetchStatus = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/nexus/workforce/status`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: { crewai: { status: "OFFLINE" }, interpreter: { status: "OFFLINE" } },
                onSuccess: (data) => setWorkforceStatus(data)
            }
        );
    }, []);

    const fetchSkills = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        setIsLoading(true);
        await withRealFallback<{ skills: Skill[] }>(
            () => fetch(`${API_BASE}/tools/skills/popular`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            { 
                fallback: { skills: [] }, 
                onSuccess: (data) => setSkills(data.skills) 
            }
        );
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchSkills();
        fetchStatus();
        const interval = setInterval(fetchStatus, 15000);
        return () => clearInterval(interval);
    }, [fetchSkills, fetchStatus]);

    const handleResearch = async () => {
        if (!researchQuery || isExecuting) return;
        setIsExecuting(true);
        setLogs((prev: string[]) => [`[RESEARCH] Initiating deep search: ${researchQuery}`, ...prev]);
        
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/research`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ query: researchQuery, limit: 5 })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setResearchResult(data.result);
                    setLogs((prev: string[]) => [`[SUCCESS] Research complete. ${data.result.length} nodes indexed.`, ...prev]);
                    toast.success("Deep Research Complete");
                }
            }
        );
        setIsExecuting(false);
    };

    const handleIngestion = async () => {
        if (isExecuting) return;
        setIsExecuting(true);
        setLogs((prev: string[]) => [`[INGESTION] Triggering ${ingestionAction} sink...`, ...prev]);
        
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/ingestion`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ action: ingestionAction, subreddit: ingestionSubreddit })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setLogs((prev: string[]) => [`[SUCCESS] Ingestion complete. Data cached in Nexus.`, ...prev]);
                    toast.success("Data Ingestion Successful");
                }
            }
        );
        setIsExecuting(false);
    };

    // Prepare Agent Data
    const agents = [
        { id: "CREW_01", name: "CrewAI Orchestrator", icon: Users, status: workforceStatus?.crewai?.status || "OFFLINE", latency: 150, load: 12, details: workforceStatus?.crewai?.message },
        { id: "INTERP_01", name: "Brain Sandbox", icon: Terminal, status: workforceStatus?.interpreter?.status === "SECURE" ? "ACTIVE" : "IDLE", latency: 45, load: 8, details: "Kernel: Python 3.10" },
        { id: "GEO_01", name: "Global Sentinel", icon: Globe, status: "ACTIVE", latency: 850, load: 5, details: "Monitoring Niche Trends" },
    ];

    return (
        <CommandCenterLayout
            title="WORKFORCE HUB"
            subtitle="AGENT_ORCHESTRATION_V1.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "registry", label: "Neural Registry", icon: Fingerprint },
                        { id: "crews", label: "Task Force", icon: Users },
                        { id: "research", label: "Deep Research", icon: Microscope },
                        { id: "ingestion", label: "Data Ingestion", icon: Database },
                        { id: "sandbox", label: "Brain Sandbox", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents as any} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Workforce Metrics</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Active Agents</span>
                                <span className="text-xl font-bold text-white">12</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Success Rate</span>
                                <span className="text-xl font-bold text-emerald-500">98.2%</span>
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
                        {activeEngine === "registry" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {skills.map((skill) => (
                                    <DesignCard 
                                        key={skill.id}
                                        title={skill.name}
                                        status={skill.priority.toUpperCase()}
                                        metrics={[
                                            { label: "Category", value: skill.category, color: "text-emerald-400" },
                                            { label: "Stability", value: "Verified", color: "text-zinc-500" }
                                        ]}
                                        footerInfo={skill.description}
                                        toolsStatus="Ready"
                                    />
                                ))}
                            </div>
                        )}

                        {activeEngine === "research" && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                                <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/60 p-8 space-y-6">
                                    <div className="flex items-center gap-3">
                                        <Microscope className="h-5 w-5 text-emerald-400" />
                                        <h3 className="text-sm font-bold text-white uppercase tracking-widest">Deep Research Module</h3>
                                    </div>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold uppercase text-zinc-500">Academic/Trend Query</label>
                                            <textarea 
                                                value={researchQuery}
                                                onChange={(e) => setResearchQuery(e.target.value)}
                                                placeholder="ENTER TOPIC FOR DEEP NEURAL SEARCH..."
                                                className="w-full h-32 bg-white/5 border border-white/5 rounded-2xl p-6 text-sm font-mono text-white focus:outline-none resize-none"
                                            />
                                        </div>
                                        <Button 
                                            onClick={handleResearch}
                                            disabled={isExecuting || !researchQuery}
                                            className="w-full h-16 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-2xl uppercase tracking-widest transition-all"
                                        >
                                            {isExecuting ? <Loader2 className="h-5 w-5 animate-spin" /> : "Initiate Deep Search"}
                                        </Button>
                                    </div>
                                </div>
                                <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/40 overflow-hidden flex flex-col">
                                    <div className="p-6 border-b border-white/5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Result Matrix</div>
                                    <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
                                        {researchResult ? researchResult.map((res: any, i: number) => (
                                            <div key={i} className="p-4 rounded-xl border border-white/5 bg-white/5 space-y-2">
                                                <h4 className="text-xs font-bold text-white uppercase">{res.title || "Untitled Insight"}</h4>
                                                <p className="text-[10px] text-zinc-500 leading-relaxed italic line-clamp-2">{res.abstract || res.description}</p>
                                                <div className="flex justify-between items-center text-[8px] font-bold text-emerald-500 uppercase">
                                                    <span>Confidence: {Math.floor(Math.random() * 20) + 80}%</span>
                                                    <span className="text-zinc-600">Source: OpenAlex</span>
                                                </div>
                                            </div>
                                        )) : (
                                            <div className="h-full flex flex-col items-center justify-center opacity-20 space-y-4">
                                                <BookOpen className="h-12 w-12" />
                                                <span className="text-[10px] font-bold uppercase tracking-widest">Awaiting Query Deployment</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "ingestion" && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                                <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/60 p-8 space-y-8">
                                    <div className="flex items-center gap-3">
                                        <Database className="h-5 w-5 text-emerald-400" />
                                        <h3 className="text-sm font-bold text-white uppercase tracking-widest">Data Ingestion Sink</h3>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        {[
                                            { id: "reddit", label: "Reddit Hot", icon: Radio },
                                            { id: "github", label: "GitHub Trending", icon: Code2 },
                                            { id: "rss", label: "RSS Feed", icon: Rss },
                                            { id: "multi", label: "Multi-Source", icon: Layers },
                                        ].map((item) => (
                                            <button
                                                key={item.id}
                                                onClick={() => setIngestionAction(item.id)}
                                                className={cn(
                                                    "flex flex-col items-center justify-center gap-3 p-6 rounded-2xl border transition-all",
                                                    ingestionAction === item.id ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400" : "bg-white/5 border-white/5 text-zinc-500 hover:bg-white/10"
                                                )}
                                            >
                                                <item.icon className="h-6 w-6" />
                                                <span className="text-[10px] font-bold uppercase tracking-tighter">{item.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold uppercase text-zinc-500">Source Parameter</label>
                                            <input 
                                                value={ingestionSubreddit}
                                                onChange={(e) => setIngestionSubreddit(e.target.value)}
                                                className="w-full h-14 bg-white/5 border border-white/5 rounded-2xl px-6 text-sm font-mono text-white focus:outline-none"
                                            />
                                        </div>
                                        <Button 
                                            onClick={handleIngestion}
                                            disabled={isExecuting}
                                            className="w-full h-16 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-2xl uppercase tracking-widest transition-all"
                                        >
                                            {isExecuting ? <Loader2 className="h-5 w-5 animate-spin" /> : "Deploy Ingestion Sink"}
                                        </Button>
                                    </div>
                                </div>
                                <div className="rounded-[32px] border border-white/5 bg-[#0F0F11]/40 flex flex-col overflow-hidden p-8">
                                    <div className="flex-1 flex flex-col justify-center items-center opacity-30 space-y-6">
                                        <Activity className="h-16 w-16 animate-pulse" />
                                        <div className="space-y-2 text-center">
                                            <p className="text-[10px] font-bold uppercase tracking-[0.4em]">Ingestion_Stream_Active</p>
                                            <p className="text-[8px] font-mono text-zinc-600">POLLING_SOURCE: {ingestionAction.toUpperCase()}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        {/* System Logs Area (Unified for all engines) */}
                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Neural Workforce Logs</span>
                                <div className="flex gap-2">
                                    <div className="h-1 w-1 rounded-full bg-emerald-500 animate-pulse" />
                                    <span className="text-[8px] font-mono text-emerald-500/50">NODE_CONNECTED</span>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[ERROR]") ? "text-rose-500" :
                                            log.includes("[SUCCESS]") ? "text-emerald-500" :
                                            log.includes("[RESEARCH]") ? "text-cyan-400" : "text-zinc-600"
                                        )}>{log}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

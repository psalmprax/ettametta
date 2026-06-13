"use client";

import React, { useState, useEffect, useCallback } from "react";
import { 
    Brain, 
    Database, 
    Search, 
    UploadCloud, 
    Zap, 
    Activity, 
    ShieldCheck, 
    Loader2, 
    CheckCircle2,
    FileText,
    Globe,
    Terminal,
    ArrowUpRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { withRealFallback } from "@/lib/real_first_utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";
import { useTelemetry } from "@/context/TelemetryContext";

interface KnowledgeStats {
    total_documents: number;
    total_embeddings: number;
    index_size_bytes: number;
    last_updated: string;
    status: string;
}

interface SearchResult {
    content: string;
    score: number;
    metadata: any;
}

export default function KnowledgePage() {
    const { agents, logs: systemLogs, pulse } = useTelemetry();
    
    const [stats, setStats] = useState<KnowledgeStats | null>(null);
    const [_isLoadingStats, setIsLoadingStats] = useState(true);
    const [activeTab, setActiveTab] = useState("overview"); // overview, ingest, query, logs

    // Ingestion State
    const [ingestText, setIngestText] = useState("");
    const [isIngesting, setIsIngesting] = useState(false);
    const [ingestMetadata, setIngestMetadata] = useState("{\"source\": \"manual_entry\"}");

    // Query State
    const [queryText, setQueryText] = useState("");
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [isQuerying, setIsQuerying] = useState(false);

    const fetchStats = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        setIsLoadingStats(true);
        await withRealFallback<KnowledgeStats | null>((signal) => fetch(`${API_BASE}/knowledge/stats`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setStats(data);
                    setIsLoadingStats(false);
                },
                onFallback: () => setIsLoadingStats(false)
            }
        );
    }, []);

    useEffect(() => {
        fetchStats();
    }, [fetchStats]);

    const handleIngest = async () => {
        if (!ingestText.trim()) return;
        setIsIngesting(true);
        
        const token = await getAuthToken();
        if (!token) return;

        let meta = {};
        try {
            meta = JSON.parse(ingestMetadata);
        } catch (e) {
            toast.error("Invalid Metadata JSON");
            setIsIngesting(false);
            return;
        }

        await withRealFallback((signal) => fetch(`${API_BASE}/knowledge/ingest`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    text: ingestText,
                    metadata: meta
                })
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Knowledge Fragment Ingested Successfully");
                    setIngestText("");
                    fetchStats();
                },
                onFallback: (err) => toast.error(`Ingestion Failed: ${err.message}`)
            }
        );
        setIsIngesting(false);
    };

    const handleQuery = async () => {
        if (!queryText.trim()) return;
        setIsQuerying(true);
        
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<SearchResult[]>((signal) => fetch(`${API_BASE}/knowledge/query`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    text: queryText,
                    limit: 5
                })
            }),
            {
                fallback: [],
                onSuccess: (data) => {
                    setSearchResults(Array.isArray(data) ? data : []);
                    if (data.length === 0) toast.info("No relevant context found");
                }
            }
        );
        setIsQuerying(false);
    };

    return (
        <CommandCenterLayout
            title="KNOWLEDGE BASE"
            subtitle="RAG_ORCHESTRATOR_V1.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "overview", label: "Neural Overview", icon: Activity },
                        { id: "ingest", label: "Context Ingestion", icon: UploadCloud },
                        { id: "query", label: "Semantic Query", icon: Search },
                        { id: "logs", label: "System Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeTab === item.id ? "bg-primary/10 text-primary border border-primary/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeTab === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(var(--primary-rgb),0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-6">
                        <div className="flex items-center justify-between">
                            <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Index Health</h4>
                            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                        </div>
                        <div className="space-y-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-tighter">Vector Nodes</span>
                                <div className="flex items-center justify-between">
                                    <span className="text-xl font-bold text-white">{stats?.total_embeddings || 0}</span>
                                    <span className="text-[10px] text-zinc-500 font-mono">{(stats?.index_size_bytes || 0) / 1024} KB</span>
                                </div>
                                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                    <motion.div initial={{ width: 0 }} animate={{ width: "65%" }} className="h-full bg-primary" />
                                </div>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-tighter">Query Latency</span>
                                <span className="text-xl font-bold text-cyan-400">{pulse?.latency_ms || 24} <span className="text-[10px] text-zinc-500">MS</span></span>
                            </div>
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeTab === "overview" && (
                            <div className="space-y-8">
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                    {[
                                        { label: "Total Docs", value: stats?.total_documents || 0, icon: FileText, color: "text-blue-400" },
                                        { label: "Embeddings", value: stats?.total_embeddings || 0, icon: Database, color: "text-cyan-400" },
                                        { label: "Index Status", value: stats?.status || "NOMINAL", icon: ShieldCheck, color: "text-emerald-400" },
                                        { label: "Providers", value: "Local NumPy", icon: Brain, color: "text-violet-400" },
                                    ].map((stat, i) => (
                                        <div key={i} className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 backdrop-blur-xl flex flex-col gap-4 group hover:border-primary/20 transition-all">
                                            <div className="flex items-center justify-between">
                                                <div className={cn("p-3 rounded-xl bg-white/5", stat.color)}>
                                                    <stat.icon className="h-5 w-5" />
                                                </div>
                                                <ArrowUpRight className="h-4 w-4 text-zinc-700 group-hover:text-white transition-colors" />
                                            </div>
                                            <div className="space-y-1">
                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{stat.label}</span>
                                                <p className="text-2xl font-bold text-white">{stat.value}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                    <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col justify-between group">
                                        <div className="space-y-6">
                                            <h3 className="text-xl font-bold text-white uppercase tracking-tighter">Global Context Synchronizer</h3>
                                            <p className="text-sm text-zinc-500 leading-relaxed">
                                                The Knowledge Base acts as the long-term memory for all autonomous agents. 
                                                Every ingested fragment increases the neural reasoning capability of the system.
                                            </p>
                                        </div>
                                        <div className="mt-8 flex gap-4">
                                            <Button onClick={() => setActiveTab("ingest")} className="flex-1 bg-primary text-black font-bold h-12 rounded-xl">Initialize Ingestion</Button>
                                            <Button onClick={() => setActiveTab("query")} variant="outline" className="flex-1 border-white/10 text-white h-12 rounded-xl">Neural Search</Button>
                                        </div>
                                    </div>
                                    <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 relative overflow-hidden flex items-center justify-center">
                                        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at center, var(--primary) 0%, transparent 70%)' }} />
                                        <Brain className="h-32 w-32 text-primary animate-pulse opacity-20" />
                                        <div className="absolute bottom-8 text-center space-y-1">
                                            <span className="text-[10px] font-mono text-primary/50 uppercase">RAG_ORCHESTRATOR_ACTIVE</span>
                                            <p className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">Latency: {pulse?.latency_ms || 24}ms</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === "ingest" && (
                            <div className="flex-1 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 p-12 flex flex-col gap-8">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-1">
                                        <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Neural Ingestion Portal</h3>
                                        <p className="text-xs text-zinc-500 uppercase tracking-widest">Inject high-fidelity context into the memory cluster</p>
                                    </div>
                                    <div className="flex gap-4">
                                        <Button variant="outline" className="border-white/10 text-zinc-400 gap-2">
                                            <UploadCloud className="h-4 w-4" /> Bulk Upload
                                        </Button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 flex-1 min-h-0">
                                    <div className="lg:col-span-2 flex flex-col gap-6">
                                        <div className="flex-1 flex flex-col gap-4">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Context Fragment (Text)</label>
                                            <textarea 
                                                value={ingestText}
                                                onChange={(e) => setIngestText(e.target.value)}
                                                placeholder="Enter raw intelligence data, niche insights, or historical context..."
                                                className="flex-1 bg-white/5 border border-white/5 rounded-2xl p-8 text-zinc-300 font-mono text-sm focus:outline-none focus:border-primary/30 transition-all resize-none"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-8">
                                        <div className="space-y-4">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Metadata Registry (JSON)</label>
                                            <textarea 
                                                value={ingestMetadata}
                                                onChange={(e) => setIngestMetadata(e.target.value)}
                                                className="w-full h-32 bg-white/5 border border-white/5 rounded-2xl p-6 text-zinc-500 font-mono text-[10px] focus:outline-none focus:border-primary/30 transition-all"
                                            />
                                        </div>
                                        <div className="space-y-4">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">System Protocols</label>
                                            <div className="space-y-2">
                                                {[
                                                    "Vectorize Fragment",
                                                    "Cross-Reference Niche",
                                                    "Persistence Lock"
                                                ].map(p => (
                                                    <div key={p} className="flex items-center gap-3 p-3 rounded-xl bg-white/2 border border-white/2">
                                                        <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                                                        <span className="text-[10px] font-bold text-zinc-500 uppercase">{p}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <Button 
                                            onClick={handleIngest}
                                            disabled={isIngesting || !ingestText}
                                            className="w-full h-16 bg-primary text-black font-bold text-lg rounded-2xl shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]"
                                        >
                                            {isIngesting ? <Loader2 className="h-6 w-6 animate-spin" /> : "Commit to Neural Core"}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === "query" && (
                            <div className="flex-1 flex flex-col gap-8">
                                <div className="flex items-center gap-6 shrink-0">
                                    <div className="relative flex-1">
                                        <input
                                            type="text"
                                            placeholder="SEARCH_HISTORICAL_CONTEXT..."
                                            value={queryText}
                                            onChange={(e) => setQueryText(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleQuery()}
                                            className="w-full bg-[#0F0F11]/60 border border-white/5 rounded-2xl p-6 pl-14 text-white font-mono text-lg focus:outline-none focus:border-primary/50 backdrop-blur-xl"
                                        />
                                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
                                    </div>
                                    <Button 
                                        onClick={handleQuery} 
                                        disabled={isQuerying}
                                        className="h-20 px-10 bg-primary text-black font-bold text-lg rounded-2xl uppercase tracking-widest flex items-center gap-3"
                                    >
                                        {isQuerying ? (
                                            <>
                                                <Loader2 className="h-6 w-6 animate-spin" />
                                                Scanning...
                                            </>
                                        ) : (
                                            "Execute Search"
                                        )}
                                    </Button>
                                </div>

                                <div className="flex-1 flex flex-col gap-6 overflow-hidden">
                                    <div className="flex items-center justify-between shrink-0">
                                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.3em]">Neural Resonance Results</h4>
                                        <span className="text-[10px] font-mono text-zinc-700">{searchResults.length} Hits Found</span>
                                    </div>
                                    
                                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-6 pr-4">
                                        {searchResults.map((res, i) => (
                                            <motion.div 
                                                key={i}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: i * 0.1 }}
                                                className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6 hover:border-primary/20 transition-all group"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-4">
                                                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                                            <Zap className="h-5 w-5 text-primary" />
                                                        </div>
                                                        <div className="flex flex-col">
                                                            <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Similarity Match</span>
                                                            <span className="text-xl font-bold text-white">{(res.score * 100).toFixed(2)}%</span>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        {Object.entries(res.metadata || {}).map(([k, v]: [string, any]) => (
                                                            <span key={k} className="px-3 py-1 rounded-full bg-white/5 text-[8px] font-bold text-zinc-500 uppercase">{k}: {String(v)}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                                <p className="text-zinc-300 leading-relaxed font-mono text-sm border-l-2 border-primary/20 pl-6">
                                                    {res.content}
                                                </p>
                                            </motion.div>
                                        ))}
                                        {searchResults.length === 0 && !isQuerying && (
                                            <div className="h-full flex flex-col items-center justify-center opacity-10 gap-6 py-20">
                                                <Globe className="h-24 w-24" />
                                                <span className="text-xl font-black uppercase tracking-[1em]">Memory Cluster Awaiting Input</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Neural Memory Logs</h3>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-[9px] font-bold text-emerald-500 uppercase">Mem_Active</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {systemLogs.filter(l => l.module === "KNOWLEDGE").map((log, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className="text-primary font-bold tracking-widest uppercase text-[9px] px-2 py-0.5 rounded bg-primary/10">
                                                {log.level || "INFO"}
                                            </span>
                                            <span className="text-zinc-400 leading-relaxed">
                                                {log.message}
                                            </span>
                                        </div>
                                    ))}
                                    {systemLogs.filter(l => l.module === "KNOWLEDGE").length === 0 && (
                                        <p className="text-zinc-600 italic">No specific memory logs recorded in this session.</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

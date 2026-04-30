"use client";

import React, { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/layout";
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
    ChevronRight,
    Loader2,
    CheckCircle2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { HighVelocityTicker } from "@/components/ui/HighVelocityTicker";

interface Skill {
    id: string;
    name: string;
    description: string;
    category: string;
    priority: "high" | "medium" | "low";
}

export default function WorkforceHub() {
    const [skills, setSkills] = useState<Skill[]>([]);
    const [categories, setCategories] = useState<string[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isExecuting, setIsExecuting] = useState(false);
    const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
    const [terminalInput, setTerminalInput] = useState("");
    
    // SEO State
    const [seoTopic, setSeoTopic] = useState("");
    const [seoResult, setSeoResult] = useState<any>(null);

    // Crew State
    const [crewTopic, setCrewTopic] = useState("");
    const [selectedCrew, setSelectedCrew] = useState<"content" | "affiliate">("content");

    const [workforceStatus, setWorkforceStatus] = useState<any>(null);
    const [isPollingStatus, setIsPollingStatus] = useState(false);

    const fetchStatus = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        setIsPollingStatus(true);
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/nexus/workforce/status`, { headers }),
            {
                fallback: { crewai: { status: "OFFLINE" }, interpreter: { status: "OFFLINE" } },
                onSuccess: (data) => setWorkforceStatus(data)
            }
        );
        setIsPollingStatus(false);
    }, []);

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        setIsLoading(true);
        await Promise.all([
            withRealFallback<{ skills: Skill[], categories?: string[] }>(
                () => fetch(`${API_BASE}/tools/skills/popular`, { headers }),
                { 
                    fallback: { skills: [] }, 
                    onSuccess: (data) => setSkills(data.skills) 
                }
            ),
            withRealFallback<{ categories: string[] }>(
                () => fetch(`${API_BASE}/tools/skills/categories`, { headers }),
                { 
                    fallback: { categories: [] }, 
                    onSuccess: (data) => setCategories(data.categories) 
                }
            )
        ]);
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchData();
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Poll every 30s
        return () => clearInterval(interval);
    }, [fetchData, fetchStatus]);

    const handleRunCrew = async () => {
        if (!crewTopic || isExecuting) return;
        setIsExecuting(true);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/crew/run`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({
                    crew_type: selectedCrew,
                    topic: crewTopic
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    toast.success("Crew Task Complete", { description: "Autonomous team has finished the objective." });
                    setTerminalOutput(prev => [`[CREW_${selectedCrew.toUpperCase()}] Objective: ${crewTopic}`, `[RESULT] ${JSON.stringify(data.result).slice(0, 500)}...`, ...prev]);
                },
                onFallback: (err) => toast.error("Crew Failed", { description: err.message })
            }
        );
        setIsExecuting(false);
    };

    const handleExecuteCode = async () => {
        if (!terminalInput || isExecuting) return;
        const code = terminalInput;
        setTerminalInput("");
        setIsExecuting(true);
        setTerminalOutput(prev => [`> ${code}`, ...prev]);

        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/interpreter/execute`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ code })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setTerminalOutput(prev => [`[OUT] ${data.output || "Execution successful"}`, ...prev]);
                },
                onFallback: (err) => setTerminalOutput(prev => [`[ERR] ${err.message}`, ...prev])
            }
        );
        setIsExecuting(false);
    };

    const handleGenerateSEO = async () => {
        if (!seoTopic || isExecuting) return;
        setIsExecuting(true);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/tools/seo/content`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}` 
                },
                body: JSON.stringify({ topic: seoTopic })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    setSeoResult(data);
                    toast.success("SEO Assets Generated");
                },
                onFallback: (err) => toast.error("SEO Generation Failed")
            }
        );
        setIsExecuting(false);
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                
                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    <HighVelocityTicker />

                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                        <div className="space-y-6">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 120 }}
                                className="h-1 bg-purple-500 shadow-[0_0_20px_#d05bff]"
                            />
                            <div className="space-y-2">
                                <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none">
                                    Workforce <span className="text-hollow">&amp; Skills</span>
                                </h1>
                                <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3 uppercase tracking-widest">
                                    <Users className="h-3 w-3 text-purple-400 animate-pulse" />
                                    Autonomous Agentic Core // Active_Skills: {skills.length}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="surface-glass p-6 text-right border border-white/5">
                                <span className="font-data-mono text-[8px] text-zinc-600 uppercase block mb-1">Crew Status</span>
                                <span className={cn("text-xl font-bold tracking-tighter", isExecuting ? "text-purple-400 animate-pulse" : "text-white")}>
                                    {isExecuting ? "ACTIVE_TASK" : "STANDBY"}
                                </span>
                            </div>
                        </div>
                    </header>

                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12 items-start">
                        {/* SKILLS REGISTRY */}
                        <div className="xl:col-span-4 space-y-12">
                            <section className="surface-glass rim-light p-8 space-y-8">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-label-caps text-[10px] text-zinc-500 flex items-center gap-3 uppercase tracking-[0.2em]">
                                        <Zap className="h-4 w-4 text-purple-400" />
                                        Skills_Registry
                                    </h3>
                                    <div className="flex gap-2">
                                        <button className="h-6 w-6 rounded-md bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all">
                                            <Search className="h-3 w-3 text-zinc-600" />
                                        </button>
                                        <button className="h-6 w-6 rounded-md bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all">
                                            <Plus className="h-3 w-3 text-zinc-600" />
                                        </button>
                                    </div>
                                </div>

                                <div className="space-y-4 max-h-[500px] overflow-y-auto custom-scrollbar pr-2">
                                    {skills.map(skill => (
                                        <div 
                                            key={skill.id}
                                            className="p-6 bg-white/2 border border-white/5 hover:border-purple-500/30 transition-all group relative overflow-hidden"
                                        >
                                            <div className="flex justify-between items-start mb-3">
                                                <span className={cn(
                                                    "px-2 py-0.5 rounded text-[7px] font-bold uppercase tracking-widest",
                                                    skill.priority === "high" ? "bg-purple-500 text-white" : "bg-white/10 text-zinc-500"
                                                )}>
                                                    {skill.priority}_PRIORITY
                                                </span>
                                                <span className="text-[8px] font-bold text-zinc-700 uppercase tracking-widest">{skill.category}</span>
                                            </div>
                                            <h4 className="text-sm font-bold text-white mb-2 uppercase">{skill.name}</h4>
                                            <p className="text-[10px] text-zinc-500 leading-relaxed uppercase">{skill.description}</p>
                                        </div>
                                    ))}
                                </div>
                            </section>

                             <section className="surface-glass p-10 space-y-6 border border-white/5 bg-zinc-950/40">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-label-caps text-[10px] text-zinc-500 uppercase tracking-widest">Protocol_Health</h3>
                                    <button 
                                        onClick={fetchStatus} 
                                        disabled={isPollingStatus}
                                        className="text-zinc-600 hover:text-purple-400 transition-colors"
                                    >
                                        <RefreshCw className={cn("h-3 w-3", isPollingStatus && "animate-spin")} />
                                    </button>
                                </div>
                                <div className="space-y-6">
                                    <div className="flex items-center justify-between">
                                        <span className="font-data-mono text-[9px] text-zinc-600">CREWAI_ENGINE:</span>
                                        <span className={cn(
                                            "font-bold text-[10px]",
                                            workforceStatus?.crewai?.status === "ONLINE" ? "text-emerald-500" : "text-rose-500"
                                        )}>
                                            {workforceStatus?.crewai?.status || "PENDING..."}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="font-data-mono text-[9px] text-zinc-600">INTERPRETER_SANDBOX:</span>
                                        <span className={cn(
                                            "font-bold text-[10px]",
                                            workforceStatus?.interpreter?.status === "SECURE" ? "text-emerald-500" : "text-rose-500"
                                        )}>
                                            {workforceStatus?.interpreter?.status || "PENDING..."}
                                        </span>
                                    </div>
                                    <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden">
                                        <motion.div 
                                            initial={{ width: 0 }}
                                            animate={{ width: workforceStatus ? "100%" : "30%" }}
                                            className="h-full bg-purple-500 shadow-[0_0_15px_#d05bff]"
                                        />
                                    </div>
                                </div>
                            </section>
                        </div>

                        {/* OPERATION CENTER */}
                        <div className="xl:col-span-8 space-y-12">
                            {/* CREW LAUNCHER */}
                            <section className="surface-glass rim-light p-10 space-y-10 relative overflow-hidden">
                                <div className="absolute inset-0 scanline opacity-5" />
                                <div className="space-y-2">
                                    <span className="font-data-mono text-[10px] text-purple-400 uppercase tracking-[0.3em]">Workforce Orchestration</span>
                                    <h2 className="text-3xl font-bold text-white uppercase tracking-tighter">Crew_Deployment_Center</h2>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
                                    <div className="md:col-span-8 space-y-6">
                                        <div className="space-y-3">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Mission Objective</label>
                                            <input 
                                                type="text" 
                                                value={crewTopic}
                                                onChange={(e) => setCrewTopic(e.target.value)}
                                                placeholder="e.g. Research trending AI fashion niches..."
                                                className="w-full h-16 bg-white/2 border border-white/5 px-6 text-sm font-bold text-white focus:outline-none focus:border-purple-500/30 transition-all placeholder:text-zinc-800"
                                            />
                                        </div>
                                        <div className="flex gap-4">
                                            <button 
                                                onClick={() => setSelectedCrew("content")}
                                                className={cn(
                                                    "flex-1 h-14 flex items-center justify-center gap-3 border text-[10px] font-bold uppercase tracking-widest transition-all",
                                                    selectedCrew === "content" ? "bg-purple-500 text-white border-purple-500" : "bg-white/2 text-zinc-600 border-white/5"
                                                )}
                                            >
                                                <FileText className="h-4 w-4" /> Content Crew
                                            </button>
                                            <button 
                                                onClick={() => setSelectedCrew("affiliate")}
                                                className={cn(
                                                    "flex-1 h-14 flex items-center justify-center gap-3 border text-[10px] font-bold uppercase tracking-widest transition-all",
                                                    selectedCrew === "affiliate" ? "bg-purple-500 text-white border-purple-500" : "bg-white/2 text-zinc-600 border-white/5"
                                                )}
                                            >
                                                <Zap className="h-4 w-4" /> Affiliate Crew
                                            </button>
                                        </div>
                                    </div>
                                    <div className="md:col-span-4">
                                        <button 
                                            onClick={handleRunCrew}
                                            disabled={!crewTopic || isExecuting}
                                            className="w-full h-full bg-linear-to-br from-purple-600 to-purple-400 flex flex-col items-center justify-center gap-4 text-white hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 disabled:grayscale group"
                                        >
                                            {isExecuting ? <Loader2 className="h-8 w-8 animate-spin" /> : <Play className="h-8 w-8 fill-white group-hover:scale-125 transition-transform" />}
                                            <span className="text-[10px] font-bold uppercase tracking-[0.2em]">Launch_Crew</span>
                                        </button>
                                    </div>
                                </div>
                            </section>

                            {/* TERMINAL & SEO */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                {/* TERMINAL */}
                                <section className="surface-glass p-10 space-y-8 bg-black relative min-h-[400px] flex flex-col border border-white/10">
                                    <div className="flex items-center justify-between border-b border-white/5 pb-4">
                                        <h3 className="font-label-caps text-[10px] text-purple-400 flex items-center gap-3">
                                            <Terminal className="h-4 w-4" /> Interpreter_Sandbox
                                        </h3>
                                        <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                                    </div>

                                    <div className="flex-1 font-mono text-[11px] space-y-3 overflow-y-auto custom-scrollbar max-h-[250px] pr-4">
                                        {terminalOutput.map((line, i) => (
                                            <p key={i} className={cn(
                                                "break-all",
                                                line.startsWith(">") ? "text-cyan-400" : 
                                                line.startsWith("[ERR]") ? "text-rose-500" : 
                                                line.startsWith("[OUT]") ? "text-emerald-400" : "text-zinc-600"
                                            )}>
                                                {line}
                                            </p>
                                        ))}
                                        {terminalOutput.length === 0 && (
                                            <p className="text-zinc-800">ETTA_OS v4.1 Ready. Initializing sandbox...</p>
                                        )}
                                    </div>

                                    <div className="relative mt-4">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-purple-500 font-bold">$&gt;</div>
                                        <input 
                                            type="text" 
                                            value={terminalInput}
                                            onChange={(e) => setTerminalInput(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleExecuteCode()}
                                            placeholder="Execute Python code..."
                                            className="w-full h-12 bg-white/5 border border-white/10 pl-12 pr-4 text-xs font-mono text-white focus:outline-none focus:border-purple-500/50"
                                        />
                                    </div>
                                </section>

                                {/* SEO FACTORY */}
                                <section className="surface-glass rim-light p-10 space-y-8">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-2xl bg-white/2 flex items-center justify-center text-cyan-400 border border-white/5">
                                            <Globe className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-white uppercase tracking-tight">SEO_Factory</h3>
                                            <p className="text-[9px] font-medium text-zinc-600 uppercase tracking-widest">Optimized Content Generation</p>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <input 
                                            type="text" 
                                            value={seoTopic}
                                            onChange={(e) => setSeoTopic(e.target.value)}
                                            placeholder="Target Topic..."
                                            className="w-full h-14 bg-white/2 border border-white/5 px-6 text-xs font-bold text-white focus:outline-none"
                                        />
                                        <button 
                                            onClick={handleGenerateSEO}
                                            disabled={!seoTopic || isExecuting}
                                            className="w-full action-primary py-4 text-[10px] tracking-widest uppercase font-bold"
                                        >
                                            Synthesize_Assets
                                        </button>
                                        
                                        <AnimatePresence>
                                            {seoResult && (
                                                <motion.div 
                                                    initial={{ opacity: 0, scale: 0.9 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    className="p-6 bg-emerald-500/10 border border-emerald-500/20 space-y-4"
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                                        <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Generation Success</span>
                                                    </div>
                                                    <p className="text-[10px] text-zinc-400 leading-relaxed line-clamp-3">
                                                        {JSON.stringify(seoResult.data || seoResult)}
                                                    </p>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </section>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

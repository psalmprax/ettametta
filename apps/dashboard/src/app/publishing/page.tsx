"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
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
    ArrowRight,
    Unlink,
    Radar,
    Cpu,
    Target
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { motion, AnimatePresence } from "framer-motion";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";
import { PlatformLinkModal } from "@/components/ui/PlatformLinkModal";
import { ManualBroadcastModal } from "@/components/ui/ManualBroadcastModal";

const getPlatformIcon = (platform: string) => {
    if (platform?.toLowerCase().includes("youtube")) return Youtube;
    if (platform?.toLowerCase().includes("instagram")) return Instagram;
    if (platform?.toLowerCase().includes("twitter") || platform?.toLowerCase().includes("x")) return Twitter;
    return Share2;
};

export default function PublishingPage() {
    const [activeEngine, setActiveEngine] = useState("nodes");
    const [accounts, setAccounts] = useState<any[]>([]);
    const [history, setHistory] = useState<any[]>([]);
    const [jobs, setJobs] = useState<any[]>([]);
    const [isPlatformModalOpen, setIsPlatformModalOpen] = useState(false);
    const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
    const [isDeploying, setIsDeploying] = useState(false);
    const [accountToUnlink, setAccountToUnlink] = useState<any | null>(null);
    const [logs, setLogs] = useState<string[]>(["EGRESS_INITIALIZED", "SYNCHRONIZING_DISTRIBUTION_NODES"]);

    const handleUnlink = async (id: string) => {
        setIsDeploying(true);
        await withRealFallback(
            async () => {
                const token = await getAuthToken();
                if (!token) return;
                return fetch(`${API_BASE}/publish/account/${id}`, {
                    method: "DELETE",
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    setAccounts(prev => prev.filter(acc => acc.id !== id));
                    toast.success("Node Unlinked");
                    setLogs(prev => [`[DECOUPLE] Decoupled node: ${id}`, ...prev]);
                }
            }
        );
        setIsDeploying(false);
        setAccountToUnlink(null);
    };

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };
        
        await Promise.all([
            withRealFallback<any>(
                () => fetch(`${API_BASE}/publish/accounts`, { headers }),
                { fallback: [], onSuccess: (data) => setAccounts(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/publish/history`, { headers }),
                { fallback: [], onSuccess: (data) => setHistory(data) }
            ),
            withRealFallback<any>(
                () => fetch(`${API_BASE}/publish/jobs`, { headers }),
                { fallback: [], onSuccess: (data) => setJobs(data) }
            )
        ]);
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleAutoBroadcast = async () => {
        const token = await getAuthToken();
        if (!token) return;
        setLogs(prev => [`[ACTION] Triggering Autonomous Broadcast Pattern...`, ...prev]);
        
        await withRealFallback(
            () => fetch(`${API_BASE}/publish/auto-broadcast`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Autonomous Broadcast Initiated");
                    setLogs(prev => [`[SUCCESS] Neural Pattern Propagated.`, ...prev]);
                }
            }
        );
    };

    // Prepare Agent Data
    const agents = [
        { id: "EGRESS_01", name: "Node Synchronizer", icon: Share2, status: "ACTIVE" as any, latency: 42, load: 8, details: "Syncing YT/Insta" },
        { id: "PROP_01", name: "Viral Injector", icon: Target, status: "ACTIVE" as any, latency: 120, load: 22, details: "Injecting Metadata" },
        { id: "AUTH_01", name: "Security Gate", icon: ShieldCheck, status: "IDLE" as any, latency: 1, load: 0, details: "Verified" },
    ];

    return (
        <CommandCenterLayout
            title="EGRESS HUB"
            subtitle="GLOBAL_DISTRIBUTION_MATRIX_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "nodes", label: "Egress Nodes", icon: Share2 },
                        { id: "jobs", label: "Egress Jobs", icon: Database },
                        { id: "matrix", label: "Global Matrix", icon: Globe },
                        { id: "broadcast", label: "Manual Egress", icon: Radio },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Egress Stats</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Nodes</span>
                                <span className="text-xl font-bold text-white">{accounts.length}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[8px] text-zinc-600 font-bold uppercase">Active Jobs</span>
                                <span className="text-xl font-bold text-cyan-500">{jobs.length}</span>
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
                        {activeEngine === "nodes" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                                <button 
                                    onClick={() => setIsPlatformModalOpen(true)}
                                    className="h-full min-h-[220px] rounded-[32px] border border-dashed border-white/10 p-10 flex flex-col items-center justify-center gap-6 group hover:border-blue-400/30 transition-all bg-[#0F0F11]/50"
                                >
                                    <div className="h-16 w-16 rounded-full bg-white/5 border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                                        <Plus className="h-8 w-8 text-zinc-700 group-hover:text-blue-400" />
                                    </div>
                                    <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-[0.4em] group-hover:text-white transition-colors">Link Distribution Node</span>
                                </button>

                                {accounts.map((acc) => {
                                    const Icon = getPlatformIcon(acc.platform);
                                    return (
                                        <DesignCard 
                                            key={acc.id}
                                            title={acc.username}
                                            status="Connected"
                                            metrics={[
                                                { label: "Platform", value: acc.platform, color: "text-blue-400" },
                                                { label: "Stability", value: "Verified", color: "text-zinc-500" }
                                            ]}
                                            footerInfo={`Node ID: ${acc.id}`}
                                            toolsStatus="Stable Link"
                                            onClick={() => setAccountToUnlink(acc)}
                                        />
                                    );
                                })}
                            </div>
                        )}

                        {activeEngine === "jobs" && (
                            <div className="space-y-6 overflow-y-auto custom-scrollbar flex-1 p-1">
                                {jobs.length === 0 ? (
                                    <div className="h-full flex flex-col items-center justify-center opacity-30 grayscale space-y-4 py-40">
                                        <Database className="h-16 w-16" />
                                        <span className="text-[10px] font-bold uppercase tracking-[0.5em]">No active egress jobs</span>
                                    </div>
                                ) : (
                                    jobs.map((job) => (
                                        <div key={job.id} className="p-8 rounded-[32px] bg-[#0F0F11] border border-white/5 flex items-center justify-between group hover:border-blue-500/20 transition-all">
                                            <div className="flex items-center gap-8">
                                                <div className="h-16 w-16 rounded-2xl bg-blue-500/10 flex items-center justify-center">
                                                    <Radio className="h-8 w-8 text-blue-500" />
                                                </div>
                                                <div className="flex flex-col gap-1">
                                                    <span className="text-lg font-bold text-white uppercase tracking-tight">{job.id}</span>
                                                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-widest">{job.status} • {new Date(job.created_at).toLocaleTimeString()}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-6">
                                                <div className="flex flex-col items-end">
                                                    <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">Progress</span>
                                                    <span className="text-xl font-bold text-white">{job.progress || 0}%</span>
                                                </div>
                                                <Button variant="outline" className="border-white/5 hover:bg-rose-500/10 hover:text-rose-500">
                                                    <X className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {activeEngine === "broadcast" && (
                            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                                <div className="xl:col-span-1 p-10 rounded-[32px] bg-[#0F0F11] border border-white/5 space-y-8">
                                    <h3 className="text-xl font-bold text-white uppercase tracking-tight">Egress Control</h3>
                                    <div className="space-y-4">
                                        <Button 
                                            onClick={() => setIsDeployModalOpen(true)}
                                            className="w-full bg-blue-500 hover:bg-blue-400 text-black font-bold h-16 rounded-2xl gap-3 text-lg"
                                        >
                                            <Radio className="h-6 w-6" />
                                            Manual Broadcast
                                        </Button>
                                        <Button 
                                            onClick={handleAutoBroadcast}
                                            variant="outline"
                                            className="w-full border-blue-500/20 text-blue-400 hover:bg-blue-500/10 font-bold h-16 rounded-2xl gap-3 text-lg"
                                        >
                                            <Zap className="h-6 w-6" />
                                            Auto-Inject Pattern
                                        </Button>
                                    </div>
                                    <p className="text-[10px] text-zinc-600 leading-relaxed font-bold uppercase tracking-widest italic">
                                        Warning: Direct neural broadcast bypasses standard moderation filters.
                                    </p>
                                </div>
                                <div className="xl:col-span-2 space-y-8">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <DesignCard 
                                            title="Propagation Health"
                                            status="Nominal"
                                            metrics={[
                                                { label: "Success Rate", value: "99.4%", color: "text-emerald-400" },
                                                { label: "Latency", value: "85ms", color: "text-zinc-500" }
                                            ]}
                                            footerInfo="Global egress nodes are operational."
                                            toolsStatus="Optimal"
                                        />
                                        <DesignCard 
                                            title="Egress Load"
                                            status="Peak"
                                            metrics={[
                                                { label: "Throughput", value: "1.2 GB/s", color: "text-cyan-400" },
                                                { label: "Buffer", value: "24%", color: "text-zinc-500" }
                                            ]}
                                            footerInfo="Cluster 04 showing high velocity."
                                            toolsStatus="Live"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "matrix" && (
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 overflow-y-auto custom-scrollbar flex-1 p-1">
                                {history.length === 0 ? (
                                    <div className="col-span-full py-40 flex flex-col items-center justify-center space-y-6 opacity-30 grayscale">
                                        <Globe className="h-16 w-16" />
                                        <p className="text-[10px] font-bold uppercase tracking-[0.5em]">Global Matrix Standby</p>
                                    </div>
                                ) : (
                                    history.map((post) => (
                                        <DesignCard 
                                            key={post.id}
                                            title={post.title}
                                            status={post.platform}
                                            metrics={[
                                                { label: "Views", value: post.view_count || 0, progress: 85, color: "text-emerald-400" },
                                                { label: "Shares", value: post.shares || 0, progress: 60, color: "text-blue-400" }
                                            ]}
                                            footerInfo={`Published: ${new Date(post.published_at).toLocaleDateString()}`}
                                            toolsStatus="Live Feed"
                                        />
                                    ))
                                )}
                            </div>
                        )}

                        <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                            <div className="p-4 border-b border-white/5 flex items-center justify-between">
                                <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Engine Logs</span>
                                <span className="text-[8px] font-mono text-blue-500/50">SYSTEM_EGRESS_ACTIVE</span>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                                {logs.map((log, i) => (
                                    <div key={i} className="flex gap-4">
                                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                                        <span className={cn(
                                            log.includes("[ACTION]") ? "text-cyan-400" :
                                            log.includes("[SUCCESS]") ? "text-emerald-500" :
                                            log.includes("[DECOUPLE]") ? "text-rose-500" : "text-zinc-600"
                                        )}>{log}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>

            <PlatformLinkModal 
                isOpen={isPlatformModalOpen} 
                onClose={() => setIsPlatformModalOpen(false)} 
            />

            <ManualBroadcastModal 
                isOpen={isDeployModalOpen}
                onClose={() => setIsDeployModalOpen(false)}
                accounts={accounts}
                onSuccess={fetchData}
            />

            <ConfirmModal 
                isOpen={!!accountToUnlink}
                onClose={() => setAccountToUnlink(null)}
                onConfirm={() => accountToUnlink && handleUnlink(accountToUnlink.id)}
                title="Unlink Node"
                description={`Are you sure you want to decouple the @${accountToUnlink?.username} node?`}
                confirmText="Execute Decouple"
                cancelText="Maintain Connection"
                isLoading={isDeploying}
            />
        </CommandCenterLayout>
    );
}

"use client";

import React, { useState, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    Share2,
    Globe,
    Database,
    Clock,
    Radio,
    Terminal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { motion, AnimatePresence } from "framer-motion";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { PlatformLinkModal } from "@/components/ui/PlatformLinkModal";
import { ManualBroadcastModal } from "@/components/ui/ManualBroadcastModal";
import { MultiPublishModal } from "@/components/ui/MultiPublishModal";
import { useTelemetry } from "@/context/TelemetryContext";
import { PlatformList } from "./PlatformList";
import { PublishQueue } from "./PublishQueue";
import { PublishModal } from "./PublishModal";

type EngineTab = "nodes" | "jobs" | "matrix" | "scheduled" | "broadcast" | "logs";

const ENGINE_TABS = [
    { id: "nodes" as EngineTab, label: "Egress Nodes", icon: Share2 },
    { id: "jobs" as EngineTab, label: "Egress Jobs", icon: Database },
    { id: "matrix" as EngineTab, label: "Global Matrix", icon: Globe },
    { id: "scheduled" as EngineTab, label: "Scheduled Posts", icon: Clock },
    { id: "broadcast" as EngineTab, label: "Manual Egress", icon: Radio },
    { id: "logs" as EngineTab, label: "Engine Logs", icon: Terminal },
];

interface PublishingContentProps {
    rightPanel?: React.ReactNode;
    leftPanel?: React.ReactNode;
}

export default function PublishingContent({ rightPanel, leftPanel }: PublishingContentProps) {
    const { agents, logs: systemLogs, status, pulse: _pulse } = useTelemetry();
    const [activeEngine, setActiveEngine] = useState<EngineTab>("nodes");
    const [accounts, setAccounts] = useState<any[]>([]);
    const [history, setHistory] = useState<any[]>([]);
    const [jobs, setJobs] = useState<any[]>([]);
    const [isPlatformModalOpen, setIsPlatformModalOpen] = useState(false);
    const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
    const [isMultiPublishModalOpen, setIsMultiPublishModalOpen] = useState(false);
    const [isDeploying, setIsDeploying] = useState(false);
    const [accountToUnlink, setAccountToUnlink] = useState<any | null>(null);
    const [_isRetrying, setIsRetrying] = useState(false);
    const [scheduledPosts, setScheduledPosts] = useState<any[]>([]);
    const [suggestedTimes, setSuggestedTimes] = useState<any[]>([]);
    const [isCancellingSchedule, setIsCancellingSchedule] = useState<string | null>(null);
    const [actionLogs, setActionLogs] = useState<string[]>(["EGRESS_INITIALIZED", "SYNCHRONIZING_DISTRIBUTION_NODES"]);

    const handleUnlink = async (id: string) => {
        setIsDeploying(true);
        await withRealFallback(
            async (signal) => {
                const token = await getAuthToken();
                if (!token) return;
                return fetch(`${API_BASE}/publish/account/${id}`, {
                    method: "DELETE",
                    headers: { Authorization: `Bearer ${token}` },
                    signal
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    setAccounts(prev => prev.filter(acc => acc.id !== id));
                    toast.success("Node Unlinked");
                    setActionLogs((prev: string[]) => [`[DECOUPLE] Decoupled node: ${id}`, ...prev]);
                }
            }
        );
        setIsDeploying(false);
        setAccountToUnlink(null);
    };

    const handleRetryPublish = async (contentId: string) => {
        setIsRetrying(true);
        const token = await getAuthToken();
        if (!token) { setIsRetrying(false); return; }

        setActionLogs((prev: string[]) => [`[RETRY] Attempting to republish: ${contentId}...`, ...prev]);

        await withRealFallback((signal) => fetch(`${API_BASE}/publish/retry/${contentId}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Retry initiated — refreshing jobs");
                    setActionLogs((prev: string[]) => [`[SUCCESS] Retry dispatched for: ${contentId}`, ...prev]);
                    fetchData();
                },
                onFallback: (err) => {
                    toast.error(`Retry failed: ${err.message}`);
                    setActionLogs((prev: string[]) => [`[ERROR] Retry failed for ${contentId}: ${err.message}`, ...prev]);
                }
            }
        );
        setIsRetrying(false);
    };

    const handleCancelSchedule = async (scheduleId: string) => {
        setIsCancellingSchedule(scheduleId);
        const token = await getAuthToken();
        if (!token) { setIsCancellingSchedule(null); return; }

        setActionLogs((prev: string[]) => [`[SCHEDULE] Cancelling scheduled post: ${scheduleId}...`, ...prev]);

        await withRealFallback((signal) => fetch(`${API_BASE}/publish/schedule/${scheduleId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    setScheduledPosts(prev => prev.filter(p => p.id !== scheduleId));
                    toast.success("Scheduled post cancelled");
                    setActionLogs((prev: string[]) => [`[SCHEDULE] Post cancelled: ${scheduleId}`, ...prev]);
                },
                onFallback: (err) => {
                    toast.error(`Cancel failed: ${err.message}`);
                    setActionLogs((prev: string[]) => [`[ERROR] Cancel failed: ${scheduleId}: ${err.message}`, ...prev]);
                }
            }
        );
        setIsCancellingSchedule(null);
    };

    const handleAutoBroadcast = async () => {
        const token = await getAuthToken();
        if (!token) return;
        setActionLogs((prev: string[]) => [`[ACTION] Triggering Autonomous Broadcast Pattern...`, ...prev]);
        
        await withRealFallback((signal) => fetch(`${API_BASE}/publish/auto-broadcast`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Autonomous Broadcast Initiated");
                    setActionLogs((prev: string[]) => [`[SUCCESS] Neural Pattern Propagated.`, ...prev]);
                }
            }
        );
    };

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };
        
        await Promise.all([
            withRealFallback<any>((signal) => fetch(`${API_BASE}/publish/accounts`, { headers }),
                { fallback: [], onSuccess: (data) => setAccounts(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/publish/history`, { headers }),
                { fallback: [], onSuccess: (data) => setHistory(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/publish/jobs`, { headers }),
                { fallback: [], onSuccess: (data) => setJobs(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/publish/scheduled`, { headers }),
                { fallback: [], onSuccess: (data) => setScheduledPosts(data) }
            ),
            withRealFallback<any>((signal) => fetch(`${API_BASE}/publish/schedule/suggested-times?count=5`, { headers }),
                { fallback: [], onSuccess: (data) => setSuggestedTimes(data?.suggestions || []) }
            ),
        ]);
    }, []);

    const defaultLeftPanel = (
        <div className="space-y-1">
            {ENGINE_TABS.map((item) => (
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
    );

    const defaultRightPanel = (
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
    );

    return (
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
                        <PlatformList
                            accounts={accounts}
                            onOpenLinkModal={() => setIsPlatformModalOpen(true)}
                            onUnlinkAccount={setAccountToUnlink}
                        />
                    )}

                    {(activeEngine === "jobs" || activeEngine === "matrix" || activeEngine === "scheduled") && (
                        <PublishQueue
                            activeTab={activeEngine}
                            jobs={jobs}
                            history={history}
                            scheduledPosts={scheduledPosts}
                            suggestedTimes={suggestedTimes}
                            isCancellingSchedule={isCancellingSchedule}
                            onRetryPublish={handleRetryPublish}
                            onCancelSchedule={handleCancelSchedule}
                        />
                    )}

                    {activeEngine === "broadcast" && (
                        <PublishModal
                            activeTab="broadcast"
                            onOpenDeployModal={() => setIsDeployModalOpen(true)}
                            onOpenMultiPublishModal={() => setIsMultiPublishModalOpen(true)}
                            onAutoBroadcast={handleAutoBroadcast}
                        />
                    )}

                    <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                        <div className="p-4 border-b border-white/5 flex items-center justify-between">
                            <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Engine Logs</span>
                            <span className="text-[8px] font-mono text-blue-500/50">{status === "open" ? "LINK_ESTABLISHED" : "LINK_OFFLINE"}</span>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                            {[
                                ...actionLogs.map(msg => ({ level: "ACTION", message: msg, timestamp: Date.now() / 1000 })),
                                ...(Array.isArray(systemLogs) ? systemLogs.filter(l => l.module === "PUBLISH") : [])
                            ].sort((a, b) => b.timestamp - a.timestamp).map((log: any, i) => (
                                <div key={i} className="flex gap-4">
                                    <span className="text-zinc-800">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                    <span className={cn(
                                        log.level === "ACTION" ? "text-cyan-400" :
                                        log.level === "SUCCESS" ? "text-emerald-500" :
                                        log.level === "DECOUPLE" ? "text-rose-500" : "text-zinc-600"
                                    )}>{log.message}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            </AnimatePresence>

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

            <MultiPublishModal 
                isOpen={isMultiPublishModalOpen}
                onClose={() => setIsMultiPublishModalOpen(false)}
                onSuccess={() => { fetchData(); toast.success("Multi-platform publish initiated"); }}
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
        </div>
    );
}

"use client";

import React from "react";
import {
    Globe,
    RefreshCw,
    Database,
    Clock,
    Calendar,
    Trash2,
    Radio,
    Zap,
    Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

interface PublishQueueProps {
    activeTab: "jobs" | "matrix" | "scheduled";
    jobs: any[];
    history: any[];
    scheduledPosts: any[];
    suggestedTimes: any[];
    isCancellingSchedule: string | null;
    onRetryPublish: (contentId: string) => void;
    onCancelSchedule: (scheduleId: string) => void;
}

export function PublishQueue({
    activeTab,
    jobs,
    history,
    scheduledPosts,
    suggestedTimes,
    isCancellingSchedule,
    onRetryPublish,
    onCancelSchedule,
}: PublishQueueProps) {
    if (activeTab === "jobs") {
        return (
            <div className="space-y-6 overflow-y-auto custom-scrollbar flex-1 p-1">
                {jobs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center opacity-60 space-y-4 py-40">
                        <Database className="h-16 w-16 text-zinc-600" />
                        <span className="text-[10px] font-bold uppercase tracking-[0.5em] text-zinc-500">No active egress jobs</span>
                        <span className="text-[8px] text-zinc-700 font-mono uppercase tracking-widest">Egress jobs appear when content is being published</span>
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
                                {(job.status === "FAILED" || job.status === "PENDING_AUTH") && (
                                    <Button
                                        variant="outline"
                                        onClick={() => onRetryPublish(job.id)}
                                        className="border-amber-500/20 hover:bg-amber-500/10 hover:text-amber-400"
                                    >
                                        <RefreshCw className="h-4 w-4" />
                                    </Button>
                                )}
                                <Button variant="outline" className="border-white/5 hover:bg-rose-500/10 hover:text-rose-500">
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        );
    }

    if (activeTab === "scheduled") {
        return (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar flex-1 p-1">
                <div className="xl:col-span-2 space-y-6">
                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Upcoming Posts</h4>
                    {scheduledPosts.length === 0 ? (
                        <div className="py-24 flex flex-col items-center justify-center space-y-4 opacity-60">
                            <Clock className="h-16 w-16 text-zinc-600" />
                            <p className="text-[10px] font-bold uppercase tracking-[0.5em] text-zinc-500">No scheduled posts</p>
                            <span className="text-[8px] text-zinc-700 font-mono uppercase tracking-widest">Schedule a post from the Manual Broadcast tab</span>
                        </div>
                    ) : (
                        scheduledPosts.map((post) => (
                            <div key={post.id} className="p-6 rounded-[32px] bg-[#0F0F11] border border-white/5 flex items-center justify-between group hover:border-blue-500/20 transition-all">
                                <div className="flex items-center gap-6">
                                    <div className="h-14 w-14 rounded-2xl bg-cyan-500/10 flex items-center justify-center">
                                        <Calendar className="h-6 w-6 text-cyan-400" />
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <span className="text-sm font-bold text-white uppercase tracking-tight">{post.platform}</span>
                                        <span className="text-xs text-zinc-500 font-bold uppercase tracking-widest">
                                            {new Date(post.scheduled_time).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                            {post.engagement_prediction && (
                                                <span className="ml-3 text-emerald-500">Predicted: {Math.round(post.engagement_prediction * 100)}%</span>
                                            )}
                                        </span>
                                        <span className="text-[8px] text-zinc-600 font-mono">{post.video_path?.split('/').pop()}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={cn(
                                        "text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full",
                                        post.status === "PENDING" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                                        "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                    )}>
                                        {post.status}
                                    </span>
                                    <Button
                                        variant="outline"
                                        onClick={() => onCancelSchedule(post.id)}
                                        disabled={isCancellingSchedule === post.id}
                                        className="h-9 border-rose-500/20 text-rose-400 hover:bg-rose-500/10 text-[10px]"
                                    >
                                        {isCancellingSchedule === post.id ? (
                                            <Loader2 className="h-3 w-3 animate-spin" />
                                        ) : (
                                            <Trash2 className="h-3 w-3 mr-1" />
                                        )}
                                        Cancel
                                    </Button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
                <div className="xl:col-span-1 space-y-6">
                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">AI Suggested Times</h4>
                    {suggestedTimes.length === 0 ? (
                        <div className="p-6 rounded-[32px] bg-[#0F0F11] border border-white/5 flex flex-col items-center justify-center py-16 opacity-60">
                            <Calendar className="h-10 w-10 mb-3 text-zinc-600" />
                            <p className="text-[8px] font-bold uppercase tracking-[0.4em] text-zinc-500">No suggestions yet</p>
                            <span className="text-[7px] text-zinc-700 font-mono mt-2 uppercase tracking-widest">AI will suggest optimal posting times as you schedule</span>
                        </div>
                    ) : (
                        suggestedTimes.map((time: any, i: number) => (
                            <div key={i} className="p-6 rounded-[32px] bg-[#0F0F11] border border-white/5 flex items-center gap-4 group hover:border-emerald-500/20 transition-all">
                                <div className="h-12 w-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                                    <Zap className="h-5 w-5 text-emerald-400" />
                                </div>
                                <div className="flex flex-col gap-0.5">
                                    <span className="text-xs font-bold text-white uppercase tracking-tight">
                                        {time.day || `Window ${i + 1}`}
                                    </span>
                                    <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
                                        {time.time || time.suggested_time || "Optimal window"}
                                    </span>
                                    {time.score && (
                                        <span className="text-[8px] text-emerald-500 font-mono">Score: {Math.round(time.score * 100)}%</span>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        );
    }

    if (activeTab === "matrix") {
        return (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 overflow-y-auto custom-scrollbar flex-1 p-1">
                {history.length === 0 ? (
                    <div className="col-span-full py-40 flex flex-col items-center justify-center space-y-6 opacity-60">
                        <Globe className="h-16 w-16 text-zinc-600" />
                        <p className="text-[10px] font-bold uppercase tracking-[0.5em] text-zinc-500">Global Matrix Standby</p>
                        <span className="text-[8px] text-zinc-700 font-mono uppercase tracking-widest">Published content appears here once distributed</span>
                    </div>
                ) : (
                    history.map((post) => (
                        <div key={post.id} className="relative">
                            <DesignCard 
                                title={post.title}
                                status={post.platform}
                                metrics={[
                                    { label: "Views", value: post.view_count || 0, progress: 85, color: "text-emerald-400" },
                                    { label: "Shares", value: post.shares || 0, progress: 60, color: "text-blue-400" }
                                ]}
                                footerInfo={`Published: ${new Date(post.published_at).toLocaleDateString()}`}
                                toolsStatus="Live Feed"
                            />
                            {post.status === "PENDING_AUTH" && (
                                <div className="absolute top-4 right-4 flex gap-2">
                                    <Button
                                        variant="outline"
                                        onClick={() => onRetryPublish(post.id)}
                                        className="h-8 border-amber-500/20 text-amber-400 hover:bg-amber-500/10 text-[8px]"
                                    >
                                        <RefreshCw className="h-3 w-3 mr-1" /> Retry
                                    </Button>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        );
    }

    return null;
}

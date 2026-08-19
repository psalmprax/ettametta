"use client";

import React, { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { MoreVertical, CreditCard, RotateCcw, Share2, Activity, Zap } from "lucide-react";

/** Module-internal — do not consume from outside. */
interface DesignCardProps {
  readonly title: string;
  readonly status?: "Current" | "Active" | "Inactive" | "Offline" | "Live Polling" | "Syncing" | "Completed" | "Scheduled" | "Nominal" | "Optimized" | "Archived" | "Story" | (string & {});
  readonly metrics: {
    label: string;
    value: string | number;
    progress?: number; // 0-100
    color?: string;
  }[];
  readonly footerInfo?: string;
  readonly toolsStatus?: "Online" | "Offline" | "Live Polling" | "Syncing" | "Archived" | (string & {});
  readonly onClick?: () => void;
  readonly actions?: ReactNode;
  readonly onRefresh?: () => void;
  readonly onDelete?: () => void;
  readonly onShare?: () => void;
  readonly onMore?: () => void;
  readonly credits?: number;
}

/** Module-internal — do not consume from outside. */
const POSITIVE_STATUSES = new Set(["Current", "Active", "Completed", "Optimized", "Story"]);
const PENDING_STATUSES = new Set(["Scheduled", "Syncing", "Live Polling", "Nominal"]);
const ONLINE_TOOLS = new Set(["Online", "Live Polling"]);

function resolveStatusTheme(status: string): string {
  if (POSITIVE_STATUSES.has(status)) return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
  if (PENDING_STATUSES.has(status)) return "bg-amber-500/10 text-amber-500 border-amber-500/20";
  if (status === "Archived") return "bg-zinc-800 text-zinc-500 border-zinc-700";
  return "bg-rose-500/10 text-rose-500 border-rose-500/20";
}

function resolveToolsStatusTheme(toolsStatus: string): { badge: string; dot: string } {
  if (ONLINE_TOOLS.has(toolsStatus)) {
    return {
      badge: "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
      dot: "bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]",
    };
  }
  if (toolsStatus === "Syncing") {
    return {
      badge: "bg-amber-500/10 border-amber-500/20 text-amber-500",
      dot: "bg-amber-500 animate-pulse shadow-[0_0_8px_#f59e0b]",
    };
  }
  if (toolsStatus === "Archived") {
    return { badge: "bg-zinc-800 border-zinc-700 text-zinc-500", dot: "bg-zinc-600" };
  }
  return { badge: "bg-rose-500/10 border-rose-500/20 text-rose-500", dot: "bg-rose-500 shadow-[0_0_8px_#ef4444]" };
}

function MetricsGrid({ metrics }: { readonly metrics: DesignCardProps["metrics"] }) {
  return (
    <div className="grid grid-cols-2 gap-4 mb-6 relative z-10 flex-grow">
      {metrics?.map((metric, i) => (
        <div key={i} className="space-y-2 p-2 rounded-lg bg-white/[0.02] border border-white/5 group-hover:bg-white/[0.04] transition-all">
          <div className="flex flex-col">
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">{metric.label}</span>
            <span className={cn("text-lg font-black tabular-nums tracking-tighter", metric.color || "text-emerald-500")}>
              {metric.value}
            </span>
          </div>
          {metric.progress !== undefined && (
            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${metric.progress}%` }}
                className={cn("h-full rounded-full", metric.color?.replace('text-', 'bg-') || "bg-emerald-500")}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function CardActions({ credits, onShare, onRefresh, onMore }: {
  readonly credits?: number;
  readonly onShare?: () => void;
  readonly onRefresh?: () => void;
  readonly onMore?: () => void;
}) {
  return (
    <div className="flex items-center gap-2 mb-6 relative z-10">
      <div className="bg-white/5 border border-white/10 rounded-lg p-1 flex items-center justify-between flex-1 mr-2 px-2 h-9">
        <div className="flex items-center gap-2">
          <CreditCard className="h-3.5 w-3.5 text-amber-500" />
          <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Credits</span>
        </div>
        <span className="text-xs font-mono font-black text-white tracking-widest tabular-nums">{credits?.toLocaleString() || "0"}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {onShare && (
          <button onClick={(e) => { e.stopPropagation(); onShare(); }} className="h-9 w-9 bg-white/5 hover:bg-white/10 rounded-lg flex items-center justify-center transition-all border border-white/10 text-zinc-400 hover:text-white group/btn">
            <Share2 className="h-4 w-4 group-hover/btn:scale-110 transition-transform" />
          </button>
        )}
        {onRefresh && (
          <button onClick={(e) => { e.stopPropagation(); onRefresh(); }} className="h-9 w-9 bg-white/5 hover:bg-white/10 rounded-lg flex items-center justify-center transition-all border border-white/10 text-zinc-400 hover:text-white group/btn">
            <RotateCcw className="h-4 w-4 group-hover/btn:rotate-180 transition-transform duration-500" />
          </button>
        )}
        {onMore && (
          <button onClick={(e) => { e.stopPropagation(); onMore(); }} className="h-9 w-9 bg-cyan-500/10 hover:bg-cyan-500/20 rounded-lg flex items-center justify-center transition-all border border-cyan-500/20 text-cyan-400 group/btn">
            <MoreVertical className="h-4 w-4 group-hover/btn:scale-110 transition-transform" />
          </button>
        )}
      </div>
    </div>
  );
}

function CardFooter({ footerInfo, toolsStatus }: { readonly footerInfo?: string; readonly toolsStatus: string }) {
  const theme = resolveToolsStatusTheme(toolsStatus);
  return (
    <div className="flex items-center justify-between pt-4 border-t border-white/5 relative z-10">
      <div className="flex items-center gap-2">
        <Zap className="h-3 w-3 text-zinc-600" />
        <span className="text-[8px] font-mono text-zinc-600 uppercase tracking-[0.2em] truncate">
          {footerInfo || "NEURAL_LINK_STABLE"}
        </span>
      </div>
      <div className={cn("flex items-center gap-1.5 px-3 py-1 rounded-full border text-[9px] font-black uppercase tracking-widest transition-all shrink-0", theme.badge)}>
        <div className={cn("h-1.5 w-1.5 rounded-full", theme.dot)} />
        {toolsStatus}
      </div>
    </div>
  );
}

export function DesignCard({
  title,
  status = "Active",
  metrics,
  footerInfo,
  toolsStatus = "Offline",
  onClick,
  onRefresh,
  onDelete,
  onShare,
  onMore,
  credits
}: DesignCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      whileHover={{ y: -4 }}
      animate={{ opacity: 1, scale: 1 }}
      onClick={onClick}
      className={cn(
        "group bg-[#0B0B0D] border border-white/5 hover:border-cyan-500/30 rounded-lg p-3 transition-all duration-500 relative overflow-hidden flex flex-col h-full shadow-2xl",
        onClick && "cursor-pointer active:scale-95"
      )}
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 blur-[60px] -mr-16 -mt-16 group-hover:bg-cyan-500/10 transition-all duration-700" />
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-violet-500/5 blur-[50px] -ml-12 -mb-12 group-hover:bg-violet-500/10 transition-all duration-700" />
      <div className="absolute inset-0 bg-linear-to-b from-transparent via-cyan-500/[0.03] to-transparent h-[200%] -translate-y-full group-hover:animate-scan-slow pointer-events-none opacity-0 group-hover:opacity-100" />

      <div className="flex items-start justify-between mb-6 relative z-10 gap-4">
        <div className="flex items-start gap-4 min-w-0">
          <div className="h-10 w-10 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center shrink-0 group-hover:border-cyan-500/30 transition-colors shadow-inner">
             <Activity className="h-5 w-5 text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="flex flex-col min-w-0">
            <h3 className="text-sm font-black tracking-tight text-white uppercase group-hover:text-cyan-400 transition-colors truncate">
              {title}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <div className="h-1 w-1 rounded-full bg-cyan-500/50" />
              <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">{footerInfo || "Telemetry Stream Active"}</span>
            </div>
          </div>
        </div>
        <span className={cn("shrink-0 px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-[0.2em] leading-none border", resolveStatusTheme(status))}>
          {status}
        </span>
      </div>

      <MetricsGrid metrics={metrics} />
      <CardActions credits={credits} onShare={onShare} onRefresh={onRefresh} onMore={onMore} />
      <CardFooter footerInfo={footerInfo} toolsStatus={toolsStatus} />

      <div className="absolute bottom-0 right-0 w-8 h-8 bg-white/2 translate-x-4 translate-y-4 rotate-45 group-hover:bg-cyan-500/20 transition-all duration-700" />
    </motion.div>
  );
}

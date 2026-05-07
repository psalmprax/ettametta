"use client";

import React, { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { CheckCircle2, MoreVertical, CreditCard, Trash2, RotateCcw, Share } from "lucide-react";

interface DesignCardProps {
  title: string;
  status?: "Current" | "Active" | "Inactive" | "Offline" | "Live Polling" | "Syncing" | "Completed" | "Scheduled" | "Nominal" | "Optimized" | "Archived" | "Story" | (string & {});
  metrics: {
    label: string;
    value: string | number;
    progress?: number; // 0-100
    color?: string;
  }[];
  footerInfo?: string;
  toolsStatus?: "Online" | "Offline" | "Live Polling" | "Syncing" | "Archived" | (string & {});
  onClick?: () => void;
  actions?: ReactNode;
  onRefresh?: () => void;
  onDelete?: () => void;
  onShare?: () => void;
  onMore?: () => void;
  credits?: number;
}

export function DesignCard({
  title,
  status = "Active",
  metrics,
  footerInfo,
  toolsStatus = "Offline",
  onClick,
  actions,
  onRefresh,
  onDelete,
  onShare,
  onMore,
  credits
}: DesignCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      onClick={onClick}
      className={cn(
        "group bg-[#0F0F11] border border-white/5 hover:border-cyan-500/30 rounded-[20px] p-4 sm:p-5 transition-all duration-300 relative overflow-hidden flex flex-col h-full",
        onClick && "cursor-pointer active:scale-95"
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      
      {/* Card Header */}
      <div className="flex items-center justify-between mb-4 relative z-10 gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-5 w-5 bg-white/10 rounded flex items-center justify-center shrink-0">
             <div className="h-2.5 w-2.5 border-2 border-white rounded-sm" />
          </div>
          <h3 className="text-base sm:text-lg font-bold tracking-tight text-slate-200 truncate">
            {title}
          </h3>
        </div>
        
        <span className={cn(
          "shrink-0 px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-wider whitespace-nowrap",
          (status === "Current" || status === "Active" || status === "Completed" || status === "Optimized" || status === "Story") ? "bg-emerald-500/10 text-emerald-500" :
          (status === "Scheduled" || status === "Syncing" || status === "Live Polling" || status === "Nominal") ? "bg-amber-500/10 text-amber-500" :
          (status === "Archived") ? "bg-slate-500/10 text-slate-500" :
          "bg-slate-800 text-slate-400"
        )}>
          {status}
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-y-3 gap-x-3 mb-4 relative z-10 flex-grow">
        {metrics?.map((metric, i) => (
          <div key={i} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold text-slate-400 truncate pr-2">{metric.label}</span>
              <span className={cn("text-[10px] sm:text-xs font-bold whitespace-nowrap", metric.color || "text-emerald-500")}>
                {metric.value}
              </span>
            </div>
            {metric.progress !== undefined && (
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
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

      {/* Credits/Value Section */}
      <div className="bg-black/20 border border-white/5 rounded-xl p-2 flex items-center justify-between mb-3 relative z-10">
        <div className="flex items-center gap-2">
          <CreditCard className="h-3 w-3 text-amber-500" />
          <span className="text-[10px] font-bold text-slate-300">Credits</span>
        </div>
        <span className="text-xs font-mono font-bold text-white tracking-widest">{credits?.toLocaleString() || "0"}</span>
      </div>

      {/* Action Overlay */}
      <div className="flex items-center gap-2 mt-auto mb-3 relative z-10">
        {onMore && (
          <button 
            onClick={(e) => { e.stopPropagation(); onMore(); }}
            className="h-8 w-8 bg-white/5 hover:bg-cyan-500/10 rounded-xl flex items-center justify-center transition-all border border-white/5 text-cyan-400 hover:text-cyan-300 hover:border-cyan-500/30 active:scale-90"
          >
            <motion.div whileHover={{ scale: 1.1 }}><MoreVertical className="h-3.5 w-3.5" /></motion.div>
          </button>
        )}
        {onRefresh && (
          <button 
            onClick={(e) => { e.stopPropagation(); onRefresh(); }}
            className="h-8 w-8 bg-white/5 hover:bg-white/10 rounded-xl flex items-center justify-center transition-all border border-white/5 text-slate-400 hover:text-white hover:border-white/20 active:scale-90"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        )}
        {onShare && (
          <button 
            onClick={(e) => { e.stopPropagation(); onShare(); }}
            className="h-8 w-8 bg-white/5 hover:bg-white/10 rounded-xl flex items-center justify-center transition-all border border-white/5 text-slate-400 hover:text-white hover:border-white/20 active:scale-90"
          >
            <Share className="h-3.5 w-3.5" />
          </button>
        )}
        {onDelete && (
          <button 
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="h-8 w-8 bg-rose-500/10 hover:bg-rose-500/20 rounded-xl flex items-center justify-center transition-all border border-rose-500/10 text-rose-400 hover:text-rose-300 active:scale-90 ml-auto"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between pt-4 border-t border-white/5 relative z-10">
        <span className="text-[8px] font-mono text-slate-600 uppercase tracking-widest truncate mr-2">
          {footerInfo || new Date().toLocaleString()}
        </span>
        
        <div className={cn(
          "flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[8px] font-bold transition-all shrink-0",
          (toolsStatus === "Online" || toolsStatus === "Live Polling") ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : 
          toolsStatus === "Syncing" ? "bg-amber-500/10 border-amber-500/20 text-amber-500" :
          toolsStatus === "Archived" ? "bg-zinc-800 border-zinc-700 text-zinc-500" :
          "bg-rose-500/10 border-rose-500/20 text-rose-500"
        )}>
          <div className={cn("h-1.5 w-1.5 rounded-full", (toolsStatus === "Online" || toolsStatus === "Live Polling") ? "bg-emerald-500 animate-pulse" : toolsStatus === "Syncing" ? "bg-amber-500 animate-pulse" : toolsStatus === "Archived" ? "bg-zinc-600" : "bg-rose-500")} />
          Tools: {toolsStatus}
        </div>
      </div>
    </motion.div>
  );
}

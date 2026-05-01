"use client";

import React, { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { CheckCircle2, MoreVertical, CreditCard, Trash2, RotateCcw, Share } from "lucide-react";

interface DesignCardProps {
  title: string;
  status?: "Current" | "Active" | "Inactive" | "Offline" | "Live Polling" | "Syncing" | "Completed" | "Scheduled" | "Nominal" | "Optimized";
  metrics: {
    label: string;
    value: string | number;
    progress?: number; // 0-100
    color?: string;
  }[];
  footerInfo?: string;
  toolsStatus?: "Online" | "Offline" | "Live Polling" | "Syncing" | "Archived";
  onClick?: () => void;
  actions?: ReactNode;
}

export function DesignCard({
  title,
  status = "Active",
  metrics,
  footerInfo,
  toolsStatus = "Offline",
  onClick,
  actions
}: DesignCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      onClick={onClick}
      className={cn(
        "group bg-[#0F0F11] border border-white/5 hover:border-cyan-500/30 rounded-[32px] p-8 transition-all duration-300 relative overflow-hidden",
        onClick && "cursor-pointer active:scale-95"
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      
      {/* Card Header */}
      <div className="flex items-start justify-between mb-8 relative z-10">
        <div className="flex items-center gap-4">
          <div className="h-6 w-6 bg-white/10 rounded flex items-center justify-center shrink-0">
             <div className="h-3 w-3 border-2 border-white rounded-sm" />
          </div>
          <h3 className="text-xl font-bold tracking-tight text-slate-200 truncate max-w-[200px]">
            {title}
          </h3>
        </div>
        
        <span className={cn(
          "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider",
          (status === "Current" || status === "Active" || status === "Completed" || status === "Optimized") ? "bg-emerald-500/10 text-emerald-500" :
          (status === "Scheduled" || status === "Syncing" || status === "Live Polling" || status === "Nominal") ? "bg-amber-500/10 text-amber-500" :
          "bg-slate-800 text-slate-400"
        )}>
          {status}
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-y-6 gap-x-12 mb-10 relative z-10">
        {metrics.map((metric, i) => (
          <div key={i} className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-400">{metric.label}</span>
              <span className={cn("text-sm font-bold", metric.color || "text-emerald-500")}>
                {metric.value}
              </span>
            </div>
            {metric.progress !== undefined && (
              <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${metric.progress}%` }}
                  className={cn("h-full rounded-full", metric.color?.replace('text-', 'bg-') || "bg-emerald-500")}
                />
              </div>
            )}
            {metric.progress === undefined && (
               <div className="text-[11px] font-mono text-slate-600">1d 21h 15m</div>
            )}
          </div>
        ))}
      </div>

      {/* Credits/Value Section */}
      <div className="bg-black/20 border border-white/5 rounded-2xl p-4 flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <CreditCard className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-bold text-slate-300">Credits</span>
        </div>
        <span className="text-lg font-mono font-bold text-white tracking-widest">1,000</span>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between pt-6 border-t border-white/5 relative z-10">
        <span className="text-[10px] font-mono text-slate-600 uppercase tracking-widest">
          {footerInfo || "05/01/2026, 02:39 PM"}
        </span>
        
        <div className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-bold transition-all",
          (toolsStatus === "Online" || toolsStatus === "Live Polling") ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : 
          toolsStatus === "Syncing" ? "bg-amber-500/10 border-amber-500/20 text-amber-500" :
          toolsStatus === "Archived" ? "bg-zinc-800 border-zinc-700 text-zinc-500" :
          "bg-rose-500/10 border-rose-500/20 text-rose-500"
        )}>
          <div className={cn("h-1.5 w-1.5 rounded-full", (toolsStatus === "Online" || toolsStatus === "Live Polling") ? "bg-emerald-500 animate-pulse" : toolsStatus === "Syncing" ? "bg-amber-500 animate-pulse" : toolsStatus === "Archived" ? "bg-zinc-600" : "bg-rose-500")} />
          Tools: {toolsStatus}
        </div>
      </div>

      {/* Action Overlay (Optional) */}
      <div className="flex items-center gap-2 mt-6 relative z-10">
        <button className="h-10 w-10 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center transition-all border border-white/5 text-cyan-400">
          <motion.div whileHover={{ scale: 1.1 }}><MoreVertical className="h-4 w-4" /></motion.div>
        </button>
        <button className="h-10 w-10 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center transition-all border border-white/5 text-slate-400">
          <RotateCcw className="h-4 w-4" />
        </button>
        <button className="h-10 w-10 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center transition-all border border-white/5 text-slate-400">
          <Share className="h-4 w-4" />
        </button>
        <button className="h-10 w-10 bg-rose-500/10 hover:bg-rose-500/20 rounded-2xl flex items-center justify-center transition-all border border-rose-500/10 text-rose-400 ml-auto">
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  );
}

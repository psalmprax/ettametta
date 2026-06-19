"use client";

import React, { ReactNode } from "react";
import DashboardLayout from "@/components/layout";
import { cn } from "@/lib/utils";
import { Search, Filter, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";

/** Module-internal — do not consume from outside. */
interface Tab {
  id: string;
  label: string;
  icon?: any;
}

/** Module-internal — do not consume from outside. */
interface DashboardPageLayoutProps {
  readonly title: string;
  readonly subtitle?: string;
  readonly tabs?: Tab[];
  readonly activeTab?: string;
  readonly onTabChange?: (tabId: string) => void;
  readonly actions?: ReactNode;
  readonly children: ReactNode;
  readonly showSearch?: boolean;
  readonly searchPlaceholder?: string;
}

export default function DashboardPageLayout({
  title,
  subtitle,
  tabs = [],
  activeTab,
  onTabChange,
  actions,
  children,
  showSearch = true,
  searchPlaceholder = "Search...",
}: DashboardPageLayoutProps) {
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-[#0A0A0B] text-white font-sans selection:bg-cyan-500/30">
        {/* Top Navigation Bar */}
        <div className="border-b border-white/5 bg-[#0F0F11]/50 backdrop-blur-xl sticky top-0 z-30">
          <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-8 h-full">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => onTabChange?.(tab.id)}
                  className={cn(
                    "flex items-center gap-2 h-full px-4 border-b-2 transition-all relative group",
                    activeTab === tab.id
                      ? "border-cyan-500 text-cyan-400 bg-cyan-500/5"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  )}
                >
                  {tab.icon && <tab.icon className={cn("h-4 w-4", activeTab === tab.id ? "text-cyan-400" : "text-slate-500")} />}
                  <span className="text-sm font-semibold tracking-tight">{tab.label}</span>
                </button>
              ))}
            </div>
            
            <div className="flex items-center gap-4">
              {actions}
            </div>
          </div>
        </div>

        <div className="max-w-[1600px] mx-auto px-6 py-8">
          {/* Header Section */}
          <div className="mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">{title}</h1>
            {subtitle && <p className="text-slate-500 text-sm font-medium">{subtitle}</p>}
          </div>

          {/* Action Toolbar */}
          <div className="bg-[#0F0F11] border border-white/5 rounded-2xl p-4 mb-8 flex flex-wrap items-center gap-4">
            {showSearch && (
              <div className="relative flex-1 min-w-[300px]">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder={searchPlaceholder}
                  className="w-full bg-black/40 border border-white/10 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition-all"
                />
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" className="bg-white/5 hover:bg-white/10 text-slate-300 gap-2 border border-white/5">
                <Filter className="h-4 w-4" />
                Hide Data
              </Button>
              <Button variant="primary" size="sm" className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold gap-2 rounded-xl px-6">
                <Plus className="h-4 w-4" />
                Add
              </Button>
              <Button variant="ghost" size="sm" className="bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5">
                <RefreshCw className="h-4 w-4" />
              </Button>
              <div className="h-8 w-px bg-white/10 mx-2" />
              <Button variant="ghost" size="sm" className="bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5">
                Import
              </Button>
              <Button variant="ghost" size="sm" className="bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5">
                Export
              </Button>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="relative z-10">
            {children}
          </div>
        </div>

        {/* Floating Footer */}
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-black/40 backdrop-blur-2xl border border-white/10 rounded-full px-6 py-3 flex items-center gap-8 shadow-2xl z-40">
          <p className="text-xs font-medium text-slate-400">Enjoying this? Give us a ⭐!</p>
          <div className="flex items-center gap-3">
             <button className="bg-[#FFD700] hover:bg-[#FFC700] text-black px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center gap-2">
               <span>⭐</span> Star
             </button>
             <button className="bg-white/5 hover:bg-white/10 text-white px-4 py-1.5 rounded-full text-xs font-bold border border-white/10 transition-all flex items-center gap-2">
               <span>💬</span> Feedback
             </button>
             <button className="bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 px-4 py-1.5 rounded-full text-xs font-bold border border-violet-500/30 transition-all flex items-center gap-2">
               <span>☕</span> Sponsor
             </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

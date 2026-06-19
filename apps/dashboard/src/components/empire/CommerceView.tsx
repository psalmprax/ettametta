"use client";

import React from "react";
import { ShoppingBag, Package, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

/** Module-internal — do not consume from outside. */
interface Props {
    commerceStatus: any;
    onSync: () => void;
    onSyncToast: () => void;
}

/**
 * Commerce tab — Store Sync (left) + Reverse Monetization (right).
 */
export default function CommerceView({ commerceStatus, onSync, onSyncToast }: Props) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-3">
                        <ShoppingBag className="h-5 w-5 text-emerald-400" />
                        Store Sync
                    </h3>
                    <div className={cn("h-2 w-2 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)]", commerceStatus?.status === "success" ? "bg-emerald-500" : "bg-zinc-700")} />
                </div>
                <div className="space-y-4">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-zinc-500 uppercase font-bold tracking-widest text-[9px]">Platform</span>
                        <span className="text-white font-bold">{commerceStatus?.source || "None"}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-zinc-500 uppercase font-bold tracking-widest text-[9px]">Status</span>
                        <span className="text-white font-bold">{commerceStatus?.status || "Awaiting Sync"}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-zinc-500 uppercase font-bold tracking-widest text-[9px]">Products</span>
                        <span className="text-white font-bold">{commerceStatus?.sample_count || 0}</span>
                    </div>
                </div>
                <Button onClick={() => { onSyncToast(); onSync(); }}
                    className="w-full h-12 bg-white/5 hover:bg-white/10 text-white rounded-xl border border-white/10 uppercase tracking-widest text-[10px] font-bold">
                    Manual Refresh
                </Button>
            </div>

            <div className="xl:col-span-2 p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-3">
                        <Package className="h-5 w-5 text-indigo-400" />
                        Reverse Monetization
                    </h3>
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Trend → Merch</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                        <div className="aspect-square rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center relative group overflow-hidden">
                            <RefreshCw className="h-8 w-8 text-zinc-700 group-hover:rotate-180 transition-all duration-700" />
                            <div className="absolute inset-x-0 bottom-0 p-4 bg-linear-to-t from-black/80 to-transparent">
                                <p className="text-[10px] text-white font-bold text-center">Awaiting Trend Detection...</p>
                            </div>
                        </div>
                        <Button className="w-full h-12 bg-indigo-500 text-white font-bold rounded-xl uppercase tracking-widest text-[10px] hover:shadow-[0_0_20px_rgba(99,102,241,0.3)]">Scan Viral Design Opportunity</Button>
                    </div>
                    <div className="space-y-6">
                        <div className="p-5 rounded-2xl bg-white/5 border border-white/5 space-y-2">
                            <h5 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Design Logic</h5>
                            <p className="text-xs text-zinc-300 leading-relaxed italic">"Identify high-engagement typography from Motivation niche and map to heavyweight hoodies."</p>
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <div className="h-1.5 w-1.5 rounded-full bg-zinc-700" />
                                <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Auto-Design Neural Model</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="h-1.5 w-1.5 rounded-full bg-zinc-700" />
                                <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Print-on-Demand Egress</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

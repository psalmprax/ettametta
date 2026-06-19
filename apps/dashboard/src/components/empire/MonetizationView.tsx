"use client";

import React from "react";
import { Zap, MessageSquareQuote, Link as LinkIcon } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { formatLabel } from "@/lib/utils";

interface Props {
    affiliateLinks: any[];
}

/**
 * Monetization tab — Affiliate registry (left) + Promo Generator (right).
 */
export default function MonetizationView({ affiliateLinks }: Props) {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full min-h-0">
            <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col min-h-0">
                <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                        <Zap className="h-5 w-5 text-amber-500" />
                        Affiliate Registry
                    </h3>
                    <Button className="h-8 px-4 text-[10px] bg-white/5 hover:bg-white/10 text-white rounded-lg border border-white/10 uppercase tracking-widest font-bold">Add Link</Button>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
                    {affiliateLinks.map((link, i) => (
                        <div key={link.id || i} className="p-6 bg-white/5 border border-white/5 rounded-[24px] group hover:border-amber-500/30 transition-all flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                    <LinkIcon className="h-5 w-5 text-amber-500" />
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold text-white">{formatLabel(link.product_name)}</h4>
                                    <p className="text-[10px] text-zinc-500 font-medium">Niche: {formatLabel(link.niche)}</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-bold text-white">${link.commission || "0.00"}</div>
                                <div className="text-[10px] text-emerald-500 font-bold tracking-widest uppercase">{link.conversion_rate || "0.0"}% CR</div>
                            </div>
                        </div>
                    ))}
                    {affiliateLinks.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-20 opacity-20 gap-4">
                            <LinkIcon className="h-12 w-12" />
                            <p className="text-[10px] font-bold uppercase tracking-widest">No Active Links Found</p>
                        </div>
                    )}
                </div>
            </div>

            <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col min-h-0">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                    <MessageSquareQuote className="h-5 w-5 text-cyan-400" />
                    Promo Generator
                </h3>
                <div className="flex-1 space-y-6">
                    <div className="space-y-4">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Select Target Link</label>
                        <select className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-xs font-bold text-white outline-none">
                            {affiliateLinks.length > 0 ? (
                                affiliateLinks.map((link, i) => (
                                    <option key={link.id || i} value={link.product_name}>
                                        {formatLabel(link.product_name)} ({formatLabel(link.niche)})
                                    </option>
                                ))
                            ) : (
                                <>
                                    <option>Select Active Link</option>
                                    <option>Neural Optimizer v1 (Demo)</option>
                                    <option>Alpha Strategy Suite (Demo)</option>
                                </>
                            )}
                        </select>
                    </div>
                    <div className="space-y-4">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Context Script</label>
                        <textarea
                            className="w-full h-40 bg-white/5 border border-white/10 rounded-[24px] px-6 py-6 text-xs font-medium text-zinc-300 outline-none resize-none"
                            placeholder="Paste your video script here to optimize the call-to-action..."
                        />
                    </div>
                    <Button className="w-full h-14 bg-amber-500 text-black font-bold rounded-2xl uppercase tracking-widest text-xs hover:shadow-[0_0_20px_rgba(245,158,11,0.3)] transition-all">Generate Optimized CTA</Button>
                </div>
            </div>
        </div>
    );
}

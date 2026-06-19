"use client";

import React from "react";
import {
    Plus,
    Share2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DesignCard } from "@/components/ui/DesignCard";

const getPlatformIcon = (platform: string) => {
    if (platform?.toLowerCase().includes("youtube")) return "Youtube";
    if (platform?.toLowerCase().includes("instagram")) return "Instagram";
    if (platform?.toLowerCase().includes("twitter") || platform?.toLowerCase().includes("x")) return "Twitter";
    return "Share2";
};

interface PlatformListProps {
    accounts: any[];
    onOpenLinkModal: () => void;
    onUnlinkAccount: (account: any) => void;
}

export function PlatformList({ accounts, onOpenLinkModal, onUnlinkAccount }: PlatformListProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            <button 
                onClick={onOpenLinkModal}
                className="h-full min-h-[220px] rounded-[32px] border border-dashed border-white/10 p-10 flex flex-col items-center justify-center gap-6 group hover:border-blue-400/30 transition-all bg-[#0F0F11]/50"
            >
                <div className="h-16 w-16 rounded-full bg-white/5 border border-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Plus className="h-8 w-8 text-zinc-700 group-hover:text-blue-400" />
                </div>
                <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-[0.4em] group-hover:text-white transition-colors">Link Distribution Node</span>
            </button>

            {accounts.map((acc) => {
                const _Icon = getPlatformIcon(acc.platform);
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
                        onClick={() => onUnlinkAccount(acc)}
                    />
                );
            })}
        </div>
    );
}

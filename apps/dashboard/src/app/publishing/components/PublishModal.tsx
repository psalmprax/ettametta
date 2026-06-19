"use client";

import React from "react";
import {
    Globe,
    Radio,
    Zap,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { DesignCard } from "@/components/ui/DesignCard";

interface PublishModalProps {
    activeTab: "broadcast";
    onOpenDeployModal: () => void;
    onOpenMultiPublishModal: () => void;
    onAutoBroadcast: () => void;
}

export function PublishModal({
    activeTab,
    onOpenDeployModal,
    onOpenMultiPublishModal,
    onAutoBroadcast,
}: PublishModalProps) {
    if (activeTab !== "broadcast") return null;

    return (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-1 p-10 rounded-[32px] bg-[#0F0F11] border border-white/5 space-y-8">
                <h3 className="text-xl font-bold text-white uppercase tracking-tight">Egress Control</h3>
                <div className="space-y-4">
                    <Button 
                        onClick={onOpenDeployModal}
                        className="w-full bg-blue-500 hover:bg-blue-400 text-black font-bold h-16 rounded-2xl gap-3 text-lg"
                    >
                        <Radio className="h-6 w-6" />
                        Manual Broadcast
                    </Button>
                    <Button 
                        onClick={onAutoBroadcast}
                        variant="outline"
                        className="w-full border-blue-500/20 text-blue-400 hover:bg-blue-500/10 font-bold h-16 rounded-2xl gap-3 text-lg"
                    >
                        <Zap className="h-6 w-6" />
                        Auto-Inject Pattern
                    </Button>
                    <hr className="border-white/5" />
                    <Button 
                        onClick={onOpenMultiPublishModal}
                        className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-16 rounded-2xl gap-3 text-lg"
                    >
                        <Globe className="h-6 w-6" />
                        Publish to All Platforms
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
    );
}

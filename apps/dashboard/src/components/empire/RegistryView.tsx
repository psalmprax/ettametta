"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { DesignCard } from "@/components/ui/DesignCard";
import { formatLabel } from "@/lib/utils";

/** Module-internal — do not consume from outside. */
const NetworkMesh = dynamic(() => import("@/components/ui/NetworkMesh"), { ssr: false });

/** Module-internal — do not consume from outside. */
interface Props {
    networkData: { nodes: any[]; links: any[] };
    blueprints: any[];
    availableNiches: string[];
    pulse: any;
    onRefresh: () => void;
    onClone: () => void;
    onShare: (id: string) => void;
}

/**
 * Registry tab — Neural Strategy Mesh + Blueprint grid + clone modal.
 *
 * Owns its own `cloningNiche` + `isCloneModalOpen` UI state because they're
 * purely visual-side concerns. All data, intents, and share-side effects
 * are passed in as props from `EmpireContent`.
 */
export default function RegistryView({
    networkData,
    blueprints,
    availableNiches,
    pulse,
    onRefresh,
    onClone,
    onShare,
}: Props) {
    const [cloningNiche, setCloningNiche] = useState("");
    const [isCloneModalOpen, setIsCloneModalOpen] = useState(false);

    const openClone = () => {
        if (!cloningNiche) return;
        setIsCloneModalOpen(true);
    };

    return (
        <>
            <div className="space-y-8 h-full flex flex-col">
                <div className="flex-1 min-h-[400px] bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden relative">
                    <div className="absolute inset-0">
                        <NetworkMesh nodes={networkData?.nodes || []} links={networkData?.links || []} />
                    </div>
                    <div className="absolute top-8 left-8 p-6 bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl max-w-sm">
                        <h4 className="text-white font-bold uppercase tracking-widest text-xs">Neural Strategy Mesh</h4>
                        <p className="text-zinc-500 text-[10px] leading-relaxed italic">Visualizing cross-pollination of winning narrative patterns.</p>
                    </div>
                    <div className="absolute top-8 right-8 flex gap-4">
                        <select
                            value={cloningNiche}
                            onChange={(e) => setCloningNiche(e.target.value)}
                            className="bg-black/60 backdrop-blur-xl border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-white outline-none"
                        >
                            <option value="">SELECT_NICHE</option>
                            {Array.isArray(availableNiches) && availableNiches.map((n) => (
                                <option key={n} value={n}>{formatLabel(n)}</option>
                            ))}
                        </select>
                        <Button onClick={openClone} className="bg-amber-500 text-black font-bold h-10 px-6 rounded-xl">Clone Protocol</Button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 shrink-0 overflow-x-auto p-1">
                    {Array.isArray(blueprints) && blueprints.map((blueprint) => (
                        <DesignCard
                            key={blueprint.id || blueprint.niche}
                            title={blueprint.name || blueprint.niche}
                            status={blueprint.status || "ACTIVE"}
                            metrics={[
                                { label: "Success", value: `${((blueprint.avg_score || 0) * 100).toFixed(1)}%`, progress: (blueprint.avg_score || 0) * 100, color: "text-emerald-400" },
                                { label: "Reach", value: blueprint.total_views ? `${(blueprint.total_views / 1000).toFixed(0)}K` : "---", color: "text-cyan-400" },
                            ]}
                            footerInfo={`ID: ${(blueprint.id || blueprint.niche).slice(0, 8)}`}
                            toolsStatus="Synced"
                            credits={pulse?.credits || 0}
                            onRefresh={() => onRefresh()}
                            onMore={() => toast.info(`Inspecting strategy: ${blueprint.niche}`)}
                            onDelete={() => toast.error(`Purged Blueprint: ${blueprint.niche}`)}
                            onShare={() => onShare(blueprint.id || blueprint.niche)}
                        />
                    ))}
                </div>
            </div>

            <ConfirmModal
                isOpen={isCloneModalOpen}
                onClose={() => setIsCloneModalOpen(false)}
                onConfirm={() => { onClone(); setIsCloneModalOpen(false); }}
                title="Initialize Empire Protocol?"
                description={`Cloning neural strategy weights into the "${cloningNiche}" cluster will initiate autonomous synthesis. Proceed?`}
                confirmText="Execute Protocol"
                variant="primary"
            />
        </>
    );
}

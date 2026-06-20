"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { NexusNode } from "@/components/ui/NexusNode";
import { Blueprint, NexusJob } from "@/lib/types";

function getNodeCoords(idx: number, total: number) {
    let x = 15 + (idx / Math.max(total - 1, 1)) * 70;
    let y = 50;
    if (total >= 4) {
        if (idx === 0) { x = 15; y = 50; }
        else if (idx === 1) { x = 45; y = 25; }
        else if (idx === 2) { x = 45; y = 75; }
        else if (idx === 3) { x = 75; y = 50; }
        else if (idx >= 4) { x = 90; y = 50; }
    }
    return { x, y };
}

function getParentIndices(idx: number, total: number): number[] {
    if (total < 4) return [idx -  1];
    if (idx === 1) return [0];
    if (idx === 2) return [0];
    if (idx === 3) return [1, 2];
    if (idx === 4) return [3];
    return [idx - 1];
}

/** Module-internal — do not consume from outside. */
interface NexusJobDetailProps {
    activeBlueprint: Blueprint | null;
    activePipelineJob: NexusJob | null;
    selectedNodeIndex: number;
    onNodeSelect: (idx: number) => void;
}

export default function NexusJobDetail({
    activeBlueprint,
    activePipelineJob,
    selectedNodeIndex,
    onNodeSelect,
}: NexusJobDetailProps) {
    const listLength = activeBlueprint?.nodes?.length || 0;

    return (
        <div className="flex-1 min-h-[450px] rounded-[32px] bg-[#0F0F11]/40 border border-white/5 relative overflow-hidden group">
            <div className="absolute inset-0 architect-grid pointer-events-none opacity-40" />

            <div className="absolute inset-0 z-0 pointer-events-none">
                <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="glowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.6" />
                            <stop offset="50%" stopColor="#22d3ee" stopOpacity="1" />
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0.6" />
                        </linearGradient>
                        <filter id="glowFilter" x="-10%" y="-10%" width="120%" height="120%">
                            <feGaussianBlur stdDeviation="1.5" result="blur" />
                            <feMerge>
                                <feMergeNode in="blur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    {activeBlueprint?.nodes?.map((node, idx) => {
                        if (idx === 0) return null;
                        const parentIndices = getParentIndices(idx, listLength);

                        return parentIndices.map((parentIdx, pI) => {
                            const start = getNodeCoords(parentIdx, listLength);
                            const end = getNodeCoords(idx, listLength);
                            const isPathActive =
                                activePipelineJob?.status === "Active" &&
                                (selectedNodeIndex === idx || selectedNodeIndex === parentIdx);
                            const pathD = `M ${start.x} ${start.y} C ${(start.x + end.x) / 2} ${start.y}, ${(start.x + end.x) / 2} ${end.y}, ${end.x} ${end.y}`;

                            return (
                                <g key={`${parentIdx}-${idx}-${pI}`}>
                                    <path d={pathD} stroke="rgba(255,255,255,0.03)" strokeWidth="2.5" fill="none" />
                                    <path
                                        d={pathD}
                                        stroke="url(#glowGrad)"
                                        strokeWidth={isPathActive ? "2.5" : "1"}
                                        fill="none"
                                        filter="url(#glowFilter)"
                                        className={cn(
                                            "opacity-40 transition-all duration-500",
                                            isPathActive ? "opacity-100" : "opacity-20"
                                        )}
                                        strokeDasharray={isPathActive ? "4, 4" : undefined}
                                    />
                                </g>
                            );
                        });
                    })}
                </svg>
            </div>

            <div className="absolute inset-0 z-10">
                {activeBlueprint?.nodes?.map((node, idx) => {
                    const isProcessing = activePipelineJob?.status === "Active" && idx === selectedNodeIndex;
                    const isComplete = activePipelineJob?.status === "Completed" || idx < selectedNodeIndex;
                    const { x, y } = getNodeCoords(idx, listLength);

                    return (
                        <div
                            key={idx}
                            className="absolute"
                            style={{ left: `${x}%`, top: `${y}%`, transform: "translate(-50%, -50%)" }}
                        >
                            <NexusNode
                                type={node.type as any}
                                label={node.label}
                                description={node.desc}
                                status={isComplete ? "complete" : isProcessing ? "processing" : "pending"}
                                progress={isProcessing ? activePipelineJob.progress : undefined}
                                active={selectedNodeIndex === idx}
                                onClick={() => onNodeSelect(idx)}
                            />
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

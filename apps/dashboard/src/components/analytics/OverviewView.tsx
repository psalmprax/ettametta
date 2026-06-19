"use client";

import React from "react";
import { DesignCard } from "@/components/ui/DesignCard";

interface Props {
    metrics: {
        views: number;
        retention: number;
        engagement: number;
        velocity: string;
        engineLoad: string;
    };
}

/**
 * Intel-Overview tab — four KPI tiles (Net Reach, Retention, Viral Velocity,
 * Conversion).
 */
export default function OverviewView({ metrics }: Props) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 w-full">
            <DesignCard
                title="Net Reach"
                status="Nominal"
                metrics={[
                    { label: "Total Views", value: metrics.views >= 1000 ? `${(metrics.views / 1000).toFixed(1)}K` : metrics.views.toString(), progress: 85, color: "text-cyan-400" },
                    { label: "Growth", value: "+14.2%", color: "text-emerald-400" },
                ]}
                footerInfo="BASELINE: STABLE"
                toolsStatus="Online"
            />
            <DesignCard
                title="Retention"
                status="Optimized"
                metrics={[
                    { label: "Attention Decay", value: `${(metrics.retention * 100).toFixed(0)}%`, progress: metrics.retention * 100, color: "text-emerald-400" },
                    { label: "Stability", value: "Locked", color: "text-cyan-400" },
                ]}
                footerInfo="HOOK_EFFICIENCY: HIGH"
                toolsStatus="Online"
            />
            <DesignCard
                title="Viral Velocity"
                status="Current"
                metrics={[
                    { label: "Propagation", value: metrics.velocity, progress: metrics.velocity === "High" ? 95 : 60, color: "text-violet-400" },
                    { label: "Load", value: metrics.engineLoad, color: "text-slate-500" },
                ]}
                footerInfo="SYSTEM_PULSE: ACTIVE"
                toolsStatus="Online"
            />
            <DesignCard
                title="Conversion"
                status="Active"
                metrics={[
                    { label: "Engagement", value: `${(metrics.engagement * 100).toFixed(1)}%`, progress: metrics.engagement * 10, color: "text-amber-400" },
                    { label: "Success Rate", value: "98.2%", color: "text-emerald-400" },
                ]}
                footerInfo="NEURAL_CONVERSION_READY"
                toolsStatus="Online"
            />
        </div>
    );
}

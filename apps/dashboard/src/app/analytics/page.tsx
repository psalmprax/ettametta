"use client";

// fallow-ignore-next-line invalid-client-export
export const dynamic = "force-dynamic";

import React, { Suspense } from "react";
import { BarChart3, Activity, Cpu, Globe, Terminal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { CommandCenterSidenav, type SidenavItem } from "@/components/ui/CommandCenterSidenav";
import { useTelemetry } from "@/context/TelemetryContext";
import { useActiveEngineTab } from "@/hooks/useActiveEngineTab";
import { useActionLogStream } from "@/hooks/useActionLogStream";
import { useAnalyticsData } from "@/hooks/useAnalyticsData";

import OverviewView from "@/components/analytics/OverviewView";
import RetentionView from "@/components/analytics/RetentionView";
import PatternsView from "@/components/analytics/PatternsView";
import PropagationView from "@/components/analytics/PropagationView";
import AnalyticsLogsTab from "@/components/analytics/AnalyticsLogsTab";
import AnalyticsRightPanel from "@/components/analytics/AnalyticsRightPanel";

const ANALYTICS_NAV: SidenavItem[] = [
    { id: "overview", label: "Intel Overview", icon: BarChart3 },
    { id: "retention", label: "Attention Decay", icon: Activity },
    { id: "patterns", label: "Neural Patterns", icon: Cpu },
    { id: "propagation", label: "Global Pulse", icon: Globe },
    { id: "logs", label: "Telemetry Logs", icon: Terminal },
];

/**
 * Analytics orchestrator.
 *
 * Five tab views + right panel all live under
 * `apps/dashboard/src/components/analytics/`. The dynamic import for
 * `GlobalPulseGlobe` lives inside `PropagationView` (alongside its sole
 * consumer). View-models are derived here.
 */
function AnalyticsContent() {
    const { agents, status, pulse } = useTelemetry();
    const [activeEngine, setActiveEngine] = useActiveEngineTab("overview", "/analytics");
    const analytics = useAnalyticsData();
    const { displayLogs } = useActionLogStream("ANALYTICS", ["ANALYTICS_INITIALIZED", "SYNCHRONIZING_HISTORICAL_DATA"]);

    // View-models for the Propagation view + right panel — defaults applied here.
    const velocity = (pulse as any)?.metrics?.global_velocity ?? 1.2;
    const signal = (pulse as any)?.metrics?.signal_strength ?? 98.4;
    const activeNodes = (pulse as any)?.metrics?.active_nodes ?? 142;
    const views = analytics.metrics.views;
    const growthPct = "14.2";

    return (
        <CommandCenterLayout
            title="INTEL CORE"
            subtitle="PERFORMANCE_MATRIX_V4.2"
            leftPanel={
                <CommandCenterSidenav
                    items={ANALYTICS_NAV}
                    active={activeEngine}
                    onSelect={setActiveEngine}
                    activeClass="bg-violet-500/10 text-violet-400 border border-violet-500/20"
                    dotClass="bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.5)]"
                />
            }
            rightPanel={
                <AnalyticsRightPanel
                    agents={agents}
                    views={views}
                    growthPct={growthPct}
                />
            }
        >
            <div className={`p-3 sm:p-4 space-y-4 relative h-full flex flex-col`}>
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "overview" && <OverviewView metrics={analytics.metrics} />}
                        {activeEngine === "retention" && <RetentionView retentionData={analytics.metrics.retentionData} />}
                        {activeEngine === "patterns" && <PatternsView />}
                        {activeEngine === "propagation" && (
                            <PropagationView
                                pulse={pulse}
                                velocity={velocity}
                                signal={signal}
                                activeNodes={activeNodes}
                                pulseIntensityMultiplier={analytics.pulseIntensityMultiplier}
                                setPulseIntensityMultiplier={analytics.setPulseIntensityMultiplier}
                            />
                        )}
                        {activeEngine === "logs" && (
                            <AnalyticsLogsTab
                                logs={displayLogs.map((l) => ({ timestamp: l.timestamp, message: l.message }))}
                                status={status}
                            />
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function AnalyticsPage() {
    return (
        <Suspense fallback={null}>
            <AnalyticsContent />
        </Suspense>
    );
}

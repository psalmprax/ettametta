"use client";

import React, { Suspense } from "react";
import { Play, Layers, Sparkles, Radar, Terminal } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { CommandCenterSidenav, type SidenavItem } from "@/components/ui/CommandCenterSidenav";
import { useTelemetry } from "@/context/TelemetryContext";
import { useActiveEngineTab } from "@/hooks/useActiveEngineTab";
import { useActionLogStream } from "@/hooks/useActionLogStream";
import { useAutonomousData } from "@/hooks/useAutonomousData";

import LaunchView from "@/components/autonomous/LaunchView";
import LogicView from "@/components/autonomous/LogicView";
import OracleView from "@/components/autonomous/OracleView";
import MarketView from "@/components/autonomous/MarketView";
import AutonomousConsoleTab from "@/components/autonomous/AutonomousConsoleTab";
import AutonomousRightPanel from "@/components/autonomous/AutonomousRightPanel";
import CompactConsole from "@/components/autonomous/CompactConsole";

/** Module-internal — do not consume from outside. */
const AUTONOMOUS_NAV: SidenavItem[] = [
    { id: "launch", label: "Launch Control", icon: Play },
    { id: "logic", label: "Logic Flow", icon: Layers },
    { id: "oracle", label: "Insight Oracle", icon: Sparkles },
    { id: "market", label: "Market Pulse", icon: Radar },
    { id: "console", label: "System Console", icon: Terminal },
];

/**
 * Autonomous (Agent Zero) orchestrator.
 *
 * Five tab views + right panel + a `CompactConsole` sibling all live under
 * `apps/dashboard/src/components/autonomous/`. View-models are derived here.
 */
function AutonomousContent() {
    const { agents, status } = useTelemetry();
    const [activeEngine, setActiveEngine] = useActiveEngineTab("launch", "/autonomous");
    const auto = useAutonomousData();
    const { addLog, displayLogs } = useActionLogStream("AGENT_ZERO", [], true);

    const handleToggle = async () => {
        const action = auto.isRunning ? "stop" : "start";
        addLog(`[PROTOCOL] Sending ${action.toUpperCase()} signal to Agent Zero...`);
        const message = await auto.toggle(action);
        if (message) addLog(`[SUCCESS] ${message}`);
        toast.success(`Agent Zero ${action === 'start' ? 'Activated' : 'Halted'}`);
    };

    // View-models for right panel — formatted timestamp OR "PENDING".
    const nextRunLabel = auto.nextRun ? new Date(auto.nextRun * 1000).toLocaleTimeString() : "PENDING";

    return (
        <CommandCenterLayout
            title="AUTONOMOUS DIRECTOR"
            subtitle="AGENT_ZERO_V4.2"
            leftPanel={
                <CommandCenterSidenav
                    items={AUTONOMOUS_NAV}
                    active={activeEngine}
                    onSelect={setActiveEngine}
                />
            }
            rightPanel={
                <AutonomousRightPanel
                    agents={agents}
                    isRunning={auto.isRunning}
                    isProcessing={auto.isProcessing}
                    nextRunLabel={nextRunLabel}
                    onToggle={handleToggle}
                />
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={`flex-1 pr-4 space-y-10 ${activeEngine !== "console" ? "overflow-y-auto custom-scrollbar" : ""}`}
                    >
                        {activeEngine === "launch" && (
                            <LaunchView
                                isRunning={auto.isRunning}
                                currentStep={auto.currentStep}
                                insights={auto.insights}
                            />
                        )}
                        {activeEngine === "logic" && <LogicView />}
                        {activeEngine === "oracle" && <OracleView insights={auto.insights} />}
                        {activeEngine === "market" && <MarketView />}
                        {activeEngine === "console" && (
                            <AutonomousConsoleTab logs={displayLogs} status={status} />
                        )}
                    </motion.div>
                </AnimatePresence>

                {activeEngine !== "console" && (
                    <CompactConsole logs={displayLogs} status={status} />
                )}
            </div>
        </CommandCenterLayout>
    );
}

export default function AutonomousPage() {
    return (
        <Suspense fallback={null}>
            <AutonomousContent />
        </Suspense>
    );
}

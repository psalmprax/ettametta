"use client";

import React, { useState, Suspense } from "react";
import { ShieldCheck, Activity, ScanLine, Terminal } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { CommandCenterSidenav, type SidenavItem } from "@/components/ui/CommandCenterSidenav";
import { useTelemetry } from "@/context/TelemetryContext";
import { useActionLogStream } from "@/hooks/useActionLogStream";
import { useSecurityData, type SecurityEvent } from "@/hooks/useSecurityData";

import SecurityStatusView from "@/components/security/SecurityStatusView";
import SecurityEventsView from "@/components/security/SecurityEventsView";
import SecurityScanView from "@/components/security/SecurityScanView";
import SecurityLogsTab from "@/components/security/SecurityLogsTab";
import SecurityRightPanel from "@/components/security/SecurityRightPanel";

const SECURITY_NAV: SidenavItem[] = [
    { id: "status", label: "Security Status", icon: ShieldCheck },
    { id: "events", label: "Event Log", icon: Activity },
    { id: "scan", label: "Vulnerability Scan", icon: ScanLine },
    { id: "logs", label: "Engine Logs", icon: Terminal },
];

/**
 * Security orchestrator.
 *
 * The four Views + right panel live under `apps/dashboard/src/components/security/`.
 * All `securityStatus?.data?.X` chains (which produce TS2339 because the
 * `data` wrapped-shape isn't declared on `SecurityStatus`) live here, not
 * in the Views.
 */
function SecurityContent() {
    const { agents, status } = useTelemetry();
    const [activeEngine, setActiveEngine] = useState("status");
    const { securityStatus, securityEvents, scanResults, isScanning, runScan } = useSecurityData();
    const { displayLogs, addLog } = useActionLogStream("SECURITY", ["SECURITY_SENTINEL_INITIALIZED"]);

    const handleScan = async () => {
        addLog("[SCAN] Initiating full system integrity audit...");
        await runScan((score) => {
            addLog(`[SCAN] Audit complete — Score: ${score}/100`);
            scanResults.forEach((f) => addLog(`[FINDING] ${f}`));
            toast.success(`Audit complete — Score: ${score}/100`);
        });
    };

    // View-models — derivation kept here so the Views don't have to weave
    // through `securityStatus?.data?.X` themselves.
    // Note: `securityStatus?.data?.X` is intentionally NOT chained. The
    // legacy `data`-wrapper access triggered a TS2339 because `SecurityStatus`
    // doesn't declare a `data` field; falling through to the flat shape is
    // identical to the original runtime behaviour for non-legacy responses.
    const healthScore = securityStatus?.health_score ?? 0;
    const threatLevel = securityStatus?.threat_level ?? "NOMINAL";
    const recentThreats: SecurityEvent[] =
        (securityStatus?.recent_threats ?? securityEvents) ?? [];
    const threatBreakdown = securityStatus?.threat_breakdown ?? { low: 0, medium: 0, high: 0, critical: 0 };
    const systemIntegrity = securityStatus?.system_integrity;

    return (
        <CommandCenterLayout
            title="SECURITY SENTINEL"
            subtitle="THREAT_DETECTION_V3.0"
            leftPanel={
                <CommandCenterSidenav
                    items={SECURITY_NAV}
                    active={activeEngine}
                    onSelect={setActiveEngine}
                />
            }
            rightPanel={
                <SecurityRightPanel
                    agents={agents}
                    healthScore={healthScore}
                    threatLevel={threatLevel}
                    threatBreakdown={threatBreakdown}
                />
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "status" && (
                            <SecurityStatusView
                                agents={agents}
                                healthScore={healthScore}
                                threatLevel={threatLevel}
                                recentThreats={recentThreats}
                                threatBreakdown={threatBreakdown}
                                isScanning={isScanning}
                                onScan={handleScan}
                                systemIntegrity={systemIntegrity}
                            />
                        )}
                        {activeEngine === "events" && <SecurityEventsView events={securityEvents} />}
                        {activeEngine === "scan" && (
                            <SecurityScanView
                                scanResults={scanResults}
                                isScanning={isScanning}
                                onScan={handleScan}
                            />
                        )}
                        {activeEngine === "logs" && (
                            <SecurityLogsTab
                                logs={displayLogs}
                                isScanning={isScanning}
                            />
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function SecurityPage() {
    return (
        <Suspense fallback={null}>
            <SecurityContent />
        </Suspense>
    );
}

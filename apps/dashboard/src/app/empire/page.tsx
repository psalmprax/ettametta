"use client";

import React, { Suspense } from "react";
import { ShieldCheck, Zap, ShoppingBag, Database, Terminal } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { copyToClipboard } from "@/lib/utils";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { CommandCenterSidenav, type SidenavItem } from "@/components/ui/CommandCenterSidenav";
import { useTelemetry } from "@/context/TelemetryContext";
import { useActiveEngineTab } from "@/hooks/useActiveEngineTab";
import { useActionLogStream } from "@/hooks/useActionLogStream";
import { useEmpireData } from "@/hooks/useEmpireData";

import RegistryView from "@/components/empire/RegistryView";
import SentinelView from "@/components/empire/SentinelView";
import MonetizationView from "@/components/empire/MonetizationView";
import CommerceView from "@/components/empire/CommerceView";
import EmpireLogsTab from "@/components/empire/EmpireLogsTab";
import EmpireRightPanel from "@/components/empire/EmpireRightPanel";

const EMPIRE_NAV: SidenavItem[] = [
    { id: "registry", label: "Empire Registry", icon: Database },
    { id: "sentinel", label: "Algo Sentinel", icon: ShieldCheck },
    { id: "monetization", label: "Promo Hub", icon: Zap },
    { id: "commerce", label: "Commerce Matrix", icon: ShoppingBag },
    { id: "logs", label: "Registry Logs", icon: Terminal },
];

/**
 * Empire orchestrator — derives all view-models and dispatches to a single
 * child component for each tab. The five Views + right panel live under
 * `apps/dashboard/src/components/empire/`.
 *
 * View-models are derived here (not in the Views) so the optional-access
 * chains (`empire.revenueReport?.platforms ?? []`) never escape into JSX.
 */
function EmpireContent() {
    const { agents, status, pulse } = useTelemetry();
    const [activeEngine, setActiveEngine] = useActiveEngineTab("registry", "/empire");
    const empire = useEmpireData();
    const { addLog, displayLogs } = useActionLogStream("EMPIRE", ["EMPIRE_INITIALIZED", "SYNCHRONIZING_GLOBAL_NODES"]);

    const handleShareClipboard = async (txt: string) => {
        const ok = await copyToClipboard(txt);
        toast[ok ? "success" : "error"](
            ok ? "Strategy Blueprint Link Copied" : "Clipboard access not available"
        );
    };

    // ConfirmModal in RegistryView already collected cloningNiche; this
    // delegate just confirms intent to the user.
    const handleClone = () => {
        toast.info("Cloning initiated via modal.");
    };

    const handleSyncCommerce = () => empire.syncCommerce("General");

    // View-models for the right panel — defaults applied here, not in the panel.
    const totalRevenue = empire.revenueReport?.total_revenue ?? 0;
    const platforms = empire.revenueReport?.platforms ?? [];
    const totalRevenueFormatted = totalRevenue.toFixed(2);
    // Preserve the original visual: "+X% Daily Avg" when revenue exists,
    // "+8.4% Velocity" fallback when revenue is still loading. Single
    // formatted string keeps the right panel purely presentational.
    const dailyAvgLabel = totalRevenue
        ? `+${((totalRevenue / 30) * 100).toFixed(1)}% Daily Avg`
        : "+8.4% Velocity";
    const velocity = pulse?.metrics?.global_velocity ?? 1.5;
    const totalPublished = pulse?.real_stats?.total_published ?? 12;

    return (
        <CommandCenterLayout
            title="EMPIRE REGISTRY"
            subtitle="STRATEGIC_MONETIZATION_V3.0"
            leftPanel={
                <CommandCenterSidenav
                    items={EMPIRE_NAV}
                    active={activeEngine}
                    onSelect={setActiveEngine}
                    activeClass="bg-amber-500/10 text-amber-500 border border-amber-500/20"
                    dotClass="bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"
                />
            }
            rightPanel={
                <EmpireRightPanel
                    agents={agents}
                    totalRevenueFormatted={totalRevenueFormatted}
                    dailyAvgLabel={dailyAvgLabel}
                    platforms={platforms}
                    velocity={velocity}
                    totalPublished={totalPublished}
                />
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "registry" && (
                            <RegistryView
                                networkData={empire.networkData}
                                blueprints={empire.blueprints}
                                availableNiches={empire.availableNiches}
                                pulse={pulse}
                                onRefresh={() => addLog("[SYSTEM] Refreshing empire snapshot...")}
                                onClone={handleClone}
                                onShare={(id) => handleShareClipboard(`https://ettametta.ai/strategy/${id}`)}
                            />
                        )}
                        {activeEngine === "sentinel" && (
                            <SentinelView
                                sentinelStatus={empire.sentinelStatus}
                                pulse={pulse}
                                onShareClipboard={handleShareClipboard}
                                onRefresh={() => empire.refresh()}
                            />
                        )}
                        {activeEngine === "monetization" && (
                            <MonetizationView affiliateLinks={empire.affiliateLinks} />
                        )}
                        {activeEngine === "commerce" && (
                            <CommerceView
                                commerceStatus={empire.commerceStatus}
                                onSync={handleSyncCommerce}
                                onSyncToast={() => toast.info("Initializing Commerce Sync...")}
                            />
                        )}
                        {activeEngine === "logs" && (
                            <EmpireLogsTab logs={displayLogs} liveStatus={status} />
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function EmpirePage() {
    return (
        <Suspense fallback={null}>
            <EmpireContent />
        </Suspense>
    );
}

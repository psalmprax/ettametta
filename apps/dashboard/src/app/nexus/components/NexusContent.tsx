"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { useTelemetry } from "@/context/TelemetryContext";
import {
    Zap,
    Database,
    Network,
    Fingerprint,
    User,
    Mic2,
    Video,
    Bot,
    Users,
    Search,
    Terminal,
    PlusCircle,
    Loader2,
} from "lucide-react";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { CommandPod } from "@/components/ui/CommandPod";
import { Button } from "@/components/ui/Button";
import { AreaChartCustom } from "@/components/ui/ChartComponents";
import PreviewScenesModal from "@/components/ui/PreviewScenesModal";
import { BlueprintBuilder } from "@/components/ui/BlueprintBuilder";
import { NeuralCanvas } from "@/components/ui/NeuralCanvas";
import { useNexusData } from "@/hooks/useNexusData";
import NexusHeader from "./NexusHeader";
import NexusJobList, { NexusJobHistory } from "./NexusJobList";
import NexusControls from "./NexusControls";
import NexusJobDetail from "./NexusJobDetail";

export default function NexusContent() {
    const { logs: systemLogs, status } = useTelemetry();
    const data = useNexusData();

    const {
        activeEngine,
        setActiveEngine,
        credits,
        refreshCredits,
        niches,
        selectedNiche,
        setSelectedNiche,
        blueprints,
        activeBlueprint,
        setActiveBlueprint,
        nexusJobs,
        activePipelineJob,
        creationMode,
        setCreationMode,
        selectedNodeIndex,
        setSelectedNodeIndex,
        isLaunching,
        handleLaunchPipeline,
        isBlueprintBuilderOpen,
        setIsBlueprintBuilderOpen,
        isNeuralCanvasOpen,
        setIsNeuralCanvasOpen,
        editingBlueprint,
        setEditingBlueprint,
        capabilities,
        searchTerm,
        setSearchTerm,
        activeCategory,
        setActiveCategory,
        filteredCapabilities,
        availableCategories,
        deployingIds,
        handleDeployAgent,
        personas,
        actionLogs,
        sandboxTab,
        setSandboxTab,
        handleSandboxExecute,
        mockTelemetry,
        handlePreviewScenes,
        handleDeleteJob,
        handleSaveBlueprint,
        handleDeleteBlueprint,
        isPreviewModalOpen,
        setIsPreviewModalOpen,
        isLoadingPreview,
        previewJobId,
        previewScenes,
        previewJobStatus,
        swappedAssets,
        setSwappedAssets,
        activeSwapDrawerIndex,
        setActiveSwapDrawerIndex,
        selectedStylePreset,
        setSelectedStylePreset,
        colorTemp,
        setColorTemp,
        grainDensity,
        setGrainDensity,
        contrast,
        setContrast,
        kenBurnsSpeed,
        setKenBurnsSpeed,
    } = data;

    const { agents, pulse } = useTelemetry();

    const displayLogs = React.useMemo(() => {
        const logs = Array.isArray(systemLogs) ? systemLogs : [];
        return [
            ...actionLogs.map((msg) => ({
                type: "log",
                level: "ACTION",
                module: "NEXUS",
                message: msg,
                timestamp: Date.now() / 1000,
            })),
            ...logs,
        ].sort((a: any, b: any) => b.timestamp - a.timestamp);
    }, [actionLogs, systemLogs]);

    return (
        <CommandCenterLayout
            title="NEXUS ENGINE"
            subtitle="PIPELINE_ORCHESTRATOR_V4.2"
            leftPanel={<NexusHeader activeEngine={activeEngine} onEngineChange={(id) => setActiveEngine(id as any)} />}
            rightPanel={
                <NexusJobList
                    nexusJobs={nexusJobs}
                    credits={credits}
                    refreshCredits={refreshCredits}
                    pulse={pulse}
                    agents={agents}
                    onPreviewScenes={handlePreviewScenes}
                    onDeleteJob={handleDeleteJob}
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
                            <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Database className="h-16 w-16 text-cyan-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Empire Registry</h3>
                                    <div className="flex flex-col gap-1 items-center">
                                        <span className="text-[10px] text-zinc-500 font-mono italic">SECURE_STORAGE_ORCHESTRATION_ACTIVE</span>
                                        <span className="text-[8px] text-cyan-500/50 font-mono">ENCRYPTED_VOXEL_HASH: 0x93F...A2</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "forge" && (
                            <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Zap className="h-16 w-16 text-cyan-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Neural Forge</h3>
                                    <div className="flex flex-col gap-1 items-center">
                                        <span className="text-[10px] text-zinc-500 font-mono italic">CREATIVE_SYNTHESIS_PIPELINE_READY</span>
                                        <span className="text-[8px] text-cyan-500/50 font-mono">ACTIVE_TEMP: 4200K_NEURAL_BURN</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "network" && (
                            <div className="h-full min-h-[500px] flex items-center justify-center border border-white/5 bg-[#0F0F11]/60 rounded-[40px] relative overflow-hidden group">
                                <div className="absolute inset-0 architect-grid pointer-events-none opacity-20" />
                                <div className="flex flex-col items-center gap-6 relative z-10 text-center">
                                    <div className="relative">
                                        <Network className="h-16 w-16 text-cyan-500 animate-pulse" />
                                        <div className="absolute -inset-4 bg-cyan-500/20 blur-2xl rounded-full -z-10" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white uppercase tracking-[0.5em]">Global Network Mesh</h3>
                                    <div className="flex flex-col gap-1 items-center">
                                        <span className="text-[10px] text-zinc-500 font-mono italic">SWARM_INTELLIGENCE_ROUTING_ACTIVE</span>
                                        <span className="text-[8px] text-cyan-500/50 font-mono">NODES_CONNECTED: 4,092_DIRECT_LINKS</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "orchestrator" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <NexusControls
                                    niches={niches}
                                    selectedNiche={selectedNiche}
                                    onNicheChange={setSelectedNiche}
                                    creationMode={creationMode}
                                    onCreationModeChange={setCreationMode}
                                    blueprints={blueprints}
                                    activeBlueprint={activeBlueprint}
                                    onBlueprintChange={setActiveBlueprint}
                                    isLaunching={isLaunching}
                                    onLaunch={handleLaunchPipeline}
                                    onNewBlueprint={() => { setEditingBlueprint(null); setIsBlueprintBuilderOpen(true); }}
                                    onEditBlueprint={() => { setEditingBlueprint(activeBlueprint); setIsNeuralCanvasOpen(true); }}
                                />
                                <NexusJobDetail
                                    activeBlueprint={activeBlueprint}
                                    activePipelineJob={activePipelineJob}
                                    selectedNodeIndex={selectedNodeIndex}
                                    onNodeSelect={setSelectedNodeIndex}
                                />
                            </div>
                        )}

                        {activeEngine === "identities" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex items-center justify-between shrink-0">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Neural Identity Lab</h3>
                                    <Button className="bg-white/5 border border-white/10 hover:bg-white/10 text-white gap-2">
                                        <PlusCircle className="h-4 w-4" /> Register New ID
                                    </Button>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 overflow-y-auto custom-scrollbar p-1">
                                    {personas?.map((persona) => (
                                        <div key={persona.id} className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6 group hover:border-cyan-500/20 transition-all">
                                            <div className="aspect-square rounded-2xl bg-zinc-900 overflow-hidden relative border border-white/5">
                                                {persona.reference_image_uri ? (
                                                    <img src={persona.reference_image_uri} alt={persona.name} className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center">
                                                        <User className="h-12 w-12 text-zinc-800" />
                                                    </div>
                                                )}
                                                <div className="absolute inset-0 bg-linear-to-t from-black/80 via-transparent to-transparent" />
                                                <div className="absolute bottom-4 left-4">
                                                    <span className="text-[8px] font-bold text-cyan-400 uppercase tracking-widest px-2 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full">Active_ID</span>
                                                </div>
                                            </div>
                                            <div className="space-y-1">
                                                <h4 className="text-lg font-bold text-white uppercase tracking-tight">{persona.name}</h4>
                                                <p className="text-[10px] font-mono text-zinc-600">ID: {persona.id}</p>
                                            </div>
                                            <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                                <div className="flex gap-2">
                                                    <div className="h-6 w-6 rounded bg-white/5 flex items-center justify-center"><Mic2 className="h-3 w-3 text-zinc-500" /></div>
                                                    <div className="h-6 w-6 rounded bg-white/5 flex items-center justify-center"><Video className="h-3 w-3 text-zinc-500" /></div>
                                                </div>
                                                <Button variant="outline" className="h-8 text-[9px] uppercase font-bold border-white/10 text-white hover:bg-cyan-500 hover:text-black">Modify</Button>
                                            </div>
                                        </div>
                                    ))}
                                    {personas.length === 0 && (
                                        <div className="col-span-4 h-full flex flex-col items-center justify-center opacity-10 gap-6 py-20">
                                            <Fingerprint className="h-24 w-24" />
                                            <span className="text-xl font-black uppercase tracking-[1em]">No Neural IDs Found</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeEngine === "crews" && (
                            <div className="space-y-8 h-full flex flex-col">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">Workforce Orchestrator</h3>
                                    <div className="flex gap-4">
                                        <div className="px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-bold uppercase tracking-widest">
                                            {capabilities.length} Available Skills
                                        </div>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 min-h-0">
                                    <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8 flex flex-col overflow-hidden">
                                        <div className="space-y-6">
                                            <div className="flex items-center justify-between">
                                                <h4 className="text-sm font-bold text-white uppercase tracking-widest">Specialized Agents</h4>
                                                <Bot className="h-4 w-4 text-cyan-400" />
                                            </div>
                                            <div className="flex flex-col gap-4">
                                                <div className="relative">
                                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-500" />
                                                    <input
                                                        type="text"
                                                        placeholder="Search skills..."
                                                        value={searchTerm}
                                                        onChange={(e) => setSearchTerm(e.target.value)}
                                                        className="w-full bg-white/5 border border-white/5 rounded-xl pl-10 pr-4 py-2 text-[10px] text-white focus:outline-none focus:border-cyan-500/30 transition-all"
                                                    />
                                                </div>
                                                <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
                                                    {availableCategories.map((cat) => (
                                                        <button
                                                            key={cat}
                                                            onClick={() => setActiveCategory(cat)}
                                                            className={cn(
                                                                "px-3 py-1.5 rounded-lg text-[8px] font-bold uppercase tracking-widest whitespace-nowrap transition-all",
                                                                activeCategory === cat ? "bg-cyan-500 text-black" : "bg-white/5 text-zinc-500 hover:text-zinc-300"
                                                            )}
                                                        >
                                                            {cat}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-4 overflow-y-auto custom-scrollbar pr-2 flex-1">
                                            {filteredCapabilities.map((worker, i) => {
                                                const isDeploying = deployingIds.has(worker.id || worker.name);
                                                return (
                                                    <div key={i} className={cn(
                                                        "p-6 bg-white/5 border border-white/5 rounded-2xl group transition-all flex items-center justify-between gap-4",
                                                        isDeploying ? "border-cyan-500/50 bg-cyan-500/5 shadow-[0_0_20px_rgba(34,211,238,0.1)]" : "hover:border-cyan-500/30"
                                                    )}>
                                                        <div className="space-y-1 flex-1">
                                                            <div className="flex items-center gap-2">
                                                                <h5 className="text-sm font-bold text-white uppercase tracking-tight">{worker.name}</h5>
                                                                <span className={cn(
                                                                    "text-[7px] px-1.5 py-0.5 rounded-sm border uppercase font-bold",
                                                                    isDeploying ? "bg-amber-500/10 text-amber-500 border-amber-500/20 animate-pulse" : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                                                                )}>
                                                                    {isDeploying ? "DEPLOYING..." : worker.category}
                                                                </span>
                                                            </div>
                                                            <p className="text-[10px] text-zinc-500 line-clamp-2">{worker.description}</p>
                                                            <p className="text-[8px] text-zinc-600 font-mono uppercase tracking-tighter pt-1">{worker.stability} Stability</p>
                                                        </div>
                                                        <div className="flex flex-col items-end gap-3">
                                                            <span className="text-[10px] text-zinc-600 font-mono">CR: {worker.credits_per_task}</span>
                                                            <Button
                                                                onClick={() => handleDeployAgent(worker)}
                                                                disabled={isDeploying}
                                                                variant="ghost"
                                                                size="sm"
                                                                className={cn(
                                                                    "h-8 text-[10px] font-bold border border-white/5",
                                                                    isDeploying ? "text-amber-500 bg-amber-500/5" : "text-cyan-400 hover:bg-cyan-500/10"
                                                                )}
                                                            >
                                                                {isDeploying ? <Loader2 className="h-3 w-3 animate-spin" /> : "Deploy"}
                                                            </Button>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                            {filteredCapabilities.length === 0 && (
                                                <div className="py-20 text-center space-y-4 opacity-20">
                                                    <Users className="h-12 w-12 mx-auto" />
                                                    <p className="text-xs font-bold uppercase tracking-widest">No Agents Match Filters</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex flex-col items-center justify-center space-y-8 text-center relative overflow-hidden">
                                        <div className="absolute inset-0 bg-linear-to-b from-cyan-500/5 to-transparent pointer-events-none" />
                                        <Network className="h-20 w-20 text-cyan-500/20 animate-pulse" />
                                        <div className="space-y-4 z-10">
                                            <h4 className="text-xl font-bold text-white uppercase tracking-tighter">Neural Workforce Mesh</h4>
                                            <p className="text-xs text-zinc-500 max-w-[280px] leading-relaxed mx-auto">
                                                Orchestrate multiple specialized agents into a unified autonomous crew.
                                                The mesh is currently operating at {pulse?.load_avg ? Math.round(pulse.load_avg * 100) : 12}% global capacity.
                                            </p>
                                        </div>
                                        <Button className="h-14 px-10 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded-2xl uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(8,145,178,0.3)] transition-all hover:scale-105">Initialize New Crew</Button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "sandbox" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-6">
                                        <div className="flex items-center gap-2">
                                            <Terminal className="h-4 w-4 text-cyan-400" />
                                            <h3 className="text-xs font-bold text-white uppercase tracking-widest">Neural Code Sandbox</h3>
                                        </div>
                                        <div className="flex items-center bg-white/5 rounded-lg p-0.5 border border-white/5">
                                            <button
                                                onClick={() => setSandboxTab("console")}
                                                className={cn(
                                                    "px-3 py-1 text-[9px] uppercase font-bold rounded-md transition-all",
                                                    sandboxTab === "console" ? "bg-cyan-500 text-black" : "text-zinc-400 hover:text-zinc-200"
                                                )}
                                            >
                                                Console
                                            </button>
                                            <button
                                                onClick={() => setSandboxTab("telemetry")}
                                                className={cn(
                                                    "px-3 py-1 text-[9px] uppercase font-bold rounded-md transition-all",
                                                    sandboxTab === "telemetry" ? "bg-cyan-500 text-black" : "text-zinc-400 hover:text-zinc-200"
                                                )}
                                            >
                                                Live Telemetry
                                            </button>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <Button
                                            size="sm"
                                            className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold px-4 h-8 text-[10px] uppercase"
                                            onClick={handleSandboxExecute}
                                        >
                                            Execute_Node
                                        </Button>
                                    </div>
                                </div>

                                {sandboxTab === "console" ? (
                                    <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 min-h-0">
                                        <div className="border-r border-white/5 flex flex-col min-h-0">
                                            <div className="p-4 border-b border-white/5 bg-white/5">
                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Script</span>
                                            </div>
                                            <div className="flex-1 p-8 font-mono text-sm text-cyan-400/80 overflow-y-auto custom-scrollbar">
                                                <pre>
{`// Initialize Intelligence Bridge
const nexus = await Nexus.connect();

// Spawn autonomous scout
const scout = await nexus.spawnAgent("SCOUT_01", {
    role: "Discovery",
    niche: "${selectedNiche || "Global"}",
    behavior: "Aggressive"
});

// Await viral triggers
scout.on("VIRAL_DETECT", async (data) => {
    console.log("[NEXUS] Outbreak detected:", data.id);
    await nexus.dispatchPipeline("AUTO_SYNTH_V1", data);
});`}
                                                </pre>
                                            </div>
                                        </div>
                                        <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-r-[32px] border-l border-white/5 overflow-hidden">
                                            <div className="p-4 border-b border-white/5 bg-white/5">
                                                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Execution Output</span>
                                            </div>
                                            <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[10px] space-y-2">
                                                {actionLogs.map((log, i) => (
                                                    <p key={i} className={cn(
                                                        log.includes("[SUCCESS]") ? "text-emerald-500" :
                                                        log.includes("[EXEC]") ? "text-cyan-400" :
                                                        log.includes("[SYSTEM]") ? "text-zinc-600" : "text-zinc-400"
                                                    )}>{log}</p>
                                                ))}
                                                <div className="animate-pulse flex gap-2">
                                                    <span className="text-white">_</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar">
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                            <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Global Latency (ms)</span>
                                                <div className="h-48 relative">
                                                    <AreaChartCustom data={mockTelemetry.latency} dataKey="value" color="#8b5cf6" height={190} />
                                                </div>
                                            </div>
                                            <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Celery Cluster Load (%)</span>
                                                <div className="h-48 relative">
                                                    <AreaChartCustom data={mockTelemetry.workerLoad} dataKey="value" color="#22d3ee" height={190} />
                                                </div>
                                            </div>
                                            <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-4">
                                                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Self-Healing Triggers</span>
                                                <div className="h-48 relative">
                                                    <AreaChartCustom data={mockTelemetry.healing} dataKey="value" color="#10b981" height={190} />
                                                </div>
                                            </div>
                                        </div>
                                        <div className="p-6 rounded-2xl bg-white/2 border border-white/5 flex items-center justify-between">
                                            <div className="space-y-1">
                                                <span className="text-[9px] font-black text-cyan-400 uppercase tracking-widest">Cluster Health Ledger</span>
                                                <p className="text-xs text-zinc-400">All core micro-services operating nominally. Autonomic recovery scripts operational.</p>
                                            </div>
                                            <span className="text-[10px] px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 font-bold uppercase">100% HEALTH</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "history" && (
                            <NexusJobHistory
                                nexusJobs={nexusJobs}
                                onPreviewScenes={handlePreviewScenes}
                                onDeleteJob={handleDeleteJob}
                            />
                        )}

                        {activeEngine === "command" && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 overflow-y-auto custom-scrollbar pr-4">
                                <CommandPod
                                    name="Nexus Master Core"
                                    status={status === "open" ? "nominal" : "offline"}
                                    load={pulse?.load_avg ? Math.round(pulse.load_avg * 100) : 15}
                                    circuitBreaker="closed"
                                    description="Primary orchestration layer for global Nexus Workforce. Synchronizing 14 neural channels."
                                />
                                <CommandPod
                                    name="Neural ID Gateway"
                                    status="nominal"
                                    load={personas.length > 0 ? 8 : 2}
                                    circuitBreaker="closed"
                                    description="High-throughput ingress for autonomous identity verification and persona mapping."
                                />
                                <CommandPod
                                    name="Pipeline Dispatcher"
                                    status="nominal"
                                    load={nexusJobs.filter((j) => j.status === "processing").length * 20}
                                    circuitBreaker="closed"
                                    description="Real-time job scheduling and blueprint execution engine."
                                />
                                <div className="col-span-full p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 flex items-center justify-between">
                                    <div className="flex flex-col gap-2">
                                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Global Master Override</span>
                                        <h4 className="text-lg font-bold text-white uppercase tracking-tight">Emergency System Halt</h4>
                                    </div>
                                    <Button variant="outline" className="h-14 px-10 border-rose-500/20 text-rose-500 hover:bg-rose-500 hover:text-white font-bold uppercase tracking-widest text-[10px]">Execute Halt_0</Button>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col h-full bg-[#0F0F11]/60 rounded-[32px] border border-white/5 overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                                    <h3 className="text-[10px] font-bold text-zinc-400 tracking-[0.2em] uppercase">Log Stream</h3>
                                    <span className="text-[8px] font-mono text-cyan-400">{status === "open" ? "NEXUS_CORE_ACTIVE" : "OFFLINE"}</span>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-[11px] space-y-2">
                                    {displayLogs?.map((log: any, i: number) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="text-zinc-700">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                                            <span className={cn(
                                                log.level === "ACTION" ? "text-cyan-400" :
                                                log.level === "ERROR" ? "text-rose-500" :
                                                log.level === "SUCCESS" ? "text-emerald-500" : "text-zinc-500"
                                            )}>{log.module ? `[${log.module}] ` : ""}{log.message}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
            <style jsx global>{`
                .architect-grid {
                    background-image:
                        linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px);
                    background-size: 40px 40px;
                }
            `}</style>

            <PreviewScenesModal
                isPreviewModalOpen={isPreviewModalOpen}
                setIsPreviewModalOpen={setIsPreviewModalOpen}
                previewJobId={previewJobId}
                previewScenes={previewScenes}
                previewJobStatus={previewJobStatus}
                isLoadingPreview={isLoadingPreview}
                handlePreviewScenes={handlePreviewScenes}
                swappedAssets={swappedAssets}
                setSwappedAssets={setSwappedAssets}
                activeSwapDrawerIndex={activeSwapDrawerIndex}
                setActiveSwapDrawerIndex={setActiveSwapDrawerIndex}
                selectedStylePreset={selectedStylePreset}
                setSelectedStylePreset={setSelectedStylePreset}
                colorTemp={colorTemp}
                setColorTemp={setColorTemp}
                grainDensity={grainDensity}
                setGrainDensity={setGrainDensity}
                contrast={contrast}
                setContrast={setContrast}
                kenBurnsSpeed={kenBurnsSpeed}
                setKenBurnsSpeed={setKenBurnsSpeed}
                availableCategories={availableCategories}
                activeCategory={activeCategory}
                setActiveCategory={setActiveCategory}
            />

            <BlueprintBuilder
                isOpen={isBlueprintBuilderOpen}
                onClose={() => setIsBlueprintBuilderOpen(false)}
                onSuccess={handleSaveBlueprint}
                initialBlueprint={editingBlueprint}
            />

            <NeuralCanvas
                isOpen={isNeuralCanvasOpen}
                onClose={() => setIsNeuralCanvasOpen(false)}
                onSave={handleSaveBlueprint}
                initialBlueprint={editingBlueprint || undefined}
                onDeleted={handleDeleteBlueprint}
            />
        </CommandCenterLayout>
    );
}

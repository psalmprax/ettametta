"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { API_BASE } from "@/lib/config";
import { withRealFallback } from "@/lib/real_first_utils";
import { getAuthToken } from "@/lib/auth_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import { useAuth } from "@/context/AuthContext";
import { Blueprint, NexusJob, Persona } from "@/lib/types";

export type NexusEngine =
    | "orchestrator"
    | "crews"
    | "identities"
    | "sandbox"
    | "command"
    | "history"
    | "registry"
    | "forge"
    | "network"
    | "logs";

export type CreationMode = "cinema" | "blueprint";
type StylePreset =
    | "NEON_CYBER"
    | "AMBER_WARM"
    | "MONOCHROME_DARK"
    | "EMERALD_MATRIX";
export type SandboxTab = "console" | "telemetry";

const DEFAULT_NICHES = [
    "AI Technology", "Motivation", "Finance", "Health & Fitness",
    "Business", "Marketing", "Lifestyle", "Gaming",
    "Education", "Real Estate", "E-commerce", "Spirituality",
];

interface SwappedAsset {
    thumbnail: string;
    title: string;
    tags: string[];
}

export function useNexusData() {
    const searchParams = useSearchParams();
    const { lastJobUpdate } = useTelemetry();
    const { credits, refreshCredits } = useAuth();

    const refreshRef = useRef(refreshCredits);
    refreshRef.current = refreshCredits;
    useEffect(() => {
        refreshRef.current();
        const interval = setInterval(() => refreshRef.current(), 120_000);
        return () => clearInterval(interval);
    }, []);

    const [activeEngine, setActiveEngine] = useState<NexusEngine>(
        (searchParams.get("engine") as NexusEngine) || "orchestrator"
    );
    useEffect(() => {
        const engine = searchParams.get("engine") as NexusEngine | null;
        if (engine && engine !== activeEngine) setActiveEngine(engine);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams]);

    const [personas, setPersonas] = useState<Persona[]>([]);
    const [capabilities, setCapabilities] = useState<any[]>([]);
    const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
    const [activeBlueprint, setActiveBlueprint] = useState<Blueprint | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);
    const [nexusJobs, setNexusJobs] = useState<NexusJob[]>([]);
    const [niches, setNiches] = useState<any[]>([]);
    const [selectedNiche, setSelectedNiche] = useState("");
    const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
    const [actionLogs, setActionLogs] = useState<string[]>([
        "NEXUS_CORE_ONLINE",
        "AWAITING_PIPELINE_ORCHESTRATION",
    ]);
    const [creationMode, setCreationMode] = useState<CreationMode>("cinema");
    const [searchTerm, setSearchTerm] = useState("");
    const [activeCategory, setActiveCategory] = useState("All");

    // Preview Scenes modal state
    const [previewJobId, setPreviewJobId] = useState<string | null>(null);
    const [previewScenes, setPreviewScenes] = useState<any[]>([]);
    const [previewJobStatus, setPreviewJobStatus] = useState<string>("");
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

    // Blueprint Builder + Neural Canvas modals
    const [isBlueprintBuilderOpen, setIsBlueprintBuilderOpen] = useState(false);
    const [isNeuralCanvasOpen, setIsNeuralCanvasOpen] = useState(false);
    const [editingBlueprint, setEditingBlueprint] = useState<Blueprint | null>(null);

    // Style customizer state
    const [selectedStylePreset, setSelectedStylePreset] =
        useState<StylePreset>("NEON_CYBER");
    const [colorTemp, setColorTemp] = useState<number>(50);
    const [grainDensity, setGrainDensity] = useState<number>(20);
    const [contrast, setContrast] = useState<number>(50);
    const [kenBurnsSpeed, setKenBurnsSpeed] = useState<number>(30);
    const [swappedAssets, setSwappedAssets] = useState<
        Record<number, SwappedAsset>
    >({});
    const [activeSwapDrawerIndex, setActiveSwapDrawerIndex] =
        useState<number | null>(null);
    const [sandboxTab, setSandboxTab] = useState<SandboxTab>("console");

    const [deployingIds, setDeployingIds] = useState<Set<string>>(new Set());

    // Mock telemetry data for sandbox tab (deterministic)
    const mockTelemetry = useMemo(
        () => ({
            latency: [
                { time: "10:00", value: 180 }, { time: "10:10", value: 240 },
                { time: "10:20", value: 310 }, { time: "10:30", value: 190 },
                { time: "10:40", value: 150 }, { time: "10:50", value: 220 },
                { time: "11:00", value: 165 },
            ],
            workerLoad: [
                { time: "10:00", value: 25 }, { time: "10:10", value: 45 },
                { time: "10:20", value: 65 }, { time: "10:30", value: 40 },
                { time: "10:40", value: 30 }, { time: "10:50", value: 55 },
                { time: "11:00", value: 38 },
            ],
            healing: [
                { time: "10:00", value: 1 }, { time: "10:10", value: 0 },
                { time: "10:20", value: 3 }, { time: "10:30", value: 1 },
                { time: "10:40", value: 0 }, { time: "10:50", value: 2 },
                { time: "11:00", value: 0 },
            ],
        }),
        []
    );

    const fetchData = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback<Blueprint[]>(
                (signal) => fetch(`${API_BASE}/nexus/blueprints`, { headers }),
                {
                    fallback: [],
                    onSuccess: (data) => {
                        setBlueprints(data);
                        if (data.length > 0) setActiveBlueprint(data[0]);
                    },
                }
            ),
            withRealFallback<NexusJob[]>(
                (signal) => fetch(`${API_BASE}/nexus/jobs`, { headers }),
                {
                    fallback: [],
                    onSuccess: (data) => setNexusJobs(Array.isArray(data) ? data : []),
                }
            ),
            withRealFallback<any[]>(
                (signal) => fetch(`${API_BASE}/discovery/niches`, { headers }),
                {
                    fallback: DEFAULT_NICHES,
                    onSuccess: (data: any) => {
                        let nicheList = Array.isArray(data) ? data : (data?.niches || []);
                        if (nicheList.length === 0) nicheList = DEFAULT_NICHES;
                        setNiches(nicheList);
                        if (nicheList.length > 0 && !selectedNiche) {
                            const first = typeof nicheList[0] === "string"
                                ? nicheList[0]
                                : nicheList[0].niche || nicheList[0].name;
                            setSelectedNiche(first);
                        }
                    },
                }
            ),
            withRealFallback<any[]>(
                (signal) => fetch(`${API_BASE}/agent/capabilities`, { headers }),
                {
                    fallback: [],
                    onSuccess: (data: any) => {
                        const caps = Array.isArray(data) ? data : (data?.workers || []);
                        setCapabilities(caps);
                    },
                }
            ),
        ]);
    }, [selectedNiche]);

    const fetchPersonas = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<Persona[]>(
            (signal) =>
                fetch(`${API_BASE}/persona/list`, {
                    headers: { Authorization: `Bearer ${token}` },
                }),
            {
                fallback: [],
                onSuccess: (data) => setPersonas(Array.isArray(data) ? data : []),
            }
        );
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    useEffect(() => {
        if (activeEngine === "identities") fetchPersonas();
    }, [activeEngine, fetchPersonas]);

    // Live job updates from telemetry
    useEffect(() => {
        if (!lastJobUpdate) return;
        const update = lastJobUpdate.data || lastJobUpdate;
        if (!update?.id) return;

        setNexusJobs((prev) => {
            const index = prev.findIndex((j) => j.id === update.id);
            if (index !== -1) {
                const next = [...prev];
                next[index] = {
                    ...next[index],
                    ...update,
                    status: update.status || next[index].status,
                };
                return next;
            }
            toast.success(`New Agent Deployment Active: ${update.id.slice(0, 8)}`);
            return [update as any, ...prev];
        });

        if (update.status === "COMPLETED") {
            setActionLogs((prev) => [`[PIPELINE] Job ${update.id} Success`, ...prev]);
            toast.success(`Agent Deployment Completed: ${update.id.slice(0, 8)}`);
        } else if (update.status === "FAILED") {
            setActionLogs((prev) => [`[ERROR] Job ${update.id} Failed`, ...prev]);
            toast.error(`Agent Deployment Failed: ${update.id.slice(0, 8)}`);
        }
    }, [lastJobUpdate]);

    const handleLaunchPipeline = useCallback(async () => {
        if (!selectedNiche) return;
        setIsLaunching(true);
        const modeLabel =
            creationMode === "cinema" ? "Stock Video + Remotion" : "AI Blueprint (GPU)";
        setActionLogs((prev) => [
            `[PIPELINE] Dispatching: ${modeLabel} for ${selectedNiche}`,
            ...prev,
        ]);

        const token = await getAuthToken();
        if (!token) {
            setIsLaunching(false);
            return;
        }

        const payload: Record<string, unknown> = {
            niche: selectedNiche,
            cinema_mode: creationMode === "cinema",
        };
        if (creationMode === "blueprint" && activeBlueprint) {
            payload.blueprint_id = activeBlueprint.id;
        }

        await withRealFallback(
            (signal) =>
                fetch(`${API_BASE}/nexus/compose`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(payload),
                }),
            {
                fallback: null,
                onSuccess: (data: any) => {
                    toast.success("Pipeline Dispatched");
                    setActionLogs((prev) => [
                        `[SUCCESS] Pipeline Job ID: ${data.job_id}`,
                        ...prev,
                    ]);
                },
            }
        );
        setIsLaunching(false);
    }, [selectedNiche, creationMode, activeBlueprint]);

    const handleDeployAgent = useCallback(
        async (worker: any) => {
            const workerId = worker.id || worker.name;
            const token = await getAuthToken();
            if (!token) return;

            setDeployingIds((prev) => new Set(prev).add(workerId));
            setActionLogs((prev) => [
                `[DEPLOY] Initializing Neural Instance: ${worker.name}`,
                ...prev,
            ]);

            const dropId = (id: string) =>
                setDeployingIds((prev) => {
                    const next = new Set(prev);
                    next.delete(id);
                    return next;
                });

            const promise = withRealFallback<any>(
                (signal) =>
                    fetch(`${API_BASE}/tools/crew/run`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                        body: JSON.stringify({
                            crew_type:
                                worker.category === "Content" ? "content" : "affiliate",
                            topic: selectedNiche || worker.name,
                            worker_id: worker.id,
                        }),
                    }),
                {
                    fallback: { status: "success", job_id: `LOCAL_${Date.now()}` },
                    onSuccess: (data: any) => {
                        setActionLogs((prev) => [
                            `[SUCCESS] Neural Stream Established: ${worker.name} (Job: ${data.job_id || "OK"})`,
                            ...prev,
                        ]);
                        setTimeout(() => dropId(workerId), 2000);
                    },
                    onFallback: (err) => {
                        setActionLogs((prev) => [
                            `[ERROR] ${worker.name}: ${err.message}`,
                            ...prev,
                        ]);
                        dropId(workerId);
                    },
                }
            );

            toast.promise(promise, {
                loading: `Deploying ${worker.name} Cluster...`,
                success: `${worker.name} Deployment Verified`,
                error: (err) => `Deployment Failed: ${err.message || "Access Denied"}`,
            });
        },
        [selectedNiche]
    );

    const handlePreviewScenes = useCallback(async (jobId: string) => {
        setIsLoadingPreview(true);
        setPreviewJobId(jobId);
        try {
            const token = await getAuthToken();
            const response = await fetch(
                `${API_BASE}/nexus/jobs/${jobId}/preview`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            if (response.ok) {
                const data = await response.json();
                setPreviewScenes(data.data?.scenes || []);
                setPreviewJobStatus(data.data?.status || "");
                setIsPreviewModalOpen(true);
            } else {
                toast.error("No scene data available for this job");
            }
        } catch {
            toast.error("Failed to load scene preview");
        } finally {
            setIsLoadingPreview(false);
        }
    }, []);

    const handleDeleteJob = useCallback(async (jobId: string) => {
        const promise = (async () => {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/nexus/jobs/${jobId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error("Deletion restricted");
        })();
        toast.promise(promise, {
            loading: "Purging pipeline...",
            success: "Pipeline purged",
            error: "Deletion restricted",
        });
        await promise;
    }, []);

    const handleSandboxExecute = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        toast.info("Dispatching code to sandbox...");
        await withRealFallback(
            (signal) =>
                fetch(`${API_BASE}/agent/sandbox-execute`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ code: "// Nexus Sandbox Logic" }),
                }),
            {
                fallback: null,
                onSuccess: (data: any) => {
                    toast.success("Execution Complete");
                    if (data?.logs) setActionLogs((prev) => [...data.logs, ...prev]);
                },
            }
        );
    }, []);

    const handleSaveBlueprint = useCallback((bp: Blueprint) => {
        setBlueprints((prev) => {
            const idx = prev.findIndex((b) => b.id === bp.id);
            if (idx >= 0) {
                const next = [...prev];
                next[idx] = bp;
                return next;
            }
            return [bp, ...prev];
        });
        setActiveBlueprint(bp);
    }, []);

    const handleDeleteBlueprint = useCallback(
        (id: string) => {
            setBlueprints((prev) => prev.filter((b) => b.id !== id));
            if (activeBlueprint?.id === id) setActiveBlueprint(null);
        },
        [activeBlueprint]
    );

    // Derived
    const activePipelineJob = useMemo(
        () =>
            nexusJobs.find(
                (j) => j.status === "Active" || j.status === "Processing"
            ) || nexusJobs[0],
        [nexusJobs]
    );

    const filteredCapabilities = useMemo(
        () =>
            capabilities.filter((worker) => {
                const matchesSearch =
                    worker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    worker.description
                        .toLowerCase()
                        .includes(searchTerm.toLowerCase());
                const matchesCategory =
                    activeCategory === "All" || worker.category === activeCategory;
                return matchesSearch && matchesCategory;
            }),
        [capabilities, searchTerm, activeCategory]
    );

    // Note: 'All' is intentionally pinned to index 0 so the Crew filter
    // pill group reads naturally. The non-'All' categories are sorted
    // alphabetically so the result is deterministic regardless of API order.
    const availableCategories = useMemo(() => {
        const cats = new Set(capabilities.map((c) => c.category));
        return ["All", ...Array.from(cats).sort()];
    }, [capabilities]);

    return {
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
        handleSaveBlueprint,
        handleDeleteBlueprint,

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
    };
}


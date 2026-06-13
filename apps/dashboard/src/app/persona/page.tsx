"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    Users,
    Plus,
    Trash2,
    Play,
    Loader2,
    Sparkles,
    Terminal,
    FileVideo
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";
import { useTelemetry } from "@/context/TelemetryContext";

interface Persona {
    id: string;
    name: string;
    reference_image_uri: string | null;
    voice_clone_id: string | null;
}

function PersonaContent() {
    const { agents, logs: _systemLogs, status: _status, pulse: _pulse } = useTelemetry();
    const [activeEngine, setActiveEngine] = useState("list");
    const [personas, setPersonas] = useState<Persona[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [isGenerating, setIsGenerating] = useState<string | null>(null);
    const [actionLogs, setActionLogs] = useState<string[]>(["PERSONA_LAB_INITIALIZED"]);

    // Create form state
    const [newPersonaName, setNewPersonaName] = useState("");
    const [newPersonaImageUri, setNewPersonaImageUri] = useState("");
    const [_showCreateForm, setShowCreateForm] = useState(false);

    // Generate form state
    const [generateTopic, setGenerateTopic] = useState("");
    const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);

    const fetchPersonas = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        setIsLoading(true);
        await withRealFallback<Persona[]>((signal) => fetch(`${API_BASE}/persona/list`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (data: any) => {
                    const list = Array.isArray(data) ? data : (data?.data || data?.personas || []);
                    setPersonas(list);
                }
            }
        );
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchPersonas();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleCreate = async () => {
        if (!newPersonaName.trim()) {
            toast.error("Please enter a persona name");
            return;
        }
        setIsCreating(true);
        setActionLogs((prev: string[]) => [`[CREATE] Registering new persona: ${newPersonaName}`, ...prev]);
        const token = await getAuthToken();
        if (!token) { setIsCreating(false); return; }

        const formData = new FormData();
        formData.append("name", newPersonaName.trim());
        if (newPersonaImageUri.trim()) {
            formData.append("reference_image_uri", newPersonaImageUri.trim());
        }

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/persona/create?name=${encodeURIComponent(newPersonaName.trim())}${newPersonaImageUri.trim() ? `&reference_image_uri=${encodeURIComponent(newPersonaImageUri.trim())}` : ""}`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success(`Persona "${newPersonaName}" created`);
                    setActionLogs((prev: string[]) => [`[SUCCESS] Persona "${newPersonaName}" created`, ...prev]);
                    setNewPersonaName("");
                    setNewPersonaImageUri("");
                    setShowCreateForm(false);
                    fetchPersonas();
                },
                onFallback: (err) => {
                    setActionLogs((prev: string[]) => [`[ERROR] Create failed: ${err.message}`, ...prev]);
                    toast.error(`Failed to create persona: ${err.message}`);
                }
            }
        );
        setIsCreating(false);
    };

    const handleDelete = async (personaId: string, personaName: string) => {
        setActionLogs((prev: string[]) => [`[DELETE] Purging persona: ${personaName}`, ...prev]);
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/persona/${personaId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success(`Persona "${personaName}" purged`);
                    setPersonas((prev) => prev.filter((p) => p.id !== personaId));
                    setActionLogs((prev: string[]) => [`[SUCCESS] Persona "${personaName}" purged`, ...prev]);
                },
                onFallback: (err) => {
                    toast.error(`Delete failed: ${err.message}`);
                    setActionLogs((prev: string[]) => [`[ERROR] Delete failed: ${err.message}`, ...prev]);
                }
            }
        );
    };

    const handleGenerate = async () => {
        if (!selectedPersonaId || !generateTopic.trim()) {
            toast.error("Please select a persona and enter a topic");
            return;
        }
        setIsGenerating(selectedPersonaId);
        setActionLogs((prev: string[]) => [`[GENERATE] Starting persona video: ${generateTopic}`, ...prev]);
        const token = await getAuthToken();
        if (!token) { setIsGenerating(null); return; }

        await withRealFallback<any>((signal) => fetch(`${API_BASE}/persona/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    persona_id: selectedPersonaId,
                    topic: generateTopic.trim()
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const videoUri = data?.data?.video_uri || data?.video_uri;
                    toast.success("Persona video generated!");
                    setActionLogs((prev: string[]) => [`[SUCCESS] Video generated: ${videoUri || "URI available"}`, ...prev]);
                    setGenerateTopic("");
                    setSelectedPersonaId(null);
                },
                onFallback: (err) => {
                    toast.error(`Generation failed: ${err.message}`);
                    setActionLogs((prev: string[]) => [`[ERROR] Generation failed: ${err.message}`, ...prev]);
                }
            }
        );
        setIsGenerating(null);
    };

    return (
        <CommandCenterLayout
            title="PERSONA LAB"
            subtitle="DIGITAL_IDENTITY_V2.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "list", label: "Personas", icon: Users },
                        { id: "create", label: "Create Persona", icon: Plus },
                        { id: "generate", label: "Generate Video", icon: Play },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Persona Stats</h4>
                        <div className="flex flex-col">
                            <span className="text-2xl font-bold text-white">{personas.length}</span>
                            <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">Registered Identities</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-bold text-rose-500">{personas.filter(p => p.voice_clone_id).length}</span>
                            <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">Voice Clones</span>
                        </div>
                    </div>
                </>
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
                        {activeEngine === "list" && (
                            <div className="overflow-y-auto custom-scrollbar flex-1 p-1">
                                {isLoading ? (
                                    <div className="flex items-center justify-center py-32">
                                        <Loader2 className="h-8 w-8 text-rose-500 animate-spin" />
                                    </div>
                                ) : personas.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-32 opacity-60">
                                        <Users className="h-16 w-16 mb-4 text-zinc-500" />
                                        <span className="text-[10px] font-bold uppercase tracking-[0.5em] text-zinc-400">No personas registered</span>
                                        <span className="text-[8px] text-zinc-700 font-mono mt-2 uppercase tracking-widest">Create a persona to generate talking-head videos</span>
                                        <button
                                            onClick={() => setActiveEngine("create")}
                                            className="mt-6 text-xs text-rose-500 hover:text-rose-400 font-bold uppercase tracking-widest"
                                        >
                                            Create your first persona
                                        </button>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                                        {personas.map((persona) => (
                                            <div key={persona.id} className="group relative">
                                                <DesignCard
                                                    title={persona.name}
                                                    status={persona.voice_clone_id ? "Voice Cloned" : "Standard"}
                                                    metrics={[
                                                        { label: "Image", value: persona.reference_image_uri ? "Linked" : "None", color: persona.reference_image_uri ? "text-emerald-400" : "text-zinc-500" },
                                                        { label: "Voice Clone", value: persona.voice_clone_id ? "Active" : "None", color: persona.voice_clone_id ? "text-rose-400" : "text-zinc-500" }
                                                    ]}
                                                    footerInfo={`ID: ${persona.id.slice(0, 8)}...`}
                                                    toolsStatus={persona.reference_image_uri ? "Ready" : "Incomplete"}
                                                    onClick={() => {
                                                        setSelectedPersonaId(persona.id);
                                                        setGenerateTopic("");
                                                        setActiveEngine("generate");
                                                    }}
                                                />
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDelete(persona.id, persona.name);
                                                    }}
                                                    className="absolute top-3 right-3 h-8 w-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all hover:bg-rose-500/20"
                                                >
                                                    <Trash2 className="h-4 w-4 text-rose-500" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "create" && (
                            <div className="flex-1 flex items-start justify-center pt-12">
                                <div className="w-full max-w-2xl p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                                            <Plus className="h-6 w-6 text-rose-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold text-white uppercase tracking-tight">New Digital Identity</h3>
                                            <p className="text-xs text-zinc-500 mt-1">Register a new persona for autonomous content generation.</p>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Persona Name</label>
                                            <input
                                                type="text"
                                                value={newPersonaName}
                                                onChange={(e) => setNewPersonaName(e.target.value)}
                                                placeholder="e.g., Alex Mentor, TechGirl, etc."
                                                className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white font-mono text-sm focus:outline-none focus:border-rose-500/30 transition-all"
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Reference Image URL (Optional)</label>
                                            <input
                                                type="text"
                                                value={newPersonaImageUri}
                                                onChange={(e) => setNewPersonaImageUri(e.target.value)}
                                                placeholder="https://example.com/portrait.jpg"
                                                className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white font-mono text-sm focus:outline-none focus:border-rose-500/30 transition-all"
                                            />
                                        </div>

                                        <div className="flex gap-4 pt-4">
                                            <Button
                                                onClick={handleCreate}
                                                disabled={isCreating || !newPersonaName.trim()}
                                                className="flex-1 bg-rose-500 hover:bg-rose-400 text-black font-bold h-14 rounded-2xl gap-3"
                                            >
                                                {isCreating ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
                                                {isCreating ? "Registering..." : "Register Persona"}
                                            </Button>
                                            <Button
                                                variant="outline"
                                                onClick={() => {
                                                    setShowCreateForm(false);
                                                    setNewPersonaName("");
                                                    setNewPersonaImageUri("");
                                                }}
                                                className="border-white/10 text-zinc-400 h-14 px-8 rounded-2xl"
                                            >
                                                Cancel
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "generate" && (
                            <div className="flex-1 flex items-start justify-center pt-12">
                                <div className="w-full max-w-2xl p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                                            <Play className="h-6 w-6 text-rose-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold text-white uppercase tracking-tight">Generate Persona Video</h3>
                                            <p className="text-xs text-zinc-500 mt-1">Select a persona and topic to generate a talking-head video.</p>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Select Persona</label>
                                            <div className="grid grid-cols-2 gap-2">
                                                {personas.map((p) => (
                                                    <button
                                                        key={p.id}
                                                        onClick={() => setSelectedPersonaId(p.id)}
                                                        className={cn(
                                                            "p-4 rounded-2xl border text-left transition-all",
                                                            selectedPersonaId === p.id
                                                                ? "bg-rose-500/10 border-rose-500/30 text-white"
                                                                : "bg-white/5 border-white/5 text-zinc-500 hover:border-white/20"
                                                        )}
                                                    >
                                                        <span className="text-xs font-bold block uppercase tracking-tight">{p.name}</span>
                                                        <span className="text-[8px] text-zinc-600 block mt-1">{p.voice_clone_id ? "Voice Clone Active" : "No Voice Clone"}</span>
                                                    </button>
                                                ))}
                                                {personas.length === 0 && (
                                                    <div className="col-span-2 p-6 rounded-2xl bg-zinc-500/5 border border-zinc-500/10 text-center">
                                                        <span className="text-[10px] text-zinc-600">No personas available. Create one first.</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Topic / Script</label>
                                            <input
                                                type="text"
                                                value={generateTopic}
                                                onChange={(e) => setGenerateTopic(e.target.value)}
                                                placeholder="e.g., The future of AI in 2026"
                                                className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white font-mono text-sm focus:outline-none focus:border-rose-500/30 transition-all"
                                            />
                                        </div>

                                        <Button
                                            onClick={handleGenerate}
                                            disabled={isGenerating !== null || !selectedPersonaId || !generateTopic.trim()}
                                            className="w-full bg-rose-500 hover:bg-rose-400 text-black font-bold h-14 rounded-2xl gap-3"
                                        >
                                            {isGenerating ? <Loader2 className="h-5 w-5 animate-spin" /> : <FileVideo className="h-5 w-5" />}
                                            {isGenerating ? "Generating..." : "Generate Persona Video"}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Persona Engine Logs</h3>
                                    </div>
                                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20">
                                        <div className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
                                        <span className="text-[9px] font-bold text-rose-500 uppercase">Lab_Active</span>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {actionLogs.map((log, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date().toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                log.startsWith("[CREATE]") ? "text-cyan-400" :
                                                log.startsWith("[SUCCESS]") ? "text-emerald-500" :
                                                log.startsWith("[ERROR]") ? "text-rose-500" :
                                                log.startsWith("[DELETE]") ? "text-orange-500" :
                                                log.startsWith("[GENERATE]") ? "text-violet-400" :
                                                "text-zinc-400"
                                            )}>{log}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function PersonaPage() {
    return (
        <Suspense fallback={null}>
            <PersonaContent />
        </Suspense>
    );
}

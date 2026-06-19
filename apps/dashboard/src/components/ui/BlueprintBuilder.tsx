"use client";

import React, { useState, useEffect, useRef } from "react";
import { X, Plus, Trash2, Save, Database, Cpu, Sparkles, Share2, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn, safeRandomUUID } from "@/lib/utils";
import { toast } from "sonner";
import { NodeType } from "./NexusNode";
import { withRealFallback } from "@/lib/real_first_utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { BlueprintNode, Blueprint } from "@/lib/types";
import { ConfirmModal } from "@/components/ui/ConfirmModal";

/** Module-internal — do not consume from outside. */
interface BlueprintBuilderProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (newBlueprint: Blueprint) => void;
    /** When provided, the builder opens in edit mode and PUTs to the
     *  existing blueprint ID instead of POSTing a new one. */
    initialBlueprint?: Blueprint | null;
}

export function BlueprintBuilder({ isOpen, onClose, onSuccess, initialBlueprint }: BlueprintBuilderProps) {
    const isEditMode = !!initialBlueprint;
    const [name, setName] = useState(initialBlueprint?.name || "");
    const [description, setDescription] = useState(initialBlueprint?.description || "");
    const [compositionId, setCompositionId] = useState(initialBlueprint?.composition_id || "ViralClip");
    const [nodes, setNodes] = useState<BlueprintNode[]>(
        initialBlueprint?.nodes && initialBlueprint.nodes.length > 0
            ? initialBlueprint.nodes
            : [{ id: safeRandomUUID(), type: "ingress", label: "Initial Node", desc: "Data entry point" }]
    );
    const [isSaving, setIsSaving] = useState(false);
    const [nodeToDelete, setNodeToDelete] = useState<BlueprintNode | null>(null);
    const previousActiveElement = useRef<HTMLElement | null>(null);

    // Re-sync state when the modal is opened with a different blueprint.
    useEffect(() => {
        if (isOpen) {
            setName(initialBlueprint?.name || "");
            setDescription(initialBlueprint?.description || "");
            setCompositionId(initialBlueprint?.composition_id || "ViralClip");
            setNodes(
                initialBlueprint?.nodes && initialBlueprint.nodes.length > 0
                    ? initialBlueprint.nodes
                    : [{ id: safeRandomUUID(), type: "ingress", label: "Initial Node", desc: "Data entry point" }]
            );
        }
    }, [isOpen, initialBlueprint]);

    // Handle escape key and focus management
    useEffect(() => {
        if (isOpen) {
            // Save the currently focused element
            previousActiveElement.current = document.activeElement as HTMLElement;

            // Focus first input after modal opens
            const timer = setTimeout(() => {
                const firstInput = document.querySelector('[data-modal-first-focus]');
                if (firstInput) (firstInput as HTMLElement).focus();
            }, 100);

            // Handle escape key
            const handleEscape = (e: KeyboardEvent) => {
                if (e.key === 'Escape') onClose();
            };
            document.addEventListener('keydown', handleEscape);

            // Cleanup: restore focus when modal closes or component unmounts
            return () => {
                clearTimeout(timer);
                document.removeEventListener('keydown', handleEscape);
                if (previousActiveElement.current) {
                    previousActiveElement.current.focus();
                }
            };
        }
    }, [isOpen, onClose]);

    const addNode = (type: NodeType) => {
        const newNode: BlueprintNode = {
            id: safeRandomUUID(),
            type,
            label: `New ${type.toUpperCase()} Node`,
            desc: "Configure this node"
        };
        setNodes([...nodes, newNode]);
    };

    const removeNode = (node: BlueprintNode) => {
        setNodeToDelete(node);
    };

    const confirmRemoveNode = () => {
        if (nodeToDelete) {
            setNodes(nodes.filter(n => n.id !== nodeToDelete.id));
            setNodeToDelete(null);
        }
    };

    const updateNode = (id: string, field: 'label' | 'desc', value: string) => {
        setNodes(nodes.map(node =>
            node.id === id ? { ...node, [field]: value } : node
        ));
    };

    const handleSave = async () => {
        if (!name || !description || nodes.length === 0) {
            toast.error("Invalid Configuration", { description: "Name, description and at least one node required." });
            return;
        }

        setIsSaving(true);
        // In edit mode, use the existing ID; in create mode, derive one from name.
        const blueprintId = isEditMode
            ? initialBlueprint!.id
            : name.toLowerCase().replace(/[^a-z0-9]/gi, '-');
        const token = getAuthToken();
        if (!token) {
            setIsSaving(false);
            return;
        }

        if (isEditMode) {
            // Edit flow: PUT to /nexus/blueprints/{id} with the changed fields.
            await withRealFallback((signal) => fetch(`${API_BASE}/nexus/blueprints/${encodeURIComponent(blueprintId)}`, {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        name,
                        description,
                        composition_id: compositionId,
                        nodes
                    }),
                    signal
                }),
                {
                    fallback: {} as any,
                    onSuccess: (data) => {
                        toast.success("Blueprint Updated", { description: `Recipe "${name}" changes have been committed.` });
                        const blueprint: Blueprint = {
                            id: data?.id || blueprintId,
                            name: data?.name || name,
                            description: data?.description || description,
                            composition_id: data?.composition_id || compositionId,
                            nodes: data?.nodes || nodes
                        };
                        onSuccess(blueprint);
                        onClose();
                    },
                    onFallback: (err) => {
                        toast.error("Update Failed", { description: err.message || "Could not update the blueprint." });
                    }
                }
            );
        } else {
            // Create flow: POST to /nexus/blueprints.
            await withRealFallback((signal) => fetch(`${API_BASE}/nexus/blueprints`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        id: blueprintId,
                        name,
                        description,
                        composition_id: compositionId,
                        nodes
                    }),
                    signal
                }),
                {
                    fallback: {} as any,
                    onSuccess: (data) => {
                        toast.success("Blueprint Saved", { description: `Recipe "${name}" is now available in the neural cluster.` });
                        const blueprint: Blueprint = {
                            id: data?.id || blueprintId,
                            name: data?.name || name,
                            description: data?.description || description,
                            composition_id: data?.composition_id || compositionId,
                            nodes: data?.nodes || nodes
                        };
                        onSuccess(blueprint);
                        onClose();
                    },
                    onFallback: (err) => {
                        toast.error("Save Failed", { description: err.message || "Could not register the blueprint." });
                    }
                }
            );
        }
        setIsSaving(false);
    };

    if (!isOpen) return null;

    // Handle escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    // Focus management: focus first input when modal opens
    useEffect(() => {
        if (isOpen) {
            const timer = setTimeout(() => {
                const firstInput = document.querySelector('[data-modal-first-focus]');
                if (firstInput) (firstInput as HTMLElement).focus();
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 sm:p-12">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/90 backdrop-blur-xl"
                onClick={onClose}
                aria-hidden="true"
            />
            
            <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-4xl bg-zinc-950 border border-white/10 rounded-5xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]"
                role="dialog"
                aria-modal="true"
                aria-labelledby="blueprint-builder-title"
            >
                <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/2">
                    <div className="space-y-1">
                        <h2 id="blueprint-builder-title" className="text-3xl font-bold text-white uppercase tracking-tighter">Blueprint <span className="text-primary">Architect</span></h2>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Neural Pipeline Configuration</p>
                    </div>
                    <button onClick={onClose} className="h-10 w-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors" aria-label="Close blueprint builder">
                        <X className="h-5 w-5 text-zinc-500" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-10 space-y-10 custom-scrollbar">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 ml-2">Recipe Name</label>
                            <input
                                data-modal-first-focus
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Viral Re-skinner V2..."
                                className="w-full bg-zinc-900 border border-white/5 rounded-2xl py-4 px-6 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-primary/40"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 ml-2">Composition ID</label>
                            <select
                                value={compositionId}
                                onChange={(e) => setCompositionId(e.target.value)}
                                className="w-full bg-zinc-900 border border-white/5 rounded-2xl py-4 px-6 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-primary/40"
                            >
                                <option value="ViralClip">ViralClip (Standard)</option>
                                <option value="CinematicShorts">CinematicShorts (Premium)</option>
                                <option value="ShortsVertical">ShortsVertical (Clean)</option>
                                <option value="AI_TalkingHead">AI_TalkingHead (Persona)</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 ml-2">Description</label>
                            <input
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Optimized for high-retention TikTok hooks..."
                                className="w-full bg-zinc-900 border border-white/5 rounded-2xl py-4 px-6 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-primary/40"
                            />
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Pipeline Nodes ({nodes.length})</h3>
                            <div className="flex gap-2">
                                <button onClick={() => addNode('ingress')} className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-[8px] font-bold uppercase text-emerald-500 hover:bg-emerald-500/20 transition-all">Add Ingress</button>
                                <button onClick={() => addNode('cognition')} className="px-3 py-1.5 bg-violet-500/10 border border-violet-500/20 rounded-lg text-[8px] font-bold uppercase text-violet-500 hover:bg-violet-500/20 transition-all">Add Cognition</button>
                                <button onClick={() => addNode('synthesis')} className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-[8px] font-bold uppercase text-cyan-500 hover:bg-cyan-500/20 transition-all">Add Synthesis</button>
                                <button onClick={() => addNode('egress')} className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-[8px] font-bold uppercase text-rose-500 hover:bg-rose-500/20 transition-all">Add Egress</button>
                            </div>
                        </div>

                        <div className="space-y-4">
                            {nodes.map((node) => (
                                <div key={node.id} className="p-6 rounded-3xl bg-white/2 border border-white/5 flex items-start gap-6 group hover:border-white/10 transition-all">
                                    <div className={cn(
                                        "h-12 w-12 rounded-2xl flex items-center justify-center shrink-0 border",
                                        node.type === 'ingress' && "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
                                        node.type === 'cognition' && "bg-violet-500/10 border-violet-500/20 text-violet-500",
                                        node.type === 'synthesis' && "bg-cyan-500/10 border-cyan-500/20 text-cyan-500",
                                        node.type === 'egress' && "bg-rose-500/10 border-rose-500/20 text-rose-500",
                                    )}>
                                        {node.type === 'ingress' && <Database className="h-5 w-5" />}
                                        {node.type === 'cognition' && <Cpu className="h-5 w-5" />}
                                        {node.type === 'synthesis' && <Sparkles className="h-5 w-5" />}
                                        {node.type === 'egress' && <Share2 className="h-5 w-5" />}
                                    </div>

                                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <input
                                            value={node.label}
                                            onChange={(e) => updateNode(node.id, 'label', e.target.value)}
                                            placeholder="Node Label"
                                            className="bg-transparent border-b border-white/5 py-2 text-sm font-bold text-white focus:outline-none focus:border-primary/40"
                                        />
                                        <input
                                            value={node.desc}
                                            onChange={(e) => updateNode(node.id, 'desc', e.target.value)}
                                            placeholder="Node Description"
                                            className="bg-transparent border-b border-white/5 py-2 text-xs font-bold text-zinc-500 focus:outline-none focus:border-primary/40"
                                        />
                                    </div>

                                    <button onClick={() => removeNode(node)} className="opacity-0 group-hover:opacity-100 p-2 text-zinc-700 hover:text-rose-500 transition-all" aria-label={`Delete node ${node.label}`}>
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="p-8 border-t border-white/5 bg-zinc-950 flex justify-end gap-4">
                    <button onClick={onClose} className="px-8 py-4 rounded-2xl border border-white/10 text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:bg-white/5 transition-all">Cancel</button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-10 py-4 rounded-2xl bg-linear-to-r from-violet-600 to-cyan-500 text-[10px] font-bold uppercase tracking-widest text-white hover:scale-105 active:scale-95 transition-all shadow-glow-violet/20 flex items-center gap-3"
                    >
                        {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        Commit Blueprint
                    </button>
                </div>
            </motion.div>

            {/* Confirmation Modal for Node Deletion */}
            <ConfirmModal
                isOpen={!!nodeToDelete}
                onClose={() => setNodeToDelete(null)}
                onConfirm={confirmRemoveNode}
                title="Delete Node?"
                description={`Remove node "${nodeToDelete?.label}" from the blueprint? This action cannot be undone.`}
                confirmText="Delete"
                cancelText="Keep"
                variant="danger"
            />
        </div>
    );
}

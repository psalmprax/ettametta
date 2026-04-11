"use client";

import React, { useState } from "react";
import { X, Plus, Trash2, Save, Layers, Cpu, Database, Play, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { NodeType } from "./NexusNode";
import { withRealFallback } from "@/lib/real_first_utils";
import { API_BASE } from "@/lib/config";

interface BlueprintBuilderProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (newBlueprint: any) => void;
}

export function BlueprintBuilder({ isOpen, onClose, onSuccess }: BlueprintBuilderProps) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [nodes, setNodes] = useState<{ type: NodeType; label: string; desc: string }[]>([
        { type: "ingress", label: "Initial Node", desc: "Data entry point" }
    ]);
    const [isSaving, setIsSaving] = useState(false);

    const addNode = (type: NodeType) => {
        setNodes([...nodes, { type, label: `New ${type.toUpperCase()} Node`, desc: "Configure this node" }]);
    };

    const removeNode = (index: number) => {
        setNodes(nodes.filter((_, i) => i !== index));
    };

    const updateNode = (index: number, field: string, value: string) => {
        const newNodes = [...nodes];
        (newNodes[index] as any)[field] = value;
        setNodes(newNodes);
    };

    const handleSave = async () => {
        if (!name || !description || nodes.length === 0) {
            toast.error("Invalid Configuration", { description: "Name, description and at least one node required." });
            return;
        }

        setIsSaving(true);
        const blueprintId = name.toLowerCase().replace(/[^a-z0-9]/gi, '-');
        const token = localStorage.getItem("et_token");

        await withRealFallback(
            () => fetch(`${API_BASE}/nexus/blueprints`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    id: blueprintId,
                    name,
                    description,
                    nodes
                })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    toast.success("Blueprint Saved", { description: `Recipe "${name}" is now available in the neural cluster.` });
                    onSuccess(data);
                    onClose();
                },
                onFallback: (err) => {
                    toast.error("Save Failed", { description: err.message || "Could not register the blueprint." });
                }
            }
        );
        setIsSaving(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 sm:p-12">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/90 backdrop-blur-xl"
                onClick={onClose}
            />
            
            <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-4xl bg-zinc-950 border border-white/10 rounded-5xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]"
            >
                <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/2">
                    <div className="space-y-1">
                        <h2 className="text-3xl font-black text-white uppercase tracking-tighter">Blueprint <span className="text-primary">Architect</span></h2>
                        <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Neural Pipeline Configuration</p>
                    </div>
                    <button onClick={onClose} className="h-10 w-10 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors">
                        <X className="h-5 w-5 text-zinc-500" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-10 space-y-10 custom-scrollbar">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-2">Recipe Name</label>
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Viral Re-skinner V2..."
                                className="w-full bg-zinc-900 border border-white/5 rounded-2xl py-4 px-6 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-primary/40"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-600 ml-2">Description</label>
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
                            <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Pipeline Nodes ({nodes.length})</h3>
                            <div className="flex gap-2">
                                <button onClick={() => addNode('ingress')} className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-[8px] font-black uppercase text-emerald-500 hover:bg-emerald-500/20 transition-all">Add Ingress</button>
                                <button onClick={() => addNode('cognition')} className="px-3 py-1.5 bg-violet-500/10 border border-violet-500/20 rounded-lg text-[8px] font-black uppercase text-violet-500 hover:bg-violet-500/20 transition-all">Add Cognition</button>
                                <button onClick={() => addNode('synthesis')} className="px-3 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-[8px] font-black uppercase text-cyan-500 hover:bg-cyan-500/20 transition-all">Add Synthesis</button>
                                <button onClick={() => addNode('egress')} className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-[8px] font-black uppercase text-rose-500 hover:bg-rose-500/20 transition-all">Add Egress</button>
                            </div>
                        </div>

                        <div className="space-y-4">
                            {nodes.map((node, idx) => (
                                <div key={idx} className="p-6 rounded-3xl bg-white/2 border border-white/5 flex items-start gap-6 group hover:border-white/10 transition-all">
                                    <div className={cn(
                                        "h-12 w-12 rounded-2xl flex items-center justify-center shrink-0 border",
                                        node.type === 'ingress' && "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
                                        node.type === 'cognition' && "bg-violet-500/10 border-violet-500/20 text-violet-500",
                                        node.type === 'synthesis' && "bg-cyan-500/10 border-cyan-500/20 text-cyan-500",
                                        node.type === 'egress' && "bg-rose-500/10 border-rose-500/20 text-rose-500",
                                    )}>
                                        {node.type === 'ingress' && <Layers className="h-5 w-5" />}
                                        {node.type === 'cognition' && <Cpu className="h-5 w-5" />}
                                        {node.type === 'synthesis' && <Database className="h-5 w-5" />}
                                        {node.type === 'egress' && <Play className="h-5 w-5" />}
                                    </div>

                                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <input
                                            value={node.label}
                                            onChange={(e) => updateNode(idx, 'label', e.target.value)}
                                            placeholder="Node Label"
                                            className="bg-transparent border-b border-white/5 py-2 text-sm font-black text-white focus:outline-none focus:border-primary/40"
                                        />
                                        <input
                                            value={node.desc}
                                            onChange={(e) => updateNode(idx, 'desc', e.target.value)}
                                            placeholder="Node Description"
                                            className="bg-transparent border-b border-white/5 py-2 text-xs font-bold text-zinc-500 focus:outline-none focus:border-primary/40"
                                        />
                                    </div>

                                    <button onClick={() => removeNode(idx)} className="opacity-0 group-hover:opacity-100 p-2 text-zinc-700 hover:text-rose-500 transition-all">
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="p-8 border-t border-white/5 bg-zinc-950 flex justify-end gap-4">
                    <button onClick={onClose} className="px-8 py-4 rounded-2xl border border-white/10 text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:bg-white/5 transition-all">Cancel</button>
                    <button 
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-10 py-4 rounded-2xl bg-linear-to-r from-violet-600 to-cyan-500 text-[10px] font-black uppercase tracking-widest text-white hover:scale-105 active:scale-95 transition-all shadow-glow-violet/20 flex items-center gap-3"
                    >
                        {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        Commit Blueprint
                    </button>
                </div>
            </motion.div>
        </div>
    );
}

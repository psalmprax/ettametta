"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn, safeRandomUUID } from "@/lib/utils";
import { 
    Plus, 
    Save, 
    Database, 
    Cpu, 
    Sparkles, 
    Share2,
    Settings2,
    Trash2
} from "lucide-react";
import { BlueprintNode, Blueprint } from "@/lib/types";

interface NodePosition {
    id: string;
    x: number;
    y: number;
}

interface NeuralCanvasProps {
    readonly isOpen: boolean;
    readonly onClose: () => void;
    readonly onSave: (blueprint: Blueprint) => void;
    readonly initialBlueprint?: Blueprint;
}

export function NeuralCanvas({ isOpen, onClose, onSave, initialBlueprint }: NeuralCanvasProps) {
    const [name, setName] = useState(initialBlueprint?.name || "");
    const [description, _setDescription] = useState(initialBlueprint?.description || "");
    const [nodes, setNodes] = useState<BlueprintNode[]>(initialBlueprint?.nodes || [
        { id: safeRandomUUID(), type: "ingress", label: "Scout Cluster", desc: "Trend source entry" }
    ]);
    const [positions, setPositions] = useState<NodePosition[]>(
        initialBlueprint?.nodes.map((n, i) => ({ id: n.id, x: 100 + i * 250, y: 300 })) || 
        [{ id: nodes[0].id, x: 150, y: 350 }]
    );
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [_isSaving, _setIsSaving] = useState(false);
    
    const canvasRef = useRef<HTMLDivElement>(null);

    const handleDrag = (id: string, info: any) => {
        setPositions(prev => prev.map(p => 
            p.id === id ? { ...p, x: p.x + info.delta.x, y: p.y + info.delta.y } : p
        ));
    };

    const addNode = (type: any) => {
        const id = safeRandomUUID();
        const newNode: BlueprintNode = {
            id,
            type,
            label: `New ${type.toUpperCase()}`,
            desc: "Neural processing unit"
        };
        setNodes([...nodes, newNode]);
        setPositions([...positions, { id, x: 100, y: 100 }]);
        setSelectedNodeId(id);
    };

    const deleteNode = (id: string) => {
        setNodes(nodes.filter(n => n.id !== id));
        setPositions(positions.filter(p => p.id !== id));
        if (selectedNodeId === id) setSelectedNodeId(null);
    };

    const updateNode = (id: string, updates: Partial<BlueprintNode>) => {
        setNodes(nodes.map(n => n.id === id ? { ...n, ...updates } : n));
    };

    const selectedNode = nodes.find(n => n.id === selectedNodeId);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-100 bg-zinc-950 flex flex-col overflow-hidden">
            {/* Toolbar */}
            <div className="h-20 border-b border-white/5 bg-black/40 backdrop-blur-xl px-8 flex items-center justify-between z-50">
                <div className="flex items-center gap-8">
                    <div className="flex flex-col">
                        <input 
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Blueprint Name..."
                            className="bg-transparent border-none text-xl font-bold text-white focus:outline-none placeholder:opacity-30 tracking-tighter uppercase"
                        />
                        <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Neural Architect Studio</span>
                    </div>
                    
                    <div className="h-8 w-px bg-white/5 mx-2" />
                    
                    <div className="flex items-center gap-2">
                        <button onClick={() => addNode("ingress")} className="node-tool text-emerald-500 hover:bg-emerald-500/10"><Plus className="h-4 w-4 mr-2" /> Ingress</button>
                        <button onClick={() => addNode("cognition")} className="node-tool text-violet-500 hover:bg-violet-500/10"><Plus className="h-4 w-4 mr-2" /> Cognition</button>
                        <button onClick={() => addNode("synthesis")} className="node-tool text-cyan-500 hover:bg-cyan-500/10"><Plus className="h-4 w-4 mr-2" /> Synthesis</button>
                        <button onClick={() => addNode("egress")} className="node-tool text-rose-500 hover:bg-rose-500/10"><Plus className="h-4 w-4 mr-2" /> Egress</button>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button onClick={onClose} className="px-6 py-3 rounded-xl border border-white/5 text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:bg-white/5">Discard</button>
                    <button 
                        onClick={() => onSave({ id: safeRandomUUID(), name, description, nodes, composition_id: "ViralClip" })}
                        className="px-8 py-3 rounded-xl bg-primary text-black text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-glow-primary/40"
                    >
                        <Save className="h-4 w-4" />
                        Commit Architecture
                    </button>
                </div>
            </div>

            <div className="flex-1 flex relative">
                {/* Canvas Area */}
                <div 
                    ref={canvasRef}
                    className="flex-1 bg-[#030712] relative overflow-hidden architect-grid"
                    onMouseDown={() => setSelectedNodeId(null)}
                >
                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
                        <defs>
                            <linearGradient id="pulseGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="transparent" />
                                <stop offset="50%" stopColor="white" />
                                <stop offset="100%" stopColor="transparent" />
                            </linearGradient>
                        </defs>
                        {positions.map((pos, i) => {
                            if (i === positions.length - 1) return null;
                            const next = positions[i + 1];
                            const dx = next.x - (pos.x + 220);
                            const _dy = (next.y + 60) - (pos.y + 60);
                            
                            const pathData = `M ${pos.x + 220} ${pos.y + 60} C ${pos.x + 220 + dx/2} ${pos.y + 60}, ${pos.x + 220 + dx/2} ${next.y + 60}, ${next.x} ${next.y + 60}`;
                            
                            return (
                                <g key={`conn-${pos.id}`}>
                                    <path 
                                        d={pathData} 
                                        fill="none" 
                                        stroke="rgba(255,255,255,0.05)" 
                                        strokeWidth="2" 
                                    />
                                    <motion.path 
                                        d={pathData}
                                        fill="none"
                                        stroke="url(#pulseGradient)"
                                        strokeWidth="2"
                                        strokeDasharray="20, 1000"
                                        animate={{ strokeDashoffset: [-1000, 1000] }}
                                        transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                                    />
                                </g>
                            );
                        })}
                    </svg>

                    {nodes.map((node) => {
                        const pos = positions.find(p => p.id === node.id) || { x: 0, y: 0 };
                        return (
                            <motion.div
                                key={node.id}
                                drag
                                dragMomentum={false}
                                onDrag={(e, info) => handleDrag(node.id, info)}
                                onMouseDown={(e) => {
                                    e.stopPropagation();
                                    setSelectedNodeId(node.id);
                                }}
                                style={{ x: pos.x, y: pos.y }}
                                className={cn(
                                    "absolute w-[240px] glass-card rounded-4xl border-2 cursor-grab active:cursor-grabbing z-20 group",
                                    selectedNodeId === node.id ? "border-primary bg-primary/5" : "border-white/5",
                                    node.type === "ingress" && "shadow-emerald-500/5",
                                    node.type === "cognition" && "shadow-violet-500/5",
                                    node.type === "synthesis" && "shadow-cyan-500/5",
                                    node.type === "egress" && "shadow-rose-500/5"
                                )}
                            >
                                <div className="p-6 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div className={cn(
                                            "h-10 w-10 rounded-xl flex items-center justify-center",
                                            node.type === "ingress" && "bg-emerald-500/10 text-emerald-500",
                                            node.type === "cognition" && "bg-violet-500/10 text-violet-500",
                                            node.type === "synthesis" && "bg-cyan-500/10 text-cyan-500",
                                            node.type === "egress" && "bg-rose-500/10 text-rose-500"
                                        )}>
                                            {node.type === "ingress" && <Database className="h-5 w-5" />}
                                            {node.type === "cognition" && <Cpu className="h-5 w-5" />}
                                            {node.type === "synthesis" && <Sparkles className="h-5 w-5" />}
                                            {node.type === "egress" && <Share2 className="h-5 w-5" />}
                                        </div>
                                        <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
                                    </div>
                                    <div className="space-y-1">
                                        <h4 className="text-xs font-bold text-white uppercase tracking-tighter">{node.label}</h4>
                                        <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">{node.type}</p>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Properties Sidebar */}
                <AnimatePresence>
                    {selectedNodeId && (
                        <motion.div 
                            initial={{ x: 400 }}
                            animate={{ x: 0 }}
                            exit={{ x: 400 }}
                            className="w-[400px] border-l border-white/5 bg-zinc-950/80 backdrop-blur-3xl z-50 p-10 space-y-12"
                        >
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-primary uppercase tracking-[0.3em]">Node Properties</span>
                                    <button onClick={() => deleteNode(selectedNodeId)} className="text-rose-500 hover:bg-rose-500/10 p-2 rounded-lg transition-colors">
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>
                                <h2 className="text-3xl font-bold text-white tracking-tighter uppercase">{selectedNode?.type} Unit</h2>
                            </div>

                            <div className="space-y-8">
                                <div className="space-y-2">
                                    <label className="text-[9px] font-bold uppercase tracking-widest text-zinc-600 ml-2">Label</label>
                                    <input 
                                        value={selectedNode?.label}
                                        onChange={(e) => updateNode(selectedNodeId, { label: e.target.value })}
                                        className="w-full bg-white/2 border border-white/5 rounded-2xl py-4 px-6 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-primary/40"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[9px] font-bold uppercase tracking-widest text-zinc-600 ml-2">Objective</label>
                                    <textarea 
                                        value={selectedNode?.desc}
                                        onChange={(e) => updateNode(selectedNodeId, { desc: e.target.value })}
                                        rows={4}
                                        className="w-full bg-white/2 border border-white/5 rounded-2xl py-4 px-6 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-primary/40 resize-none"
                                    />
                                </div>
                            </div>

                            <div className="p-8 rounded-4xl bg-primary/5 border border-primary/10 space-y-4">
                                <div className="flex items-center gap-3">
                                    <Settings2 className="h-4 w-4 text-primary" />
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-primary">Advanced Logic</span>
                                </div>
                                <p className="text-[10px] text-zinc-400 leading-relaxed font-medium">
                                    This node is connected to the {selectedNode?.type} cluster. Processing velocity is set to high-retention optimization by default.
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
            
            <style jsx global>{`
                .architect-grid {
                    background-image: 
                        linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px);
                    background-size: 40px 40px;
                }
                .node-tool {
                    display: flex;
                    align-items: center;
                    padding: 8px 16px;
                    border-radius: 12px;
                    font-size: 9px;
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    transition: all 0.2s;
                    background: rgba(255,255,255,0.02);
                    border: 1px border-white/5;
                }
                .shadow-glow-primary {
                    box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.2);
                }
            `}</style>
        </div>
    );
}

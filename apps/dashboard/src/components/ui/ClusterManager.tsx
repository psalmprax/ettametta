"use client";

import React, { useState, useEffect } from "react";
import { 
    Cpu, 
    Plus, 
    Trash2, 
    Activity, 
    ShieldCheck, 
    Server, 
    Loader2, 
    X, 
    CheckCircle2, 
    AlertCircle,
    Key
} from "lucide-react";
import { AI_GATEWAY_URL, INTERNAL_API_TOKEN } from "@/lib/config";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { withRealFallback } from "@/lib/real_first_utils";

interface Node {
    url: string;
    status: string;
    last_seen: string | null;
}

export function ClusterManager({ onClose }: { onClose: () => void }) {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [newNodeUrl, setNewNodeUrl] = useState("");
    const [provisioningNode, setProvisioningNode] = useState<string | null>(null);
    const [sshKey, setSshKey] = useState("");
    const [sshPort, setSshPort] = useState("22");
    const [isAdminToken, setAdminToken] = useState(INTERNAL_API_TOKEN);

    const fetchNodes = async () => {
        await withRealFallback(
            async () => {
                return fetch(`${AI_GATEWAY_URL}/health`);
            },
            {
                fallback: nodes,
                onSuccess: (data: any) => {
                    const nodeData = data.nodes || data.telemetry || [];
                    setNodes(Array.isArray(nodeData) ? nodeData : []);
                }
            }
        );
        setIsLoading(false);
    };

    useEffect(() => {
        fetchNodes();
        const interval = setInterval(fetchNodes, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleAddNode = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newNodeUrl) return;
        await withRealFallback(
            async () => {
                return fetch(`${AI_GATEWAY_URL}/register`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-Admin-Token': isAdminToken 
                    },
                    body: JSON.stringify({ url: newNodeUrl })
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Node added to cluster registry");
                    const addedUrl = newNodeUrl;
                    setNewNodeUrl("");
                    setIsAdding(false);
                    fetchNodes();
                    setProvisioningNode(addedUrl);
                },
                onFallback: (err: any) => {
                    toast.error("Registration Failed", {
                        description: err.message || "Unauthorized: Please provide Admin Token"
                    });
                }
            }
        );
    };

    const handleRemoveNode = async (url: string) => {
        await withRealFallback(
            async () => {
                return fetch(`${AI_GATEWAY_URL}/nodes/${encodeURIComponent(url)}`, {
                    method: 'DELETE',
                    headers: { 'X-Admin-Token': isAdminToken }
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Node removed from cluster");
                    fetchNodes();
                },
                onFallback: (err: any) => {
                    toast.error("Removal Failed", { description: err.message });
                }
            }
        );
    };

    const handleProvision = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!provisioningNode || !sshKey) return;
        
        const ipMatch = provisioningNode.match(/h?t?t?p?s?:\/\/(.*?):/);
        const ip = ipMatch ? ipMatch[1] : provisioningNode;

        await withRealFallback(
            async () => {
                return fetch(`${AI_GATEWAY_URL}/nodes/provision`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-Admin-Token': isAdminToken 
                    },
                    body: JSON.stringify({
                        ip: ip,
                        ssh_key: sshKey,
                        port: parseInt(sshPort) || 22
                    })
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Provisioning started in background");
                    setProvisioningNode(null);
                    setSshKey("");
                    fetchNodes();
                },
                onFallback: (err: any) => {
                    toast.error("Provisioning failed", { description: err.message });
                }
            }
        );
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="w-full max-w-4xl bg-zinc-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
                
                {/* Header */}
                <div className="p-8 border-b border-white/5 flex items-center justify-between bg-linear-to-r from-zinc-950 to-zinc-900 shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-neon-cyan/20 rounded-2xl animate-pulse-slow">
                            <Cpu className="h-8 w-8 text-neon-cyan" />
                        </div>
                        <div>
                            <h2 className="text-3xl font-black text-white uppercase tracking-tighter">Cluster Topology</h2>
                            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest leading-none">Neural Infrastructure Management</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                        <X className="h-6 w-6 text-zinc-500" />
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    <div className="space-y-8">
                        {/* Admin Auth Section */}
                        <div className="p-5 bg-zinc-900/40 rounded-2xl border border-white/5 flex items-center gap-4 shadow-inner">
                            <div className="p-2 bg-zinc-800 rounded-lg">
                                <ShieldCheck className="h-5 w-5 text-zinc-400" />
                            </div>
                            <div className="flex-1">
                                <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest mb-1">Administrative Privileges</p>
                                <input 
                                    type="password"
                                    placeholder="ENTER MASTER ACCESS TOKEN"
                                    value={isAdminToken}
                                    onChange={(e) => setAdminToken(e.target.value)}
                                    className="bg-transparent border-none outline-none text-[10px] font-black tracking-widest text-white w-full uppercase placeholder:text-zinc-800"
                                />
                            </div>
                        </div>

                        {/* Nodes Status Grid */}
                        <div className="space-y-6">
                            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-neon-cyan animate-pulse" />
                                    <h3 className="text-sm font-black text-white uppercase tracking-widest">Active Neural Grid</h3>
                                </div>
                                <button 
                                    onClick={() => setIsAdding(true)}
                                    className="flex items-center gap-2 px-6 py-2.5 bg-white text-black text-[10px] font-black uppercase tracking-widest rounded-full hover:bg-neon-cyan transition-all transform hover:scale-105 active:scale-95"
                                >
                                    <Plus className="h-3 w-3" />
                                    Deploy Node
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                {isLoading ? (
                                    <div className="col-span-full py-20 flex flex-col items-center justify-center gap-6">
                                        <div className="relative">
                                            <Loader2 className="h-12 w-12 text-zinc-800 animate-spin" />
                                            <Cpu className="h-6 w-6 text-neon-cyan absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                                        </div>
                                        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 animate-pulse">Syncing Neural Fabric...</span>
                                    </div>
                                ) : nodes.length === 0 ? (
                                    <div className="col-span-full py-20 text-center border-2 border-dashed border-white/5 rounded-[40px] bg-zinc-950/50">
                                        <div className="mb-4 flex justify-center text-zinc-800">
                                            <Server className="h-16 w-16" />
                                        </div>
                                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-700 max-w-xs mx-auto">Grid is currently disconnected. Initiate deployment to stabilize infrastructure.</p>
                                    </div>
                                ) : nodes.map((node) => (
                                    <div key={node.url} className="group relative p-6 bg-zinc-900/60 border border-white/5 rounded-[32px] hover:border-white/20 hover:bg-zinc-900 transition-all duration-500 overflow-hidden">
                                        {/* Background Glow */}
                                        <div className={cn(
                                            "absolute -right-10 -top-10 w-40 h-40 blur-[80px] opacity-10 transition-opacity",
                                            node.status === "READY" ? "bg-green-500" : node.status === "PROVISIONING" ? "bg-neon-cyan" : "bg-red-500"
                                        )} />

                                        <div className="flex items-start justify-between relative z-10">
                                            <div className="flex items-center gap-4">
                                                <div className={cn(
                                                    "p-4 rounded-2xl shadow-xl transition-all duration-500",
                                                    node.status === "READY" ? "bg-green-500/10" : 
                                                    node.status === "PROVISIONING" ? "bg-neon-cyan/10" : "bg-red-500/10"
                                                )}>
                                                    <Server className={cn(
                                                        "h-6 w-6",
                                                        node.status === "READY" ? "text-green-500" : 
                                                        node.status === "PROVISIONING" ? "text-neon-cyan animate-pulse" : "text-red-500"
                                                    )} />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-black text-white tracking-widest truncate max-w-[140px] uppercase">{node.url.replace('http://', '').replace(':8122', '')}</p>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <div className={cn("w-1.5 h-1.5 rounded-full scale-110", 
                                                            node.status === "READY" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : 
                                                            node.status === "PROVISIONING" ? "bg-neon-cyan animate-ping" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
                                                        )} />
                                                        <span className="text-[9px] font-black uppercase tracking-widest text-zinc-500">{node.status}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => handleRemoveNode(node.url)}
                                                className="p-3 hover:bg-red-500 hover:text-white text-zinc-600 rounded-2xl transition-all duration-300"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </div>
                                        
                                        <div className="mt-6 flex items-center justify-between gap-4 relative z-10">
                                            {node.status === "UNCONFIGURED" || node.status === "OFFLINE" ? (
                                                <button 
                                                    onClick={() => setProvisioningNode(node.url)}
                                                    className="flex-1 py-3.5 bg-white text-black text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-neon-cyan hover:shadow-[0_0_20px_rgba(0,255,255,0.3)] transition-all transform active:scale-95"
                                                >
                                                    Configure Hardware
                                                </button>
                                            ) : (
                                                <div className="flex-1 py-3.5 bg-zinc-800/50 rounded-2xl flex items-center justify-center gap-3">
                                                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                                                    <span className="text-[10px] font-black text-white/50 uppercase tracking-widest">Neural Link Active</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Overlays / Modals */}
                <AnimatePresence mode="wait">
                    {isAdding && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 z-[60] bg-zinc-950/95 backdrop-blur-md p-8 flex flex-col items-center justify-center"
                        >
                            <motion.form 
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                onSubmit={handleAddNode} 
                                className="w-full max-w-sm space-y-8"
                            >
                                <div className="text-center">
                                    <div className="inline-block p-4 bg-white/5 rounded-3xl mb-6">
                                        <Plus className="h-10 w-10 text-white" />
                                    </div>
                                    <h4 className="text-4xl font-black text-white uppercase tracking-tighter">New Node</h4>
                                    <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mt-2">Expansion Module Integration</p>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[9px] font-black text-zinc-500 uppercase tracking-widest px-1 text-center block w-full">Hardware Endpoint URL</label>
                                    <input 
                                        autoFocus
                                        placeholder="HTTP://172.105.101.44:8122"
                                        value={newNodeUrl}
                                        onChange={(e) => setNewNodeUrl(e.target.value)}
                                        className="w-full p-5 bg-zinc-900 border border-white/10 rounded-3xl text-center text-sm font-black text-white uppercase placeholder:text-zinc-800 tracking-widest focus:border-neon-cyan/40 transition-all outline-none"
                                    />
                                </div>
                                <div className="flex gap-4">
                                    <button 
                                        type="button"
                                        onClick={() => setIsAdding(false)}
                                        className="flex-1 py-5 bg-zinc-900 border border-white/5 text-white/50 text-[10px] font-black uppercase tracking-widest rounded-3xl hover:bg-red-500/10 hover:text-red-500 transition-all"
                                    >
                                        Abort
                                    </button>
                                    <button 
                                        type="submit"
                                        className="flex-1 py-5 bg-white text-black text-[10px] font-black uppercase tracking-widest rounded-3xl hover:bg-neon-cyan hover:shadow-2xl transition-all"
                                    >
                                        Integrate
                                    </button>
                                </div>
                            </motion.form>
                        </motion.div>
                    )}

                    {provisioningNode && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 z-[60] bg-black/95 backdrop-blur-xl p-8 flex flex-col items-center justify-center overflow-y-auto"
                        >
                            <motion.form 
                                initial={{ y: 40, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                onSubmit={handleProvision} 
                                className="w-full max-w-2xl space-y-8"
                            >
                                <div className="text-center">
                                    <div className="inline-block p-5 bg-neon-cyan/10 rounded-[40px] mb-8 animate-pulse-slow">
                                        <Key className="h-12 w-12 text-neon-cyan" />
                                    </div>
                                    <h4 className="text-5xl font-black text-white uppercase tracking-tighter leading-tight">Hardened Provisioning</h4>
                                    <p className="text-xs font-bold text-zinc-500 uppercase tracking-[0.5em] mt-3">{provisioningNode.replace('http://', '')}</p>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-4">
                                        <label className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.3em] px-4">SSH Deployment Port</label>
                                        <input 
                                            placeholder="22"
                                            value={sshPort}
                                            onChange={(e) => setSshPort(e.target.value)}
                                            className="w-full p-6 bg-zinc-900 border border-white/5 rounded-3xl text-sm font-black text-white placeholder:text-zinc-800 tracking-widest focus:border-neon-cyan/40 outline-none"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        <label className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.3em] px-4">Active User</label>
                                        <div className="w-full p-6 bg-zinc-800/30 border border-white/5 rounded-3xl text-sm font-black text-white/30 tracking-widest cursor-not-allowed">
                                            ROOT (DEFAULT)
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="p-8 bg-red-950/20 border-2 border-red-500/20 rounded-[48px] relative overflow-hidden">
                                    <div className="absolute top-0 left-0 w-full h-1 bg-red-500/30" />
                                    <div className="flex gap-6 items-start">
                                        <div className="p-3 bg-red-500/10 rounded-2xl">
                                            <AlertCircle className="h-8 w-8 text-red-500" />
                                        </div>
                                        <div>
                                            <h5 className="text-[10px] font-black text-red-500 uppercase tracking-[0.2em] mb-2">Zero-Storage Handshake Protocol</h5>
                                            <p className="text-[9px] font-bold text-red-100/50 leading-relaxed uppercase tracking-widest">
                                                This private key is held strictly in volatile RAM. It is never saved to disk 
                                                and is purged immediately upon task resolution. Architecture confirms 
                                                ephemeral usage–zero persistence.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <div className="flex justify-between px-4">
                                        <label className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.3em]">Neural Access Credentials (Ephemeral)</label>
                                        <span className="text-[8px] font-black text-neon-cyan/50 uppercase tracking-[0.3em] font-mono">ONE-TIME DEPLOYMENT KEY</span>
                                    </div>
                                    <textarea 
                                        autoFocus
                                        data-gramm="false"
                                        data-gramm_editor="false"
                                        data-enable-grammarly="false"
                                        placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
                                        rows={10}
                                        value={sshKey}
                                        onChange={(e) => setSshKey(e.target.value)}
                                        className="w-full p-8 bg-zinc-950/50 border border-white/5 rounded-[40px] text-[10px] font-mono text-neon-cyan focus:border-neon-cyan/40 outline-none leading-relaxed shadow-inner"
                                    />
                                </div>
                                
                                <div className="flex gap-6 pb-8">
                                    <button 
                                        type="button"
                                        onClick={() => { setProvisioningNode(null); setSshKey(""); }}
                                        className="flex-1 py-6 bg-zinc-900/50 border border-white/5 text-white text-[12px] font-black uppercase tracking-widest rounded-3xl hover:bg-red-500/10 hover:border-red-500/20 hover:text-red-500 transition-all transform hover:-translate-y-1"
                                    >
                                        Disengage
                                    </button>
                                    <button 
                                        type="submit"
                                        className="flex-[2] py-6 bg-[#22d3ee] text-black text-[12px] font-black uppercase tracking-[0.2em] rounded-3xl hover:bg-white transition-all transform hover:-translate-y-1 shadow-[0_20px_50px_rgba(0,255,255,0.2)]"
                                    >
                                        Confirm & Deploy
                                    </button>
                                </div>
                            </motion.form>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

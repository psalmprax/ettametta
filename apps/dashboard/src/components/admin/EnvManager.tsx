"use client";

import React, { useState, useEffect } from "react";
import { 
    Upload, 
    FileText, 
    ShieldCheck, 
    AlertCircle, 
    RefreshCw, 
    CheckCircle2,
    Lock,
    Eye,
    EyeOff,
    Search,
    Power,
    TriangleAlert
} from "lucide-react";
import { API_BASE } from "@/lib/config";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface EnvKey {
    keys: string[];
    count: number;
}

export default function EnvManager() {
    const [envData, setEnvData] = useState<EnvKey | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isUploading, setIsUploading] = useState(false);
    const [isRestarting, setIsRestarting] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [showRestartConfirm, setShowRestartConfirm] = useState(false);

    const fetchEnvKeys = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem("et_token");
            const response = await fetch(`${API_BASE}/admin/system/env`, {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setEnvData(data);
            }
        } catch (error) {
            console.error("Failed to fetch env keys:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchEnvKeys();
    }, []);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const token = localStorage.getItem("et_token");
            const response = await fetch(`${API_BASE}/admin/system/env/upload`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                toast.success("Protocol Updated", {
                    description: data.message
                });
                fetchEnvKeys();
            } else {
                const errorData = await response.json();
                toast.error("Validation Failed", {
                    description: errorData.detail?.message || "Invalid .env format"
                });
            }
        } catch (error) {
            toast.error("Upload Error", {
                description: "Failed to communicate with the master node."
            });
        } finally {
            setIsUploading(false);
            if (event.target) event.target.value = "";
        }
    };

    const handleRestart = async () => {
        setIsRestarting(true);
        setShowRestartConfirm(false);
        try {
            const token = localStorage.getItem("et_token");
            const response = await fetch(`${API_BASE}/admin/system/restart`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (response.ok) {
                toast.loading("System Reboot Initiated...", {
                    description: "Standby while the kernel synchronizes.",
                    duration: 10000
                });
                
                // Wait for the server to go down and come back up
                setTimeout(() => {
                    const checkHealth = setInterval(async () => {
                        try {
                            const health = await fetch(`${API_BASE.replace("/api/v1", "")}/health`);
                            if (health.ok) {
                                clearInterval(checkHealth);
                                setIsRestarting(false);
                                toast.success("Kernel Synchronized", {
                                    description: "System is back online."
                                });
                                fetchEnvKeys();
                            }
                        } catch (e) {
                            // Still down
                        }
                    }, 2000);
                }, 3000);
            }
        } catch (error) {
            setIsRestarting(false);
            toast.error("Process Error", {
                description: "Failed to send the termination signal."
            });
        }
    };

    const filteredKeys = envData?.keys.filter(k => 
        k.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
        <section className="relative card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl overflow-hidden">
            {isRestarting && (
                <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center space-y-6">
                    <RefreshCw className="h-16 w-16 text-red-500 animate-spin" />
                    <div className="text-center">
                        <h4 className="text-2xl font-black text-white uppercase">System <span className="text-hollow">Rebooting</span></h4>
                        <p className="text-zinc-500 text-sm mt-2">Diverting power for kernel synchronization...</p>
                    </div>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                        <Lock className="h-8 w-8 text-red-500" />
                    </div>
                    <div>
                        <h3 className="text-3xl font-black text-white uppercase tracking-tighter">Environment <span className="text-hollow">Master</span></h3>
                        <p className="text-zinc-500 text-sm">Direct manipulation of the production .env protocol.</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => setShowRestartConfirm(true)}
                        className="flex items-center gap-3 px-6 py-3 rounded-xl transition-all font-bold text-[10px] uppercase tracking-widest border border-red-500/20 bg-red-500/10 text-red-500 hover:bg-red-500/20"
                    >
                        <Power className="h-4 w-4" />
                        Restart Protocol
                    </button>

                    <label className={cn(
                        "flex items-center gap-3 px-6 py-3 rounded-xl cursor-pointer transition-all font-bold text-[10px] uppercase tracking-widest border border-white/10 hover:bg-white/5",
                        isUploading ? "opacity-50 pointer-events-none" : "bg-zinc-900/50"
                    )}>
                        {isUploading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                        {isUploading ? "Uploading..." : "Upload .env"}
                        <input type="file" className="hidden" onChange={handleFileUpload} accept=".env" />
                    </label>
                </div>
            </div>

            {showRestartConfirm && (
                <div className="p-8 rounded-3xl bg-zinc-950 border border-red-500/30 space-y-6 animate-in fade-in zoom-in duration-300">
                    <div className="flex items-start gap-6">
                        <div className="h-12 w-12 rounded-xl bg-red-500/20 flex items-center justify-center shrink-0">
                            <TriangleAlert className="h-6 w-6 text-red-500" />
                        </div>
                        <div className="space-y-2">
                            <h4 className="text-lg font-black text-white uppercase">Confirm System Cycler</h4>
                            <p className="text-zinc-500 text-sm leading-relaxed">This will terminate the API process to force a Docker reboot. Active sessions might experience a momentary disconnect. Continue?</p>
                        </div>
                    </div>
                    <div className="flex items-center justify-end gap-4">
                        <button onClick={() => setShowRestartConfirm(false)} className="px-6 py-2 text-[10px] font-black uppercase text-zinc-500 hover:text-white transition-colors">Cancel</button>
                        <button onClick={handleRestart} className="px-8 py-3 bg-red-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-red-600 transition-all shadow-[0_0_20px_rgba(239,68,68,0.3)]">Initiate Restart</button>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 pt-6 border-t border-white/5">
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Active Protocol Keys</h4>
                        <span className="text-[10px] font-bold text-red-500 px-2 py-0.5 rounded bg-red-500/10">{envData?.count || 0} Total</span>
                    </div>

                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600" />
                        <input 
                            type="text" 
                            placeholder="Filter configuration..."
                            className="w-full bg-zinc-950/50 border border-white/5 rounded-xl py-4 pl-12 pr-6 text-white text-sm outline-none focus:border-red-500/50 transition-colors"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    <div className="max-h-[300px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                        {isLoading ? (
                            Array(5).fill(0).map((_, i) => (
                                <div key={i} className="h-12 w-full bg-white/5 rounded-lg animate-pulse" />
                            ))
                        ) : filteredKeys.map(key => (
                            <div key={key} className="flex items-center justify-between p-4 bg-zinc-900/30 border border-white/5 rounded-xl hover:border-white/10 transition-colors group">
                                <span className="font-mono text-xs text-zinc-300">{key}</span>
                                <CheckCircle2 className="h-4 w-4 text-emerald-500/30 group-hover:text-emerald-500 transition-colors" />
                            </div>
                        ))}
                    </div>
                </div>

                <div className="space-y-6">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Security Protocol</h4>
                    <div className="p-8 rounded-3xl bg-red-500/5 border border-red-500/10 space-y-6">
                        <div className="flex items-start gap-4">
                            <ShieldCheck className="h-6 w-6 text-red-500 mt-1" />
                            <div>
                                <p className="text-white font-bold text-sm mb-1">Backup Protection</p>
                                <p className="text-zinc-500 text-xs leading-relaxed">Each upload automatically generates a timestamped backup in the root directory. Reversion is possible via terminal.</p>
                            </div>
                        </div>

                        <div className="flex items-start gap-4">
                            <AlertCircle className="h-6 w-6 text-amber-500 mt-1" />
                            <div>
                                <p className="text-white font-bold text-sm mb-1">State Persistence</p>
                                <p className="text-zinc-500 text-xs leading-relaxed">Changes to .env are hot-swapped for the API but require a <strong>Restart Protocol</strong> to sync Workers and external nodes.</p>
                            </div>
                        </div>

                        <div className="flex items-start gap-4">
                            <FileText className="h-6 w-6 text-zinc-400 mt-1" />
                            <div>
                                <p className="text-white font-bold text-sm mb-1">Validation Engine</p>
                                <p className="text-zinc-500 text-xs leading-relaxed">Regex-based sanity checks prevent malformed configuration from reaching the production kernel.</p>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 rounded-3xl bg-zinc-950/50 border border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
                                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                            </div>
                            <span className="text-xs font-bold text-zinc-300 tracking-wider uppercase">Kernel Synchronized</span>
                        </div>
                        <button onClick={fetchEnvKeys} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                            <RefreshCw className={cn("h-4 w-4 text-zinc-500", isLoading && "animate-spin")} />
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
}

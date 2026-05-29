"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
    Key,
    Database,
    Shield,
    Bell,
    Server,
    Save,
    EyeOff,
    Eye,
    CheckCircle2,
    Cpu,
    Loader2,
    Layout,
    User,
    CreditCard,
    Sparkles,
    Wand2,
    Film,
    Bot,
    Workflow,
    Code,
    ShoppingCart,
    TrendingUp,
    Globe,
    Link2,
    Unlink,
    RefreshCw,
    Phone,
    Send,
    Terminal,
    Activity,
    Radio,
    ChevronRight,
    Fingerprint,
    Lock,
    Settings,
    ShieldCheck,
    Dna,
    Target,
    Clock
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { ThemeSwitcher } from "@/components/theme-toggle";
import { Button } from "@/components/ui/Button";

const SettingsSchema = z.object({
    groq_api_key: z.string().optional(),
    youtube_api_key: z.string().optional(),
    elevenlabs_api_key: z.string().optional(),
    active_monetization_strategy: z.string().optional(),
});

type SettingsValues = z.infer<typeof SettingsSchema>;

export default function SettingsPage() {
    const [activeEngine, setActiveEngine] = useState("identity");
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [showKey, setShowKey] = useState<Record<string, boolean>>({});
    const [logs, setLogs] = useState<string[]>(["IDENTITY_INITIALIZED", "PROTOCOL_READY"]);
    const { agents, logs: systemLogs, status, pulse } = useTelemetry();
    
    const { register, handleSubmit, reset } = useForm<SettingsValues>({
        resolver: zodResolver(SettingsSchema)
    });

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback((signal) => fetch(`${API_BASE}/settings/`, { headers: { Authorization: `Bearer ${token}` }, signal }),
            { fallback: null, onSuccess: (data: any) => reset(data) }
        );
        setIsLoading(false);
    }, [reset]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleSave = handleSubmit(async (data) => {
        setIsSaving(true);
        setLogs((prev: string[]) => [`[PROTOCOL] Committing personal identity updates...`, ...prev]);
        const token = await getAuthToken();
        if (!token) return;
        
        const payload = Object.entries(data).map(([key, value]) => ({
            key,
            value: String(value ?? ""),
            category: "api_key"
        }));

        await withRealFallback((signal) => fetch(`${API_BASE}/settings/user`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload),
                signal
            }),
            {
                fallback: null,
                onSuccess: () => {
                    toast.success("Protocol Updated");
                    setLogs((prev: string[]) => [`[SUCCESS] Identity synchronized with neural vault.`, ...prev]);
                    reset(data);
                }
            }
        );
        setIsSaving(false);
    });

    // Remove mocked agents; using real agents from useTelemetry

    return (
        <CommandCenterLayout
          title="CORE CONFIG"
          subtitle="CENTRAL_COMMAND_V4.0"
          leftPanel={
            <div className="space-y-1">
              {[
                { id: "identity", label: "Neural Identity", icon: Fingerprint },
                { id: "security", label: "Security Hub", icon: Lock },
                { id: "infrastructure", label: "Infrastructure", icon: Server },
                { id: "operations", label: "Operations", icon: Settings },
                { id: "logs", label: "Session Logs", icon: Terminal },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveEngine(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                    activeEngine === item.id ? "bg-violet-500/10 text-violet-400 border border-violet-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                  {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.5)]" />}
                </button>
              ))}
            </div>
          }
          rightPanel={
            <>
              <AgentMatrix agents={agents} />
              <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Aesthetic Mode</h4>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-400 font-bold uppercase">Theme Engine</span>
                  <ThemeSwitcher />
                </div>
              </div>
              <Button onClick={handleSave} disabled={isSaving} className="w-full bg-violet-500 hover:bg-violet-400 text-white font-bold h-14 rounded-2xl">
                {isSaving ? "Synchronizing..." : "Commit Protocol"}
              </Button>
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
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-10">
                  {activeEngine === "identity" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                       <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                         <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Administrator Alias</span>
                         <h3 className="text-2xl font-bold text-white uppercase tracking-tight">User_Sovereign</h3>
                       </div>
                       <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                         <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Clearance Level</span>
                         <h3 className="text-2xl font-bold text-violet-400 uppercase tracking-tight">Level 5 (Admin)</h3>
                       </div>
                    </div>
                  )}

                  {activeEngine === "security" && (
                    <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-12">
                       <div className="space-y-8">
                          {[
                              { label: "GROQ_API_KEY", id: "groq_api_key" },
                              { label: "YOUTUBE_API_KEY", id: "youtube_api_key" },
                              { label: "ELEVEN_LABS_KEY", id: "elevenlabs_api_key" },
                          ].map((key) => (
                              <div key={key.id} className="space-y-4">
                                  <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{key.label}</label>
                                  <div className="relative">
                                      <input
                                          type={showKey[key.id] ? "text" : "password"}
                                          {...register(key.id as any)}
                                          className="w-full h-16 bg-black/60 border border-white/10 rounded-2xl px-6 text-white font-mono text-xs tracking-widest focus:border-violet-500/50 outline-none"
                                      />
                                      <button
                                          type="button"
                                          onClick={() => setShowKey(prev => ({ ...prev, [key.id]: !prev[key.id] }))}
                                          className="absolute right-6 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-white"
                                      >
                                          {showKey[key.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                      </button>
                                  </div>
                              </div>
                          ))}
                       </div>
                    </div>
                  )}
                </div>

                <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                  <div className="p-4 border-b border-white/5 flex items-center justify-between">
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Session Logs</span>
                    <span className="text-[8px] font-mono text-violet-500/50">IDENTITY_HUB_ACTIVE</span>
                  </div>
                  <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                    {logs.map((log, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                        <span className={cn(
                          log.includes("[PROTOCOL]") ? "text-cyan-400" :
                          log.includes("[SUCCESS]") ? "text-emerald-500" : "text-zinc-600"
                        )}>{log}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </CommandCenterLayout>
    );
}

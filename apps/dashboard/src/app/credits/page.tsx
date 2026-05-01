"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    Coins,
    CreditCard,
    Zap,
    RefreshCw,
    Copy,
    Check,
    Gift,
    Clock,
    TrendingUp,
    Share2,
    Users,
    Activity,
    Vault,
    Package,
    History,
    Network,
    ShieldCheck,
    Terminal,
    Database,
    Cpu
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE, WS_BASE } from "@/lib/config";
import { toast } from "sonner";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix, AssetQuickview } from "@/components/ui/CommandCenterComponents";
import { DesignCard } from "@/components/ui/DesignCard";
import { Button } from "@/components/ui/Button";

interface CreditBalance {
    balance: number;
    tier: string;
    tier_discount_percent: number;
}

interface Transaction {
    id: string;
    created_at: string;
    action: string;
    amount: number;
    balance_after: number;
}

export default function CreditsPage() {
    const [activeEngine, setActiveEngine] = useState("vault");
    const [balance, setBalance] = useState<CreditBalance | null>(null);
    const [costs, setCosts] = useState<any[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [referralCode, setReferralCode] = useState<any>(null);
    const [packages, setPackages] = useState<any[]>([]);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [logs, setLogs] = useState<string[]>(["VAULT_INITIALIZED", "SYNCHRONIZING_LEDGER"]);

    const fetchData = useCallback(async () => {
        setIsRefreshing(true);
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback(() => fetch(`${API_BASE}/credits/balance`, { headers }), { fallback: null, onSuccess: setBalance }),
            withRealFallback(() => fetch(`${API_BASE}/credits/costs`, { headers }), { fallback: [], onSuccess: setCosts }),
            withRealFallback(() => fetch(`${API_BASE}/credits/transactions`, { headers }), { fallback: [], onSuccess: setTransactions }),
            withRealFallback(() => fetch(`${API_BASE}/credits/referral/code`, { headers }), { fallback: null, onSuccess: setReferralCode }),
            withRealFallback(() => fetch(`${API_BASE}/credits/packages`, { headers }), { fallback: [], onSuccess: setPackages }),
        ]);
        setIsRefreshing(false);
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handlePurchase = async (packageId: string) => {
        const token = await getAuthToken();
        if (!token) return;

        setLogs((prev: string[]) => [`[PROTOCOL] Initializing Credit Acquisition: ${packageId}`, ...prev]);
        await withRealFallback(
            () => fetch(`${API_BASE}/credits/purchase`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ package_id: packageId })
            }),
            {
                fallback: null,
                onSuccess: (data: any) => {
                    if (data.checkout_url || data.url) window.location.href = data.checkout_url || data.url;
                }
            }
        );
    };

    // Prepare Agent Data
    const agents = [
        { id: "FIN_01", name: "Ledger Guard", icon: ShieldCheck, status: "ACTIVE" as any, latency: 2, load: 1, details: "Syncing Transactions" },
        { id: "VAULT_01", name: "Vault Warden", icon: Vault, status: "ACTIVE" as any, latency: 4, load: 1, details: "Resource Secure" },
        { id: "NODE_01", name: "Referral Linker", icon: Network, status: "IDLE" as any, latency: 1, load: 0, details: "Standby" },
    ];

    return (
        <CommandCenterLayout
          title="CREDIT VAULT"
          subtitle="RESOURCE_ALLOCATION_V4.0"
          leftPanel={
            <div className="space-y-1">
              {[
                { id: "vault", label: "Credit Vault", icon: Vault },
                { id: "acquisition", label: "Acquisition", icon: Package },
                { id: "history", label: "Ledger", icon: History },
                { id: "network", label: "Neural Network", icon: Network },
                { id: "logs", label: "Resource Logs", icon: Terminal },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveEngine(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                    activeEngine === item.id ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                  {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.5)]" />}
                </button>
              ))}
            </div>
          }
          rightPanel={
            <>
              <AgentMatrix agents={agents} />
              <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Vault Balance</h4>
                <div className="flex flex-col">
                  <span className="text-2xl font-bold text-white">{balance?.balance || 0} CR</span>
                  <span className="text-[8px] text-cyan-400 font-bold uppercase tracking-widest">{balance?.tier || "Free"} Status</span>
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
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-10">
                  {activeEngine === "vault" && (
                    <div className="h-full flex flex-col justify-center items-center text-center space-y-8">
                       <div className="relative">
                         <div className="absolute inset-0 bg-cyan-400/20 blur-[100px] rounded-full animate-pulse" />
                         <h2 className="text-9xl font-bold text-white tracking-tighter relative z-10">{balance?.balance || 0}</h2>
                       </div>
                       <div className="space-y-2">
                         <span className="text-2xl font-bold text-cyan-400 uppercase tracking-widest">Neural Credits Available</span>
                         <p className="text-zinc-600 text-[10px] font-bold uppercase tracking-[0.4em]">Allocated for autonomous synthesis</p>
                       </div>
                    </div>
                  )}

                  {activeEngine === "acquisition" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                      {packages.map((pkg) => (
                        <div key={pkg.id} className="p-10 rounded-[40px] bg-[#0F0F11]/60 border border-white/5 space-y-10 group hover:border-cyan-500/20 transition-all">
                          <div className="space-y-4">
                            <h3 className="text-2xl font-bold text-white uppercase tracking-tight">{pkg.name}</h3>
                            <span className="text-4xl font-bold text-white tracking-tighter">{pkg.price_formatted}</span>
                          </div>
                          <ul className="space-y-3">
                            {pkg.features?.map((f: string, i: number) => (
                              <li key={i} className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                                <div className="h-1 w-1 bg-cyan-400 rounded-full" /> {f}
                              </li>
                            ))}
                          </ul>
                          <Button onClick={() => handlePurchase(pkg.id)} className="w-full bg-cyan-500 text-black font-bold h-14 rounded-2xl">Acquire</Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {activeEngine === "history" && (
                    <div className="space-y-4">
                      {transactions.map((tx) => (
                        <div key={tx.id} className="p-6 rounded-[24px] bg-[#0F0F11]/60 border border-white/5 flex items-center justify-between group hover:border-cyan-500/20 transition-all">
                          <div className="flex items-center gap-6">
                            <div className={cn("h-12 w-12 rounded-xl flex items-center justify-center", tx.amount > 0 ? "bg-emerald-500/10 text-emerald-500" : "bg-white/5 text-zinc-700")}>
                              {tx.amount > 0 ? <TrendingUp className="h-6 w-6" /> : <Clock className="h-6 w-6" />}
                            </div>
                            <div>
                              <h4 className="text-sm font-bold text-white uppercase">{tx.action}</h4>
                              <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">{new Date(tx.created_at).toLocaleString()}</p>
                            </div>
                          </div>
                          <span className={cn("text-lg font-bold tabular-nums", tx.amount > 0 ? "text-emerald-400" : "text-zinc-500")}>
                            {tx.amount > 0 ? "+" : ""}{tx.amount}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                  <div className="p-4 border-b border-white/5 flex items-center justify-between">
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Resource Logs</span>
                    <span className="text-[8px] font-mono text-cyan-500/50">VAULT_LEDGER_ACTIVE</span>
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

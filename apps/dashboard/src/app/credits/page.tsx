"use client";

import React, { useState, useEffect, useCallback } from "react";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import {
    Clock,
    TrendingUp,
    Vault,
    Package,
    History,
    Network,
    Terminal,
    BarChart3
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";
import { EngineSidebar } from "@/components/shared/EngineSidebar";
import { LogsPanel } from "@/components/shared/LogsPanel";
import { PageShell } from "@/components/shared/PageShell";

/** Module-internal — do not consume from outside. */
interface CreditBalance {
    balance: number;
    tier: string;
    tier_discount_percent: number;
}

/** Module-internal — do not consume from outside. */
interface Transaction {
    id: string;
    created_at: string;
    action: string;
    amount: number;
    balance_after: number;
}

/** Module-internal — do not consume from outside. */
interface UsageBreakdown {
    total_spent: number;
    by_action: Record<string, number>;
    action_count: number;
}

export default function CreditsPage() {
    const [activeEngine, setActiveEngine] = useState("vault");
    const [balance, setBalance] = useState<CreditBalance | null>(null);
    const [_costs, setCosts] = useState<any[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [_referralCode, setReferralCode] = useState<any>(null);
    const [packages, setPackages] = useState<any[]>([]);
    const [usage, setUsage] = useState<UsageBreakdown | null>(null);
    const [usageMonth, setUsageMonth] = useState<string>(() => {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    });
    const [_isRefreshing, setIsRefreshing] = useState(false);
    const [logs, setLogs] = useState<string[]>(["VAULT_INITIALIZED", "SYNCHRONIZING_LEDGER"]);
    const { agents, logs: _systemLogs, status: _status, pulse: _pulse } = useTelemetry();

    const fetchData = useCallback(async () => {
        setIsRefreshing(true);
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback((signal) => fetch(`${API_BASE}/credits/balance`, { headers, signal }), { fallback: null, onSuccess: setBalance }),
            withRealFallback((signal) => fetch(`${API_BASE}/credits/costs`, { headers, signal }), { fallback: [], onSuccess: setCosts }),
            withRealFallback((signal) => fetch(`${API_BASE}/credits/transactions`, { headers, signal }), { fallback: [], onSuccess: setTransactions }),
            withRealFallback((signal) => fetch(`${API_BASE}/credits/referral/code`, { headers, signal }), { fallback: null, onSuccess: setReferralCode }),
            withRealFallback((signal) => fetch(`${API_BASE}/credits/packages`, { headers, signal }), { fallback: [], onSuccess: setPackages }),
            withRealFallback((signal) => fetch(`${API_BASE}/credits/usage?month=${usageMonth}`, { headers, signal }), { fallback: null, onSuccess: setUsage }),
        ]);
        setIsRefreshing(false);
    }, [usageMonth]);

    useEffect(() => {
        fetchData();
    }, [fetchData, usageMonth]);

    // Generate month options: current month and 5 previous
    const monthOptions = React.useMemo(() => {
        const options: { value: string; label: string }[] = [];
        const now = new Date();
        for (let i = 0; i < 6; i++) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            const label = d.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
            options.push({ value, label });
        }
        return options;
    }, []);

    const handlePurchase = async (packageId: string) => {
        const token = await getAuthToken();
        if (!token) return;

        setLogs((prev: string[]) => [`[PROTOCOL] Initializing Credit Acquisition: ${packageId}`, ...prev]);
        await withRealFallback((signal) => fetch(`${API_BASE}/credits/purchase`, {
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

    // Using real agents from useTelemetry

    return (
        <CommandCenterLayout
          title="CREDIT VAULT"
          subtitle="RESOURCE_ALLOCATION_V4.0"
          leftPanel={
            <EngineSidebar
              items={[
                { id: "vault", label: "Credit Vault", icon: Vault },
                { id: "spending", label: "Spending", icon: BarChart3 },
                { id: "acquisition", label: "Acquisition", icon: Package },
                { id: "history", label: "Ledger", icon: History },
                { id: "network", label: "Neural Network", icon: Network },
                { id: "logs", label: "Resource Logs", icon: Terminal },
              ]}
              activeId={activeEngine}
              onSelect={setActiveEngine}
              accentColor="cyan"
            />
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
          <PageShell activeKey={activeEngine}>
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

                  {activeEngine === "spending" && usage && (
                    <div className="space-y-8">
                      {/* Month selector */}
                      <div className="flex items-end justify-between">
                        <div className="space-y-1">
                          <h3 className="text-lg font-bold text-white uppercase tracking-tight">Monthly Spend</h3>
                          <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-[0.3em]">Per-Action Breakdown</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <select
                            value={usageMonth}
                            onChange={(e) => setUsageMonth(e.target.value)}
                            className="bg-[#0F0F11] border border-white/10 text-white text-[10px] font-bold uppercase tracking-widest px-3 py-2 rounded-xl focus:outline-none focus:border-cyan-500/40 appearance-none cursor-pointer"
                          >
                            {monthOptions.map((opt) => (
                              <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {usage.action_count > 0 && (
                        <>
                          {/* Total header */}
                          <div className="flex items-end justify-end">
                            <div className="text-right">
                              <span className="text-3xl font-bold text-white tabular-nums">{usage.total_spent}</span>
                              <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest ml-2">CR TOTAL</span>
                            </div>
                          </div>

                          {/* Horizontal bar chart */}
                          <div className="space-y-3">
                            {Object.entries(usage.by_action).map(([action, amount]) => {
                              const pct = usage.total_spent > 0 ? (amount / usage.total_spent) * 100 : 0;
                              return (
                                <div key={action} className="space-y-1.5">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                                      {action.replace(/_/g, ' ')}
                                    </span>
                                    <span className="text-xs font-bold text-white tabular-nums">
                                      {amount} <span className="text-zinc-600 font-normal">CR</span>
                                    </span>
                                  </div>
                                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                      className="h-full rounded-full"
                                      style={{
                                        width: `${pct}%`,
                                        background: `linear-gradient(90deg, #22d3ee, #06b6d4)`,
                                      }}
                                      initial={{ width: 0 }}
                                      animate={{ width: `${pct}%` }}
                                      transition={{ duration: 0.8, ease: "easeOut" }}
                                    />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </>
                      )}

                      {usage.action_count === 0 && (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                          <BarChart3 className="h-12 w-12 text-zinc-800 mb-4" />
                          <p className="text-sm font-bold text-zinc-600 uppercase tracking-wider">No spending this month</p>
                          <p className="text-[9px] text-zinc-700 font-bold uppercase tracking-[0.3em] mt-1">Generate content to see usage</p>
                        </div>
                      )}
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

                <LogsPanel logs={logs} label="Resource Logs" badge="VAULT_LEDGER_ACTIVE" accentColor="cyan" />
          </PageShell>
        </CommandCenterLayout>
    );
}

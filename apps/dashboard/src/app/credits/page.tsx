"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
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
    Users
} from "lucide-react";
import { motion, Variants } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { toast } from "sonner";

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.08,
            delayChildren: 0.1
        }
    }
};

const itemVariants: Variants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
        y: 0,
        opacity: 1,
        transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] }
    }
};

interface CreditBalance {
    balance: number;
    tier: string;
    tier_discount_percent: number;
}

interface CreditCost {
    action: string;
    base_cost: number;
    user_cost: number;
}

interface Transaction {
    id: string;
    created_at: string;
    action: string;
    amount: number;
    balance_after: number;
}

interface ReferralCode {
    code: string;
    share_url: string;
}

interface ReferralStats {
    total_referrals: number;
    credits_earned: number;
    referrals: Array<{
        id: string;
        username: string;
        created_at: string;
        credits_awarded: number;
    }>;
}

interface ReferralStatsResponse {
    total_referrals: number;
    total_credits_earned: number;
}

interface CreditPackage {
    id: string;
    name: string;
    credits: number;
    price: number;
    price_formatted: string;
    features: string[];
    popular?: boolean;
}

const PACKAGE_STYLES: Record<string, { icon: React.ReactNode; color: string; perCredit: string }> = {
    starter: {
        icon: <Zap className="h-6 w-6 text-emerald-400" />,
        color: "emerald",
        perCredit: "~$0.10/cr"
    },
    pro: {
        icon: <TrendingUp className="h-6 w-6 text-primary" />,
        color: "primary",
        perCredit: "~$0.075/cr"
    },
    enterprise: {
        icon: <CreditCard className="h-6 w-6 text-amber-400" />,
        color: "amber",
        perCredit: "~$0.05/cr"
    }
};

export default function CreditsPage() {
    const [balance, setBalance] = useState<CreditBalance | null>(null);
    const [costs, setCosts] = useState<CreditCost[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [referralCode, setReferralCode] = useState<ReferralCode | null>(null);
    const [referralStats, setReferralStats] = useState<ReferralStats | null>(null);
    const [referralStatsOverview, setReferralStatsOverview] = useState<ReferralStatsResponse | null>(null);
    const [packages, setPackages] = useState<CreditPackage[]>([]);
    const [applyCode, setApplyCode] = useState("");
    const [isPurchasing, setIsPurchasing] = useState<string | null>(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isApplying, setIsApplying] = useState(false);
    const [copied, setCopied] = useState(false);

    const authHeaders = () => {
        const token = localStorage.getItem("et_token");
        return { Authorization: `Bearer ${token}` };
    };

    const fetchBalance = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/balance`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setBalance(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchCosts = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/costs`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setCosts(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchTransactions = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/transactions`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setTransactions(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchReferralCode = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/referral/code`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setReferralCode(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchReferrals = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/referrals`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setReferralStats(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchReferralStatsOverview = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/referral/stats`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setReferralStatsOverview(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchPackages = async () => {
        try {
            const res = await fetch(`${API_BASE}/credits/packages`, {
                headers: authHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setPackages(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const refreshAll = async () => {
        setIsRefreshing(true);
        await Promise.all([
            fetchBalance(),
            fetchCosts(),
            fetchTransactions(),
            fetchReferralCode(),
            fetchReferrals(),
            fetchReferralStatsOverview(),
            fetchPackages()
        ]);
        setIsRefreshing(false);
    };

    useEffect(() => {
        refreshAll();
    }, []);

    const handlePurchase = async (packageId: string) => {
        setIsPurchasing(packageId);
        try {
            const res = await fetch(`${API_BASE}/credits/purchase`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...authHeaders()
                },
                body: JSON.stringify({ package_id: packageId })
            });
            if (res.ok) {
                const data = await res.json();
                if (data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else if (data.url) {
                    window.location.href = data.url;
                } else {
                    toast.success("Purchase initiated successfully");
                    refreshAll();
                }
            } else {
                const err = await res.json().catch(() => ({}));
                toast.error(err.detail || "Purchase failed");
            }
        } catch (err) {
            console.error(err);
            toast.error("Network error during purchase");
        } finally {
            setIsPurchasing(null);
        }
    };

    const handleApplyReferral = async () => {
        if (!applyCode.trim()) return;
        setIsApplying(true);
        try {
            const res = await fetch(`${API_BASE}/credits/referral/apply`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...authHeaders()
                },
                body: JSON.stringify({ code: applyCode.trim() })
            });
            if (res.ok) {
                toast.success("Referral code applied successfully");
                setApplyCode("");
                refreshAll();
            } else {
                const err = await res.json().catch(() => ({}));
                toast.error(err.detail || "Invalid referral code");
            }
        } catch (err) {
            console.error(err);
            toast.error("Network error applying code");
        } finally {
            setIsApplying(false);
        }
    };

    const handleCopyCode = () => {
        if (!referralCode?.share_url) return;
        navigator.clipboard.writeText(referralCode.share_url);
        setCopied(true);
        toast.success("Referral link copied to clipboard");
        setTimeout(() => setCopied(false), 2000);
    };

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            });
        } catch {
            return dateStr;
        }
    };

    return (
        <DashboardLayout>
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="section-container relative pb-20 space-y-10"
            >
                {/* Header */}
                <motion.div variants={itemVariants} className="flex items-end justify-between">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="h-1 w-8 bg-primary rounded-full shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary">Credits System</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">
                            Credit <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-500 text-hollow">Vault</span>
                        </h1>
                        <p className="text-zinc-500 font-medium">Manage your <span className="text-zinc-300 font-bold">credit balance</span>, purchase packages, and track usage.</p>
                    </div>
                    <button
                        onClick={refreshAll}
                        disabled={isRefreshing}
                        className="glass-card px-6 py-4 rounded-xl flex items-center gap-3 group hover:border-primary/50 transition-all font-black uppercase tracking-widest text-[10px]"
                    >
                        <RefreshCw className={cn("h-4 w-4 text-zinc-500 group-hover:text-primary transition-colors", isRefreshing && "animate-spin")} />
                        <span className="text-zinc-500 group-hover:text-white">Refresh</span>
                    </button>
                </motion.div>

                {/* Balance Overview */}
                <motion.div variants={itemVariants}>
                    <div className="glass-card p-8 rounded-3xl bg-primary/5 border-primary/10 relative overflow-hidden">
                        <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                            <div className="space-y-4 text-center md:text-left">
                                <div className="flex items-center gap-3 justify-center md:justify-start">
                                    <div className="h-3 w-3 rounded-full bg-primary animate-pulse shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Current Balance</span>
                                </div>
                                <div className="flex items-baseline gap-3">
                                    <h2 className="text-6xl md:text-7xl font-black text-white tracking-tighter">
                                        {balance?.balance ?? "--"}
                                    </h2>
                                    <span className="text-xl font-black text-primary uppercase tracking-tight">Credits</span>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">
                                        Tier: <span className="text-primary">{balance?.tier || "Free"}</span>
                                    </span>
                                    {balance?.tier_discount_percent ? (
                                        <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 text-[9px] font-black uppercase tracking-widest">
                                            {balance.tier_discount_percent}% Discount Active
                                        </span>
                                    ) : null}
                                </div>
                            </div>
                            <div className="h-20 w-20 rounded-3xl bg-primary/20 flex items-center justify-center border border-primary/30 shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]">
                                <Coins className="h-10 w-10 text-primary" />
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Credit Packages */}
                <motion.div variants={itemVariants} className="space-y-6">
                    <div className="flex items-center gap-3">
                        <CreditCard className="h-5 w-5 text-zinc-500" />
                        <h3 className="text-xs font-black uppercase tracking-[0.25em] text-zinc-500">Credit Packages</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {packages.length > 0 ? packages.map((pkg) => {
                            const style = PACKAGE_STYLES[pkg.id] || PACKAGE_STYLES["starter"];
                            return (
                                <motion.div
                                    key={pkg.id}
                                    whileHover={{ scale: 1.02, y: -5 }}
                                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                                    className={cn(
                                        "glass-card p-8 rounded-3xl space-y-6 relative overflow-hidden group",
                                        pkg.popular && "border-primary/40 bg-primary/5"
                                    )}
                                >
                                    {pkg.popular && (
                                        <div className="absolute top-0 right-0 bg-primary text-white text-[8px] font-black uppercase tracking-widest px-4 py-2 rounded-bl-2xl">
                                            Most Popular
                                        </div>
                                    )}
                                    <div className="space-y-4">
                                        <div className={cn(
                                            "h-12 w-12 rounded-2xl flex items-center justify-center border",
                                            style.color === "emerald" && "bg-emerald-500/10 border-emerald-500/20",
                                            style.color === "primary" && "bg-primary/10 border-primary/20",
                                            style.color === "amber" && "bg-amber-500/10 border-amber-500/20"
                                        )}>
                                            {style.icon}
                                        </div>
                                        <div className="space-y-1">
                                            <h3 className="text-xl font-black text-white uppercase tracking-tight">{pkg.name}</h3>
                                            {pkg.features && pkg.features.length > 0 && (
                                                <ul className="space-y-1">
                                                    {pkg.features.map((feature, fi) => (
                                                        <li key={fi} className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">
                                                            · {feature}
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-4xl font-black text-white tracking-tighter">{pkg.price_formatted || `$${(pkg.price / 100).toFixed(2)}`}</span>
                                            <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{style.perCredit}</span>
                                        </div>
                                        <p className="text-sm font-bold text-primary">{pkg.credits} Credits</p>
                                    </div>
                                    <button
                                        onClick={() => handlePurchase(pkg.id)}
                                        disabled={isPurchasing === pkg.id}
                                        className={cn(
                                            "w-full font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px]",
                                            pkg.popular
                                                ? "bg-primary hover:bg-primary/90 text-white shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]"
                                                : "bg-white/5 hover:bg-white/10 border border-white/10 hover:border-primary/50 text-zinc-300 hover:text-white"
                                        )}
                                    >
                                        {isPurchasing === pkg.id ? (
                                            <RefreshCw className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <CreditCard className="h-4 w-4" />
                                        )}
                                        Purchase
                                    </button>
                                </motion.div>
                            );
                        }) : (
                            <div className="col-span-3 glass-card p-12 rounded-3xl text-center">
                                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-700">Loading packages...</p>
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* Credit Costs & Transaction History */}
                <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Credit Costs */}
                    <div className="glass-card overflow-hidden rounded-3xl">
                        <div className="p-8 border-b border-white/5 bg-white/[0.02] flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                <Zap className="h-5 w-5 text-amber-500" />
                            </div>
                            <div className="space-y-0.5">
                                <h3 className="font-black uppercase tracking-tight text-white">Credit Costs</h3>
                                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Action Cost Matrix</p>
                            </div>
                        </div>
                        <div className="divide-y divide-white/5">
                            {costs.length > 0 ? costs.map((cost, i) => (
                                <div key={i} className="flex items-center justify-between p-5 hover:bg-white/[0.02] transition-all">
                                    <div className="flex items-center gap-4">
                                        <div className="h-2 w-2 rounded-full bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                                        <span className="text-sm font-bold text-white uppercase tracking-tight">{cost.action}</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        {cost.user_cost < cost.base_cost && (
                                            <span className="text-[9px] font-bold text-zinc-600 line-through uppercase tracking-widest">{cost.base_cost}</span>
                                        )}
                                        <span className={cn(
                                            "text-sm font-black tabular-nums",
                                            cost.user_cost < cost.base_cost ? "text-emerald-500" : "text-primary"
                                        )}>
                                            {cost.user_cost} <span className="text-[9px] text-zinc-600 font-bold">cr</span>
                                        </span>
                                    </div>
                                </div>
                            )) : (
                                <div className="p-12 text-center">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-zinc-700">Loading cost matrix...</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Transaction History */}
                    <div className="glass-card overflow-hidden rounded-3xl">
                        <div className="p-8 border-b border-white/5 bg-white/[0.02] flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                <Clock className="h-5 w-5 text-primary neon-glow" />
                            </div>
                            <div className="space-y-0.5">
                                <h3 className="font-black uppercase tracking-tight text-white">Transaction History</h3>
                                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Recent Credit Activity</p>
                            </div>
                        </div>
                        <div className="divide-y divide-white/5">
                            {transactions.length > 0 ? transactions.map((tx) => (
                                <div key={tx.id} className="flex items-center justify-between p-5 hover:bg-white/[0.02] transition-all">
                                    <div className="flex items-center gap-4">
                                        <div className={cn(
                                            "h-8 w-8 rounded-xl flex items-center justify-center border",
                                            tx.amount > 0
                                                ? "bg-emerald-500/10 border-emerald-500/20"
                                                : "bg-red-500/10 border-red-500/20"
                                        )}>
                                            {tx.amount > 0 ? (
                                                <TrendingUp className="h-4 w-4 text-emerald-500" />
                                            ) : (
                                                <Zap className="h-4 w-4 text-red-500" />
                                            )}
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-white uppercase tracking-tight">{tx.action}</p>
                                            <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">{formatDate(tx.created_at)}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className={cn(
                                            "text-sm font-black tabular-nums",
                                            tx.amount > 0 ? "text-emerald-500" : "text-red-500"
                                        )}>
                                            {tx.amount > 0 ? "+" : ""}{tx.amount}
                                        </p>
                                        <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest tabular-nums">
                                            Bal: {tx.balance_after}
                                        </p>
                                    </div>
                                </div>
                            )) : (
                                <div className="p-12 text-center">
                                    <Clock className="h-8 w-8 text-zinc-800 mx-auto mb-3" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-zinc-700">No transactions yet</p>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>

                {/* Referral Section */}
                <motion.div variants={itemVariants} className="space-y-6">
                    <div className="flex items-center gap-3">
                        <Gift className="h-5 w-5 text-zinc-500" />
                        <h3 className="text-xs font-black uppercase tracking-[0.25em] text-zinc-500">Referral Program</h3>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Referral Code Card */}
                        <div className="glass-card p-8 rounded-3xl space-y-6 bg-primary/5 border-primary/10 relative overflow-hidden">
                            <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                            <div className="space-y-1">
                                <h3 className="font-black uppercase tracking-tight text-white">Your Referral Code</h3>
                                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Share and earn credits</p>
                            </div>
                            <div className="space-y-4">
                                <div className="bg-zinc-950/50 rounded-2xl border border-white/10 p-5 flex items-center justify-between">
                                    <span className="text-2xl font-black text-primary tracking-[0.2em] uppercase">
                                        {referralCode?.code || "LOADING..."}
                                    </span>
                                    <button
                                        onClick={handleCopyCode}
                                        className="p-3 rounded-xl bg-primary/10 hover:bg-primary/20 border border-primary/20 transition-all"
                                    >
                                        {copied ? (
                                            <Check className="h-4 w-4 text-emerald-500" />
                                        ) : (
                                            <Copy className="h-4 w-4 text-primary" />
                                        )}
                                    </button>
                                </div>
                                <div className="flex items-center gap-3">
                                    <Share2 className="h-4 w-4 text-zinc-600" />
                                    <p className="text-[10px] font-bold text-zinc-500 truncate flex-1">
                                        {referralCode?.share_url || "Generating link..."}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Referral Stats */}
                        <div className="glass-card p-8 rounded-3xl space-y-6">
                            <div className="space-y-1">
                                <h3 className="font-black uppercase tracking-tight text-white">Referral Stats</h3>
                                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Network growth metrics</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-white/[0.02] rounded-2xl border border-white/5 p-5 text-center space-y-2">
                                    <Users className="h-6 w-6 text-blue-400 mx-auto" />
                                    <p className="text-3xl font-black text-white tracking-tighter">{referralStats?.total_referrals ?? 0}</p>
                                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Referrals</p>
                                </div>
                                <div className="bg-white/[0.02] rounded-2xl border border-white/5 p-5 text-center space-y-2">
                                    <Coins className="h-6 w-6 text-primary mx-auto" />
                                    <p className="text-3xl font-black text-white tracking-tighter">{referralStats?.credits_earned ?? 0}</p>
                                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Earned</p>
                                </div>
                            </div>
                            {referralStats?.referrals && referralStats.referrals.length > 0 && (
                                <div className="space-y-3 pt-2 border-t border-white/5">
                                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Recent Referrals</p>
                                    {referralStats.referrals.slice(0, 5).map((ref) => (
                                        <div key={ref.id} className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="h-2 w-2 rounded-full bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
                                                <span className="text-xs font-bold text-zinc-400">{ref.username}</span>
                                            </div>
                                            <span className="text-[10px] font-black text-emerald-500">+{ref.credits_awarded} cr</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Apply Referral Code */}
                        <div className="glass-card p-8 rounded-3xl space-y-6">
                            <div className="space-y-1">
                                <h3 className="font-black uppercase tracking-tight text-white">Apply Code</h3>
                                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Have a referral code?</p>
                            </div>
                            <div className="space-y-4">
                                <input
                                    id="referral-code"
                                    name="referral-code"
                                    type="text"
                                    placeholder="Enter referral code"
                                    value={applyCode}
                                    onChange={(e) => setApplyCode(e.target.value.toUpperCase())}
                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-4 text-sm text-white outline-none focus:border-primary/50 transition-all font-bold placeholder:text-zinc-600 uppercase tracking-[0.15em]"
                                />
                                <button
                                    onClick={handleApplyReferral}
                                    disabled={isApplying || !applyCode.trim()}
                                    className="w-full bg-primary hover:bg-primary/90 text-white font-black py-4 rounded-xl transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-[10px] disabled:opacity-50 shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]"
                                >
                                    {isApplying ? (
                                        <RefreshCw className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Gift className="h-4 w-4" />
                                    )}
                                    Apply Code
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Referral Statistics */}
                    <div className="glass-card p-8 rounded-3xl bg-primary/5 border-primary/10 relative overflow-hidden">
                        <div className="absolute inset-0 scanline opacity-[var(--scanline-opacity)] pointer-events-none" />
                        <div className="space-y-1 mb-6">
                            <h3 className="font-black uppercase tracking-tight text-white">Referral Statistics</h3>
                            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Overall referral performance</p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-white/[0.02] rounded-2xl border border-white/5 p-6 flex items-center gap-5">
                                <div className="h-14 w-14 rounded-2xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                                    <Users className="h-7 w-7 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-4xl font-black text-white tracking-tighter">{referralStatsOverview?.total_referrals ?? referralStats?.total_referrals ?? 0}</p>
                                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Total Referrals</p>
                                </div>
                            </div>
                            <div className="bg-white/[0.02] rounded-2xl border border-white/5 p-6 flex items-center gap-5">
                                <div className="h-14 w-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                    <Coins className="h-7 w-7 text-emerald-400" />
                                </div>
                                <div>
                                    <p className="text-4xl font-black text-white tracking-tighter">{referralStatsOverview?.total_credits_earned ?? referralStats?.credits_earned ?? 0}</p>
                                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-600">Total Credits Earned from Referrals</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </DashboardLayout>
    );
}

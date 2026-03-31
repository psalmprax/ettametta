"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
import {
    TrendingUp,
    Search,
    ArrowUpRight,
    ArrowDownRight,
    BarChart3,
    Zap,
    Globe,
    DollarSign,
    Activity,
    Sparkles,
    Loader2,
    RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { toast } from "sonner";

interface MarketData {
    symbol: string;
    price: number;
    change: number;
    change_percent: number;
    volume: number;
    high: number;
    low: number;
    market_cap?: number;
    name?: string;
}

interface CryptoData {
    id: string;
    name: string;
    symbol: string;
    price: number;
    change_24h: number;
    market_cap: number;
    volume_24h?: number;
    image?: string;
}

interface TrendingCoin {
    id: string;
    name: string;
    symbol: string;
    price?: number;
    change_24h?: number;
    market_cap?: number;
    score?: number;
}

interface ScreenerResult {
    symbol: string;
    name: string;
    price: number;
    change_percent: number;
    volume: number;
    market_cap?: number;
    sector?: string;
    signal?: string;
}

export default function TradingPage() {
    const [marketSymbol, setMarketSymbol] = useState("");
    const [marketData, setMarketData] = useState<MarketData | null>(null);
    const [isSearchingMarket, setIsSearchingMarket] = useState(false);

    const [cryptoId, setCryptoId] = useState("");
    const [cryptoData, setCryptoData] = useState<CryptoData | null>(null);
    const [isLookingUpCrypto, setIsLookingUpCrypto] = useState(false);

    const [trendingCoins, setTrendingCoins] = useState<TrendingCoin[]>([]);
    const [isLoadingTrending, setIsLoadingTrending] = useState(true);

    const [screenerResults, setScreenerResults] = useState<ScreenerResult[]>([]);
    const [isRunningScreener, setIsRunningScreener] = useState(false);

    const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    useEffect(() => {
        const fetchTrending = async () => {
            try {
                const token = localStorage.getItem("et_token");
                const res = await fetch(`${API_BASE}/trading/crypto/trending`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (res.ok) {
                    const data = await res.json();
                    setTrendingCoins(data.coins || data || []);
                } else {
                    toast.error("Failed to fetch trending cryptos");
                }
            } catch (error) {
                console.error("Failed to fetch trending cryptos:", error);
            } finally {
                setIsLoadingTrending(false);
            }
        };
        fetchTrending();
    }, []);

    const handleMarketSearch = async () => {
        if (!marketSymbol.trim()) {
            toast.error("Enter a stock symbol");
            return;
        }
        setIsSearchingMarket(true);
        setAiAnalysis(null);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/trading/market/${marketSymbol.toUpperCase()}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setMarketData(data);
                toast.success(`Loaded data for ${marketSymbol.toUpperCase()}`);
            } else {
                toast.error("Symbol not found");
                setMarketData(null);
            }
        } catch (error) {
            toast.error("Failed to fetch market data");
            setMarketData(null);
        } finally {
            setIsSearchingMarket(false);
        }
    };

    const handleCryptoLookup = async () => {
        if (!cryptoId.trim()) {
            toast.error("Enter a coin ID");
            return;
        }
        setIsLookingUpCrypto(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/trading/crypto/${cryptoId.toLowerCase()}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setCryptoData(data);
                toast.success(`Loaded data for ${cryptoId}`);
            } else {
                toast.error("Coin not found");
                setCryptoData(null);
            }
        } catch (error) {
            toast.error("Failed to fetch crypto data");
            setCryptoData(null);
        } finally {
            setIsLookingUpCrypto(false);
        }
    };

    const handleRunScreener = async () => {
        setIsRunningScreener(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/trading/screener`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setScreenerResults(data.results || data || []);
                toast.success("Screener scan complete");
            } else {
                toast.error("Screener failed");
            }
        } catch (error) {
            toast.error("Failed to run screener");
        } finally {
            setIsRunningScreener(false);
        }
    };

    const handleAiAnalysis = async () => {
        if (!marketData?.symbol) return;
        setIsAnalyzing(true);
        try {
            const token = localStorage.getItem("et_token");
            const res = await fetch(`${API_BASE}/trading/analysis/${marketData.symbol}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setAiAnalysis(data.analysis || data.insight || data.text || JSON.stringify(data));
                toast.success("AI analysis complete");
            } else {
                toast.error("Analysis failed");
            }
        } catch (error) {
            toast.error("Failed to fetch AI analysis");
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="h-1 w-8 bg-primary rounded-full" />
                            <span className="text-[10px] font-black tracking-[0.3em] text-primary uppercase">Market Intelligence</span>
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black tracking-tighter uppercase text-white leading-none">
                            Trading <span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-emerald-400 text-hollow">Terminal</span>
                        </h1>
                        <p className="text-zinc-500 mt-2 max-w-lg text-sm font-medium leading-relaxed">
                            Real-time <span className="text-zinc-300 font-bold">market intelligence</span> and AI-powered analysis for strategic positioning.
                        </p>
                    </div>
                </div>

                {/* Market Search + Crypto Lookup */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
                    {/* Stock Symbol Search */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass-card p-8 space-y-6"
                    >
                        <div className="flex items-center gap-4 border-b border-white/5 pb-6">
                            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                <BarChart3 className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                                <h3 className="text-lg font-black text-white uppercase tracking-tighter">Market Search</h3>
                                <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Equity Lookup</p>
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <input
                                type="text"
                                placeholder="Symbol (e.g. AAPL)"
                                value={marketSymbol}
                                onChange={(e) => setMarketSymbol(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleMarketSearch()}
                                className="flex-1 bg-zinc-950/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none focus:border-primary/50 transition-colors"
                            />
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleMarketSearch}
                                disabled={isSearchingMarket}
                                className="bg-primary hover:bg-primary/90 text-black font-black px-6 py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(var(--primary-rgb),0.2)] flex items-center gap-2 uppercase text-[10px] tracking-widest disabled:opacity-50"
                            >
                                {isSearchingMarket ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                                Search
                            </motion.button>
                        </div>

                        <AnimatePresence>
                            {marketData && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="space-y-4"
                                >
                                    <div className="p-6 rounded-2xl bg-zinc-950/50 border border-white/5 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <h4 className="text-2xl font-black text-white tracking-tighter">{marketData.symbol}</h4>
                                                {marketData.name && <p className="text-zinc-500 text-xs font-bold">{marketData.name}</p>}
                                            </div>
                                            <div className="text-right">
                                                <p className="text-3xl font-black text-white tabular-nums">${marketData.price?.toFixed(2)}</p>
                                                <div className={cn("flex items-center gap-1 justify-end", marketData.change >= 0 ? "text-emerald-500" : "text-red-500")}>
                                                    {marketData.change >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                                                    <span className="text-sm font-black tabular-nums">
                                                        {marketData.change >= 0 ? "+" : ""}{marketData.change?.toFixed(2)} ({marketData.change_percent?.toFixed(2)}%)
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/5">
                                            <StatBlock label="Volume" value={marketData.volume?.toLocaleString()} />
                                            <StatBlock label="High" value={`$${marketData.high?.toFixed(2)}`} />
                                            <StatBlock label="Low" value={`$${marketData.low?.toFixed(2)}`} />
                                            {marketData.market_cap && <StatBlock label="Market Cap" value={`$${(marketData.market_cap / 1e9).toFixed(2)}B`} />}
                                        </div>
                                    </div>

                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={handleAiAnalysis}
                                        disabled={isAnalyzing}
                                        className="w-full bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-500 font-black py-4 rounded-2xl transition-all flex items-center justify-center gap-3 uppercase text-[10px] tracking-widest"
                                    >
                                        {isAnalyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                                        AI Analysis
                                    </motion.button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>

                    {/* Crypto Price Lookup */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="glass-card p-8 space-y-6"
                    >
                        <div className="flex items-center gap-4 border-b border-white/5 pb-6">
                            <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                <DollarSign className="h-5 w-5 text-amber-500" />
                            </div>
                            <div>
                                <h3 className="text-lg font-black text-white uppercase tracking-tighter">Crypto Lookup</h3>
                                <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Digital Asset Intelligence</p>
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <input
                                type="text"
                                placeholder="Coin ID (e.g. bitcoin)"
                                value={cryptoId}
                                onChange={(e) => setCryptoId(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleCryptoLookup()}
                                className="flex-1 bg-zinc-950/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none focus:border-primary/50 transition-colors"
                            />
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleCryptoLookup}
                                disabled={isLookingUpCrypto}
                                className="bg-amber-500 hover:bg-amber-500/90 text-black font-black px-6 py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(245,158,11,0.2)] flex items-center gap-2 uppercase text-[10px] tracking-widest disabled:opacity-50"
                            >
                                {isLookingUpCrypto ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                                Lookup
                            </motion.button>
                        </div>

                        <AnimatePresence>
                            {cryptoData && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                >
                                    <div className="p-6 rounded-2xl bg-zinc-950/50 border border-white/5 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <h4 className="text-2xl font-black text-white tracking-tighter">{cryptoData.name}</h4>
                                                <p className="text-zinc-500 text-xs font-bold uppercase">{cryptoData.symbol}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-3xl font-black text-white tabular-nums">${cryptoData.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</p>
                                                <div className={cn("flex items-center gap-1 justify-end", (cryptoData.change_24h ?? 0) >= 0 ? "text-emerald-500" : "text-red-500")}>
                                                    {(cryptoData.change_24h ?? 0) >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                                                    <span className="text-sm font-black tabular-nums">
                                                        {(cryptoData.change_24h ?? 0) >= 0 ? "+" : ""}{cryptoData.change_24h?.toFixed(2)}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                                            <StatBlock label="Market Cap" value={`$${(cryptoData.market_cap / 1e9).toFixed(2)}B`} />
                                            {cryptoData.volume_24h && <StatBlock label="24h Volume" value={`$${(cryptoData.volume_24h / 1e9).toFixed(2)}B`} />}
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </div>

                {/* AI Analysis Panel */}
                <AnimatePresence>
                    {aiAnalysis && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className="glass-card p-8 space-y-6 mb-10 relative overflow-hidden"
                        >
                            <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-2xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                    <Sparkles className="h-6 w-6 text-amber-500" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-black text-white uppercase tracking-tighter">
                                        AI <span className="text-amber-400">Analysis</span>
                                    </h3>
                                    <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">
                                        Neural Market Assessment for {marketData?.symbol}
                                    </p>
                                </div>
                            </div>
                            <p className="text-zinc-400 text-sm font-medium leading-relaxed whitespace-pre-wrap">{aiAnalysis}</p>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Trending Cryptos */}
                <div className="glass-card p-8 space-y-6 mb-10">
                    <div className="flex items-center justify-between border-b border-white/5 pb-6">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                <TrendingUp className="h-5 w-5 text-emerald-500" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white uppercase tracking-tighter">
                                    Trending <span className="text-emerald-400">Cryptos</span>
                                </h3>
                                <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Live Market Pulse</p>
                            </div>
                        </div>
                    </div>

                    {isLoadingTrending ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                            {Array.from({ length: 8 }).map((_, i) => (
                                <div key={i} className="h-32 rounded-2xl bg-zinc-950/50 border border-white/5 animate-pulse" />
                            ))}
                        </div>
                    ) : trendingCoins.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                            {trendingCoins.map((coin, idx) => (
                                <motion.div
                                    key={coin.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    whileHover={{ y: -4 }}
                                    className="p-5 rounded-2xl bg-zinc-950/50 border border-white/5 hover:border-primary/20 transition-all space-y-3"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                                                <span className="text-[10px] font-black text-primary uppercase">{coin.symbol?.slice(0, 3)}</span>
                                            </div>
                                            <div>
                                                <p className="text-sm font-black text-white">{coin.name}</p>
                                                <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest">{coin.symbol}</p>
                                            </div>
                                        </div>
                                        {coin.score !== undefined && (
                                            <span className="text-[8px] font-black text-primary bg-primary/10 px-2 py-1 rounded-lg">#{coin.score}</span>
                                        )}
                                    </div>
                                    {coin.price !== undefined && (
                                        <div className="flex items-center justify-between pt-2 border-t border-white/5">
                                            <span className="text-xs font-black text-white tabular-nums">${coin.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</span>
                                            {coin.change_24h !== undefined && (
                                                <span className={cn("text-[10px] font-black tabular-nums", coin.change_24h >= 0 ? "text-emerald-500" : "text-red-500")}>
                                                    {coin.change_24h >= 0 ? "+" : ""}{coin.change_24h?.toFixed(2)}%
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <div className="py-12 text-center">
                            <p className="text-zinc-500 font-bold uppercase text-[10px] tracking-widest">No trending data available</p>
                        </div>
                    )}
                </div>

                {/* Market Screener */}
                <div className="glass-card p-8 space-y-6">
                    <div className="flex items-center justify-between border-b border-white/5 pb-6">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                                <Activity className="h-5 w-5 text-blue-500" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white uppercase tracking-tighter">
                                    Market <span className="text-blue-400">Screener</span>
                                </h3>
                                <p className="text-zinc-500 text-[9px] font-black uppercase tracking-widest">Opportunity Scanner</p>
                            </div>
                        </div>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleRunScreener}
                            disabled={isRunningScreener}
                            className="bg-blue-500/10 hover:bg-blue-500/20 text-blue-500 font-black py-3 px-6 rounded-xl transition-all text-[10px] uppercase tracking-widest border border-blue-500/20 flex items-center gap-2 disabled:opacity-50"
                        >
                            {isRunningScreener ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                            Run Screener
                        </motion.button>
                    </div>

                    {screenerResults.length > 0 ? (
                        <div className="overflow-hidden rounded-2xl border border-white/5 bg-white/1">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="bg-white/2 border-b border-white/5">
                                        <tr>
                                            <th className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">Symbol</th>
                                            <th className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">Name</th>
                                            <th className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">Price</th>
                                            <th className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">Change</th>
                                            <th className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">Volume</th>
                                            <th className="p-4 text-[10px] font-black text-zinc-500 uppercase tracking-widest">Signal</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {screenerResults.map((row, idx) => (
                                            <motion.tr
                                                key={`${row.symbol}-${idx}`}
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                transition={{ delay: idx * 0.03 }}
                                                className="hover:bg-white/2 transition-colors"
                                            >
                                                <td className="p-4">
                                                    <span className="text-sm font-black text-white uppercase">{row.symbol}</span>
                                                </td>
                                                <td className="p-4">
                                                    <span className="text-xs text-zinc-400 font-bold truncate max-w-[150px] block">{row.name}</span>
                                                </td>
                                                <td className="p-4">
                                                    <span className="text-xs font-black text-white tabular-nums">${row.price?.toFixed(2)}</span>
                                                </td>
                                                <td className="p-4">
                                                    <span className={cn("text-xs font-black tabular-nums", row.change_percent >= 0 ? "text-emerald-500" : "text-red-500")}>
                                                        {row.change_percent >= 0 ? "+" : ""}{row.change_percent?.toFixed(2)}%
                                                    </span>
                                                </td>
                                                <td className="p-4">
                                                    <span className="text-xs text-zinc-400 font-bold tabular-nums">{row.volume?.toLocaleString()}</span>
                                                </td>
                                                <td className="p-4">
                                                    {row.signal && (
                                                        <span className={cn(
                                                            "text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-lg",
                                                            row.signal === "buy" ? "bg-emerald-500/10 text-emerald-500" :
                                                            row.signal === "sell" ? "bg-red-500/10 text-red-500" :
                                                            "bg-zinc-500/10 text-zinc-400"
                                                        )}>
                                                            {row.signal}
                                                        </span>
                                                    )}
                                                </td>
                                            </motion.tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        !isRunningScreener && (
                            <div className="py-12 text-center">
                                <Globe className="h-10 w-10 text-zinc-700 mx-auto mb-3" />
                                <p className="text-zinc-500 font-bold uppercase text-[10px] tracking-widest">Run screener to scan for opportunities</p>
                            </div>
                        )
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}

function StatBlock({ label, value }: { label: string; value: string }) {
    return (
        <div className="space-y-1">
            <p className="text-[8px] font-black text-zinc-600 uppercase tracking-widest">{label}</p>
            <p className="text-sm font-black text-white tabular-nums">{value}</p>
        </div>
    );
}

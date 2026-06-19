"use client";

import { useCallback, useEffect, useState } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";

interface EmpireBlueprint {
    id?: string;
    niche?: string;
    name?: string;
    status?: string;
    avg_score?: number;
    total_views?: number;
}

interface RevenuePlatformStat {
    platform: string;
    revenue: number;
    views?: number;
    clicks?: number;
}

interface RevenueReport {
    total_revenue?: number;
    platforms?: RevenuePlatformStat[];
}

interface AffiliateLink {
    id?: string;
    product_name?: string;
    niche?: string;
    commission?: number | string;
    conversion_rate?: string | number;
}

interface CommerceStatus {
    status?: string;
    source?: string;
    sample_count?: number;
}

const DEFAULT_NICHES: string[] = [
    "Motivation", "AI Technology", "Finance", "Fitness",
    "Business & Entrepreneurship", "Marketing & Sales",
    "Lifestyle & Travel", "Gaming & Esports",
    "Education & E-Learning", "Real Estate",
    "E-commerce & Dropshipping", "Spirituality & Mindfulness",
    "Relationships & Dating", "Fashion & Beauty",
    "Food & Cooking", "Sports & Athletics",
    "Arts & Entertainment", "Personal Finance",
    "Crypto & Web3", "Productivity & Habits",
];

/**
 * Data hook for the Empire page.
 *
 * Polls seven monetization endpoints every 15s. The full refresh could be
 * later split into focused endpoints per active tab, but is intentionally
 * coarse here: the polling is cheap, and switching tabs re-runs `refresh()`
 * through `useEffect`'s `activeEngine` dependency.
 */
export function useEmpireData() {
    const [networkData, setNetworkData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
    const [blueprints, setBlueprints] = useState<EmpireBlueprint[]>([]);
    const [revenueReport, setRevenueReport] = useState<RevenueReport | null>(null);
    const [sentinelStatus, setSentinelStatus] = useState<any>(null);
    const [availableNiches, setAvailableNiches] = useState<string[]>(DEFAULT_NICHES);
    const [affiliateLinks, setAffiliateLinks] = useState<AffiliateLink[]>([]);
    const [commerceStatus, setCommerceStatus] = useState<CommerceStatus | null>(null);

    const refresh = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            withRealFallback<any>(
                (signal) => fetch(`${API_BASE}/no-face/sentinel/status`, { headers, signal }),
                { fallback: null, onSuccess: (data) => setSentinelStatus(data) }
            ),
            withRealFallback<RevenueReport | null>(
                (signal) => fetch(`${API_BASE}/monetization/revenue/summary?days=30`, { headers, signal }),
                { fallback: null, onSuccess: (data) => setRevenueReport(data) }
            ),
            withRealFallback<{ blueprints: EmpireBlueprint[] }>(
                (signal) => fetch(`${API_BASE}/monetization/empire/blueprints`, { headers, signal }),
                {
                    fallback: { blueprints: [] },
                    onSuccess: (data) => {
                        const list = Array.isArray(data) ? data : (data?.blueprints ?? []);
                        setBlueprints(list);
                    },
                }
            ),
            withRealFallback<RevenueReport | null>(
                (signal) => fetch(`${API_BASE}/monetization/report`, { headers, signal }),
                { fallback: null, onSuccess: (data) => setRevenueReport(data) }
            ),
            withRealFallback<any[]>(
                (signal) => fetch(`${API_BASE}/discovery/niches`, { headers, signal }),
                {
                    fallback: [],
                    onSuccess: (data: any) => {
                        const list = Array.isArray(data) ? data : (data?.data ?? []);
                        if (Array.isArray(list) && list.length > 0) {
                            setAvailableNiches(
                                list.map((n: any) =>
                                    typeof n === "string" ? n : (n?.niche ?? "General")
                                )
                            );
                        }
                    },
                    onFallback: () => setAvailableNiches(DEFAULT_NICHES),
                }
            ),
            withRealFallback<{ nodes: any[]; links: any[] }>(
                (signal) => fetch(`${API_BASE}/monetization/empire/network`, { headers, signal }),
                { fallback: { nodes: [], links: [] }, onSuccess: (data) => setNetworkData(data) }
            ),
            withRealFallback<{ links: AffiliateLink[] }>(
                (signal) => fetch(`${API_BASE}/monetization/links`, { headers, signal }),
                {
                    fallback: { links: [] },
                    onSuccess: (data) => setAffiliateLinks(
                        Array.isArray(data?.links) ? data.links : []
                    ),
                }
            ),
        ]);
    }, []);

    const syncCommerce = useCallback(async (niche: string) => {
        const token = await getAuthToken();
        if (!token) return;
        await            withRealFallback<CommerceStatus | null>(
                (signal) =>
                    fetch(`${API_BASE}/monetization/commerce/sync?niche=${encodeURIComponent(niche)}`, {
                        method: "POST",
                        headers: { Authorization: `Bearer ${token}` },
                        signal,
                    }),
                { fallback: null, onSuccess: (data) => setCommerceStatus(data) }
            );
    }, []);

    const cloneStrategy = useCallback(
        async (sourceNiche: string, targetNiche: string) => {
            const token = await getAuthToken();
            if (!token) return false;
            // withRealFallback returns the fallback (null) when the request
            // is intercepted (network failure, 401, abort, etc.). Distinguishing
            // `null` (failed) from a real response object preserves the original
            // fire-and-forget UX of handleClone without falsely reporting
            // "Strategy Cloned" on a network error.
            const result = await withRealFallback<any>(
                (signal) =>
                    fetch(`${API_BASE}/monetization/empire/clone`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                        body: JSON.stringify({
                            source_niche: sourceNiche,
                            target_niche: targetNiche,
                            auto_publish: true,
                        }),
                        signal,
                    }),
                { fallback: null }
            );
            return result !== null;
        },
        []
    );

    useEffect(() => {
        refresh();
        const interval = setInterval(refresh, 15000);
        return () => clearInterval(interval);
    }, [refresh]);

    return {
        networkData,
        blueprints,
        revenueReport,
        sentinelStatus,
        availableNiches,
        affiliateLinks,
        commerceStatus,
        refresh,
        syncCommerce,
        cloneStrategy,
    };
}

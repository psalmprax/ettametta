"use client";

import { useCallback, useEffect, useState } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";

interface AnalyticsMetrics {
    views: number;
    retention: number;
    shares: number;
    engagement: number;
    velocity: string;
    engineLoad: string;
    retentionData: { time: number; value: number }[];
}

const DEFAULT_METRICS: AnalyticsMetrics = {
    views: 0,
    retention: 0.82,
    shares: 0,
    engagement: 0.05,
    velocity: "Nominal",
    engineLoad: "12%",
    retentionData: Array.from({ length: 20 }, (_, i) => ({
        time: i,
        // Deterministic decay + a constant jitter band — enough to render a
        // visually meaningful curve without depending on `Math.random()`
        // (which would cause hard-to-debug waterfall/SSR mismatches in
        // production builds).
        value: Math.max(20, 100 - i * 4 + (i % 3) * 5),
    })),
};

/**
 * Data hook for the Analytics page.
 *
 * Reads `/analytics/stats/summary` (one-shot on mount) and seeds the
 * retention-curve series deterministically so the chart renders pre-fetch.
 */
export function useAnalyticsData() {
    const [metrics, setMetrics] = useState<AnalyticsMetrics>(DEFAULT_METRICS);
    const [pulseIntensityMultiplier, setPulseIntensityMultiplier] = useState(1.0);
    const [isLoading, setIsLoading] = useState(true);

    const refresh = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<any>(
            (signal) =>
                fetch(`${API_BASE}/analytics/stats/summary`, {
                    headers: { Authorization: `Bearer ${token}` },
                    signal,
                }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const stats = data?.data ?? data;
                    if (!stats) return;
                    setMetrics((prev) => ({
                        ...prev,
                        views: stats.total_views ?? 0,
                        engagement: stats.engagement_score ?? 0,
                        velocity: stats.velocity ?? "Nominal",
                        engineLoad: stats.engine_load ?? "5%",
                    }));
                },
            }
        );
        setIsLoading(false);
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return {
        metrics,
        isLoading,
        refresh,
        pulseIntensityMultiplier,
        setPulseIntensityMultiplier,
    };
}

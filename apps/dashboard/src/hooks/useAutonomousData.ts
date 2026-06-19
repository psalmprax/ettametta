"use client";

import { useCallback, useEffect, useState } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";

/** Module-internal — do not consume from outside. */
interface ZeroStatus {
    is_running: boolean;
    current_step: string;
    last_run: number | null;
    next_run: number | null;
}

/** Module-internal — do not consume from outside. */
interface ZeroInsight {
    title?: string;
    hook?: string;
}

/**
 * Data hook for the Autonomous (Agent Zero) page.
 *
 * Polls `/zero/status` and `/zero/insights` every 10s. Exposes a `toggle()`
 * helper that posts to `/zero/start` or `/zero/stop` based on current state.
 */
export function useAutonomousData() {
    const [isRunning, setIsRunning] = useState(false);
    const [currentStep, setCurrentStep] = useState("IDLE");
    const [lastRun, setLastRun] = useState<number | null>(null);
    const [nextRun, setNextRun] = useState<number | null>(null);
    const [insights, setInsights] = useState<ZeroInsight | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const refresh = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        const headers = { Authorization: `Bearer ${token}` };

        await Promise.all([
            // Generics include `| null` because `fallback: null` is intentional
            // — callers guard via `if (!data) return;` in `onSuccess`.
            withRealFallback<ZeroStatus | null>(
                (signal) => fetch(`${API_BASE}/zero/status`, { headers, signal }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        if (!data) return;
                        setIsRunning(!!data.is_running);
                        setCurrentStep(data.current_step ?? "IDLE");
                        setLastRun(data.last_run ?? null);
                        setNextRun(data.next_run ?? null);
                    },
                }
            ),
            withRealFallback<{ insights?: ZeroInsight } | ZeroInsight | null>(
                (signal) => fetch(`${API_BASE}/zero/insights`, { headers, signal }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        if (!data) return;
                        const insight =
                            (data as { insights?: ZeroInsight }).insights ?? (data as ZeroInsight);
                        setInsights(insight);
                    },
                }
            ),
        ]);
    }, []);

    const toggle = useCallback(
        async (action: "start" | "stop") => {
            setIsProcessing(true);
            const token = await getAuthToken();
            if (!token) {
                setIsProcessing(false);
                return null;
            }
            let message: string | null = null;
            await withRealFallback<{ message?: string } | null>(
                (signal) =>
                    fetch(`${API_BASE}/zero/${action}`, {
                        method: "POST",
                        headers: { Authorization: `Bearer ${token}` },
                        signal,
                    }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        setIsRunning(action === "start");
                        message = data?.message ?? null;
                        refresh();
                    },
                }
            );
            setIsProcessing(false);
            return message;
        },
        [refresh]
    );

    useEffect(() => {
        refresh();
        const interval = setInterval(refresh, 10000);
        return () => clearInterval(interval);
    }, [refresh]);

    return {
        isRunning,
        currentStep,
        lastRun,
        nextRun,
        insights,
        isProcessing,
        refresh,
        toggle,
    };
}

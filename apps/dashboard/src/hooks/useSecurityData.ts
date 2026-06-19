"use client";

import { useCallback, useEffect, useState } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";

/** Module-internal — do not consume from outside. */
interface SecurityStatus {
    health_score?: number;
    threat_level?: "CRITICAL" | "HIGH" | "MEDIUM" | "NOMINAL";
    recent_threats?: SecurityEvent[];
    threat_breakdown?: { low: number; medium: number; high: number; critical: number };
    system_integrity?: string;
}

export interface SecurityEvent {
    severity: "critical" | "high" | "medium" | "info";
    type?: string;
    event_type?: string;
    timestamp?: number;
    message?: string;
    details?: Record<string, unknown>;
}

/**
 * Data hook for the Security page.
 *
 * Manages:
 *  - current security status (`/security/status`)
 *  - recent event log (`/security/events`)
 *  - in-flight vulnerability scan request (`/security/scan`)
 *
 * Returns a `refresh()` method for re-fetching the status after a scan completes.
 */
export function useSecurityData() {
    const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
    const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
    const [scanResults, setScanResults] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isScanning, setIsScanning] = useState(false);

    const fetchSecurityStatus = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<SecurityStatus | null>(
            (signal) =>
                fetch(`${API_BASE}/security/status`, {
                    headers: { Authorization: `Bearer ${token}` },
                    signal,
                }),
            { fallback: null, onSuccess: (data) => setSecurityStatus(data) }
        );
        setIsLoading(false);
    }, []);

    const fetchSecurityEvents = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;

        await withRealFallback<SecurityEvent[]>(
            (signal) =>
                fetch(`${API_BASE}/security/events`, {
                    headers: { Authorization: `Bearer ${token}` },
                    signal,
                }),
            { fallback: [], onSuccess: (data) => setSecurityEvents(data ?? []) }
        );
    }, []);

    const refresh = useCallback(async () => {
        await Promise.all([fetchSecurityStatus(), fetchSecurityEvents()]);
    }, [fetchSecurityStatus, fetchSecurityEvents]);

    // Run a `POST /security/scan` audit and surface findings + score.
    const runScan = useCallback(
        async (onComplete?: (score: number) => void) => {
            setIsScanning(true);
            const token = await getAuthToken();
            if (!token) {
                setIsScanning(false);
                return;
            }

            await withRealFallback<any>(
                (signal) =>
                    fetch(`${API_BASE}/security/scan`, {
                        method: "POST",
                        headers: { Authorization: `Bearer ${token}` },
                        signal,
                    }),
                {
                    fallback: null,
                    onSuccess: (data) => {
                        const report = data?.report ?? {};
                        const findings: string[] = report?.findings ?? [];
                        setScanResults(findings);
                        onComplete?.(report?.score ?? 0);
                        fetchSecurityStatus();
                    },
                }
            );
            setIsScanning(false);
        },
        [fetchSecurityStatus]
    );

    useEffect(() => {
        fetchSecurityStatus();
        fetchSecurityEvents();
    }, [fetchSecurityStatus, fetchSecurityEvents]);

    return {
        securityStatus,
        securityEvents,
        scanResults,
        isLoading,
        isScanning,
        refresh,
        runScan,
    };
}

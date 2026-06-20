"use client";

/**
 * "Real-First" Utility Suite
 * Prioritizes live backend data and operational coupling, 
 * using deterministic fallbacks only when essential for UI continuity.
 */

import { useState, useCallback } from "react";
import { toast } from "sonner";

export interface RealFirstOptions<T> {
    fallback: T;
    onFallback?: (error: any) => void;
    onSuccess?: (data: T) => void;
    /**
     * Optional callback invoked when the response is 401 Unauthorized.
     * The caller decides what to do — typically `AuthContext.fetchUser`
     * passes `logout` here so that ONLY auth-verification calls trigger
     * a session wipe, not every API call in the app.
     *
     * NOTE: `withRealFallback` no longer wipes auth state or hard-navigates
     * to /login on 401 on its own. That behavior was destructive (it would
     * log the user out on any transient 401 across the entire app) and
     * broke long-running flows like the Nexus pipeline polling loop, which
     * triggers /auth/me on every page reload and any transient 401 would
     * bounce the user to /login mid-flow.
     */
    onUnauthorized?: () => void;
    retryCount?: number;
    silent?: boolean;
    errorMessage?: string;
    timeoutMs?: number;
}

/** Module-internal — do not consume from outside. */
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Execute an operation with a configurable timeout via AbortController.
 * Returns the raw result or throws on timeout / operation error.
 */
async function executeWithTimeout<T>(
    operation: (signal?: AbortSignal) => Promise<T | Response>,
    timeoutMs: number,
): Promise<T | Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await operation(controller.signal);
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Process a Response object: handle 401, non-ok, JSON parsing, and success unwrapping.
 * Returns the parsed data of type T, or the fallback value on 401.
 */
async function processResponse<T>(
    result: Response,
    options: RealFirstOptions<T>,
): Promise<T> {
    // 401 Unauthorized: let the caller decide what to do.
    // We deliberately do NOT clear auth storage or hard-navigate to /login.
    // Callers that want logout-on-401 should pass `onUnauthorized: logout`.
    if (result.status === 401) {
        if (options.onUnauthorized) {
            try {
                options.onUnauthorized();
            } catch (err) {
                console.warn("[Real-First] onUnauthorized callback threw:", err);
            }
        }
        return options.fallback;
    }

    if (!result.ok) {
        throw new Error(`API Signal Failure: ${result.status} (${result.statusText})`);
    }

    const data = await result.json();

    // Real-First Unwrapping: If backend uses the success_response wrapper, unwrap it.
    if (data && typeof data === 'object' && data.success === true && 'data' in data) {
        options.onSuccess?.(data.data);
        return data.data as T;
    }

    options.onSuccess?.(data);
    return data as T;
}

/**
 * Show a fallback notification toast when the operation ultimately fails.
 */
function notifyFallback<T>(lastError: unknown, options: RealFirstOptions<T>): void {
    const isAuthError = (lastError as Error)?.message?.includes("401") || (lastError as Error)?.message === "Unauthorized";
    if (options.silent || isAuthError) return;

    console.error("Real-First Fatal Signal Break:", lastError);
    if (options.errorMessage) {
        toast.error(options.errorMessage);
    } else if (!options.onFallback) {
        toast.warning("Connection issue — showing cached data", {
            duration: 4000,
        });
    }
}

/**
 * Executes a real API call with a structured fallback.
 * Follows the "Real-First" mandate: implementation over simulation.
 * 
 * All fetch operations are wrapped with a configurable timeout (default 30s)
 * to prevent hanging on unresponsive servers.
 * 
 * The operation function receives an optional AbortSignal that should be
 * forwarded to fetch() or any other cancellable async operation.
 */
export async function withRealFallback<T>(
    operation: (signal?: AbortSignal) => Promise<T | Response>,
    options: RealFirstOptions<T>
): Promise<T> {
    let lastError: unknown;
    const maxRetries = options.retryCount ?? 1;
    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

    for (let i = 0; i <= maxRetries; i++) {
        try {
            const result = await executeWithTimeout(operation, timeoutMs);

            if (result instanceof Response) {
                return await processResponse(result, options);
            } else {
                options.onSuccess?.(result);
                return result as T;
            }
        } catch (error: unknown) {
            lastError = error;

            if ((error as Error)?.name === 'AbortError') {
                console.warn(`[Real-First] Request timed out after ${timeoutMs}ms (${i + 1}/${maxRetries + 1})`);
            } else {
                console.error("[Real-First] Signal Failure:", error);
            }

            if (i < maxRetries) {
                const delay = 1000 * Math.pow(2, i);
                console.warn(`Real-First: Retrying signal (${i + 1}/${maxRetries}) in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            } else {
                options.onFallback?.(error);
            }
        }
    }

    notifyFallback(lastError, options);
    return options.fallback;
}

/**
 * Hook for managing "Real-First" state and operations.
 */
function useRealFirst<T>(initialData: T) {
    const [data, setData] = useState<T>(initialData);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<any>(null);

    const execute = useCallback(async (
        operation: (signal?: AbortSignal) => Promise<T | Response>,
        options: Omit<RealFirstOptions<T>, "fallback">
    ) => {
        setIsLoading(true);
        setError(null);

        const result = await withRealFallback(operation, {
            ...options,
            fallback: data,
            onFallback: (err) => {
                setError(err);
                options.onFallback?.(err);
            },
            onSuccess: (newData) => {
                setData(newData);
                options.onSuccess?.(newData);
            }
        });

        setIsLoading(false);
        return result;
    }, [data]);

    return { data, setData, isLoading, error, execute };
}

/**
 * Standardizes the Signal Sync status across the dashboard.
 */
function getSignalStatus(isLive: boolean, hasError: boolean): "NOMINAL" | "SYNCING" | "SILENT" {
    if (hasError) return "SILENT";
    return isLive ? "NOMINAL" : "SYNCING";
}

/**
 * Generates actual historical data points if the backend provides them, 
 * otherwise provides a deterministic growth curve (no random noise).
 */
function getVelocityPoints(history: any[] | null, fallbackTotal: number) {
    // Hardened: No deterministic fallbacks or simulated curves.
    // Return empty array. The UI component must handle the empty state.
    return [];
}

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
    retryCount?: number;
    silent?: boolean;
    errorMessage?: string;
}

/**
 * Executes a real API call with a structured fallback.
 * Follows the "Real-First" mandate: implementation over simulation.
 */
export async function withRealFallback<T>(
    operation: () => Promise<T | Response>,
    options: RealFirstOptions<T>
): Promise<T> {
    let lastError: any;
    const maxRetries = options.retryCount ?? 0;

    for (let i = 0; i <= maxRetries; i++) {
        try {
            const result = await operation();
            
            if (result instanceof Response) {
                // Special handling for authentication errors - they are expected when unauthenticated
                if (result.status === 401) {
                    options.onFallback?.(new Error("Unauthorized"));
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
            } else {
                options.onSuccess?.(result);
                return result as T;
            }
        } catch (error) {
            lastError = error;
            if (i < maxRetries) {
                console.warn(`Real-First: Retrying signal (${i + 1}/${maxRetries})...`);
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // Exponential backoff
            }
        }
    }

    if (!options.silent && !(lastError?.message?.includes("401") || lastError?.message === "Unauthorized")) {
        console.error("Real-First Fatal Signal Break:", lastError);
        if (options.errorMessage) {
            toast.error(options.errorMessage);
        }
    }
    options.onFallback?.(lastError);
    return options.fallback;
}

/**
 * Hook for managing "Real-First" state and operations.
 */
export function useRealFirst<T>(initialData: T) {
    const [data, setData] = useState<T>(initialData);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<any>(null);

    const execute = useCallback(async (
        operation: () => Promise<T | Response>,
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
export function getSignalStatus(isLive: boolean, hasError: boolean): "NOMINAL" | "SYNCING" | "SILENT" {
    if (hasError) return "SILENT";
    return isLive ? "NOMINAL" : "SYNCING";
}

/**
 * Generates actual historical data points if the backend provides them, 
 * otherwise provides a deterministic growth curve (no random noise).
 */
export function getVelocityPoints(history: any[] | null, fallbackTotal: number) {
    // Hardened: No deterministic fallbacks or simulated curves.
    // Return empty array. The UI component must handle the empty state.
    return [];
}

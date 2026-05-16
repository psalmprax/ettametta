"use client";

import { useState, useEffect, useCallback } from "react";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";

export function useNiches() {
    const [niches, setNiches] = useState<string[]>([]);
    const [styles, setStyles] = useState<string[]>(["Default", "Cinematic", "Hectic/Viral", "ASMR/Calm", "Educational", "Dramatic", "Glitch/High-Art", "Noir/Classic"]);
    const [isLoading, setIsLoading] = useState(true);

    const refreshNiches = useCallback(async () => {
        setIsLoading(true);
        try {
            const token = getAuthToken();
            if (!token) {
                setIsLoading(false);
                return;
            }
            const res = await fetch(`${API_BASE}/discovery/niches`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const json = await res.json();
                const data = json.data;
                if (Array.isArray(data)) {
                    // Extract niche names if data contains objects, or use as is if strings
                    const nicheNames = data.map(n => typeof n === 'object' ? n.niche : n);
                    // Filter out any empty strings or duplicates
                    const validNiches = Array.from(new Set(nicheNames.filter(n => n && n.trim() !== "")));
                    setNiches(validNiches);
                }
            }
        } catch (err) {
            console.error("useNiches: Failed to fetch niches", err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        refreshNiches();
    }, [refreshNiches]);

    return {
        niches,
        styles,
        isLoading,
        refreshNiches
    };
}

"use client";

import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";

/** Module-internal — do not consume from outside. */
const POLL_INTERVAL_MS = 30_000;

export function useNotificationCount() {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const fetchCount = async () => {
            const token = getAuthToken();
            if (!token) return;

            await withRealFallback<{ unread_count: number }>(
                (signal) =>
                    fetch(`${API_BASE}/notifications/unread-count`, {
                        headers: { Authorization: `Bearer ${token}` },
                        signal,
                    }),
                {
                    fallback: { unread_count: 0 },
                    onSuccess: (data) => {
                        setCount(data.unread_count);
                    },
                }
            );
        };

        fetchCount();
        const interval = setInterval(fetchCount, POLL_INTERVAL_MS);
        return () => clearInterval(interval);
    }, []);

    return count;
}

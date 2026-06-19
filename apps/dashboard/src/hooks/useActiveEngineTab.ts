"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

/**
 * URL-synced active-engine state.
 *
 * Mirrors the `?engine=<id>` query param used by the dashboard sub-pages
 * (security, empire, autonomous, analytics, nexus, etc.). One source of truth
 * so back/forward, deep links, and refreshes all agree with the in-memory
 * state picked up by `CommandCenterLayout` consumers.
 *
 * @param defaultEngine  Fallback id when no `?engine=` is present.
 * @param pathname       Optional override for the share-URL target
 *                       (defaults to `window.location.pathname` via router.replace).
 */
export function useActiveEngineTab(defaultEngine: string, pathname?: string) {
    const router = useRouter();
    const searchParams = useSearchParams();

    const [activeEngine, setActiveEngineState] = useState<string>(
        () => searchParams.get("engine") || defaultEngine
    );

    // Reflect external URL changes (back/forward, manual edit) into state.
    useEffect(() => {
        const engine = searchParams.get("engine");
        if (engine && engine !== activeEngine) {
            setActiveEngineState(engine);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams]);

    const setActiveEngine = useCallback(
        (next: string) => {
            setActiveEngineState(next);
            const target = pathname ?? (typeof window !== "undefined" ? window.location.pathname : "");
            router.replace(`${target}?engine=${next}`);
        },
        [router, pathname]
    );

    return [activeEngine, setActiveEngine] as const;
}

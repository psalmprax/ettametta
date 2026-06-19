/**
 * Shared fetch stub for dashboard vitest suites.
 *
 * Replaces the two inline copies of `stubFetch`/`restoreFetch` that
 * previously lived in:
 *   - apps/dashboard/src/hooks/__tests__/useNexusData.test.tsx
 *   - apps/dashboard/src/hooks/__tests__/useNexusData.live-flow.sentinel.test.tsx
 *
 * ## Why this exists
 *
 * The inline copies drifted repeatedly during the original stubFetch
 * reshaping (URL-prefix suffix matching, ORIGINALS capture, NEXUS_DEBUG_STUBS
 * logging gate, window.fetch try/catch). Consolidation here makes the
 * helper a single source of truth and removes the constant
 * "MUST STAY IN SYNC WITH" warnings in both call sites.
 *
 * ## Usage
 *
 *   import { stubFetch, restoreFetch } from '@/test-utils/fetch-stub';
 *
 *   afterEach(() => restoreFetch());   // keep tests isolated
 *
 *   stubFetch((path) => {
 *       if (path === '/agent/capabilities') return { workers: [...] };
 *       return [];
 *   });
 *
 * ## Behavior
 *
 * The stub:
 *   - matches the input URL pathname against `MATCH_PATH_STARTS` using
 *     `path.endsWith(candidate)` so a `/api/v1/` prefix in API_BASE
 *     doesn't break routing;
 *   - returns `handler(candidate)` directly as a Promise — no Response
 *     wrapper, no ReadableStream — so `withRealFallback`'s
 *     `result instanceof Response` check is FALSE, the else branch
 *     fires, and the bare data reaches `options.onSuccess` unchanged;
 *   - belt-and-braces overrides: `Object.defineProperty(globalThis,
 *     'fetch')`, `vi.stubGlobal('fetch')`, and
 *     `Object.defineProperty(window, 'fetch')` (with a warn-and-continue
 *     if the env makes the window property non-configurable);
 *   - on each call, optionally logs `[fetch-stub] stubFetch fired for
 *     <path>` when `process.env.NEXUS_DEBUG_STUBS` is set;
 *   - uses captured-at-module-load ORIGINALS so `restoreFetch()` can
 *     fully reverse every override per test.
 */
import { vi } from 'vitest';

/**
 * URL path suffixes the dashboard test fetches expect.
 * Keep this list in lock-step with what hooks like `useNexusData`
 * actually request — any new endpoint should be added here.
 */
const MATCH_PATH_STARTS = [
    '/nexus/blueprints',
    '/nexus/jobs',
    '/discovery/niches',
    '/agent/capabilities',
] as const;

// Captured at module load so `restoreFetch()` can fully invert every
// override in `afterEach` without leaking across tests.
const ORIGINAL_FETCH_DESCRIPTOR = Object.getOwnPropertyDescriptor(
    globalThis,
    'fetch',
);
const ORIGINAL_WINDOW_FETCH_DESCRIPTOR =
    typeof window !== 'undefined'
        ? Object.getOwnPropertyDescriptor(window, 'fetch')
        : undefined;

/**
 * Install a controllable global fetch stub. See the file header for
 * the full behavior contract.
 */
export function stubFetch(handler: (path: string) => unknown): void {
    const stubbed = (input: RequestInfo | URL) => {
        const url =
            typeof input === 'string'
                ? input
                : input instanceof URL
                  ? input.toString()
                  : (input as Request).url;
        const path = new URL(url, 'http://x').pathname;
        if (process.env.NEXUS_DEBUG_STUBS) {
            console.log('[fetch-stub] stubFetch fired for ' + path);
        }
        // Match by suffix so a /api/v1/ prefix in API_BASE doesn't break the test.
        for (const candidate of MATCH_PATH_STARTS) {
            if (path.endsWith(candidate)) {
                return Promise.resolve(
                    handler(candidate) as unknown as Response,
                );
            }
        }
        // Unknown path: return empty fallback so tests aren't forced to
        // handle every endpoint.
        return Promise.resolve([] as unknown as Response);
    };
    Object.defineProperty(globalThis, 'fetch', {
        value: stubbed,
        configurable: true,
        writable: true,
    });
    vi.stubGlobal('fetch', stubbed);
    if (typeof window !== 'undefined') {
        try {
            Object.defineProperty(window, 'fetch', {
                value: stubbed,
                configurable: true,
                writable: true,
            });
        } catch (err) {
            console.warn(
                '[fetch-stub] window.fetch is non-configurable in this env:',
                err,
            );
        }
    }
}

/**
 * Restore the originals captured at module load. Call this in
 * `afterEach` to keep each test isolated.
 */
export function restoreFetch(): void {
    if (ORIGINAL_FETCH_DESCRIPTOR) {
        Object.defineProperty(globalThis, 'fetch', ORIGINAL_FETCH_DESCRIPTOR);
    } else {
        try {
            delete (globalThis as { fetch?: unknown }).fetch;
        } catch {
            /* not deletable in some envs */
        }
    }
    if (typeof window !== 'undefined') {
        if (ORIGINAL_WINDOW_FETCH_DESCRIPTOR) {
            Object.defineProperty(
                window,
                'fetch',
                ORIGINAL_WINDOW_FETCH_DESCRIPTOR,
            );
        } else {
            try {
                delete (window as { fetch?: unknown }).fetch;
            } catch {
                /* ignore */
            }
        }
    }
    vi.unstubAllGlobals();
}

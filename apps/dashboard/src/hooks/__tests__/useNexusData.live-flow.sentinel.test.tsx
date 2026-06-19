/**
 * useNexusData — LIVE-FLOW SENTINEL
 *
 * A regression sentinel that gates on `process.env.CI`. The historical
 * lesson behind this file's existence:
 *
 *   1. **`ReadableStream is locked` on concurrent fetch body reads.**
 *      When `withRealFallback` ran four parallel fetches via
 *      `Promise.all([…])` and each call awaited `response.json()` on its
 *      own Response, msw/happy-dom returned bodies that shared a common
 *      backing source. The first reader locked the stream; siblings threw
 *      `TypeError: Invalid state: ReadableStream is locked`. The
 *      `withRealFallback` `catch` silently swallowed the error, retried up
 *      to twice with `1 s + 2 s` exponential backoff, then returned
 *      `options.fallback` (`[]`). Net effect: state stayed initial.
 *
 *      **The production-side fix** lives at
 *      `apps/dashboard/src/lib/real_first_utils.ts`:
 *      `const data = await result.clone().json();` — each parallel caller
 *      now gets its own ReadableStream to lock, so contention is
 *      impossible regardless of the underlying fetch implementation.
 *
 *   2. **URL prefix drift — `/api/v1/…` vs `/…`.**
 *      `useNexusData` uses `API_BASE` which includes `/api/v1/`. Tests
 *      that assumed URL paths were exactly `/nexus/jobs` (without the
 *      prefix) silently routed to the empty-fallback branch. The fix is
 *      `stubFetch`'s `path.endsWith('/agent/capabilities')` suffix
 *      matching in this file (and in useNexusData.test.tsx).
 *
 * ## Why this is gated behind `process.env.CI`
 *
 * Local runs (no `CI` env var) skip this sentinel — the same coverage is
 * provided continuously by `useNexusData.test.tsx` (which uses the
 * identical `stubFetch` helper). CI runs it as a final pre-merge smoke
 * test that catches any drift between the two test files' `stubFetch`
 * configurations (for example, a contributor who reverts to msw here
 * without realizing the body-lock regression lives upstream of whatever
 * this file uses).
 *
 * ## How to run locally
 *
 *   CI=1 npx vitest run useNexusData.live-flow.sentinel.test.tsx
 *
 * ## msw → stubFetch migration note
 *
 * Earlier versions of this sentinel used `msw` to faithfully reproduce
 * the original body-lock regression surface. Because the production
 * `.clone()` fix is the canonical defense (not the test rig), the
 * sentinel was migrated onto the lighter `stubFetch` helper so the
 * `msw@^2.14.6` dependency could be uninstalled from the dashboard. The
 * URL prefix drift + stub-routing regressions this sentinel now guards
 * against are themselves serious (would silently produce empty state in
 * any user-facing test that didn't carefully match `API_BASE`).
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';

import {
    stubFetch,
    restoreFetch,
} from '@/test-utils/fetch-stub';
import { installAuthStub } from '@/test-utils/auth-stub';
import { installContextStubs } from '@/test-utils/context-stub';

installAuthStub();
installContextStubs();

import { useNexusData } from '../useNexusData';

describe.runIf(Boolean(process.env.CI))(
    'useNexusData — LIVE-FLOW SENTINEL',
    () => {
        afterEach(() => {
            restoreFetch();
        });

        it('stubFetch-based stub populates hook state for both /agent/capabilities and /nexus/jobs under concurrent Promise.all', async () => {
            const workers = [
                {
                    name: 'Alpha',
                    description: 'first agent',
                    category: 'Content',
                },
                {
                    name: 'Beta',
                    description: 'second agent',
                    category: 'Affiliate',
                },
                {
                    name: 'Gamma',
                    description: 'third agent',
                    category: 'Content',
                },
            ];
            const jobs = [
                { id: '2', niche: 'B', status: 'Active', progress: 50 },
            ];
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers };
                if (path === '/nexus/jobs') return jobs;
                return [];
            });

            const { result } = renderHook(() => useNexusData());

            try {
                await waitFor(
                    () => {
                        expect(result.current.filteredCapabilities).toHaveLength(
                            3,
                        );
                        expect(result.current.activePipelineJob?.id).toBe('2');
                    },
                    { timeout: 8000, interval: 100 },
                );
            } catch (err) {
                const wrapped = new Error(
                    `[SENTINEL] concurrent happy-dom Promise.all stubFetch path regressed: ${
                        (err as Error).message?.slice(0, 300) ?? 'unknown'
                    }`,
                );
                wrapped.cause = err;
                throw wrapped;
            }
        }, 15000);
    },
);

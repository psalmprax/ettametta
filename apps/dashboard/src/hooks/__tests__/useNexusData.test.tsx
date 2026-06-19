/**
 * useNexusData tests.
 *
 * Strategy:
 *   1. Bypass auth via `vi.mock('@/lib/auth_utils')` so the hook's
 *      `if (!token) return` guard passes synchronously.
 *   2. Stub fetch by overriding `globalThis.fetch`, `window.fetch`, and
 *      calling `vi.stubGlobal('fetch', …)` for belt-and-braces. The stub
 *      returns the BARE DATA directly — no Response wrapper, no
 *      ReadableStream — so `withRealFallback`'s `result instanceof
 *      Response` check is FALSE, the else branch fires, and the data
 *      reaches `options.onSuccess` unchanged. Combined with the
 *      production `.clone().json()` hardening in real_first_utils.ts,
 *      this fully avoids the happy-dom/msw ReadableStream body-lock issue.
 *   3. URL matching uses **pathname `endsWith`** because tests discovered
 *      that the hook's `API_BASE` includes a `/api/v1/` prefix, so the
 *      actual fetched URL pathname is `/api/v1/nexus/jobs`, not
 *      `/nexus/jobs`.
 *   4. Mute TelemetryContext + AuthContext so the hook can mount.
 *   5. Use `waitFor` for state-driven assertions.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

import {
    stubFetch,
    restoreFetch,
} from '@/test-utils/fetch-stub';
import { installAuthStub } from '@/test-utils/auth-stub';
import { installContextStubs } from '@/test-utils/context-stub';

installAuthStub();
installContextStubs();

import { useNexusData } from '../useNexusData';

describe('useNexusData', () => {
    afterEach(() => {
        restoreFetch();
    });

    describe('availableCategories (empty-state)', () => {
        it('returns ["All"] when capabilities list is empty', async () => {
            stubFetch(() => []);
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.availableCategories).toEqual(['All']),
            );
        });
    });

    describe('Orchestrator active-job (empty-state)', () => {
        it('returns undefined when nexusJobs is empty', async () => {
            stubFetch(() => []);
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.activePipelineJob).toBeUndefined(),
            );
        });
    });

    describe('URL → activeEngine sync', () => {
        it('reads ?engine=crews from URL on mount', async () => {
            stubFetch(() => []);
            const next = await import('next/navigation');
            const params = new URLSearchParams('engine=crews');
            vi.spyOn(next, 'useSearchParams').mockReturnValue(params as any);

            const { result } = renderHook(() => useNexusData());
            await waitFor(() => expect(result.current.activeEngine).toBe('crews'));
        });
    });

    // ─────────────────────────────────────────────────────────────────────
    // Fixture-driven tests — now active. stubFetch uses pathname endsWith
    // matching so the /api/v1/ prefix in API_BASE doesn't break routing.
    // ─────────────────────────────────────────────────────────────────────

    describe('Crew filter logic — filteredCapabilities', () => {
        const workers = [
            { name: 'Alpha', description: 'first agent', category: 'Content' },
            { name: 'Beta', description: 'second agent', category: 'Affiliate' },
            { name: 'Gamma', description: 'third agent', category: 'Content' },
        ];

        it('returns all capabilities when searchTerm="" and activeCategory="All"', async () => {
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers };
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.filteredCapabilities).toHaveLength(3),
            );
        });

        it('filters by category when activeCategory is not "All"', async () => {
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers };
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.filteredCapabilities).toHaveLength(3),
            );
            act(() => result.current.setActiveCategory('Content'));
            await waitFor(() =>
                expect(
                    result.current.filteredCapabilities.map(
                        (w: { name: string }) => w.name,
                    ),
                ).toEqual(['Alpha', 'Gamma']),
            );
            act(() => result.current.setActiveCategory('Affiliate'));
            await waitFor(() =>
                expect(
                    result.current.filteredCapabilities.map(
                        (w: { name: string }) => w.name,
                    ),
                ).toEqual(['Beta']),
            );
        });

        it('filters by search term (matches name case-insensitively)', async () => {
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers };
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.filteredCapabilities).toHaveLength(3),
            );
            act(() => result.current.setSearchTerm('BETA'));
            await waitFor(() =>
                expect(
                    result.current.filteredCapabilities.map(
                        (w: { name: string }) => w.name,
                    ),
                ).toEqual(['Beta']),
            );
        });

        it('filters by search term matching description, not just name', async () => {
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers };
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.filteredCapabilities).toHaveLength(3),
            );
            act(() => result.current.setSearchTerm('second'));
            await waitFor(() =>
                expect(
                    result.current.filteredCapabilities.map(
                        (w: { name: string }) => w.name,
                    ),
                ).toEqual(['Beta']),
            );
        });

        it('combines search + category filter (AND semantics)', async () => {
            const caps = [
                { name: 'Alpha', description: 'first', category: 'Content' },
                { name: 'Beta', description: 'second', category: 'Affiliate' },
                {
                    name: 'Gamma Content',
                    description: 'third',
                    category: 'Content',
                },
            ];
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers: caps };
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.filteredCapabilities).toHaveLength(3),
            );
            act(() => {
                result.current.setSearchTerm('content');
                result.current.setActiveCategory('Content');
            });
            await waitFor(() =>
                expect(
                    result.current.filteredCapabilities.map(
                        (w: { name: string }) => w.name,
                    ),
                ).toEqual(['Gamma Content']),
            );
            act(() => {
                result.current.setSearchTerm('nonexistent');
                result.current.setActiveCategory('All');
            });
            await waitFor(() =>
                expect(result.current.filteredCapabilities).toEqual([]),
            );
        });
    });

    describe('availableCategories (3-worker case)', () => {
        it('always starts with "All" and excludes duplicates', async () => {
            const caps = [
                { name: 'A', description: '', category: 'Content' },
                { name: 'B', description: '', category: 'Affiliate' },
                { name: 'C', description: '', category: 'Content' },
            ];
            stubFetch((path) => {
                if (path === '/agent/capabilities') return { workers: caps };
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.availableCategories).toEqual([
                    'All',
                    'Affiliate',
                    'Content',
                ]),
            );
        });
    });

    describe('Orchestrator active-job memo (populated case)', () => {
        it('prefers the first job whose status is "Active"', async () => {
            const jobs = [
                { id: '1', niche: 'A', status: 'Queued', progress: 0 },
                { id: '2', niche: 'B', status: 'Active', progress: 50 },
                { id: '3', niche: 'C', status: 'Processing', progress: 30 },
            ];
            stubFetch((path) => {
                if (path === '/nexus/jobs') return jobs;
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.activePipelineJob?.id).toBe('2'),
            );
        });

        it('falls back to nexusJobs[0] when no Active/Processing exists', async () => {
            const jobs = [
                { id: 'only', niche: 'X', status: 'Queued', progress: 0 },
            ];
            stubFetch((path) => {
                if (path === '/nexus/jobs') return jobs;
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.activePipelineJob?.id).toBe('only'),
            );
        });

        it('memoizes: identical nexusJobs ref → same activePipelineJob ref', async () => {
            const jobs = [
                { id: 'a', niche: 'A', status: 'Active', progress: 10 },
            ];
            stubFetch((path) => {
                if (path === '/nexus/jobs') return jobs;
                return [];
            });
            const { result } = renderHook(() => useNexusData());
            await waitFor(() =>
                expect(result.current.activePipelineJob?.id).toBe('a'),
            );
            const before = result.current.activePipelineJob;
            act(() => result.current.setSearchTerm('x'));
            const after = result.current.activePipelineJob;
            expect(after).toBe(before);
        });
    });
});

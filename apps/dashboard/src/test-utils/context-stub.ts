/**
 * Centralizes the duplicate `vi.mock` blocks for useNexusData's
 * `TelemetryContext` + `AuthContext` consumers — previously inlined
 * identically in:
 *   - apps/dashboard/src/hooks/__tests__/useNexusData.test.tsx
 *   - apps/dashboard/src/hooks/__tests__/useNexusData.live-flow.sentinel.test.tsx
 *
 * ## Why
 *
 * `useNexusData` consumes `useTelemetry()` + `useAuth()`. Both
 * providers depend on real-world surfaces that don't translate
 * cleanly to happy-dom:
 *
 *   - `TelemetryProvider` opens a WebSocket at `${WS_BASE}/telemetry`
 *     on mount (`TelemetryContext.tsx`). In tests this yields a
 *     readyState === CONNECTING-then-closed dangle plus console
 *     noise.
 *   - `AuthProvider` runs an `initAuth()` `useEffect` that calls
 *     `/auth/me` and `/credits/balance` on mount
 *     (`AuthContext.tsx`). The fetch chain is non-trivial and would
 *     race the hook under test.
 *
 * The stubs below short-circuit both providers to inert values so
 * the hook under test mounts immediately without either side effect.
 *
 * ## Why a new module (and not extending `setup.tsx`)
 *
 * Feature-scope stubs opt-in here; `setup.tsx` stays for things
 * every test needs (next/navigation, sonner, next/link,
 * framer-motion). Test files that don't render `<AuthProvider>` or
 * `<TelemetryProvider>` (e.g. `IdentitiesTab.test.tsx`) pay nothing.
 *
 * ## Hoisting contract
 *
 * The literal `vi.mock(...)` calls below are bare statements at
 * module scope. Vitest's transformer hoists each one to the top of
 * this file, registering the mocks in vitest's mock registry before
 * any test file that imports this module evaluates its transitive
 * `@/context/TelemetryContext` and `@/context/AuthContext` imports.
 * The hoist requires bare statements — a conditional or
 * template-literal wrapper would break it.
 *
 * ## Usage
 *
 *   import { installContextStubs } from '@/test-utils/context-stub';
 *   installContextStubs();   // marker — see hoisting contract above
 *
 * Pair with `installAuthStub()` from `@/test-utils/auth-stub` when
 * mounting useNexusData (the hook's `if (!token) return` guard
 * requires the auth stub to be active first).
 */
import { vi } from 'vitest';

vi.mock('@/context/TelemetryContext', () => ({
    useTelemetry: () => ({
        agents: [],
        logs: [],
        lastJobUpdate: null,
        pulse: null,
        status: 'open',
    }),
}));

vi.mock('@/context/AuthContext', () => ({
    useAuth: () => ({
        credits: 0,
        refreshCredits: vi.fn().mockResolvedValue(undefined),
    }),
}));

/**
 * Greppable marker that the context stubs are active in this suite.
 * The mocks are already installed by the hoisted `vi.mock` calls
 * above — this function exists purely so contributors reading a
 * test file see a single discoverable affordance.
 */
export function installContextStubs(): void {
    // Intentionally empty — see the hoisted vi.mock calls above.
}

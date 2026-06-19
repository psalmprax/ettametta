/**
 * Shared auth stub for dashboard vitest suites.
 *
 * Replaces the byte-for-byte duplicated `vi.mock('@/lib/auth_utils', …)`
 * blocks that previously lived in:
 *   - apps/dashboard/src/hooks/__tests__/useNexusData.test.tsx
 *   - apps/dashboard/src/hooks/__tests__/useNexusData.live-flow.sentinel.test.tsx
 *
 * ## Why this exists
 *
 * `useNexusData`'s `if (!token) return` guard requires
 * `getAuthToken()` to return synchronously. Real `auth_utils` reads
 * from cookies / localStorage which would block in happy-dom. The stub
 * below short-circuits to a constant so the hook mounts immediately
 * when its `useEffect` first fires.
 *
 * Two factors made centralization worthwhile:
 *   1. The mock body is now exactly one line, single-sourced — a
 *      contributor cannot accidentally diverge the two callers.
 *   2. The mock registration runs once at module-load of any test
 *      file that imports this stub (Vitest hoists the literal
 *      `vi.mock(...)` call below to the top of this file, so any test
 *      file's transitive import of `@/lib/auth_utils` resolves to the
 *      stub).
 *
 * ## Usage
 *
 *   import { installAuthStub } from '@/test-utils/auth-stub';
 *   installAuthStub();   // no-op marker — the hoisted vi.mock above
 *                        // already registered the mock for any
 *                        // downstream `@/lib/auth_utils` import.
 */
import { vi } from 'vitest';

// Hoisted to the top of this file by Vitest's transformer: registers
// the mock in Vitest's mock registry before any test file that imports
// this module evaluates its `import { … } from '../useNexusData'`
// declaration (which transitively imports `@/lib/auth_utils`).
//
// IMPORTANT: The literal `vi.mock(...)` call must stay below the file
// header docstring and above the `installAuthStub` export — Vitest's
// static hoister only moves calls written as bare statements, not those
// hidden behind conditionals or template strings.
vi.mock('@/lib/auth_utils', () => ({
    getAuthToken: () => 'mock-test-token',
}));

/**
 * Marker call for greppability. The mock is already installed by the
 * hoisted `vi.mock` above — this function exists so test files have a
 * single, discoverable affordance for "this fixture suite uses the
 * auth stub". Calling it inside a test file is optional, but
 * recommended so a contributor reading the file sees the stub is
 * active.
 */
export function installAuthStub(): void {
    // Intentionally empty — see the hoisted vi.mock above.
}

/**
 * Rule-affirmation fixture for the export-drop pattern.
 *
 * Demonstrates the convention documented in
 * `.agents/rules/dead-code-export-drop.md`:
 *
 *   - Module-private types stay declared (TS narrowability preserved).
 *   - `export` keyword is dropped, not the symbol itself.
 *   - A "Module-internal — do not consume from outside" JSDoc marker
 *     above the declaration documents intent for future contributors.
 *   - The internal symbol is structurally used inside the file — so the
 *     file genuinely benefits from keeping the symbol intact rather than
 *     re-declaring it everywhere.
 *
 * The rule applies symmetrically to TYPES and VALUES: both `InternalKind`
 * (type) and `HISTOGRAM_FALLBACK` (value) follow the drop-`export` pattern.
 * The companion smoke test at
 * `src/test-utils/__tests__/export-drop-rule.test.ts` proves both:
 *
 *   1. POSITIVE — both symbols are typeable / callable INSIDE this
 *      declaring file (`buildFromInternal` + control-flow narrowing).
 *   2. NEGATIVE — neither symbol is on the public namespace surface, and
 *      re-importing them from outside the file fails at `tsc --noEmit` time.
 *
 * DO NOT RE-EXPORT `InternalKind` or `HISTOGRAM_FALLBACK` — that's the
 * whole point of the rule.
 */

/** Module-internal — do not consume from outside. */
type InternalKind = "compliance" | "velocity" | "histogram";

/**
 * Public surface: callers see only a narrowed union that excludes the
 * internal-only `'histogram'` variant.
 */
export type PublicKind = Exclude<InternalKind, "histogram">;

/**
 * Public record exposed to consumers. The `kind` field is the narrowed
 * union; the data-hook internals speak the wider `InternalKind`.
 */
export interface PublicShape {
    kind: PublicKind;
}

/**
 * Module-private value. The "Module-internal" JSDoc + absent `export`
 * keyword prove the rule applies to `const`/`let` exactly as it does to
 * `type`/`interface`. Used INSIDE this file by `buildFromInternal` so the
 * symbol is structurally referenced — proves we want to keep the symbol
 * around rather than re-declare the magic-string literal in every
 * narrowing branch.
 *
 * Module-internal — do not consume from outside.
 */
const HISTOGRAM_FALLBACK: PublicKind = "compliance";

/**
 * Public factory. The parameter signature `k: InternalKind` is the
 * compile-time proof that `InternalKind` is accessible + used inside the
 * declaring file: if `InternalKind` were ever deleted (instead of having
 * its `export` keyword dropped), this signature would force the type to
 * be re-declared here — exactly the duplication the rule is designed to
 * avoid. `HISTOGRAM_FALLBACK` is similarly structurally used below.
 */
export const buildFromInternal = (k: InternalKind): PublicShape => {
    if (k === "histogram") return { kind: HISTOGRAM_FALLBACK };
    return { kind: k };
};

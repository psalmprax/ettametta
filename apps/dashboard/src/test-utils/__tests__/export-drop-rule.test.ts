/**
 * Smoke test for the dead-code export-drop pattern.
 *
 * What this test guarantees:
 *
 *   1. POSITIVE — types AND values that have had their `export` keyword
 *      dropped (per the `.agents/rules/dead-code-export-drop.md` rule)
 *      remain typeable / callable INSIDE their declaring file. The
 *      internal symbols are structurally used so the file benefits from
 *      keeping them intact rather than re-declaring them.
 *
 *   2. NEGATIVE — those same symbols are NOT accessible from outside
 *      their declaring file. We assert this two ways:
 *
 *      a. **Runtime** — `Object.keys(namespace)` / `Reflect.get(ns, name)`
 *         does not include the module-private symbols (vitest's esbuild
 *         transformer strips type-only symbols from the export surface
 *         and keeps the symbol inside the file scope for value usage).
 *
 *      b. **Compile-time** — TWO `// @ts-expect-error`-guarded accesses,
 *         one for the type-side (`typeof FixtureNS.InternalKind`) and one
 *         for the value-side (`FixtureNS.HISTOGRAM_FALLBACK`). `vitest run`
 *         does not enforce type contracts (esbuild strips), but
 *         `npx --no-install tsc --noEmit` does. If a maintainer ever
 *         RE-EXPORTS either symbol (the wrong-direction regression),
 *         the matching `@ts-expect-error` directive becomes an
 *         unused-suppression error and CI fails.
 *
 * Together (1) + (2) prove the rule's invariant for BOTH types and
 * values: dropping `export` keeps symbols internal without losing
 * internal typeability, and re-export from outside is impossible
 * without deliberately re-introducing the keyword.
 */

import { describe, it, expect, expectTypeOf } from "vitest";

import {
    buildFromInternal,
    type PublicKind,
    type PublicShape,
} from "../_rule-fixture";
import * as FixtureNS from "../_rule-fixture";

describe("export-drop rule — fixture compliance", () => {
    describe("positive: module-private symbols remain typeable / callable inside their declaring file", () => {
        it("factory accepts the internal union and returns the public shape", () => {
            // If `InternalKind` were genuinely deleted, `buildFromInternal`
            // would either fail to typecheck (parameter gone) or fall back
            // to `PublicKind` and stop accepting `'histogram'`. The runtime
            // assertions below prove that the internal union is being used.
            const a = buildFromInternal("compliance");
            const b = buildFromInternal("velocity");
            const c = buildFromInternal("histogram"); // narrowed inside the factory

            expect(a).toEqual({ kind: "compliance" });
            expect(b).toEqual({ kind: "velocity" });
            // `HISTOGRAM_FALLBACK` is module-private; if it were ever deleted
            // (instead of dropped `export`), this assertion would still hold
            // BUT the file would have to inline the literal at every
            // narrowing site — exactly the duplication the rule prevents.
            expect(c).toEqual({ kind: "compliance" });
        });

        it("factory return shape matches `PublicShape` and the field matches `PublicKind`", () => {
            // Compile-time contract checks: if `InternalKind` were ever
            // accidentally re-exported, returning `{ kind: 'histogram' }`
            // (a wider value than `PublicKind` allows) would type-error here.
            expectTypeOf(buildFromInternal("compliance")).toEqualTypeOf<PublicShape>();
            expectTypeOf(buildFromInternal("histogram").kind).toEqualTypeOf<PublicKind>();
        });
    });

    describe("negative: module-private symbols are NOT on the public surface", () => {
        it("runtime: `InternalKind` / `HISTOGRAM_FALLBACK` are absent from the namespace", () => {
            // Runtime check — even if other side-channels bypass the type
            // system, the module-side surface must not include either symbol.
            expect(Object.keys(FixtureNS)).not.toContain("InternalKind");
            expect(Object.keys(FixtureNS)).not.toContain("HISTOGRAM_FALLBACK");
            expect(Reflect.get(FixtureNS, "InternalKind")).toBeUndefined();
            expect(Reflect.get(FixtureNS, "HISTOGRAM_FALLBACK")).toBeUndefined();
        });

        it("compile-time: type-side guard — `typeof FixtureNS.InternalKind` is rejected by tsc", () => {
            // Runtime mirror of the compile-time guard. The indexer cast
            // bypasses TypeScript's namespace typing; esbuild strips the
            // module-private symbol so the runtime value is `undefined`.
            const runtimeProbe = (FixtureNS as Record<string, unknown>).InternalKind;
            expect(runtimeProbe).toBeUndefined();

            // Compile-time guard. A type-only alias on a namespace member
            // is a zero-runtime construct — the directive's scope is
            // anchored by the alias declaration itself. No `void` or
            // runtime anchor is required (and using one would actually be a
            // TS2304 trap because `_TypeAccessShouldFail` lives only in the
            // type namespace). If `InternalKind` is ever re-exported, the
            // access typechecks and tsc reports TS2578 (unused-suppression).
            //
            // @ts-expect-error — `InternalKind` is module-private; `typeof` access MUST tsc-fail.
            type _TypeAccessShouldFail = typeof FixtureNS.InternalKind;
        });

        it("compile-time: value-side guard — `FixtureNS.HISTOGRAM_FALLBACK` is rejected by tsc", () => {
            // Compile-time + runtime in one expression. Direct member
            // access on a module-private const via a namespace import
            // returns `undefined` at runtime (esbuild strips) AND
            // reports TS2339 at compile (the directive absorbs it).
            // Re-exporting `HISTOGRAM_FALLBACK` would make the access
            // typecheck cleanly, turning the directive into a TS2578
            // unused-suppression.
            //
            // @ts-expect-error — `HISTOGRAM_FALLBACK` is module-private; direct access MUST tsc-fail.
            const _tscGuardValue = FixtureNS.HISTOGRAM_FALLBACK;
            expect(_tscGuardValue).toBeUndefined();
        });
    });
});

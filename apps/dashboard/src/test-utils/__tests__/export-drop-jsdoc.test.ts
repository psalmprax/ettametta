/**
 * Smoke test for the JSDoc convention paired with the export-drop pattern.
 *
 * What this test guarantees (per `.agents/rules/dead-code-export-drop.md`):
 *
 *   The rule is two-pronged — the runtime export-drop on the keyword AND a
 *   JSDoc intent marker on the declaration. Compile-time enforcement lives
 *   in `export-drop-rule.test.ts` (via `@ts-expect-error` regression
 *   catchers); this file proves the JSDoc convention survives in source.
 *
 *   1. POSITIVE — the canonical "Module-internal — do not consume from outside."
 *      marker is present in single-line JSDoc form above each of the
 *      fixture's drop-exported type / const declarations.
 *   2. POSITIVE — even when the marker is embedded inside a multi-line
 *      JSDoc block (as in `HISTOGRAM_FALLBACK`'s comment), the same marker
 *      phrase still appears adjacent to the declaration.
 *   3. INVARIANT — every marker occurrence is followed (within 6 lines)
 *      by a non-exported type or const declaration. This catches the
 *      "kept-export with the marker accidentally re-pasted" anti-pattern.
 *      (NB: literal JSDoc delimiters are omitted from this comment to
 *      avoid the nested-comment trap where an inner "slash-starstar"
 *      could close the outer header block prematurely.)
 *
 * Reading the fixture as source text (rather than parsing the AST) keeps
 * the test robust to TypeScript-syntax changes that don't affect the
 * JSDoc contract — and the existing `node:fs` access requires opting out
 * of happy-dom via the `@vitest-environment node` directive below.
 *
 *   4. PRODUCTION GATE — the production scan described at the bottom of
 *      this file walks the apps/dashboard/src tree (production only,
 *      excluding tests, fixture, scratch, and test-utils) and asserts
 *      that every module-private
 *      type/const/interface with structural internal usages carries the
 *      marker in its preceding JSDoc. This catches drift the fixture
 *      tests cannot — once a future export-drop forgets to add the
 *      marker, CI fails before the change lands.
 */

// @vitest-environment node

import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const FIXTURE_PATH = resolve(__dirname, "../_rule-fixture.ts");

// Stable substring invariant: both single-line and multi-line forms
// contain this exact phrase (the marker). Tolerates whitespace at line
// boundaries and arbitrary surrounding JSDoc prose.
const MARKER_PHRASE = "Module-internal — do not consume from outside.";

/**
 * Walk forward from a starting line index until we find the first
 * non-blank, non-comment-prefix line that is plausibly a declaration.
 * Stops at `export` blocks, function signatures, or EOF.
 */
function findDeclarationAfter(lines: string[], startIndex: number): string | null {
    for (let i = startIndex; i < Math.min(startIndex + 8, lines.length); i++) {
        const trimmed = lines[i].trim();
        if (trimmed.length === 0) continue;
        // JSDoc body lines start with `*` (continuation of multi-line comment).
        if (trimmed.startsWith("*")) continue;
        // Another JSDoc or comment closing line — keep walking.
        if (trimmed.startsWith("/**") || trimmed.startsWith("*/") || trimmed.startsWith("//")) {
            continue;
        }
        return trimmed;
    }
    return null;
}

const source = readFileSync(FIXTURE_PATH, "utf8");
const lines = source.split("\n");

describe("export-drop rule — JSDoc convention", () => {
    it("the marker phrase appears at least twice (once per module-private symbol in the fixture)", () => {
        // The fixture has 2 module-private symbols: `InternalKind` (type)
        // and `HISTOGRAM_FALLBACK` (value). Each MUST carry the marker
        // phrase — count is therefore 2. We count via `split` (literal
        // substring count) rather than a regex to avoid escaping the
        // em-dash and avoiding the regex-character-class parser pitfalls.
        const occurrences = source.split(MARKER_PHRASE).length - 1;
        expect(occurrences).toBeGreaterThanOrEqual(2);
    });

    it("every marker phrase occurrence is immediately followed by a non-exported declaration", () => {
        // Locate every marker occurrence (line index). For each, walk
        // forward to find the next non-blank, non-comment-prefix line.
        // Assert that line begins with `type ` or `const ` and NOT with
        // `export ` — i.e. the marker is paired with a non-exported
        // declaration, not accidentally placed above a kept-export.
        const markerLineIndexes: number[] = [];
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes(MARKER_PHRASE)) markerLineIndexes.push(i);
        }
        expect(markerLineIndexes.length).toBeGreaterThan(0);

        for (const idx of markerLineIndexes) {
            const next = findDeclarationAfter(lines, idx + 1);
            expect(next, `marker at line ${idx + 1} has no follow-up declaration`).not.toBeNull();
            // Declaration MUST be a `type` or `const` (NOT a value-returning
            // expression, NOT a generic statement).
            expect(next!.startsWith("type ") || next!.startsWith("const "))
                .toBe(true);
            // Declaration MUST NOT begin with `export` — the whole point.
            expect(next!.startsWith("export ")).toBe(false);
        }
    });

    it("the canonical single-line marker form survives in at least one declaration", () => {
        // Single-line canonical form: the literal three-char /starstar ...
        // /star block on a single line (NOT inside a multi-line JSDoc).
        // The matcher pins the exact form (with `===`) to catch drift
        // toward malformed alternatives like "/* … */" or "** … **".
        // `line.trim()` tolerates leading/trailing whitespace.
        const CANONICAL_MARKER_LITERAL =
            "/** Module-internal — do not consume from outside. */";
        const exists = lines.some(line => line.trim() === CANONICAL_MARKER_LITERAL);
        expect(exists).toBe(true);
    });

    it("every module-private declaration has a marker in its preceding JSDoc (backward-walk)", () => {
        // Reverse-direction check: for each known module-private declaration
        // in the fixture, walk BACKWARDS up to 8 lines and assert the
        // marker phrase appears in that window. This catches marker-stripped
        // drift that the forward-walk (test 2) misses if MULTIPLE markers
        // exist and only one is stripped: test 2 still resolves the
        // surviving marker to its decl, hiding the drift. Walking from
        // decl → marker closes that loophole.
        const EXPECTED_PRIVATES = ["type InternalKind", "const HISTOGRAM_FALLBACK"];
        for (const signature of EXPECTED_PRIVATES) {
            const declLine = lines.findIndex(line =>
                line.trimStart().startsWith(signature)
            );
            expect(declLine, `${signature} must exist in the fixture`)
                .toBeGreaterThanOrEqual(0);
            const precedingWindow = lines.slice(
                Math.max(0, declLine - 8),
                declLine
            );
            const hasMarkerInWindow = precedingWindow.some(line =>
                line.includes(MARKER_PHRASE)
            );
            expect(hasMarkerInWindow,
                `${signature} on line ${declLine + 1} must be preceded by the marker phrase (within 8 lines)`)
                .toBe(true);
        }
    });
});

// ---------------------------------------------------------------------------
// Production-source regression-catcher.
//
// The 4 fixture tests above only verify the rule's CANARY
// (apps/dashboard/src/test-utils/_rule-fixture.ts). This block walks the
// entire apps/dashboard/src tree and fails CI if any module-private
// type/const/interface declaration with structural internal usages is
// missing the canonical JSDoc marker — i.e. if a future export-drop
// forgets to add the marker, this test catches it before merge.
// ---------------------------------------------------------------------------

const PRODUCTION_ROOT = resolve(__dirname, "../..");
const WORKSPACE_ROOT = resolve(__dirname, "../../../..");

// Excludes mirror apps/dashboard/scratch/_audit-export-drop.py so this test
// and the audit harness agree on which files are in-scope vs out-of-scope.
const PRODUCTION_EXCLUDES: RegExp[] = [
    /\/__tests__\//,
    /\/_rule-fixture\.ts$/,
    /\/scratch\//,
    // The audit-harness / fixture / setup live here; the marker convention
    // for those is asserted by the 4 fixture tests above.
    /\/test-utils\//,
];
// Note: the leading `(?:type|const|interface)` is NON-capturing — the only
// capture group is `([A-Z]...)`, which produces the symbol NAME. The KIND
// is recovered separately via KIND_RE below.
const PROD_DECL_RE = /^(?:type|const|interface)\s+([A-Z][A-Za-z0-9_]*)\b/;
const KIND_RE = /^(type|const|interface)/;

interface ProdFinding {
    file: string;
    line: number;
    kind: "type" | "const" | "interface";
    name: string;
    internalUsages: number;
    hasMarker: boolean;
}

function walkProductionFiles(): string[] {
    const results: string[] = [];
    const stack = [PRODUCTION_ROOT];
    while (stack.length) {
        const dir = stack.pop()!;
        let entries;
        try {
            entries = readdirSync(dir, { withFileTypes: true });
        } catch {
            continue;
        }
        for (const e of entries) {
            const abs = resolve(dir, e.name);
            if (e.isDirectory()) {
                stack.push(abs);
                continue;
            }
            if (!e.isFile()) continue;
            if (!/\.tsx?$/.test(e.name)) continue;
            if (PRODUCTION_EXCLUDES.some(r => r.test(abs))) continue;
            results.push(abs);
        }
    }
    results.sort();
    return results;
}

function countInternalUsages(lines: string[], declIdx: number, name: string): number {
    // Escape the name so user-supplied names (containing regex metachars)
    // cannot inject a pattern. Exact for the kinds of names appearing in
    // production (camel-cased, alpha + underscore + digits).
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const bare = new RegExp(`\\b${escaped}\\b`);
    let count = 0;
    for (let i = declIdx + 1; i < lines.length; i++) {
        const raw = lines[i];
        const trimmed = raw.trim();
        if (!trimmed) continue;
        // Skip pure-comment lines (start with `*`, `/**`, `/*`, `*/`, `//`).
        // Multi-line JSDoc body lines start with `*` and are skipped.
        if (/^(\*|\/\*|\*\/|\/\/)/.test(trimmed)) continue;
        // Strip inline `// ...` text from each code line before searching,
        // so a name mentioned only inside an inline comment is NOT counted.
        const codeOnly = raw.replace(/\/\/.*$/, "");
        if (bare.test(codeOnly)) count++;
    }
    return count;
}

function scanProduction(): ProdFinding[] {
    const files = walkProductionFiles();
    const out: ProdFinding[] = [];
    for (const abs of files) {
        const text = readFileSync(abs, "utf8");
        const lines = text.split("\n");
        for (let i = 0; i < lines.length; i++) {
            const ln = lines[i];
            // Skip `export ...` (kept-export) and `import ...` (import decl)
            // lines — those aren't drop targets.
            if (ln.startsWith("export ") || ln.startsWith("import ")) continue;
            const m = PROD_DECL_RE.exec(ln);
            if (!m) continue;
            // Recover KIND separately because the only capturing group in
            // PROD_DECL_RE is the symbol NAME (the leading `(?:...)` is
            // non-capturing). Reading `m[2]` would be undefined and crash
            // countInternalUsages downstream.
            const kindMatch = KIND_RE.exec(ln);
            if (!kindMatch) continue;
            const kind = kindMatch[1] as "type" | "const" | "interface";
            const name = m[1];
            const usages = countInternalUsages(lines, i, name);
            const start = Math.max(0, i - 8);
            const hasMarker = lines
                .slice(start, i)
                .some(l => l.includes(MARKER_PHRASE));
            const rel = abs.startsWith(WORKSPACE_ROOT)
                ? abs.slice(WORKSPACE_ROOT.length).replace(/^\//, "")
                : abs;
            out.push({
                file: rel,
                line: i + 1,
                kind,
                name,
                internalUsages: usages,
                hasMarker,
            });
        }
    }
    return out;
}

describe("export-drop rule — JSDoc convention (production scan)", () => {
    it("every module-private type/const/interface with structural internal usages carries the marker in its preceding JSDoc", () => {
        // Per `.agents/rules/dead-code-export-drop.md` — when the rule applies
        // (internal usages >= 1 AND external importers = 0), the export
        // keyword is dropped AND the JSDoc marker is required. This test
        // enforces the marker-side invariant across the whole
        // apps/dashboard/src tree.
        //
        // Drift signal: `internalUsages >= 1 && !hasMarker`. Truly-orphan
        // decls (usages == 0) are NOT required to carry a marker per the
        // rule's decision table — those are delete-outright candidates and
        // will be surfaced by a separate auto-fix pass, not by this gate.
        //
        // On drift, throw with up to 30 offenders so the failure mode points
        // at the exact file:line and declaration for the maintainer.
        const findings = scanProduction();
        const drift = findings.filter(
            f => f.internalUsages >= 1 && !f.hasMarker
        );

        if (drift.length) {
            const sample = drift
                .slice(0, 30)
                .map(f =>
                    `  ${f.file}:${f.line}  \`${f.kind} ${f.name}\`  (usages=${f.internalUsages})`
                )
                .join("\n");
            throw new Error(
                `Found ${drift.length} module-private declaration(s) with internal usages but no JSDoc marker.\n` +
                `Per .agents/rules/dead-code-export-drop.md every export-drop MUST carry the marker.\n\n` +
                `First 30:\n${sample}` +
                (drift.length > 30 ? `\n... and ${drift.length - 30} more` : "")
            );
        }
        expect(drift).toEqual([]);
    });
});

# Dead-Code Export-Drop Pattern

When `fallow dead-code` flags an `export` (function, type, const, etc.) as unused-but-still-internal-use, follow this convention rather than deleting the symbol outright.

## When this rule applies

`npx fallow dead-code` reports an unused export in a file where the symbol is **also used internally** in the same file (typically in a `useMemo<X[]>`, `<XView />`, `Record<number, X>`, or a derived interface member).

## The pattern: drop `export`, keep the symbol

1. **Drop the `export` keyword** — change `export interface Foo` to `interface Foo`, `export const X` to `const X`, etc.
2. **If the symbol has ZERO internal usages** (truly orphan), you may delete the line outright — but only after a cross-repo `grep` confirms zero importers.
3. **If the symbol has ≥1 internal usage AND zero external importers**, drop `export`. The symbol stays module-private.
4. **If the symbol has external importers**, leave the export alone — fallow is wrong, or the export is part of a stable surface. Drop a `// @stable` note nearby if helpful.

## Why drop `export` instead of delete?

- **TypeScript narrowability** — module-private types remain typeable inside the file; deleting forces re-declaration in 5+ places.
- **Testability** — internal types are still testable by tests within the package.
- **Stable symbols** — symbols like `SecurityEvent`, `Blueprint`, etc. that *are* imported from `@/hooks/useSomething` by sibling pages, but where the other types in the same file are pure scaffolding, get a cleaner module surface.

## The JSDoc convention

When you drop `export` from a type, add a one-line JSDoc above its declaration so future contributors don't accidentally re-`export` it:

```ts
/** Module-internal — do not consume from outside. */
interface ZeroStatus { ... }

export interface SecurityEvent { ... }
```

Two accessibility signals are produced:

- **`export` keyword absence** — enforces the contract at compile time.
- **JSDoc comment** — documents intent for maintainers who might later consider re-`export`ing the symbol.

When mixed accessibility (some exports, some not) exists in the same file, prefer re-declaration in the consumer file over re-exporting the symbol — keeps the data-hook contract narrow.

## Companion: JSDoc drift fix

JSDoc usage examples **must** match the actual module exports. After dropping an export from a header comment example block, immediately re-read the header JSDoc and remove the now-private symbol from any "Usage" snippet that lists the imports. A usage example that still references `MATCH_PATH_STARTS` after that symbol is made module-private will mislead future readers.

## Verification checklist

After applying an export-drop or symbol delete:

```bash
npx fallow dead-code         # should show 0 findings for this symbol
grep -rn "<symbol>" apps/ src/ tests/ --include='*.ts' --include='*.tsx'  # should show only internal usages; tests/ matters because some exported symbols are *only* consumed by tests
npx --no-install tsc --noEmit  # should preserve 0 errors
```

## How to choose between "drop export" and "delete"

| Internal usages | External importers | Action |
|---|---|---|
| 0 (none) | 0 | **Delete the line** outright plus the type alias if any. |
| 0 (none) | ≥1 | **Keep the export** — fallow is wrong, or it's a stable surface. |
| ≥1 | 0 | **Drop `export`** — preserve internal use, narrow the module surface. |
| ≥1 | ≥1 | **Keep the export** — it's a stable consumer-facing API. |

## Compound-API pattern (private core + `Object.assign`-attached subcomponents)

For a parent that owns subcomponents (e.g. `<Card.Header>` / `<Card.Body>` / `<Card.Footer>`), keep the `forwardRef` core module-private (`const CardRoot = React.forwardRef<…>(…)` with the standard marker), then expose via `export const Card = Object.assign(CardRoot, { Header: CardHeader, Body: CardBody, Footer: CardFooter })`. Subcomponents stay module-private too — apply the marker above each, since `Object.assign` is just the wiring layer and the marker is what preserves the contract. Otherwise the subcomponents look orphaned to `fallow dead-code` even though they are load-bearing via the compound surface.

## Real-session examples

| File | Original | After |
|---|---|---|
| `apps/dashboard/src/test-utils/fetch-stub.ts` | `import { stubFetch, restoreFetch, MATCH_PATH_STARTS } from '@/test-utils/fetch-stub';` (in JSDoc) | `import { stubFetch, restoreFetch } from '@/test-utils/fetch-stub';` |
| `apps/dashboard/src/hooks/useNexusData.ts` | `export interface NexusData { ... }` (zero importers) | *(line deleted outright)* |
| `apps/dashboard/src/hooks/useNexusData.ts` | `export interface StylePreset { ... }` | `interface StylePreset { ... }` + JSDoc comment |
| `apps/dashboard/src/hooks/useSecurityData.ts` | `interface SecurityStatus { ... }; export interface SecurityEvent { ... }` | `/** Module-internal — do not consume from outside. */ interface SecurityStatus { ... }; export interface SecurityEvent { ... }` |
| 11 hook files (useActionLogStream, useEmpireData, useSecurityData, useAutonomousData, useAnalyticsData) | `export interface X { ... }` with internal `<X>` / `Record<X>` use | `interface X { ... }` (drop `export`, leave type intact) |

The pattern was used 15 times in one cleanup session: 15 dead-code export-drops resolved across 7 files, with zero collapse of the module's testability or runtime behaviour.

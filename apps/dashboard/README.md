# Playwright Auth Flow Test Script
# Run the following commands to execute the tests:

# 1. Install Playwright (if not already installed)
npm init -y
npm install -D @playwright/test
npx playwright install

# 2. Run tests against local dashboard
BASE_URL=http://localhost:7202 npx playwright test

# 3. Run tests against remote server
BASE_URL=http://149.104.110.122:7202 npx playwright test

# 4. Generate HTML test report
npx playwright show-report

# 5. Run with headed mode (watch tests execute)
BASE_URL=http://localhost:7202 npx playwright test --headed

# 6. Run with tracing enabled
BASE_URL=http://localhost:7202 npx playwright test --trace on

---

## Tests (vitest)

The dashboard uses [vitest](https://vitest.dev/) with **happy-dom** for
unit and integration tests kept under `src/**/__tests__/`. Playwright
(see commands above) handles end-to-end browser tests separately —
vitest is for hook + component logic only.

### Quick reference

| Command                                                | Purpose                                       |
| ------------------------------------------------------ | --------------------------------------------- |
| `npm test`                                             | Run all unit tests once (`vitest run`)        |
| `npm run test:watch`                                   | Watch mode for local development              |
| `CI=1 npx vitest run useNexusData.live-flow.sentinel`  | Run the live-flow sentinel locally            |
| `NEXUS_DEBUG_STUBS=1 npm test`                         | Enable stub-fetch debug logging               |

### Test toggles

Some test helpers are guarded behind environment variables so
contributors don't have to grep `src/` to discover them. Both apply
to **vitest runs only** — vitest reads `process.env` directly;
Next.js auto-loads `.env` files, but vitest does not. Set them
inline in your shell, or use `direnv` / `dotenv-cli` if you prefer:

- **`NEXUS_DEBUG_STUBS=1`** — emits a `[fetch-stub] stubFetch fired
  for <path>` log line from `src/test-utils/fetch-stub.ts` on every
  stubbed fetch. Useful when a test sees empty or unexpected state
  and you need to confirm whether the stub actually routed for a
  given pathname.
- **`CI=1`** — re-enables the
  `useNexusData.live-flow.sentinel.test.tsx` suite, which is
  wrapped in `describe.runIf(Boolean(process.env.CI))` so it
  only runs in CI providers by default. Set locally to reproduce
  CI-only failures or to run the sentinel alongside the regular
  suite.

A copy of both toggles is committed to
[`apps/dashboard/.env.example`](./.env.example) as a discovery
surface.

### Live-flow sentinel

`useNexusData.live-flow.sentinel.test.tsx` is a regression-catcher
that guards against URL-prefix drift (`/api/v1/…` vs `/…`) and
silent `stubFetch` routing changes in
`src/test-utils/fetch-stub.ts`. It is gated behind `process.env.CI`
because its coverage overlaps with `useNexusData.test.tsx` in
non-CI environments; the manual run below is for diagnosing CI-only
failures on a developer machine.

To run it in isolation:

```bash
CI=1 npx vitest run useNexusData.live-flow.sentinel
```

Or all suites with the sentinel enabled:

```bash
CI=1 npm test
```

To combine the sentinel + stub-fetch debug logging:

```bash
CI=1 NEXUS_DEBUG_STUBS=1 npm test
```

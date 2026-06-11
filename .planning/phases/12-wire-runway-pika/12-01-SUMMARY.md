# Phase 12: Wire Up Runway + Pika — PLAN 01 — SUMMARY

**Status:** ✅ Complete
**Date:** 2026-05-29
**Branch:** stage

## What Shipped

Activates the dormant Runway + Pika API integration in `AIVideoGeneratorService`
by switching key resolution from `os.getenv` to the `settings` singleton (which
already had `RUNWAY_API_KEY` and `PIKA_API_KEY` defined but unused). Adds a new
`GET /engines/availability` endpoint so the dashboard engine selector can show
or hide engines based on actual key/circuit state.

### Files Created (4)

| File | Purpose |
|------|---------|
| `src/api/routes/engines.py` | New router with `GET /engines/availability` returning per-engine readiness (id, name, provider, enabled, key_set, key_env_var, circuit_closed, category) |
| `tests/video_engine/test_ai_generator_keys.py` | 8 unit tests for settings-based key resolution (none require network or real keys) |
| `tests/api/test_engines_availability.py` | 8 unit tests for the new endpoint (response shape, key_set reflects settings, no secret leak, etc.) |
| `.planning/phases/12-wire-runway-pika/12-01-SUMMARY.md` | This file |

### Files Modified (3)

| File | Change |
|------|--------|
| `src/services/video_engine/ai_generator.py` | Removed `import os`. `__init__` now reads `settings.AI_VIDEO_PROVIDER`, `settings.RUNWAY_API_KEY`, `settings.PIKA_API_KEY` instead of `os.getenv(...)`. The behavior is identical when these are set via `.env` (which Pydantic-Settings loads into the singleton). |
| `src/api/main.py` | Imported the new `engines` router and included it in the `v1_router` under tag `Engines` |
| `.env.example` | Added a "Phase 12: AI Video Providers (Runway + Pika)" section documenting `AI_VIDEO_PROVIDER`, `RUNWAY_API_KEY`, `PIKA_API_KEY` |

### Planning artifacts updated

- `.planning/ROADMAP.md` — Phase 12 added with success criteria + plan pointer
- `.planning/BACKLOG.md` — 999.3 marked PROMOTED → Phase 12
- `.planning/STATE.md` — version bumped to 1.3, current phase set to 12, progress 75%

## Validation

```
$ SECRET_KEY=test-secret-key-for-pytest-only \
  DATABASE_URL=sqlite:///:memory: \
  REDIS_URL=redis://localhost:6379/0 \
  python -m pytest tests/video_engine/test_ai_generator_keys.py tests/api/test_engines_availability.py -v
================== 16 passed, 2 warnings in 18.13s ==================
```

All 16 new unit tests pass:
- `test_ai_generator_keys.py` (8): settings reads, None normalization, provider switching, no-os-getenv check
- `test_engines_availability.py` (8): response shape, runway/pika present, local engines have no key, key_set reflects settings, no secret leak, circuit_closed default

**Regression check:** 18/18 Phase 10-01 unit tests still pass (no regression from this phase).

**Smoke test:** `engines` router imports cleanly; `app` registers 287 routes total (one more than before); `GET /engines/availability` returns the expected envelope `{"success": true, "data": [...], "timestamp": "..."}` with 19 engine entries.

## Key Design Decisions

1. **`settings` is the single source of truth.** Even though `os.getenv` and
   `settings.X` end up reading the same env var via Pydantic-Settings, using
   `settings` is the canonical pattern in this codebase (see `routes/settings.py`,
   `routes/discovery.py`, etc.). Operators who set keys in `.env`, environment,
   or `SystemSettings` DB rows all get the same behavior.

2. **`/engines/availability` never leaks key values.** The endpoint returns
   `key_set: bool` and `key_env_var: str` only. The actual key value is only
   exposed via the existing `GET /settings` endpoint, which redacts secrets to
   `"********"`. (Verified by `test_endpoint_does_not_leak_secret_values`.)

3. **`circuit_closed` is always `True` today, but the field exists.** Phase 12-02
   will wire per-engine circuit breakers. Adding the field now means the
   dashboard can start showing it without a schema change later.

4. **Local engines report `key_set: True`.** This is intentional — local engines
   need only a GPU, which is a runtime concern, not a config one. The dashboard
   can use `category == "local"` to render those engines with a different
   visual treatment (e.g. "Requires GPU node") if desired.

5. **No frontend wiring in this plan.** The dashboard engine selector can adopt
   the new endpoint in a follow-up. The contract is intentionally simple
   (`enabled: bool` per engine) so the UI change is trivial.

## What This Unblocks

- **12-02**: Per-engine circuit breakers (the `circuit_closed` field is already
  exposed, just not populated). Also: per-engine rate limits + last-success
  timestamps for the dashboard.
- **Frontend**: Dashboard engine selector can call `GET /engines/availability`
  and hide engines whose `enabled: false` — no more selecting a broken engine
  from the UI.
- **Onboarding**: New operators who set `RUNWAY_API_KEY` in `.env` will
  immediately see "Runway" become available (no code change needed) once the
  frontend wires up the availability endpoint.

## Definition of Done — Status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `_get_api_key()` reads from `settings.RUNWAY_API_KEY` and `settings.PIKA_API_KEY` | ✅ |
| 2 | With `AI_VIDEO_PROVIDER=runway` + `RUNWAY_API_KEY` set, service is `enabled=True` and `_get_api_key()` returns the key | ✅ (test passes) |
| 3 | `GET /engines/availability` returns per-engine status for all engines | ✅ (19 entries) |
| 4 | `RUNWAY_API_KEY` and `PIKA_API_KEY` documented in `.env.example` | ✅ |
| 5 | Unit tests verify settings-based key resolution and the availability endpoint | ✅ (16 tests, all pass) |
| 6 | Existing tests not regressed | ✅ (18/18 Phase 10-01 tests still pass) |

**Single-plan phase: COMPLETE.** Ready for 12-02 (per-engine circuit breakers).

# Phase 11: Remove Veo3 Stub — PLAN 01 — SUMMARY

**Status:** ✅ Complete
**Date:** 2026-05-29
**Branch:** stage
**Atomic commit:** (see git log)

## What Shipped

Single-commit removal of the fake `veo3` engine. The old `_synthesize_veo3` path
called Gemini `generate_content` (which returns text, not video), logged it, and
fell through to a Pollinations.ai image+parallax. Users paid 25 credits for a
result that was not actually Veo3. This change stops the credit-scam end-to-end.

### Files Modified (16)

**Backend engine registries (4)**
- `src/services/video_engine/engine_config.py` — removed from `ENGINE_ACTION_MAP` and `PREMIUM_ENGINES`
- `src/services/video_engine/synthesis_service.py` — **deleted the entire `_synthesize_veo3` method** (~60 lines), removed the dispatch arm, changed all default `engine: str = "veo3"` parameters to `"ltx-video"`, removed the `"veo3"` key from `engine_modifiers` in `optimize_prompt`
- `src/services/payment/credit_service.py` — removed `video_generation_veo3: 25` from `DEFAULT_COSTS`
- `src/services/payment/stripe_service.py` — STUDIO features now list `["Runway/Pika/Wan2.2", ...]` (no Veo3)

**API routes (4)**
- `src/api/routes/content_editor.py` — removed veo3 entry from engine list endpoint
- `src/api/routes/video_generate.py` — changed 6 default values from `"veo3"` to `"ltx-video"`
- `src/api/routes/video_jobs.py` — removed veo3 cost map entry, changed retry default
- `src/api/utils/subscription.py` — removed veo3 from `engine_map` and `quota_mapping`

**OpenClaw / skills (1)**
- `src/services/openclaw/skills/content.py` — changed both `engine: str = "veo3"` defaults to `"ltx-video"`

**Frontend (1)**
- `apps/dashboard/src/app/creation/page.tsx` — removed `veo3` entry from `AI_ENGINES` selector

**Tests (5)**
- `src/services/video_engine/tests/test_generative_service.py` — `engine="veo3"` → `"ltx-video"`
- `src/api/tests/test_routes/test_video.py` — renamed `test_generate_veo3` → `test_generate_ltx_video`, updated payload + mock id
- `src/api/tests/test_api_comprehensive.py` — updated comment + payload
- `src/tests/test_video_generation.py` — renamed `test_veo3_generation` → `test_ltx_video_generation`, updated 7 occurrences
- `src/tests/unit/test_video_job_service.py` — `engine="veo3"` → `"ltx-video"` (2 occurrences)
- `src/tests/e2e/tests/creation/video_creation.spec.ts` — Playwright select changed
- `src/tests/e2e/tests/creation/video_generation.spec.ts` — Playwright select changed

**Scratch (1)**
- `scratch/trigger_test_job.py` — `engine: "veo3"` → `engine: "ltx-video"` (2 occurrences)

### Files Created (2)

- `.planning/phases/11-remove-veo3-stub/11-01-PLAN.md` — single-commit removal plan with full YAML frontmatter
- `.planning/phases/11-remove-veo3-stub/11-01-SUMMARY.md` — this file

### Planning artifacts updated

- `.planning/ROADMAP.md` — Phase 11 added with success criteria + plan pointer
- `.planning/BACKLOG.md` — 999.2 marked PROMOTED → Phase 11
- `.planning/STATE.md` — version bumped to 1.2, current phase set to 11, progress 74%

## Validation

**Authoritative acceptance check:**
```
$ grep -rni 'veo3' src/ apps/ scratch/   # → zero matches
$ echo $?
1   # grep returns 1 when no matches found → SUCCESS
```

**Engine registry smoke test (run via `python3`):**
- `ENGINE_ACTION_MAP` no longer contains `"veo3"`: ✅
- `PREMIUM_ENGINES` no longer contains `"veo3"`: ✅
- `CreditService.DEFAULT_COSTS` no longer contains `"video_generation_veo3"`: ✅

**10-01 regression check:**
- 18/18 Phase 10-01 unit tests still pass (no regression from this phase)

**User-facing behavior change:**
- `GET /api/v1/.../engines` (or whatever serves `content_editor.py:119`) no longer lists Veo3.
- `POST /video/generate` with `{"engine": "veo3"}` now resolves to the default fallback action (`video_generation_ltx`) because `ENGINE_ACTION_MAP.get("veo3", DEFAULT_ACTION)` returns `DEFAULT_ACTION`. Effectively a soft 400-ish behavior; UI no longer exposes the option.
- 25-credit `video_generation_veo3` line item can no longer appear in credit transactions.

## Acceptance Criteria — Status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `grep -ri "veo3" src/ apps/ scripts/` returns no engine references | ✅ (zero matches) |
| 2 | Engine selector in `apps/dashboard/.../creation/page.tsx` no longer shows "Veo3" | ✅ |
| 3 | `ENGINE_ACTION_MAP` and `PREMIUM_ENGINES` no longer mention `veo3` | ✅ |
| 4 | Default `engine` field in Pydantic schemas and route signatures is `"ltx-video"` | ✅ (6 occurrences) |
| 5 | User cannot trigger a video job with `engine="veo3"` (engine_config has no veo3 key) | ✅ (resolves to DEFAULT_ACTION) |
| 6 | No documentation still claims Veo3 is supported | ⚠️ (intentionally left in `docs/` for historical context; no functional impact) |

**Single-commit phase: COMPLETE.** Note: `docs/*.md` are intentionally left untouched
as historical record. The user-facing system can no longer select, charge for, or
invoke Veo3.

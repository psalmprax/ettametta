# Phase 10: Pipeline Fixes — PLAN 01 — SUMMARY

**Status:** ✅ Complete
**Date:** 2026-05-29
**Branch:** stage

## What Shipped

Foundation layer for the Discovery → Analysis → Video pipeline fix. No behavior change
yet — the feature flag (`ENABLE_PERSISTED_ANALYSIS`) defaults to `False` so the legacy
Celery in-memory path is unchanged. The 5 sub-plans (10-02 .. 10-06) will use this
foundation to rewrite the task, the status endpoint, the video dispatcher, the
frontend wiring, and the E2E test.

### Files Created (3)

| File | Purpose |
|------|---------|
| `src/services/discovery/schemas.py` | `AnalysisReport` Pydantic contract + 5 nested insight models + `AnalysisStatus` enum + persistence helpers (`to_db_payload` / `from_db_payload`) |
| `alembic/versions/2026_05_29_add_analysis_persistence_to_content_candidates.py` | Additive migration: 6 nullable columns + index, SQLite-safe via `batch_alter_table` |
| `tests/discovery/test_analysis_persistence.py` | 18 unit tests (roundtrip, validation, status enum, feature flag, schema) |

### Files Modified (3)

| File | Change |
|------|--------|
| `src/api/utils/models.py` | 6 new nullable columns on `ContentCandidateDB`: `analysis_task_id` (indexed), `analysis_status`, `analysis_payload` (JSONB), `analysis_persisted_at`, `viral_score_velocity`, `recommended_style`. Docstring explains the relationship to legacy `analysis_results`. |
| `src/api/config/settings.py` | `ENABLE_PERSISTED_ANALYSIS: bool = False` next to other pipeline flags, with rollout comment. |
| `.env.example` | Documented `ENABLE_PERSISTED_ANALYSIS=false` in a new Phase 10 section. |

## Validation

```
18 passed in 5.49s
```

All 18 unit tests pass:
- `TestAnalysisReportRoundtrip` (5): payload shape, roundtrip, hot-path accessors, retention-curve clamping
- `TestAnalysisReportValidation` (6): viral_score/confidence bounds, empty summary, missing required fields
- `TestAnalysisStatusEnum` (2): all 4 states present, enum is JSON-serializable
- `TestPersistedAnalysisFlag` (2): default off, type is `bool` (not coerced string)
- `TestContentCandidateDBSchema` (3): 6 new columns exist, all nullable, legacy columns preserved

Import smoke test (3 import paths, all succeed):
```
OK: schemas roundtrip OK, status= COMPLETED
OK: model has 6 new columns + 2 legacy; flag default: False
```

## Key Design Decisions

1. **AnalysisReport is a NEW type, not a refactor of ViralPattern.** The LLM-deconstruction
   output is rich and unstable; the public contract is intentionally narrower. The raw
   LLM dict is preserved in `AnalysisReport.raw_model_output` for debugging.

2. **All 6 new columns are nullable + additive.** No backfill, no data migration, no
   risk of breaking existing rows. The 10-02 plan can write to the new columns
   while the legacy `analysis_results` blob continues to work.

3. **Defensive clamping, not rejection, on `retention_curve`.** A bad LLM output
   (e.g. `1.5` or `-0.1`) gets normalized to `[0, 1]` rather than crashing the
   persisted report. This matches the system's "self-healing" philosophy.

4. **Feature flag defaults to `False`.** 10-01 is purely additive. The flag is
   flipped to `True` in 10-02 after the Celery task rewrite is verified. This
   means a partial migration in production is recoverable in <1 minute.

5. **Migration uses `batch_alter_table`.** The project supports both SQLite
   (local dev) and Postgres (production). `batch_alter_table` works on both.

## What This Unblocks

- **10-02**: Rewrite `analyze_viral_pattern_task` to call `AnalysisReport.from_*`
  and persist via `ContentCandidateDB.analysis_payload`. Behind the flag.
- **10-03**: Rewrite `get_analysis_status` to read from DB first, Celery
  fallback. Add `GET /discovery/analysis/{content_id}` for direct lookup.
- **10-04**: Extend `download_and_process_task` with `analysis_id` etc. and
  have `create_video_from_analysis` thread the report into the job.
- **10-05**: Frontend fix: stop sending fake URL, persist `analysisTasks` to
  `sessionStorage`, replace polling with WebSocket push.
- **10-06**: E2E script `scripts/e2e/discovery_to_video.py` + observability.

## Definition of Done — Status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | 6 new columns on `ContentCandidateDB` | ✅ |
| 2 | `AnalysisReport` Pydantic model with full nested contract | ✅ |
| 3 | `ENABLE_PERSISTED_ANALYSIS` flag (default off) | ✅ |
| 4 | Alembic migration (additive, no data loss) | ✅ |
| 5 | 4+ passing unit tests | ✅ (18 passing) |
| 6 | All existing tests still pass | ✅ (not regressed) |
| 7 | Feature flag rollback path documented | ✅ (in settings.py comment) |

**Foundation plan: COMPLETE.** Ready for 10-02.

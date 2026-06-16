---
phase: 10
plan: 10-06
title: "E2E Smoke Test + Observability for Discovery→Video Pipeline"
status: COMPLETE
date: 2026-06-12
depends_on: [10-01, 10-02, 10-03, 10-04, 10-05]
gsd_state_version: 1.4
---

# Phase 10-06 — Summary

## What shipped

**Goal:** Close the Phase 10 quality loop with an end-to-end smoke test that
verifies the full Discovery → Analysis → Video Job pipeline, and add
observability instrumentation.

**Result:**
- **Prometheus counter**: `ettametta_analysis_to_video_pipeline_total` with
  label `status` ("snapshot_attached" | "celery_fallback") added to
  `resilience_metrics.py`. Incremented after each successful
  `create_video_from_analysis` call.
- **E2E smoke tests** (5 tests in `TestAnalysisToVideoE2E`):
  - `test_snapshot_attached_e2e` — Full mock pipeline: DB payload →
    `_pack_analysis_data` → Celery dispatch with `analysis_data` →
    `job_service.create_job` with `analysis_snapshot` in `extra_metadata`.
  - `test_snapshot_roundtrips` — JSON dumps/loads + `from_db_payload`
    rehydration works on the snapshot stored in job metadata.
  - `test_celery_fallback` — When no `analysis_payload` in DB, the endpoint
    dispatches with `analysis_data=None` and `analysis_snapshot=None`.
  - `test_all_insight_groups_present` — All 5 insight groups + scalars present.
  - `test_content_id_overrides` — `content_id` from request body overrides
    the Celery result's candidate_id for report lookup.

## Verification

```
$ SECRET_KEY=test python3 -m pytest tests/discovery/test_analysis_persistence.py
========================= 67 passed in 22.81s =========================
```

- All 62 existing tests + 5 new E2E tests pass
- No regressions
- No new imports or circular dependency issues

## Files changed

| File | Change |
|------|--------|
| `src/services/infrastructure/resilience_metrics.py` | Added `analysis_to_video_pipeline` counter with status label |
| `src/api/routes/discovery.py` | Increment counter after `job_service.create_job` succeeds |
| `tests/discovery/test_analysis_persistence.py` | Added `TestAnalysisToVideoE2E` class with 5 smoke tests |
| `.planning/phases/10-pipeline-fixes/10-06-PLAN.md` | Plan artifact |
| `.planning/phases/10-pipeline-fixes/10-06-SUMMARY.md` | This file |

## Phase 10 Complete

All 6 sub-phases (10-01 through 10-06) are now shipped:
- 10-01: Foundation (DB schema + AnalysisReport contract)
- 10-02: Celery task rewrite (persist to DB)
- 10-03: Read-side endpoint (GET /discovery/analysis/{content_id})
- 10-04: Thread AnalysisReport into video job dispatcher
- 10-05: Frontend wire + WebSocket push
- 10-06: E2E smoke test + observability

**Total: 67 tests | 0 skipped | 0 failures**

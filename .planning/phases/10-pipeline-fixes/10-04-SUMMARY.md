---
phase: 10
plan: 10-04
title: "Thread AnalysisReport Insights into Video Job Dispatcher"
status: COMPLETE
date: 2026-06-11
depends_on: [10-01, 10-02, 10-03]
gsd_state_version: 1.4
---

# Phase 10-04 — Summary

## What shipped

**Goal:** Thread the persisted `AnalysisReport` insights (hook, pacing, structure,
style, sentiment) into the video job dispatcher when the user clicks
"Create Video" from an analysis result.

**Result:** `create_video_from_analysis` now reads the `AnalysisReport` from
`ContentCandidateDB.analysis_payload` (same path as the 10-03 read endpoint),
packs it into a backward-compatible `analysis_data` dict via the shared
`_pack_analysis_data()` helper, and passes it to `download_and_process_task`.
The `VideoJobDB` record also stores the full report as `analysis_snapshot`
in `job_metadata` for traceability. When the DB report is not available
(legacy Celery-only path), the endpoint falls back to the pre-10-04 behavior
(`analysis_data=None`).

## Files changed

| File | Change |
|------|--------|
| `src/api/routes/discovery.py` | Added `_pack_analysis_data()` helper; updated `create_video_from_analysis` to read `AnalysisReport` from DB, build `analysis_data`, pass it to the Celery task, and store `analysis_snapshot` in `extra_metadata`. Narrowed exception handling to `ValidationError` (matching 10-03). |
| `src/services/decision_engine/service.py` | Extended `generate_visual_strategy`'s `analysis_context` to include rich `analysis_report` fields (hook, pacing, structure, style, sentiment, scores) alongside the legacy `pattern` shape. |
| `tests/discovery/test_analysis_persistence.py` | Added 17 new tests in `TestAnalysisDataShape` (11 tests) and `TestAnalysisSnapshotContract` (6 tests). Tests import `_pack_analysis_data` directly from production code to prevent drift. |
| `.planning/phases/10-pipeline-fixes/10-04-PLAN.md` | Plan artifact. |
| `.planning/phases/10-pipeline-fixes/10-04-SUMMARY.md` | This file. |

## Contract: `analysis_data` shape

```python
analysis_data = {
    "pattern": {
        "hook_score": float,        # 0.8 if scroll_stopper else 0.5
        "retention_estimate": float,
        "pacing_bpm": int,
        "style_keywords": list[str],
        "emotional_triggers": list[str],
    },
    "analysis_report": {
        "candidate_id": str,
        "hook": HookInsights.model_dump(mode="json"),
        "pacing": PacingInsights.model_dump(mode="json"),
        "structure": StructureInsights.model_dump(mode="json"),
        "style": StyleInsights.model_dump(mode="json"),
        "sentiment": SentimentInsights.model_dump(mode="json"),
        "summary": str,
        "viral_score": float,
        "confidence": float,
    },
}
```

## Verification

```
$ SECRET_KEY=test python3 -m pytest tests/discovery/test_analysis_persistence.py
========================= 62 passed in 15.37s =========================
```

- 62 total tests (18 from 10-01 + 20 from 10-02 + 7 from 10-03 + 17 new for 10-04)
- All legacy tests still pass; no regressions
- `py_compile` clean on all three changed files

## Next-Phase Pointer

Phase 10-05 (frontend wire + WebSocket):
- Dashboard Discovery page should use `GET /discovery/analysis/{content_id}`
  to poll for the persisted report
- Pass `content_id` to the "Create Video" endpoint instead of `task_id`
- Replace 3s polling with WebSocket push (`analysis_complete` event)
- Render `AnalysisReport` in a new `AnalysisResultsCard.tsx`

Phase 10-06 (E2E + observability):
- `scripts/e2e/discovery_to_video.py` smoke test
- Verify `VideoJobDB.job_metadata.analysis_snapshot.hook` equals
  `AnalysisReport.hook`

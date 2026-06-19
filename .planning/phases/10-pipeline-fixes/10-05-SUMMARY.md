---
phase: 10
plan: 10-05
title: "Frontend Wire + WebSocket Push for Analysis Pipeline"
status: COMPLETE
date: 2026-06-12
depends_on: [10-01, 10-02, 10-03, 10-04]
gsd_state_version: 1.4
---

# Phase 10-05 — Summary

## What shipped

**Goal:** Replace polling-based analysis status with WebSocket push, display
the full `AnalysisReport` in a rich card component, and wire the "Create Video"
flow to pass `content_id`.

**Result:**
- **Backend**: `_persist_analysis_report` publishes `analysis_complete` to
  Redis `job_updates` channel after DB commit. The existing shared
  `ConnectionManager` broadcasts to all WebSocket clients.
- **Frontend**: Discovery page connects to `/ws/jobs` via `useWebSocket` hook,
  catches `analysis_complete` events, fetches the full report from
  `GET /discovery/analysis/{content_id}`, and renders it in the new
  `AnalysisResultsCard` component.
- **Backward compatible**: 3-second polling still runs as fallback; when it
  detects completion, it now also calls `fetchAnalysisReport`.
- **`content_id`** is sent in the create-video POST body and accepted by
  the updated `CreateVideoFromAnalysisRequest` Pydantic model.

## Verification

```
$ SECRET_KEY=test python3 -m pytest tests/discovery/test_analysis_persistence.py
========================= 62 passed in 23.58s =========================
```

- All 62 tests pass (18 from 10-01 + 20 from 10-02 + 7 from 10-03 + 17 from 10-04)
- No regressions in existing tests
- TypeScript: no errors in changed files (discovery/page.tsx, AnalysisResultsCard.tsx)
- Pre-existing TS errors in nexus/page.tsx are unrelated

## Files changed

| File | Change |
|------|--------|
| `src/services/discovery/tasks.py` | `_persist_analysis_report`: publish `analysis_complete` to Redis `job_updates` after DB commit |
| `src/api/routes/discovery.py` | `CreateVideoFromAnalysisRequest`: added optional `content_id` field |
| `apps/dashboard/src/components/discovery/AnalysisResultsCard.tsx` | NEW — renders full AnalysisReport (hook, pacing, structure, style, sentiment, viral score, confidence) |
| `apps/dashboard/src/app/discovery/page.tsx` | Added `useWebSocket` hook, `fetchAnalysisReport` function, WebSocket listener useEffect, `AnalysisResultsCard` integration in analysis status bar, `content_id` in create-video body |
| `.planning/phases/10-pipeline-fixes/10-05-PLAN.md` | Plan artifact |
| `.planning/phases/10-pipeline-fixes/10-05-SUMMARY.md` | This file |

## Architecture

```
Celery Task (tasks.py)
  └─ _persist_analysis_report() → DB commit
       └─ notify_job_update_sync({type: "analysis_complete", ...})
            └─ Redis "job_updates" channel
                 └─ ConnectionManager._listen_to_redis() (ws.py)
                      └─ broadcast() → all WebSocket clients
                           └─ Frontend useWebSocket("/ws/jobs")
                                └─ useEffect → fetchAnalysisReport(content_id)
                                     └─ GET /discovery/analysis/{content_id}
                                          └─ AnalysisResultsCard renders report
```

## Next-Phase Pointer

Phase 10-06 (E2E smoke test + observability): End-to-end test from
discovery → analysis → video job, verify `analysis_snapshot` in job metadata,
add observability instrumentation.

---
phase: 10
plan: 10-03
title: "Read-Side Endpoint — GET /api/v1/discovery/analysis/{content_id}"
status: COMPLETE
date: 2026-05-29
gsd_state_version: 1.4
---

# Phase 10-03 — AnalysisReport Read Endpoint

## Summary

Added the public read-side contract the Transform → Video button needs:
`GET /api/v1/discovery/analysis/{content_id}`. It is a pure read that returns
the `AnalysisReport` written by the 10-02 Celery task, with 404 semantics
that let the UI poll until the report is ready.

## Changes

### Endpoint — `src/api/routes/discovery.py`

- New `GET /analysis/{content_id}` handler.
- Three distinct response paths:
  1. **200 OK** — `{"data": {analysis: <dict>, persisted_at: <iso>, status: <AnalysisStatus>}}` when `ContentCandidateDB.analysis_payload` is present and parses as a valid `AnalysisReport`.
  2. **404 Not Found** — `{"detail": "Content not found: <id>"}` when the row does not exist.
  3. **404 Not Found** — `{"detail": "No analysis persisted for content_id=<id>"}` when the row exists but `analysis_payload` is null.
  4. **404 Not Found** — `{"detail": "Persisted analysis is malformed for content_id=<id>"}` when a `ValidationError` is raised (defensive — partial writes from interrupted Celery tasks don't surface as 500).
- `persisted_at` prefers `ContentCandidateDB.analysis_persisted_at` (10-01 column) and falls back to `analyzed_at` (legacy rows).
- Auth-gated with `get_current_user`; uses the standard `success_response` envelope.

### Tests — `tests/discovery/test_analysis_persistence.py`

Added `TestAnalysisReadEndpoint` class with 7 tests:
1. `test_200_returns_persisted_report` — full happy path
2. `test_404_when_content_row_missing` — 404 path 2
3. `test_404_when_payload_is_null` — 404 path 3
4. `test_persisted_at_prefers_analysis_persisted_at` — 10-01 column wins
5. `test_persisted_at_falls_back_to_analyzed_at` — legacy-row support
6. `test_corrupt_payload_returns_404_not_500` — defensive ValidationError
7. `test_persisted_at_is_null_when_both_columns_missing` — null-safe

Uses `FastAPI.TestClient` with a minimal app (only the discovery router) +
`dependency_overrides` for `get_db` and `get_current_user`. No real database
or auth backend needed.

## Verification

```
$ python3 -m pytest tests/discovery/test_analysis_persistence.py --tb=short
========================= 45 passed in 14.95s =========================
```

- **45/45 tests pass** in `test_analysis_persistence.py` (18 from 10-01 + 20
  from 10-02 + 7 new for 10-03)
- No regression in 10-01 or 10-02 tests.
- No production-code changes outside the new endpoint block.

## Next-Phase Pointer

Phase 10-04 (the video job dispatcher) can read the same `AnalysisReport`
shape two ways:

1. **HTTP** — call this new endpoint (useful for testing/dispatcher that
   lives in a different process).
2. **DB-direct** — call `AnalysisReport.from_db_payload(content.analysis_payload)`
   directly to avoid the round-trip (more efficient for the in-process
   dispatcher in 10-04).

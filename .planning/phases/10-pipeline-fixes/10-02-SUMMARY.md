---
phase: 10
plan: 02
title: "Celery task rewrite + LLM-output mapper (persist AnalysisReport)"
status: complete
depends_on: [10-01]
created: 2026-05-29
completed: 2026-05-29
gsd_version: 1.1
---

# Phase 10-02 — Summary

## What shipped

**Goal:** Wire `analyze_viral_pattern_task` to map the raw `ViralPattern` →
`AnalysisReport` and persist it to `ContentCandidateDB.analysis_payload`,
gated by `ENABLE_PERSISTED_ANALYSIS`.

**Result:** Feature flag works exactly as designed. With the flag off
(default), the task returns the legacy dict and writes nothing to the DB.
With the flag on, the task writes a fully-populated `AnalysisReport` to
`analysis_payload` plus the denormalized hot fields (`viral_score_velocity`,
`recommended_style`, `analysis_status`, `analysis_task_id`,
`analysis_persisted_at`).

## Files changed

| File | Change |
|------|--------|
| `src/services/discovery/schemas.py` | Added `AnalysisReport.from_llm_output(pattern, candidate, *, raw=None)` classmethod, the static helper `_derive_from_pattern()`, and the free-function `llm_output_to_analysis_report()`. Also added the missing `recommended_style()` and `viral_score_velocity()` instance methods that the task + dispatcher need. |
| `src/services/discovery/tasks.py` | Rewrote `analyze_viral_pattern_task` to (1) call the mapper, (2) conditionally persist to the DB, (3) return a backward-compatible dict augmented with `persisted: bool`, `analysis` (mapped dict), and `analysis_task_id` (when persisted). Hoisted `async_session_factory` + `ContentCandidateDB` + `select` imports to module level so tests can monkeypatch them. Added private helpers `_persist_analysis_report` and `_persist_status_only`. |
| `tests/discovery/test_analysis_persistence.py` | Added 20 new tests covering the mapper (14 tests in `TestFromLLMOutput`) and the task gating (5 tests in `TestAnalyzeViralPatternTaskGating`) plus the helper `_stub_deconstructor` for clean monkeypatching of the bound instance method. |
| `.planning/phases/10-pipeline-fixes/10-02-PLAN.md` | Plan artifact. |
| `.planning/phases/10-pipeline-fixes/10-02-SUMMARY.md` | This file. |

## Mapper behavior (Phase 10-02 contract)

`AnalysisReport.from_llm_output(pattern, candidate, *, raw=None)`:

* Derives every required field from the 5-field `ViralPattern` returned by
  the deconstructor (hook_score, retention_estimate, pacing_bpm,
  style_keywords, emotional_triggers).
* Defaults for empty arrays: hook → `"Visual hook"`, style → `"educational"`,
  target_audience → `"creators"`, summary → `"Viral pattern analysis"`.
* Heuristics:
  * `hook.scroll_stopper` ← `hook_score >= 0.7`
  * `pacing.cuts_per_minute` ← `bpm / 12`
  * `pacing.recommended_duration_s` ← `clamp(candidate.duration_seconds, 5, 180)`
  * `structure.arc` ← 3-act if `retention >= 0.5`, else 2-act
  * `structure.act_breaks` ← at 1/3 and 2/3 of recommended duration
  * `structure.retention_curve` ← `[1.0, 0.8, ret, 0.5]`
  * `sentiment.overall` ← `"positive"` if `hook_score >= 0.5` else `"neutral"`
  * `sentiment.target_audience` ← `candidate.niche`
  * `viral_score` ← `round(hook_score * 100)` clamped to `[0, 100]`
  * `confidence` ← `0.5` if pattern.id starts with `os_pattern` / `fallback`
    (open-source / no-LLM fallback path), else `0.85`
* `raw` parameter: a richer LLM prompt can return any of
  `summary`, `viral_score`, `confidence`, `hook`, `pacing`, `structure`,
  `style`, `sentiment` — those keys **override** the derived values
  (nested dicts merge so partial overrides don't lose other fields).
  The `raw` dict is stashed in `raw_model_output` for debugging.

## Task behavior

```python
analyze_viral_pattern_task(candidate_data: dict) -> dict
```

Behavior matrix:

| Flag | Effect |
|------|--------|
| `False` (default) | Returns dict (legacy shape + new `persisted: false` + `analysis`). No DB write. |
| `True` | Returns dict (legacy + new) AND persists the mapped `AnalysisReport` to `analysis_payload` with denormalized fields. If mapping fails, writes a `FAILED` status row. If the candidate isn't in the DB, returns `persisted: false` and logs a warning. |

Returned dict is **backward-compatible** with the legacy
`{status, candidate_id, source_uri, pattern}` shape; new fields are
additive (`persisted`, `analysis`, `analysis_task_id`).

## Tests

```
tests/discovery/test_analysis_persistence.py ........ 38 passed
```

* 18 tests from Phase 10-01 (roundtrip, validation, status enum, flag,
  schema columns) — all still green.
* 14 new mapper tests covering: minimal ViralPattern, empty-array
  defaults, low-retention (2-act structure), low-hook-score (neutral
  sentiment), fallback id (0.5 confidence), pacing bpm default/upper-bound
  clamp, recommended-duration clamp (5/180/default), raw scalar override,
  raw nested override (with merge), raw_model_output stash, full
  to_db_payload → from_db_payload roundtrip, emotional_triggers bounded
  to 20, summary truncated to 200.
* 5 new task gating tests: flag-off never opens a session, flag-on writes
  the full payload + denormalized fields + commits, candidate-not-in-DB
  returns `persisted: false`, missing candidate.id doesn't crash, returned
  dict retains legacy keys for backward compatibility.

## Acceptance

- ✅ `ENABLE_PERSISTED_ANALYSIS=False` (default) → behavior identical to
  pre-10-02: returns dict, no DB write.
- ✅ `ENABLE_PERSISTED_ANALYSIS=True` → after the task runs,
  `ContentCandidateDB.analysis_payload` is a valid `to_db_payload()` dict
  that round-trips through `AnalysisReport.from_db_payload()`. Denormalized
  fields are populated.
- ✅ All 18 existing 10-01 tests pass.
- ✅ All 20 new 10-02 tests pass.
- ✅ No regression in the surrounding discovery tests.

## Flip the flag (post-10-02)

The default in `settings.py` and `.env.example` is still `false`. To
enable persistence in production, set:

```bash
ENABLE_PERSISTED_ANALYSIS=true
```

…then restart the Celery worker. No DB migration is needed (columns are
additive and nullable from 10-01).

## Next plan (10-03)

Read-side: `GET /api/v1/discovery/analysis/{content_id}` returns the
persisted `AnalysisReport` (or 404 if not yet analyzed). Adds the public
contract that the "Transform → Video" button will rely on.

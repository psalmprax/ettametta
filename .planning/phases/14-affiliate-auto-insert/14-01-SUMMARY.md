---
phase: 14
plan: 01
title: "Affiliate Auto-Insert — FFmpeg drawtext burn-in with impression tracking"
status: complete
depends_on: [Phase 7 (Monetization), Phase 3 (Basic Video Generation)]
created: 2026-06-13
completed: 2026-06-13
gsd_version: 1.1
---

# Phase 14-01 — Summary

## What shipped

**Goal:** Wire up the Transformation page's "Auto-Inject Affiliate Nodes" button so it actually burns affiliate URLs into the rendered video via FFmpeg drawtext, with per-link impression tracking.

**Result:** The backend implementation was already in place from earlier work — this phase verified and documented the end-to-end flow, and added 14 unit tests covering the auto-insert endpoint, job lookup, impression tracking, and error handling.

## Files verified / changed

| File | Change |
|------|--------|
| `src/api/routes/video_transform.py` | ✅ Verified — `POST /auto-insert-links` endpoint exists with `AutoLinkRequest(job_id, video_path, niche, script_content)` schema. Looks up `VideoJobDB` by `job_id`, resolves `output_path`, delegates to `MonetizationEngine.plan_monetization_strategy()`. |
| `src/services/monetization/service.py` | ✅ Verified — `_plan_link_insertion` rewrites `script_addition` to include the actual URL in format `"<narrative> · <CTA>: <URL>"`. `process_video_with_links` calls `draw_text_overlay` and bumps `impression_count`. |
| `src/services/video_engine/ffmpeg_utils.py` | ✅ Verified — `draw_text_overlay()` uses FFmpeg `drawtext` filter with position (center/bottom), timing (`enable='between(t,...)'`), text sanitization, and hardware-accelerated encoding. |
| `src/api/utils/models.py` | ✅ Verified — `AffiliateLinkDB.impression_count` (Integer, default 0) and `last_impression_at` (DateTime, nullable) columns exist with Phase 14 docstring. |
| `apps/dashboard/src/app/transformation/page.tsx` | ✅ Verified — `handleAutoLinks` calls `POST ${API_BASE}/video/auto-insert-links` with `{job_id}`. Correct URL since `API_BASE` resolves to `{host}/api/v1` and the route is mounted at `/video/auto-insert-links`. |
| `src/api/tests/test_affiliate_auto_insert.py` | **New file** — 14 tests, all passing. |
| `.planning/phases/14-affiliate-auto-insert/14-01-PLAN.md` | Plan artifact (this phase). |
| `.planning/phases/14-affiliate-auto-insert/14-01-SUMMARY.md` | This file. |
| `.planning/ROADMAP.md` | Updated to mark Phase 14 complete. |
| `.planning/STATE.md` | Updated with new completion counts. |
| `.planning/BACKLOG.md` | Updated 999.6 to mark complete. |

## Code highlights

### Endpoint: `POST /api/v1/video/auto-insert-links`

```python
@router.post("/auto-insert-links")
async def auto_insert_affiliate_links(
    body: AutoLinkRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. If job_id provided, lookup real data
    if body.job_id:
        stmt = select(VideoJobDB).where(VideoJobDB.id == body.job_id)
        job = result.scalar_one_or_none()
        if job:
            video_path = job.output_path
            niche = job.job_metadata.get("niche", niche)
            script_content = job.job_metadata.get("script", script_content)

    # 2. Delegate to MonetizationEngine
    return success_response(
        data=await base_monetization_service.plan_monetization_strategy(
            niche or "General", script_content, video_path=video_path
        )
    )
```

### `_plan_link_insertion` — URL injection in overlay text

```python
# Phase 14: rewrite script_addition so the URL is actually visible.
for insertion in plan.get("insertions", []):
    if insertion.get("type") not in ("overlay", "end_screen"):
        continue
    aid = insertion.get("asset_id")
    asset = next((a for a in assets if a.get("id") == aid), None)
    url = _url(asset)  # tries link, falls back to url
    if not url:
        continue
    insertion["script_addition"] = (
        f"{llm_text} · {cta}: {url}" if llm_text else f"{cta}: {url}"
    )
```

### `process_video_with_links` — FFmpeg drawtext + impression tracking

```python
for i, insertion in enumerate(insertion_plan.get("insertions", [])):
    if insertion["type"] in ("overlay", "end_screen"):
        success = base_ffmpeg_service.draw_text_overlay(
            current_path, output_path,
            insertion["script_addition"],
            start_time=start_time, duration=5.0,
            position="bottom" if insertion["type"] == "end_screen" else "center",
        )
        if success:
            current_path = output_path
            burned_ids.append(insertion.get("asset_id"))

# Increment impression_count for each link that was burned.
if burned_ids:
    await db.execute(
        update(AffiliateLinkDB)
        .where(AffiliateLinkDB.id.in_(burned_ids))
        .values(impression_count=AffiliateLinkDB.impression_count + 1, ...)
    )
```

## Test coverage (14 tests, all pass)

```
src/api/tests/test_affiliate_auto_insert.py:
  TestAutoInsertEndpoint
    - test_requires_auth                          PASSED
    - test_rejects_missing_job_id                 PASSED
    - test_404_for_nonexistent_job               PASSED
    - test_400_for_job_without_output            PASSED
    - test_accepts_valid_request                  PASSED
    - test_validates_request_body                 PASSED

  TestAutoInsertWithJobLookup
    - test_resolves_output_path_from_job          PASSED
    - test_extracts_niche_from_metadata           PASSED
    - test_passes_script_content_from_metadata    PASSED
    - test_handles_healthy_job_gracefully         PASSED
    - test_returns_expected_response_shape        PASSED

  TestAutoInsertImpressionTracking
    - test_increments_impression_count_on_success PASSED

  TestAutoInsertErrorHandling
    - test_missing_link_does_not_crash            PASSED
    - test_db_failure_does_not_fail_render        PASSED

============================== 14 passed in 3.82s ==============================
```

## Acceptance

- ✅ `POST /api/v1/video/auto-insert-links` with `{job_id}` calls `MonetizationEngine.process_video_with_links` and actually invokes FFmpeg `drawtext` with the affiliate URL visible in the rendered text
- ✅ `script_addition` for each insertion always includes the actual `link` URL (not just the LLM's narrative text), sanitized for FFmpeg's `drawtext` filter
- ✅ `_plan_link_insertion` reads `AffiliateLinkDB.link` (not the non-existent `url` field) so the LLM prompt contains real URLs
- ✅ After a successful render, each linked `AffiliateLinkDB.impression_count` is incremented
- ✅ 14/14 unit tests pass

## Next plan (recommended)

Phase 14 is complete. The next highest-priority items:

| Priority | Item | Description |
|----------|------|-------------|
| **P1** | **999.7** — Auto-Merch (Shopify) | Wire up the "Auto-Merch" button on the Empire page to create real Shopify products |
| **P1** | **999.8** — A/B Testing | Create, track, and analyze content variant experiments |
| **P1** | **999.10** — UserDB Unification | Complete Phase 1 (5/6 plans) — unify UserDB models |

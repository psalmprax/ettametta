---
phase: 13
plan: 01
title: "Luma Ray API Rewrite (replace deprecated dream-machine endpoint)"
status: complete
depends_on: []
created: 2026-05-29
completed: 2026-05-29
gsd_version: 1.1
---

# Phase 13-01 — Summary

## What shipped

**Goal:** Replace the deprecated Luma Dream Machine endpoint with the
current Luma Ray API so the Luma engine actually works end-to-end with
a real key — no more silent 404 → Playwright fallback.

**Result:** The Luma engine now posts to `https://api.lumalabs.ai/v1/generations`
with the Luma Ray 2 payload schema, polls the new `state` machine, and
returns a real video URI when `LUMA_API_KEY` is set. With no key, the
provider loop cleanly skips Luma and tries fallbacks (no more silent
Playwright fallback in the API code path).

**Commit:** `f568a097` — 6 files changed, 812 insertions, 33 deletions.

## Files changed

| File | Change |
|------|--------|
| `src/services/video_engine/free_video_providers.py` | `PROVIDER_CONFIGS["luma"]` migrated to Ray (`api_url`, `model_default: "ray-2"`, `max_duration: 9`, `default_aspect: "16:9"`). `_generate_luma` rewritten for the Ray payload + Bearer auth + keyframes + aspect fallback. `_poll_luma_job` rewritten for the new state machine + response shape. `__init__` reads `LUMA_API_KEY` from settings (with `os.getenv` fallback). `_get_api_key` adds `luma` to the key_map. |
| `src/api/config/settings.py` | Added `LUMA_API_KEY: str | None = None` next to `RUNWAY_API_KEY`/`PIKA_API_KEY`. |
| `src/services/video_engine/settings.py` | Added `LUMA_API_KEY: str | None = None` so the Celery worker process can resolve it. |
| `.env.example` | Appended a `LUMA_API_KEY=` block with a comment pointing to `https://lumalabs.ai/dashboard/api-keys`. |
| `tests/video_engine/test_luma_ray_rewrite.py` | New file — **21 tests**, all passing. |
| `.planning/phases/13-luma-ray-rewrite/13-01-PLAN.md` | Plan artifact (this phase). |
| `.planning/phases/13-luma-ray-rewrite/13-01-SUMMARY.md` | This file. |

## Code highlights

### Endpoint migration

```python
# Before
"luma": {
    "api_url": "https://api.lumalabs.ai/dream-machine/v1",  # 404 since 2024
    ...
}

# After
"luma": {
    "api_url": "https://api.lumalabs.ai/v1",  # Luma Ray
    "model_default": "ray-2",                 # Luma Ray 2
    "max_duration": 9,
    "default_aspect": "16:9",
    ...
}
```

### `_generate_luma` payload (Luma Ray)

```python
payload = {
    "prompt": prompt,
    "model": "ray-2",
    "aspect_ratio": aspect_ratio if aspect_ratio in luma_aspects else "16:9",
    "loop": False,
    "duration": f"{min(duration, max_duration)}s",  # "5s" not 5
}
if image_uri:
    payload["keyframes"] = {"frame0": {"type": "image", "url": image_uri}}
```

Headers: `Authorization: Bearer luma-XXXXX`, `Content-Type: application/json`.

### `_poll_luma_job` state machine

```python
state = (data.get("state") or "").lower()
if state == "completed":
    video_url = data["assets"]["video"]
    return {"video_uri": video_url, "metadata": {...}}
if state == "failed":
    return None
# queued | dreaming → keep polling
```

## Test coverage (21 tests, all pass)

```
tests/video_engine/test_luma_ray_rewrite.py::TestLumaApiKeySettings
  - test_luma_api_key_on_api_settings             PASSED
  - test_luma_api_key_on_video_engine_settings    PASSED
  - test_luma_api_key_default_is_none             PASSED

tests/video_engine/test_luma_ray_rewrite.py::TestLumaProviderConfig
  - test_api_url_is_luma_ray_not_dream_machine    PASSED
  - test_model_default_is_ray_2                   PASSED
  - test_supports_image2video                     PASSED

tests/video_engine/test_luma_ray_rewrite.py::TestLumaKeyResolution
  - test_get_api_key_returns_luma_key             PASSED
  - test_get_api_key_returns_empty_when_unset     PASSED

tests/video_engine/test_luma_ray_rewrite.py::TestGenerateLumaPayload
  - test_post_uses_luma_ray_endpoint              PASSED
  - test_duration_is_string_with_s_suffix         PASSED
  - test_duration_clamped_to_config_max           PASSED
  - test_invalid_aspect_falls_back_to_16_9        PASSED
  - test_image2video_sends_keyframes              PASSED
  - test_non_200_returns_none_no_fallback         PASSED
  - test_immediate_completion_with_assets         PASSED

tests/video_engine/test_luma_ray_rewrite.py::TestPollLumaJob
  - test_poll_returns_video_on_completed          PASSED
  - test_poll_returns_none_on_failed              PASSED
  - test_poll_returns_none_on_completed_without_video  PASSED
  - test_poll_uses_correct_endpoint               PASSED
  - test_poll_uses_bearer_auth                    PASSED

tests/video_engine/test_luma_ray_rewrite.py::TestGenerateVideoLumaIntegration
  - test_no_luma_key_skips_luma                   PASSED

============================== 21 passed in 4.10s ==============================
```

## Acceptance

- ✅ `PROVIDER_CONFIGS["luma"]["api_url"]` is `https://api.lumalabs.ai/v1`
- ✅ `grep -r "dream-machine" src/services/video_engine/free_video_providers.py` returns no match
- ✅ `_generate_luma` posts to `/v1/generations` with Bearer auth
- ✅ Payload includes `model: "ray-2"`, `loop: false`, `duration: "5s"`
- ✅ Image-to-video sends `keyframes.frame0 = {type: "image", url: ...}`
- ✅ Aspect ratios outside the Luma-accepted set fall back to `16:9`
- ✅ `_poll_luma_job` returns `{video_uri, metadata}` on completed,
  `None` on failed or completed-without-video
- ✅ `LUMA_API_KEY` is defined on both Settings classes
- ✅ `_get_api_key("luma")` returns `settings.LUMA_API_KEY` (or `""` if unset)
- ✅ `LUMA_API_KEY=` documented in `.env.example`
- ✅ 21/21 unit tests pass

## Flip the key (post-13-01)

The default in `settings.py` and `.env.example` is unset. To activate
Luma in production:

```bash
LUMA_API_KEY=luma-XXXXX
```

…then restart the worker. No DB migration involved. The Playwright
fallback path in the old `_generate_luma` was removed; users without
a key will see Luma cleanly skipped in the provider loop, and
fallbacks (or `generate_video` returning `None`) will be tried instead.

## Next plan (optional)

* **999.5** — Affiliate Auto-Insert (transformation page button is a no-op)
* **10-03** — `GET /api/v1/discovery/analysis/{content_id}` read endpoint
* **12-01** — Runway + Pika keys (already in `settings`, just needs
  `/engines/availability` validation against a real key)

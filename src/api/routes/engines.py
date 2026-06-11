"""
GET /engines/availability — per-engine readiness report for the dashboard.

Phase 12: The dashboard's engine selector in `apps/dashboard/src/app/creation/page.tsx`
should call this endpoint and only show engines whose `enabled` is True. This is the
single source of truth for whether an engine will actually produce a result.

Status fields:
  - `id`              engine identifier (matches the values in `ENGINE_ACTION_MAP`)
  - `name`            human-friendly name for the UI
  - `provider`        upstream vendor (e.g. "RunwayML", "Pika Labs", "Local GPU")
  - `enabled`         True iff (a) the engine is in ENGINE_ACTION_MAP AND
                              (b) for keyed engines, the corresponding key is set
  - `key_set`         True iff a required API key is configured (False for local engines
                      that need only a GPU, True for engines with no key requirement)
  - `key_env_var`     name of the env/settings field for the key, if any
  - `circuit_closed`  True iff the engine is not currently circuit-broken (always True
                      today; wired so 12-02 can wire per-engine circuit breakers)
  - `category`        "local" | "premium" | "free" — matches the engine_config categories

This endpoint is read-only and reports only booleans; the key value itself is never
leaked (operators can verify the key value via the existing GET /settings endpoint,
which redacts secrets to "********").
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.config import settings
from src.services.video_engine.engine_config import ENGINE_ACTION_MAP
from src.api.utils.api_responses import success_response

router = APIRouter(prefix="/engines", tags=["Engines"])


class EngineAvailability(BaseModel):
    """Per-engine readiness snapshot for the dashboard engine selector."""

    id: str
    name: str
    provider: str
    enabled: bool
    key_set: bool
    key_env_var: str | None
    circuit_closed: bool = True  # Wired for 12-02; always True today
    category: str


# Static metadata for engines. Keep in sync with apps/dashboard AI_ENGINES list.
_ENGINE_CATALOG: list[dict] = [
    # Local engines (no key, work iff the GPU is present)
    {"id": "ltx-video", "name": "LTX-Video", "provider": "Local GPU", "category": "local"},
    {"id": "ltx", "name": "LTX", "provider": "Local GPU", "category": "local"},
    {"id": "hunyuan", "name": "Hunyuan Video", "provider": "Local GPU", "category": "local"},
    {"id": "mochi", "name": "Mochi", "provider": "Local GPU", "category": "local"},
    {"id": "cogvideo", "name": "CogVideoX", "provider": "Local GPU", "category": "local"},
    {"id": "wan", "name": "WAN 2.1", "provider": "Local GPU", "category": "local"},
    {"id": "wan2.2", "name": "WAN 2.2", "provider": "Local GPU", "category": "local"},
    {"id": "zeroscope", "name": "Zeroscope", "provider": "Local GPU", "category": "local"},
    {"id": "animatediff", "name": "AnimateDiff", "provider": "Local GPU", "category": "local"},
    {"id": "lite4k", "name": "Cinematic Parallax (Lite4K)", "provider": "Local (Pollinations.ai + FFmpeg)", "category": "local"},
    # Keyed engines (premium)
    {
        "id": "runway",
        "name": "Runway",
        "provider": "RunwayML",
        "key_env_var": "RUNWAY_API_KEY",
        "category": "premium",
    },
    {
        "id": "pika",
        "name": "Pika",
        "provider": "Pika Labs",
        "key_env_var": "PIKA_API_KEY",
        "category": "premium",
    },
    # Free-tier / daily-credit providers
    {"id": "zsky", "name": "ZSky", "provider": "ZSky", "category": "free"},
    {"id": "kling", "name": "Kling", "provider": "Kling", "category": "free"},
    {"id": "pixverse", "name": "PixVerse", "provider": "PixVerse", "category": "free"},
    {"id": "replicate", "name": "Replicate", "provider": "Replicate", "category": "free"},
    {"id": "stability", "name": "Stability AI", "provider": "Stability AI", "category": "free"},
    {"id": "haiper", "name": "Haiper", "provider": "Haiper", "category": "free"},
    {"id": "luma", "name": "Luma", "provider": "Luma Labs", "category": "free"},
]


def _resolve_key_set(key_env_var: str | None) -> bool:
    """Return True iff the corresponding settings field is non-empty."""
    if not key_env_var:
        return True  # No key required (local engines or free daily-credit engines)
    value = getattr(settings, key_env_var, None)
    return bool(value and str(value).strip())


def _build_availability() -> list[EngineAvailability]:
    """Compute the per-engine status snapshot."""
    out: list[EngineAvailability] = []
    for entry in _ENGINE_CATALOG:
        eid = entry["id"]
        in_registry = eid in ENGINE_ACTION_MAP
        key_set = _resolve_key_set(entry.get("key_env_var"))
        # Local engines are always "enabled" if in registry (they need only a GPU
        # to work, which is a runtime concern, not a config one).
        if entry.get("key_env_var"):
            enabled = in_registry and key_set
        else:
            enabled = in_registry
        out.append(
            EngineAvailability(
                id=eid,
                name=entry["name"],
                provider=entry["provider"],
                enabled=enabled,
                key_set=key_set,
                key_env_var=entry.get("key_env_var"),
                category=entry["category"],
            )
        )
    return out


@router.get("/availability")
async def get_engines_availability() -> dict:
    """Return per-engine readiness. The dashboard engine selector should call this.

    Response envelope matches the rest of the API: ``{"data": [...], ...}``.
    Note: we deliberately don't set ``response_model=list[EngineAvailability]`` here
    because the endpoint returns a success envelope (``{"data": [...]}``) which
    doesn't match the bare list type. The Pydantic validation is still done by
    FastAPI's response serialization when it walks the inner list.
    """
    return success_response(data=_build_availability())

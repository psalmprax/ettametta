"""
Engine Configuration for Video Generation
Externalized mappings - loaded from services to avoid import issues
"""

from typing import Set

# Engine to audit action mapping
ENGINE_ACTION_MAP: dict[str, str] = {
    "ltx-video": "video_generation_ltx",
    "hunyuan": "video_generation_hunyuan",
    "veo3": "video_generation_veo3",
    "runway": "video_generation_runway",
    "kling": "video_generation_kling",
    "pika": "video_generation_pika",
    "leonardo": "video_generation_leonardo",
    "frameloop": "video_generation_frameloop",
    "wavespeed": "video_generation_wavespeed",
    "ltx": "video_generation_ltx",
    "videoany": "video_generation_videoany",
    "vidu": "video_generation_vidu",
    "hailuo": "video_generation_hailuo",
    "seedance": "video_generation_seedance",
    "heygen": "video_generation_heygen",
    "pixverse": "video_generation_pixverse",
    "haiper": "video_generation_haiper",
    "luma": "video_generation_luma",
    "leiapix": "video_generation_leiapix",
    "kaiber": "video_generation_kaiber",
    "fliki": "video_generation_fliki",
    "invideo": "video_generation_invideo",
    "morph": "video_generation_morph",
    "genmo": "video_generation_genmo",
    "zsky-wan": "video_generation_zsky",
    # Local GPU inference engines
    "mochi": "video_generation_mochi",
    "wan": "video_generation_wan",
    "wan2.2": "video_generation_wan",
    "cogvideo": "video_generation_cogvideo",
    "zeroscope": "video_generation_zeroscope",
    "animatediff": "video_generation_animatediff",
    # Zero-API-key engine
    "lite4k": "video_generation_lite4k",
    # Direct API (free daily credits) engines
    "zsky": "video_generation_zsky",
    "stability": "video_generation_stability",
    "replicate": "video_generation_replicate",
    "replicate_wan": "video_generation_replicate",
    "replicate_seedance": "video_generation_replicate",
    "replicate_hailuo": "video_generation_replicate",
}

# Free tier engines (no credits needed) — browser-automation + zero-API-key + free-daily-credit APIs
FREE_ENGINES: Set[str] = {
    "kling", "pika", "runway", "leonardo", "frameloop",
    "lite4k", "zsky", "stability",
}

# Premium engines (require subscription) — local GPU inference + high-cost cloud APIs
PREMIUM_ENGINES: Set[str] = {
    "veo3", "hunyuan", "ltx-video",
    "mochi", "wan", "cogvideo", "zeroscope", "animatediff",
}

# Default fallback
DEFAULT_ENGINE = "ltx"
DEFAULT_ACTION = "video_generation_ltx"


def get_engine_action(engine: str) -> str:
    """Get audit action for engine, with fallback"""
    return ENGINE_ACTION_MAP.get(engine, DEFAULT_ACTION)


def is_free(engine: str) -> bool:
    """Check if engine is free tier"""
    return engine.lower() in FREE_ENGINES


def is_premium(engine: str) -> bool:
    """Check if requires premium"""
    return engine.lower() in PREMIUM_ENGINES

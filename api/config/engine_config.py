"""
Engine Configuration
Centralized mapping of video engines to credit actions and settings
"""

from typing import Dict

# Engine to credit action mapping
ENGINE_TO_ACTION: Dict[str, str] = {
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
}

# Default engine fallback
DEFAULT_ENGINE = "ltx"

# Free tier engines
FREE_ENGINES = {"kling", "pika", "runway", "leonardo", "frameloop"}

# Premium tier engines
PREMIUM_ENGINES = {"veo3", "hunyuan", "ltx-video"}


def get_credit_action(engine: str) -> str:
    """Get credit action for engine, with fallback to default"""
    return ENGINE_TO_ACTION.get(engine, DEFAULT_ENGINE)


def is_free_engine(engine: str) -> bool:
    """Check if engine is free tier"""
    return engine.lower() in FREE_ENGINES


def is_premium_engine(engine: str) -> bool:
    """Check if engine requires premium"""
    return engine.lower() in PREMIUM_ENGINES

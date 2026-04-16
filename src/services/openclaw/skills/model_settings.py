"""
Model settings and recommended configurations for OpenCLAW skills.
Each provider has specific capabilities and recommended parameters.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ModelSettings:
    """Configuration for a model/provider"""

    name: str
    type: str  # "video" or "image"
    supported_aspect_ratios: List[str]
    supported_resolutions: List[str]
    features: List[str]  # image-to-video, animation, etc.
    recommended_for: List[str]  # use cases
    max_duration: Optional[int] = None  # seconds
    is_free: bool = True
    requires_auth: bool = False


MODEL_SETTINGS: Dict[str, ModelSettings] = {
    # === IMAGE GENERATORS ===
    "perchance": ModelSettings(
        name="Perchance AI",
        type="image",
        supported_aspect_ratios=["1:1", "9:16", "16:9", "4:3", "3:4"],
        supported_resolutions=["square", "portrait", "landscape", "hd", "portrait_hd"],
        features=[
            "negative_prompts",
            "seed_control",
            "batch_generation",
            "style_templates",
        ],
        recommended_for=[
            "social_media",
            "product_photos",
            "anime",
            "artwork",
            "portraits",
        ],
        is_free=True,
    ),
    "leonardo": ModelSettings(
        name="Leonardo AI",
        type="image",
        supported_aspect_ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"],
        supported_resolutions=["512", "768", "1024"],
        features=["image_to_video", "controlnet", "inpainting", "style_models"],
        recommended_for=["concept_art", "game_assets", "characters", "environments"],
        is_free=True,
    ),
    # === VIDEO GENERATORS ===
    "pixverse": ModelSettings(
        name="PixVerse",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["540", "720", "1080"],
        features=["image_to_video", "text_to_video", "character_animation"],
        recommended_for=["short_form", "social_media", "characters"],
        max_duration=10,
        is_free=True,
    ),
    "kling": ModelSettings(
        name="Kling AI",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video", "video_extend"],
        recommended_for=["cinematic", "high_quality", "professional"],
        max_duration=20,
        is_free=True,
    ),
    "haiper": ModelSettings(
        name="Haiper AI",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video", "animated_drawings"],
        recommended_for=["animated_content", "short_clips", "social_media"],
        max_duration=8,
        is_free=True,
    ),
    "luma": ModelSettings(
        name="Luma Dream Machine",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["image_to_video", "camera_motion", "text_to_video"],
        recommended_for=["product_shots", "cinematic", "photorealistic"],
        max_duration=10,
        is_free=True,
    ),
    "runway": ModelSettings(
        name="Runway Gen",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["image_to_video", "video_to_video", "motion_lora"],
        recommended_for=["professional", "film", "creative"],
        max_duration=10,
        is_free=True,
    ),
    "pika": ModelSettings(
        name="Pika",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video", "video_extend"],
        recommended_for=["short_form", "quick_generation"],
        max_duration=10,
        is_free=True,
    ),
    "ltx": ModelSettings(
        name="LTX Video",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["512", "768", "1024"],
        features=["text_to_video", "cartoon", "animated"],
        recommended_for=["cartoon", "animation", "tech_content"],
        max_duration=16,
        is_free=True,
    ),
    "vidu": ModelSettings(
        name="VidU",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["image_to_video", "character_consistency"],
        recommended_for=["characters", "portraits"],
        max_duration=10,
        is_free=True,
    ),
    "hailuo": ModelSettings(
        name="Hailuo",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video"],
        recommended_for=["short_clips", "social_media"],
        max_duration=10,
        is_free=True,
    ),
    "seedance": ModelSettings(
        name="Seedance",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video"],
        recommended_for=["advertising", "promos"],
        max_duration=10,
        is_free=True,
    ),
    "leiapix": ModelSettings(
        name="LeiaPix",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1", "4:3"],
        supported_resolutions=["720", "1080"],
        features=["image_to_video", "motion_effects"],
        recommended_for=["image_to_video", "cinemagraphs"],
        max_duration=8,
        is_free=True,
    ),
    "fliki": ModelSettings(
        name="Fliki",
        type="video",
        supported_aspect_ratios=["16:9", "9:16"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "voiceover"],
        recommended_for=["video_with_audio", "voiceover_content"],
        max_duration=30,
        is_free=True,
    ),
    "invideo": ModelSettings(
        name="InVideo AI",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "templates", "video_editing"],
        recommended_for=["social_media", "marketing", "youtube"],
        max_duration=30,
        is_free=True,
    ),
    "kaiber": ModelSettings(
        name="Kaiber",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["image_to_video", "style_transfer", "animation"],
        recommended_for=["artistic", "animation", "music_videos"],
        max_duration=30,
        is_free=True,
    ),
    "morph": ModelSettings(
        name="Morph Studio",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video"],
        recommended_for=["short_clips", "animation"],
        max_duration=10,
        is_free=True,
    ),
    "genmo": ModelSettings(
        name="Genmo",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["512", "768", "1024"],
        features=["text_to_video", "creative", "artistic"],
        recommended_for=["creative", "artistic", "experimental"],
        max_duration=10,
        is_free=True,
    ),
    "heygen": ModelSettings(
        name="HeyGen",
        type="video",
        supported_aspect_ratios=["16:9", "9:16"],
        supported_resolutions=["720", "1080"],
        features=["avatar", "talking_head", "voiceover"],
        recommended_for=["avatars", "presentations", "talking_head"],
        max_duration=60,
        is_free=True,
    ),
    "frameloop": ModelSettings(
        name="FrameLoop",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video"],
        recommended_for=["motion_design", "creative"],
        max_duration=10,
        is_free=True,
    ),
    "wavespeed": ModelSettings(
        name="WaveSpeed AI",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video"],
        recommended_for=["quick_generation", "short_form"],
        max_duration=10,
        is_free=True,
    ),
    "videoany": ModelSettings(
        name="Video Any",
        type="video",
        supported_aspect_ratios=["16:9", "9:16", "1:1"],
        supported_resolutions=["720", "1080"],
        features=["text_to_video", "image_to_video"],
        recommended_for=["general", "short_form"],
        max_duration=10,
        is_free=True,
    ),
}


def get_model_settings(provider: str) -> Optional[ModelSettings]:
    """Get settings for a provider"""
    return MODEL_SETTINGS.get(provider.lower())


def get_recommended_settings(provider: str, use_case: str = None) -> Dict[str, Any]:
    """
    Get recommended settings for a provider based on use case.

    Args:
        provider: Provider name (e.g., "pixverse", "perchance")
        use_case: Optional use case - "short_form", "cinematic", "product", etc.

    Returns:
        Dict of recommended settings
    """
    settings = get_model_settings(provider)
    if not settings:
        return {}

    recs = {
        "aspect_ratio": "16:9",
        "resolution": "720",
    }

    # Use case specific recommendations
    if use_case == "short_form" or use_case == "tiktok" or use_case == "reels":
        recs["aspect_ratio"] = "9:16"
        recs["resolution"] = "720"
    elif use_case == "cinematic" or use_case == "film":
        recs["aspect_ratio"] = "16:9"
        recs["resolution"] = "1080"
    elif use_case == "product":
        recs["aspect_ratio"] = "1:1"
        recs["resolution"] = "1080"
    elif use_case == "portrait":
        recs["aspect_ratio"] = "9:16"
        recs["resolution"] = "1080"
    elif use_case == "story":
        recs["aspect_ratio"] = "9:16"
        recs["resolution"] = "720"
        recs["max_duration"] = 15

    # Override with provider capabilities
    if settings.supported_aspect_ratios:
        # Prioritize use case aspect ratio if supported
        use_case_ratio = recs.get("aspect_ratio")
        if use_case_ratio and use_case_ratio in settings.supported_aspect_ratios:
            recs["aspect_ratio"] = use_case_ratio
        else:
            recs["aspect_ratio"] = settings.supported_aspect_ratios[0]

    return recs


def get_image_recommended_settings(
    provider: str, style: str = None, format: str = None
) -> Dict[str, Any]:
    """
    Get recommended settings for image generation.

    Args:
        provider: Provider name
        style: "photo", "anime", "product", "artwork", "portrait"
        format: "square", "portrait", "landscape", "story"

    Returns:
        Dict of recommended settings
    """
    settings = get_model_settings(provider)
    if not settings or settings.type != "image":
        return {}

    recs = {
        "resolution": "hd",
        "aspect_ratio": "1:1",
        "generator": style or "default",
    }

    # Style specific
    style_map = {
        "photo": "photo",
        "anime": "anime",
        "product": "product",
        "artwork": "default",
        "portrait": "photo",
    }

    if style:
        recs["generator"] = style_map.get(style, "default")

    # Format specific
    format_map = {
        "square": "1:1",
        "portrait": "9:16",
        "landscape": "16:9",
        "story": "9:16",
    }

    if format:
        recs["aspect_ratio"] = format_map.get(format, "1:1")
        if format == "story":
            recs["resolution"] = "portrait_hd"
        elif format == "square":
            recs["resolution"] = "hd"

    return recs


def list_providers(
    type: str = None, feature: str = None, use_case: str = None, free_only: bool = False
) -> List[str]:
    """
    List available providers with optional filtering.

    Args:
        type: "video" or "image"
        feature: Filter by feature (e.g., "image_to_video")
        use_case: Filter by recommended use case
        free_only: Only free providers

    Returns:
        List of provider names
    """
    results = []

    for name, settings in MODEL_SETTINGS.items():
        if type and settings.type != type:
            continue
        if free_only and not settings.is_free:
            continue
        if feature and feature not in settings.features:
            continue
        if use_case and use_case not in settings.recommended_for:
            continue
        results.append(name)

    return results

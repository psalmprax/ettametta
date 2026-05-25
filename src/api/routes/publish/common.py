"""
Shared constants, Pydantic models, and helper utilities for the publish module.

Consolidated from the original monolithic publish.py to eliminate duplication
and centralize reusable components.
"""

import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ─── Supported Platforms ────────────────────────────────────────────────

SUPPORTED_PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "types": ["YouTube Shorts", "YouTube Video"],
        "oauth_provider": "google",
        "max_duration": 60,
        "aspect_ratios": ["9:16", "16:9"],
        "monetization": True,
    },
    "tiktok": {
        "name": "TikTok",
        "types": ["TikTok Video"],
        "oauth_provider": "tiktok",
        "max_duration": 180,
        "aspect_ratios": ["9:16"],
        "monetization": True,
    },
    "instagram": {
        "name": "Instagram",
        "types": ["Instagram Reels", "Instagram Video"],
        "oauth_provider": "facebook",
        "max_duration": 90,
        "aspect_ratios": ["9:16", "1:1", "4:5"],
        "monetization": True,
    },
    "facebook": {
        "name": "Facebook",
        "types": ["Facebook Reels", "Facebook Video"],
        "oauth_provider": "facebook",
        "max_duration": 240,
        "aspect_ratios": ["9:16", "16:9", "1:1"],
        "monetization": True,
    },
    "x": {
        "name": "X (Twitter)",
        "types": ["X Video"],
        "oauth_provider": "twitter",
        "max_duration": 140,
        "aspect_ratios": ["16:9", "1:1"],
        "monetization": True,
    },
    "linkedin": {
        "name": "LinkedIn",
        "types": ["LinkedIn Video"],
        "oauth_provider": "linkedin",
        "max_duration": 600,
        "aspect_ratios": ["16:9", "1:1", "9:16"],
        "monetization": False,
    },
    "snapchat": {
        "name": "Snapchat",
        "types": ["Snapchat Spotlight"],
        "oauth_provider": "snapchat",
        "max_duration": 180,
        "aspect_ratios": ["9:16"],
        "monetization": True,
    },
    "twitch": {
        "name": "Twitch",
        "types": ["Twitch Clip"],
        "oauth_provider": "twitch",
        "max_duration": 60,
        "aspect_ratios": ["16:9"],
        "monetization": True,
    },
}

# ─── Platform Name → Key Mapping ────────────────────────────────────────

PLATFORM_NAME_TO_KEY = {
    "youtube shorts": "youtube",
    "youtube video": "youtube",
    "youtube": "youtube",
    "tiktok": "tiktok",
    "tiktok video": "tiktok",
    "instagram reels": "instagram",
    "instagram video": "instagram",
    "instagram": "instagram",
    "facebook reels": "facebook",
    "facebook video": "facebook",
    "facebook": "facebook",
    "x video": "x",
    "x": "x",
    "twitter": "x",
    "linkedin video": "linkedin",
    "linkedin": "linkedin",
    "snapchat spotlight": "snapchat",
    "snapchat": "snapchat",
    "twitch clip": "twitch",
    "twitch": "twitch",
}

# ─── OAuth Scopes ───────────────────────────────────────────────────────

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# ─── Pydantic Models ───────────────────────────────────────────────────


class PublishRequest(BaseModel):
    video_path: str
    niche: str
    platform: str = "YouTube Shorts"
    account_id: str | None = None
    inject_monetization: bool = False
    variant_b_title: str | None = None
    variant_b_description: str | None = None


class MultiPlatformPublishRequest(BaseModel):
    video_path: str
    niche: str
    platforms: list[str]
    account_id: str | None = None
    inject_monetization: bool = False
    variant_b_title: str | None = None
    variant_b_description: str | None = None


class OpenCLIPostRequest(BaseModel):
    platform: str
    content: str
    media_url: str | None = None


# ─── URL Helpers ────────────────────────────────────────────────────────


def resolve_platform_key(platform_name: str) -> str:
    """Resolve a human-readable platform name to its canonical key."""
    return PLATFORM_NAME_TO_KEY.get(platform_name.lower(), platform_name.lower())


def extract_platform_id(source_uri: str) -> tuple[str | None, str]:
    """
    Extract a platform-specific video ID and platform key from a source URI.

    Returns (platform_id, platform_key). Returns (None, platform_key) if
    the ID cannot be extracted. Supports YouTube and TikTok URL formats.
    """
    if not source_uri:
        return None, ""

    platform_key = ""
    platform_id = None

    # YouTube Extraction
    if "youtube.com" in source_uri or "youtu.be" in source_uri:
        platform_key = "youtube"
        if "youtu.be" in source_uri:
            platform_id = source_uri.split("/")[-1].split("?")[0]
        else:
            url_parts = source_uri.split("/")
            for i, part in enumerate(url_parts):
                if part == "watch" and i + 1 < len(url_parts):
                    platform_id = url_parts[i + 1].split("&")[0].split("?")[0]
                    break
                elif part.startswith("UC") or len(part) == 11:
                    platform_id = part.split("?")[0]
                    break

    # TikTok Extraction
    elif "tiktok.com" in source_uri:
        platform_key = "tiktok"
        url_clean = source_uri.split("?")[0]
        url_parts = url_clean.split("/")
        for part in reversed(url_parts):
            if part.isdigit() and len(part) >= 15:
                platform_id = part
                break
            elif len(part) >= 8 and any(c.isalnum() for c in part):
                platform_id = part
                break

    return platform_id, platform_key

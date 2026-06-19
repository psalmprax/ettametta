from fastapi import APIRouter
from src.api.utils.api_responses import success_response

router = APIRouter()

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


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of all supported platforms for publishing"""
    return success_response(
        data={"platforms": SUPPORTED_PLATFORMS, "count": len(SUPPORTED_PLATFORMS)}
    )

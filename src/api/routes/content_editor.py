from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.services.openclaw.skills.content_editor import content_editor_skill
import logging

router = APIRouter(prefix="/content-editor", tags=["Content Editor"])
logger = logging.getLogger(__name__)


class FindContentRequest(BaseModel):
    source: str = "youtube"  # youtube, tiktok, reddit
    query: str = ""
    niche: str = "motivation"
    limit: int = 5


class CreateViralRequest(BaseModel):
    source: str = "youtube"
    url_or_query: str
    niche: str = "motivation"
    style: str = "fast"  # fast, cinematic, story
    add_cta: bool = True
    add_title: bool = True


class GenerateRequest(BaseModel):
    prompt: str
    provider: str = "kling"
    niche: str = "general"
    style: str = "fast"


class FindContentResponse(BaseModel):
    status: str
    videos: list[dict] = []


@router.post("/find")
async def find_content(
    request: Request,
    body: FindContentRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Find content from YouTube, TikTok, or Reddit for remixing.
    """
    try:
        result = await content_editor_skill.find_content(
            source=body.source,
            query=body.query,
            niche=body.niche,
            limit=body.limit,
        )

        return result

    except Exception as e:
        logger.exception(f"[ContentEditor] Find failed: {e}")
        raise HTTPException(
            status_code=503, detail="Content search service unavailable"
        )


@router.post("/viral")
async def create_viral_edit(
    request: Request,
    body: CreateViralRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Create viral content: find → cut → remix → polish with Remotion.
    """
    try:
        result = await content_editor_skill.create_viral_with_remotion(
            source=body.source,
            url_or_query=body.url_or_query,
            niche=body.niche,
            add_cta=body.add_cta,
            add_title=body.add_title,
        )

        return result

    except Exception as e:
        logger.exception(f"[ContentEditor] Viral creation failed: {e}")
        raise HTTPException(
            status_code=503, detail="Content processing service unavailable"
        )


@router.get("/providers")
async def get_providers(
    current_user: UserDB = Depends(get_current_user),
):
    """
    List available video generation providers/skills.
    Each provider is tagged with:
      - browser_automation: true if it relies on Playwright (no stable API)
      - has_direct_api: true if there's a working HTTP/API integration
      - free: whether free credits are available
      - credits: approximate daily free credits (if applicable)
      - platform_cost: platform credits deducted per generation (0 = free)
    """
    return {
        "providers": {
            "generation": [
                # --- Direct API providers (working HTTP integrations) ---
                {"id": "kling", "name": "Kling AI", "free": True, "credits": 100, "platform_cost": 0, "has_direct_api": True, "browser_automation": False},
                {"id": "pika", "name": "Pika", "free": True, "credits": 10, "platform_cost": 10, "has_direct_api": True, "browser_automation": False},
                {"id": "runway", "name": "Runway", "free": True, "credits": 10, "platform_cost": 30, "has_direct_api": True, "browser_automation": False},
                {"id": "haiper", "name": "Haiper", "free": True, "credits": 25, "platform_cost": 0, "has_direct_api": True, "browser_automation": False},
                {"id": "luma", "name": "Luma Dream Machine", "free": True, "credits": 15, "platform_cost": 0, "has_direct_api": True, "browser_automation": False},
                {"id": "pixverse", "name": "PixVerse", "free": True, "credits": 20, "platform_cost": 0, "has_direct_api": True, "browser_automation": False},
                {"id": "stability", "name": "Stability AI", "free": True, "credits": 25, "platform_cost": 0, "has_direct_api": True, "browser_automation": False},
                {"id": "zsky", "name": "ZSky AI", "free": True, "credits": 50, "platform_cost": 0, "has_direct_api": True, "browser_automation": False},
                {"id": "replicate", "name": "Replicate", "free": False, "credits": 0, "platform_cost": 5, "has_direct_api": True, "browser_automation": False},

                # --- Local GPU inference engines (requires GPU node) ---
                {"id": "mochi", "name": "Mochi", "free": False, "credits": 0, "platform_cost": 15, "has_direct_api": True, "browser_automation": False},
                {"id": "wan", "name": "Wan 2.2", "free": False, "credits": 0, "platform_cost": 15, "has_direct_api": True, "browser_automation": False},
                {"id": "cogvideo", "name": "CogVideo", "free": False, "credits": 0, "platform_cost": 20, "has_direct_api": True, "browser_automation": False},
                {"id": "zeroscope", "name": "ZeroScope", "free": False, "credits": 0, "platform_cost": 10, "has_direct_api": True, "browser_automation": False},
                {"id": "animatediff", "name": "AnimateDiff", "free": False, "credits": 0, "platform_cost": 15, "has_direct_api": True, "browser_automation": False},
                {"id": "lite4k", "name": "Lite4K Cinematic", "free": True, "credits": None, "platform_cost": 5, "has_direct_api": True, "browser_automation": False, "note": "No API key required — uses Pollinations.ai + FFmpeg"},
                # --- Browser-automation only (Playwright-based, no stable API) ---
                {"id": "leonardo", "name": "Leonardo", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "frameloop", "name": "Frameloop", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "wavespeed", "name": "WaveSpeedAI", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "ltx", "name": "LTX Studio", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "videoany", "name": "VideoAny", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "vidu", "name": "Vidu", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "hailuo", "name": "Hailuo", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "seedance", "name": "Seedance", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "heygen", "name": "HeyGen", "free": True, "credits": 3, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "kaiber", "name": "Kaiber", "free": True, "credits": 20, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "fliki", "name": "Fliki", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "invideo", "name": "InVideo", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "morph", "name": "Morph Studio", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "genmo", "name": "Genmo", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True},
                {"id": "leiapix", "name": "LeiaPix", "free": True, "credits": 0, "platform_cost": 0, "has_direct_api": False, "browser_automation": True, "note": "Image-to-video depth animation via browser automation"},
            ],
            "content_editor": [
                {
                    "id": "content_editor",
                    "name": "Content Editor",
                    "description": "Find, cut, remix existing content",
                },
            ],
            "remotion": [
                {
                    "id": "cinematic_minimal",
                    "name": "Cinematic Minimal",
                    "template": True,
                },
                {"id": "hormozi", "name": "Hormozi Style", "template": True},
            ],
        }
    }


@router.post("/generate")
async def generate_video(
    request: Request,
    body: GenerateRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Generate video using selected provider.
    Accepts JSON body: {"prompt": "...", "provider": "kling"}
    """
    try:
        result = await content_editor_skill.create_viral_edit(
            source=body.provider,
            url_or_query=body.prompt,
            niche=body.niche if hasattr(body, "niche") else "general",
            style=body.style if hasattr(body, "style") else "fast",
        )
        return result

    except Exception as e:
        logger.exception(f"[ContentEditor] Generation failed: {e}")
        raise HTTPException(
            status_code=503, detail="Content generation service unavailable"
        )

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from api.utils.database import get_db
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
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
    videos: List[Dict] = []


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
        from services.openclaw.skills.content_editor import content_editor_skill

        result = await content_editor_skill.find_content(
            source=body.source,
            query=body.query,
            niche=body.niche,
            limit=body.limit,
        )

        return result

    except Exception as e:
        logger.error(f"[ContentEditor] Find failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        from services.openclaw.skills.content_editor import content_editor_skill

        result = await content_editor_skill.create_viral_with_remotion(
            source=body.source,
            url_or_query=body.url_or_query,
            niche=body.niche,
            add_cta=body.add_cta,
            add_title=body.add_title,
        )

        return result

    except Exception as e:
        logger.error(f"[ContentEditor] Viral creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_providers(
    current_user: UserDB = Depends(get_current_user),
):
    """
    List available video generation providers/skills.
    """
    return {
        "providers": {
            "generation": [
                {"id": "kling", "name": "Kling AI", "free": True, "credits": 66},
                {"id": "pika", "name": "Pika", "free": True, "credits": 150},
                {"id": "runway", "name": "Runway", "free": True},
                {"id": "leonardo", "name": "Leonardo", "free": True},
                {"id": "frameloop", "name": "Frameloop", "free": True},
                {"id": "wavespeed", "name": "WaveSpeedAI", "free": True},
                {"id": "ltx", "name": "LTX Studio", "free": True},
                {"id": "videoany", "name": "VideoAny", "free": True},
                {"id": "vidu", "name": "Vidu", "free": True},
                {"id": "hailuo", "name": "Hailuo", "free": True},
                {"id": "seedance", "name": "Seedance", "free": True},
                {"id": "heygen", "name": "HeyGen", "free": True, "credits": 3},
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
        logger.error(f"[ContentEditor] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

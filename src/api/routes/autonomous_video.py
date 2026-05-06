"""
Autonomous Video Editing API Routes
===================================
Endpoints for AI-driven autonomous video post-production.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from src.api.routes.auth import get_current_user
from src.api.utils.models import UserDB
from src.api.utils.api_responses import success_response
from src.services.video_engine.autonomous_editor import base_autonomous_editor

router = APIRouter(prefix="/video/autonomous", tags=["Autonomous Video"])


class AutoEditRequest(BaseModel):
    script_segments: list[dict]
    video_clips: list[dict]
    audio_track: str | None = None
    background_music: str | None = None
    style: str = "dynamic"  # dynamic, aggressive, smooth, asmr
    output_filename: str | None = None


@router.post("/edit")
async def autonomous_video_edit(
    request: AutoEditRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Fully autonomous video editing pipeline.
    Takes raw clips + script and produces polished final video with:
    - Smart clip matching and pacing
    - Auto-generated captions
    - Intelligent transitions and effects
    - Audio mixing (voiceover + background music)
    """
    try:
        result = await base_autonomous_editor.auto_edit_video(
            script_segments=request.script_segments,
            video_clips=request.video_clips,
            audio_track=request.audio_track,
            background_music=request.background_music,
            style=request.style,
            output_filename=request.output_filename,
        )
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-edit failed: {str(e)}")


class BrollRequest(BaseModel):
    main_clip: str
    broll_library: list[str]
    keywords: list[str]


@router.post("/add-broll")
async def smart_broll_insertion(
    request: BrollRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Intelligently insert B-roll footage based on keyword matching.
    Analyzes main clip content and inserts relevant B-roll at optimal timestamps.
    """
    try:
        result_path = await base_autonomous_editor.add_smart_broll(
            main_clip=request.main_clip,
            broll_library=request.broll_library,
            keywords=request.keywords,
        )
        return success_response(data={"output_path": result_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"B-roll insertion failed: {str(e)}")

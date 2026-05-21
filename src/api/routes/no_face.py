import logging
from fastapi import APIRouter, HTTPException, Depends

logger = logging.getLogger(__name__)
from pydantic import BaseModel
from typing import Any
from src.services.script_generator.service import base_script_service
from src.services.decision_engine.hook_validator import base_validator_service
from src.services.voiceover.service import base_voiceover_service
from src.services.stock_media.service import base_stock_media_service
from src.services.visual_generator.service import base_visual_generator_service
from src.services.multiplatform.translator import base_multiplatform_service
from src.services.scheduler.empire_mode import base_scheduler_service
from src.services.sentinel.algorithm_tracker import base_algorithm_service
from src.api.utils.auth import get_current_user
from src.api.utils.api_responses import success_response

router = APIRouter(prefix="/no-face", tags=["Automation"])


class ScriptRequest(BaseModel):
    topic: str
    niche: str | None = None  # Auto-detected if not provided
    duration_seconds: int = 60
    style: str = "story"
    engine: str = "cloud"
    script: list[dict] | None = None
    use_gpu: bool = False
    batch_count: int = 1


class HookRequest(BaseModel):
    hook: str


@router.post("/script")
async def generate_script(
    request: ScriptRequest, current_user=Depends(get_current_user)
):
    """
    Generates a viral-optimized script for a faceless video.
    """
    try:
        script = await base_script_service.generate_script(
            topic=request.topic,
            niche=request.niche,
            duration_sec=request.duration_seconds,
            style=request.style,
        )
        return success_response(data=script)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Script generation failed: {e}")
        raise HTTPException(status_code=503, detail="Script generation service unavailable")


@router.post("/validate-hook")
async def validate_hook(request: HookRequest, current_user=Depends(get_current_user)):
    """
    Analyzes a hook and provides a viral score and alternatives.
    """
    try:
        analysis = await base_validator_service.validate_hook(request.hook)
        return success_response(data=analysis)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Hook validation failed: {e}")
        raise HTTPException(status_code=503, detail="Hook validation service unavailable")


class VoiceoverRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.post("/synthesize-audio")
async def synthesize_audio(
    request: VoiceoverRequest, current_user=Depends(get_current_user)
):
    """
    Synthesizes audio for a segment.
    """
    path = await base_voiceover_service.generate_voiceover(
        request.text, request.voice_id
    )
    if not path:
        raise HTTPException(status_code=503, detail="Failed to generate voiceover")
    return success_response(data={"audio_uri": path})


class StockSearchRequest(BaseModel):
    query: str


@router.post("/search-stock")
async def search_stock(request: StockSearchRequest, current_user=Depends(get_current_user)):
    """
    Searches for Pexels stock video assets.
    """
    results = await base_stock_media_service.search_videos(request.query)
    return success_response(data=results)


class ImageGenRequest(BaseModel):
    prompt: str


@router.post("/generate-image")
async def generate_image(
    request: ImageGenRequest, current_user=Depends(get_current_user)
):
    """
    Generates an AI image for a segment.
    """
    path = await base_visual_generator_service.generate_image(request.prompt)
    if not path:
        raise HTTPException(status_code=503, detail="Failed to generate image")
    return success_response(data={"image_uri": path})


class TranslateRequest(BaseModel):
    script: dict[str, Any]
    target_language: str


@router.post("/translate-script")
async def translate_script(
    request: TranslateRequest, current_user=Depends(get_current_user)
):
    """
    Translates script segments for global reach.
    """
    # Map 'script' to 'segments' for the translator service
    segments = request.script.get("segments", [])
    translated_segments = await base_multiplatform_service.translate_script_segments(
        segments, request.target_language
    )
    
    # Return updated script
    translated_script = {**request.script, "segments": translated_segments}
    return success_response(data=translated_script)


@router.post("/launch-cinema")
async def launch_automated_video(
    request: ScriptRequest, current_user=Depends(get_current_user)
):
    """
    End-to-end automated video generation (Script -> Video).
    """
    try:
        from src.services.nexus_engine.auto_creator import base_creator_service

        # 1. Use existing script or generate new one
        if request.script:
            script = request.script
            logger.info("Using provided script override for cinema launch")
        else:
            script = await base_script_service.generate_script(
                topic=request.topic,
                niche=request.niche,
                duration_sec=request.duration_seconds,
                style=request.style,
            )
        
        # 2. Trigger Auto-Creator (Standard 4.2: Automated Pipeline)
        job_id = await base_creator_service.launch_automated_video(
            user_id=current_user.id,
            topic=request.topic,
            niche=request.niche,
            style=request.style,
            duration=request.duration_seconds,
            engine=request.engine,
            script=script,
            use_gpu=request.use_gpu,
            batch_count=request.batch_count
        )
        
        return success_response(data={
            "message": "Cinema sequence initiated",
            "job_id": job_id,
            "script": script
        })
    except Exception as e:
        logging.error(f"Cinema launch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Cinema engine currently offline: {str(e)}")


@router.get("/sentinel/status")
async def get_sentinel_status(current_user=Depends(get_current_user)):
    """
    Returns the algorithm sync status.
    """
    status = await base_algorithm_service.get_sync_status()
    return success_response(data=status)


from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services.script_generator.service import base_script_generator
from services.decision_engine.hook_validator import base_hook_validator
from services.voiceover.service import base_voiceover_service
from services.stock_media.service import base_stock_service
from services.visual_generator.service import base_visual_generator
from services.multiplatform.translator import base_global_adapter
from services.scheduler.empire_mode import base_empire_scheduler
from services.sentinel.algorithm_tracker import base_algorithm_sentinel
from api.routes.auth import get_current_user

router = APIRouter(prefix="/no-face", tags=["No-Face Monetization"])

class ScriptRequest(BaseModel):
    topic: str
    niche: str = "AI Technology"
    duration: int = 60
    style: str = "story"

class HookRequest(BaseModel):
    hook: str

@router.post("/generate-script")
async def generate_script(request: ScriptRequest, current_user = Depends(get_current_user)):
    """
    Generates a viral-optimized script for a faceless video.
    """
    try:
        script = await base_script_generator.generate_script(
            topic=request.topic,
            niche=request.niche,
            duration_sec=request.duration,
            style=request.style
        )
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-hook")
async def validate_hook(request: HookRequest, current_user = Depends(get_current_user)):
    """
    Analyzes a hook and provides a viral score and alternatives.
    """
    try:
        analysis = await base_hook_validator.validate_hook(request.hook)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class VoiceoverRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None

@router.post("/generate-voiceover")
async def generate_voiceover(request: VoiceoverRequest, current_user = Depends(get_current_user)):
    """
    Synthesizes audio for a segment.
    """
    path = await base_voiceover_service.generate_voiceover(request.text, request.voice_id)
    if not path:
        raise HTTPException(status_code=500, detail="Failed to generate voiceover")
    return {"audio_url": path}

@router.get("/search-stock")
async def search_stock(query: str, current_user = Depends(get_current_user)):
    """
    Searches for Pexels stock video assets.
    """
    results = await base_stock_service.search_videos(query)
    return results

class ImageGenRequest(BaseModel):
    prompt: str

@router.post("/generate-image")
async def generate_image(request: ImageGenRequest, current_user = Depends(get_current_user)):
    """
    Generates an AI image for a segment.
    """
    path = await base_visual_generator.generate_image(request.prompt)
    if not path:
        raise HTTPException(status_code=500, detail="Failed to generate image")
    return {"image_url": path}

class LocalizeRequest(BaseModel):
    segments: List[Dict[str, Any]]
    target_lang: str

@router.post("/localize")
async def localize_script(request: LocalizeRequest, current_user = Depends(get_current_user)):
    """
    Translates script segments for global reach.
    """
    translated = await base_global_adapter.translate_script_segments(request.segments, request.target_lang)
    return translated

class EmpireCloneRequest(BaseModel):
    base_script: Dict[str, Any]
    target_niche: str

@router.post("/empire/clone")
async def empire_clone(request: EmpireCloneRequest, current_user = Depends(get_current_user)):
    """
    Clones a script strategy for a new niche.
    """
    cloned = await base_empire_scheduler.clone_strategy(request.base_script, request.target_niche)
    return cloned

@router.get("/sentinel/status")
async def get_sentinel_status(current_user = Depends(get_current_user)):
    """
    Returns the algorithm sync status.
    """
    status = await base_algorithm_sentinel.get_sync_status()
    return status

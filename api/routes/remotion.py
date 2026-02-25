from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.video_engine.remotion_service import remotion_service
import logging
import uuid

router = APIRouter(prefix="/remotion", tags=["remotion"])
logger = logging.getLogger(__name__)

class RenderRequest(BaseModel):
    title: str
    subtitle: str
    video_url: Optional[str] = None
    composition_id: str = "ViralClip"

async def run_render_task(composition_id: str, props: Dict[str, Any], job_id: str):
    """Background task to execute Remotion render."""
    try:
        output_name = f"render_{job_id}.mp4"
        result = await remotion_service.render_video(composition_id, props, output_name)
        if result:
            logger.info(f"Successfully rendered video for job {job_id}")
        else:
            logger.error(f"Render task failed for job {job_id}")
    except Exception as e:
        logger.error(f"Error in background render task: {e}")

@router.post("/render")
async def trigger_render(req: RenderRequest, background_tasks: BackgroundTasks):
    """
    Triggers a programmatic Remotion render in the background.
    """
    job_id = str(uuid.uuid4())[:8]
    
    props = {
        "title": req.title,
        "subtitle": req.subtitle,
        "video_url": req.video_url or "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    }
    
    background_tasks.add_task(run_render_task, req.composition_id, props, job_id)
    
    return {
        "status": "pending",
        "job_id": job_id,
        "message": "Render task queued in background."
    }

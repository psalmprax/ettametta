from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
from src.services.video_engine.remotion_service import RemotionService
import logging

# Backward compatibility
base_remotion_service = RemotionService()
import uuid
from src.api.utils.auth import get_current_user

from src.shared.enums import SystemJobStatus

router = APIRouter(prefix="/remotion", tags=["remotion"])
logger = logging.getLogger(__name__)


class RenderRequest(BaseModel):
    title: str
    subtitle: str
    video_uri: str | None = None
    composition_id: str = "ViralClip"


async def run_render_task(composition_id: str, props: dict[str, Any], job_id: str):
    """Background task to execute Remotion render."""
    try:
        output_name = f"render_{job_id}.mp4"
        result = await base_remotion_service.render_video(
            composition_id, props, output_name
        )
        if result:
            logger.info(f"Successfully rendered video for job {job_id}")
        else:
            logger.error(f"Render task failed for job {job_id}")
    except Exception as e:
        logger.error(f"Error in background render task: {e}")


@router.post("/render")
async def trigger_render(
    req: RenderRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """
    Triggers a programmatic Remotion render in the background.
    Requires authentication.
    """
    job_id = str(uuid.uuid4())[:8]

    props = {
        "title": req.title,
        "subtitle": req.subtitle,
        "video_uri": req.video_uri
        or "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    }

    background_tasks.add_task(run_render_task, req.composition_id, props, job_id)

    return {
        "status": SystemJobStatus.QUEUED.value,
        "job_id": job_id,
        "message": "Render task queued in background.",
    }

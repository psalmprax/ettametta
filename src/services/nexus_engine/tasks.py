import asyncio
import logging
from src.api.utils.celery import celery_app
from src.services.nexus_engine.auto_creator import base_creator_service

logger = logging.getLogger(__name__)

def run_async(coro):
    """Run async coroutine in sync context (Celery worker)"""
    return asyncio.run(coro)

@celery_app.task(name="nexus.create_cinema_video")
def create_cinema_video_task(
    job_id: str,
    topic: str,
    niche: str,
    user_id: str | None = None,
    style: str = "CINEMATIC_DOC",
    duration_seconds: int = 60
):
    """
    Celery task wrapper for AutoCreator.create_cinema_video.
    """
    _ = user_id
    logger.info(f"[Nexus Task] Starting cinema video generation for job {job_id}")
    try:
        result = run_async(base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche=niche,
            style=style,
            duration_seconds=duration_seconds
        ))
        logger.info(f"[Nexus Task] Completed job {job_id}. Output: {result}")
        return {"status": "success", "output_path": result}
    except Exception as e:
        logger.exception(f"[Nexus Task] Job {job_id} FAILED")
        return {"status": "error", "error": str(e)}

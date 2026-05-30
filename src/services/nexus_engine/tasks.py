import asyncio
import logging
from datetime import datetime, timedelta
from src.api.utils.celery import celery_app
from src.services.nexus_engine.auto_creator import base_creator_service

logger = logging.getLogger(__name__)

def run_async(coro):
    """Run async coroutine in sync context (Celery worker)"""
    return asyncio.run(coro)


def _mark_job_failed(job_id: str, error: str) -> None:
    """Update nexus_jobs row to FAILED and notify WebSocket clients."""
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import NexusJobDB
    from src.api.routes.ws import notify_nexus_job_update_sync
    from src.shared.enums import SystemJobStatus
    from sqlalchemy import select

    async def _do():
        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                job.status = SystemJobStatus.FAILED
                job.error_log = error
                # Mark any ACTIVE node as FAILED
                import json
                raw = job.node_status or {}
                current_status = dict(raw) if isinstance(raw, dict) else json.loads(raw) if isinstance(raw, str) else {}
                for node, st in current_status.items():
                    if st == "ACTIVE":
                        current_status[node] = "FAILED"
                job.node_status = current_status
                await db.commit()

    try:
        asyncio.run(_do())
    except Exception:
        logger.exception(f"[Nexus Task] Failed to update DB for job {job_id}")

    try:
        notify_nexus_job_update_sync({
            "id": str(job_id),
            "status": SystemJobStatus.FAILED,
            "progress": 0,
            "error": error,
        })
    except Exception:
        logger.exception(f"[Nexus Task] Failed to send WS notification for job {job_id}")


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
        _mark_job_failed(job_id, str(e))
        return {"status": "error", "error": str(e)}


@celery_app.task(name="nexus.cleanup_stale_jobs")
def cleanup_stale_jobs_task():
    """Mark nexus jobs stuck in non-terminal states for >30 minutes as FAILED."""
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import NexusJobDB
    from src.api.routes.ws import notify_nexus_job_update_sync
    from src.shared.enums import SystemJobStatus
    from sqlalchemy import select

    STALE_THRESHOLD_MINUTES = 30
    # Use naive UTC — SQLAlchemy columns store naive datetimes
    cutoff = datetime.utcnow() - timedelta(minutes=STALE_THRESHOLD_MINUTES)

    async def _do():
        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(
                NexusJobDB.status.notin_([
                    SystemJobStatus.COMPLETED,
                    SystemJobStatus.FAILED,
                    SystemJobStatus.ABORTED,
                ]),
                NexusJobDB.updated_at < cutoff,
            )
            result = await db.execute(stmt)
            stale_jobs = result.scalars().all()

            if not stale_jobs:
                logger.info("[Nexus Cleanup] No stale jobs found")
                return 0

            for job in stale_jobs:
                age = datetime.utcnow() - (job.updated_at or job.created_at)
                stale_minutes = int(age.total_seconds() / 60)
                original_status = job.status
                logger.warning(
                    f"[Nexus Cleanup] Marking stale job {job.id} as FAILED "
                    f"(status={original_status}, node={job.current_node}, "
                    f"stale for {stale_minutes}min)"
                )
                job.status = SystemJobStatus.FAILED
                job.error_log = (
                    f"Job stuck in {original_status} state for "
                    f"{stale_minutes} minutes — auto-failed by cleanup"
                )
                import json as _json
                raw = job.node_status or {}
                current_status = dict(raw) if isinstance(raw, dict) else _json.loads(raw) if isinstance(raw, str) else {}
                for node, st in current_status.items():
                    if st == "ACTIVE":
                        current_status[node] = "FAILED"
                job.node_status = current_status

                try:
                    notify_nexus_job_update_sync({
                        "id": str(job.id),
                        "status": SystemJobStatus.FAILED,
                        "progress": job.progress or 0,
                        "error": job.error_log,
                    })
                except Exception:
                    pass

            await db.commit()
            logger.warning(f"[Nexus Cleanup] Marked {len(stale_jobs)} stale jobs as FAILED")
            return len(stale_jobs)

    return asyncio.run(_do())

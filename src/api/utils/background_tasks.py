"""
Background Task Error Wrapper

FastAPI's BackgroundTasks silently swallow exceptions — if a background task crashes,
the exception is logged but never propagated, and the job in the database stays in
QUEUED/COMPOSING status forever with no WebSocket notification to the frontend.

This module provides a wrapper that:
1. Catches exceptions from background tasks
2. Updates job status to FAILED in database
3. Sends WebSocket notification to frontend
4. Logs errors properly with full traceback
"""

import asyncio
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Coroutine

from src.api.utils.database import async_session_factory
from src.api.routes.ws import notify_nexus_job_update_sync
from src.shared.enums import SystemJobStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def _update_job_failed(
    job_id: str,
    error: Exception,
    job_model: type | None,
    progress: int = 0,
    custom_error: str | None = None,
) -> None:
    """
    Update a job to FAILED status in the database and send WebSocket notification.

    Args:
        job_id: The job ID (string UUID)
        error: The exception that occurred
        job_model: The SQLAlchemy model class (e.g., NexusJobDB, VideoJobDB) or None
        progress: Progress value to set (default 0 for failed)
        custom_error: Optional custom error message (defaults to str(error))
    """
    error_msg = custom_error or str(error)
    full_traceback = traceback.format_exc()

    # If no job model, just log the error (for jobs without DB tracking)
    if job_model is None:
        logger.error(f"[BackgroundTask] Job {job_id} failed (no DB model): {error_msg}\n{full_traceback}")
        return

    try:
        async with async_session_factory() as db:
            stmt = select(job_model).where(job_model.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

            if job:
                job.status = SystemJobStatus.FAILED
                job.progress = progress
                job.error_log = f"{error_msg}\n\nTraceback:\n{full_traceback}"
                await db.commit()

                # Send WebSocket notification
                notify_nexus_job_update_sync({
                    "id": str(job.id),
                    "status": SystemJobStatus.FAILED.value,
                    "progress": progress,
                    "niche": getattr(job, "niche", ""),
                    "error": error_msg,
                })

                logger.error(f"[BackgroundTask] Job {job_id} marked FAILED: {error_msg}")
            else:
                logger.warning(f"[BackgroundTask] Job {job_id} not found for failure update")
    except Exception as db_error:
        logger.exception(f"[BackgroundTask] Failed to update job {job_id} to FAILED: {db_error}")


def safe_background_task(
    job_id: str,
    job_model: type,
    error_prefix: str = "Background task",
) -> Callable:
    """
    Decorator that wraps a background task coroutine to handle errors gracefully.

    Usage:
        @safe_background_task(job_id=new_job.id, job_model=NexusJobDB)
        async def my_background_task():
            await do_something()

        background_tasks.add_task(my_background_task)

    Or as a wrapper function:
        background_tasks.add_task(
            safe_background_task_wrapper(
                run_nexus_composition,
                new_job.id,
                NexusJobDB
            )(new_job.id, request)
        )

    Args:
        job_id: The job ID (string UUID)
        job_model: The SQLAlchemy model class (e.g., NexusJobDB, VideoJobDB)
        error_prefix: Prefix for error log messages

    Returns:
        Decorated coroutine function that handles errors
    """
    def decorator(
        coro_func: Callable[..., Coroutine[Any, Any, Any]]
    ) -> Callable[..., Coroutine[Any, Any, None]]:
        @wraps(coro_func)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            try:
                await coro_func(*args, **kwargs)
            except asyncio.CancelledError:
                # Don't mark as failed for cancellation - just log and re-raise
                logger.info(f"[{error_prefix}] Job {job_id} was cancelled")
                raise
            except Exception as e:
                logger.exception(f"[{error_prefix}] Job {job_id} failed: {e}")
                await _update_job_failed(job_id, e, job_model)

        return wrapper

    return decorator


async def safe_background_task_wrapper(
    coro_func: Callable[..., Coroutine[Any, Any, Any]],
    job_id: str,
    job_model: type,
    error_prefix: str = "Background task",
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Wrapper function to safely execute a background task coroutine.

    Usage:
        background_tasks.add_task(
            safe_background_task_wrapper,
            run_nexus_composition,
            new_job.id,
            NexusJobDB,
            new_job.id,  # args for run_nexus_composition
            request,     # kwargs for run_nexus_composition
        )

    Args:
        coro_func: The coroutine function to execute
        job_id: The job ID (string UUID)
        job_model: The SQLAlchemy model class
        error_prefix: Prefix for error log messages
        *args: Positional arguments to pass to coro_func
        **kwargs: Keyword arguments to pass to coro_func
    """
    try:
        await coro_func(*args, **kwargs)
    except asyncio.CancelledError:
        logger.info(f"[{error_prefix}] Job {job_id} was cancelled")
        raise
    except Exception as e:
        logger.exception(f"[{error_prefix}] Job {job_id} failed: {e}")
        await _update_job_failed(job_id, e, job_model)


class BackgroundTaskManager:
    """
    Context manager for managing multiple background tasks with error handling.

    Usage:
        async with BackgroundTaskManager() as btm:
            btm.add_task(run_nexus_composition, new_job.id, request, job_id=new_job.id, job_model=NexusJobDB)
            btm.add_task(another_task, job_id=other_job.id, job_model=VideoJobDB)
        # All tasks are awaited, errors handled
    """

    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    def add_task(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, Any]],
        job_id: str,
        job_model: type,
        error_prefix: str = "Background task",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add a background task with error handling."""
        task = asyncio.create_task(
            safe_background_task_wrapper(
                coro_func, job_id, job_model, error_prefix, *args, **kwargs
            )
        )
        self._tasks.append(task)

    async def __aenter__(self) -> "BackgroundTaskManager":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._tasks:
            # Wait for all tasks, collect exceptions
            results = await asyncio.gather(*self._tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.exception(f"BackgroundTaskManager: Task {i} failed: {result}")


# Convenience function for the most common pattern in this codebase
async def run_nexus_composition_safe(
    job_id: str,
    request: Any,  # NexusComposeRequest
) -> None:
    """
    Safe wrapper for run_nexus_composition that handles errors properly.
    Use this instead of directly calling run_nexus_composition in background_tasks.
    """
    from src.api.routes.nexus import run_nexus_composition
    await safe_background_task_wrapper(
        run_nexus_composition,
        job_id,
        None,  # Will be inferred from the function
        "Nexus Composition",
        job_id,
        request,
    )

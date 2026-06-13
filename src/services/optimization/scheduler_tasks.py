"""
Scheduled Posts and Cleanup Tasks for ettametta
Celery tasks for automated posting and video cleanup
"""

from src.api.utils.celery import celery_app
from src.api.utils.models import ScheduledPostDB, PublishedContentDB
from src.services.optimization.models import PostMetadata
from src.services.optimization.auth import token_manager
from src.shared.enums import ContentPublishStatus, SystemJobStatus
import datetime
import logging
import asyncio
import os
from sqlalchemy import select

logger = logging.getLogger(__name__)


# NOTE: Module paths start from the project root (src/ is in PYTHONPATH via the Celery
# worker entry point or Docker container setup). All publisher references use the full
# ``src.services.optimization.<publisher>.<singleton>`` path.
PLATFORM_PUBLISHERS: dict[str, str] = {
    "youtube": "src.services.optimization.youtube_publisher.base_youtube_service",
    "youtube_shorts": "src.services.optimization.youtube_publisher.base_youtube_service",
    "tiktok": "src.services.optimization.tiktok_publisher.base_tiktok_service",
    "instagram": "src.services.optimization.instagram_publisher.base_instagram_service",
    "facebook": "src.services.optimization.facebook_publisher.base_facebook_publisher_service",
    "linkedin": "src.services.optimization.linkedin_publisher.base_linkedin_publisher_service",
    "x": "src.services.optimization.x_publisher.base_x_publisher_service",
}

# Maximum retry attempts per scheduled post
MAX_SCHEDULE_RETRIES = 3


def _get_publisher(platform: str):
    """Dynamically load publisher for platform"""
    platform_key = platform.lower().replace(" ", "_").replace("-", "_")
    publisher_path = PLATFORM_PUBLISHERS.get(platform_key)

    if not publisher_path:
        logger.warning(f"[Scheduler] No publisher found for platform: {platform}")
        return None

    module_path, publisher_name = publisher_path.rsplit(".", 1)
    try:
        from importlib import import_module

        module = import_module(module_path)
        return getattr(module, publisher_name)
    except Exception as e:
        logger.exception(f"[Scheduler] Failed to load publisher {publisher_path}: {e}")
        return None


async def _check_and_post_scheduled_internal(task_self):
    """Internal async logic for posting scheduled content"""
    from src.api.utils.database import get_async_session
    async with get_async_session() as db:
        processed = 0
        failed = 0
        try:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            stmt = select(ScheduledPostDB).where(
                ScheduledPostDB.status == ContentPublishStatus.PENDING,
                ScheduledPostDB.scheduled_time <= now,
            )
            result = await db.execute(stmt)
            pending_posts = result.scalars().all()

            logger.info(
                f"[Scheduler] Found {len(pending_posts)} pending posts to process (batch cycle at {now.isoformat()})"
            )
            
            if len(pending_posts) == 0:
                return {
                    "processed": 0,
                    "failed": 0,
                    "total": 0,
                    "status": SystemJobStatus.COMPLETED,
                    "message": "No pending posts found",
                }

            for post in pending_posts:
                post_id = post.id
                platform = post.platform
                user_id = post.user_id
                account_id = post.account_id
                video_path = post.video_path
                
                try:
                    logger.info(f"[Scheduler] Processing post {post_id}: platform={platform}, video={video_path}")
                    
                    meta_dict = post.metadata_json
                    if not meta_dict:
                        logger.error(f"[Scheduler] No metadata for post {post_id}")
                        post.status = ContentPublishStatus.FAILED
                        post.error_message = "No metadata available"
                        await db.commit()
                        failed += 1
                        continue

                    metadata = PostMetadata(**meta_dict)
                    logger.info(f"[Scheduler] Post {post_id}: loaded metadata title="{metadata.title}"")

                    # Check authentication tokens
                    user_tokens = await token_manager.get_token_data(
                        platform, user_id
                    )
                    if not user_tokens:
                        logger.warning(
                            f"[Scheduler] Post {post_id}: No auth tokens for user {user_id} on {platform}. Skipping."
                        )
                        post.status = ContentPublishStatus.FAILED
                        post.error_message = f"No authentication tokens for {platform}"
                        await db.commit()
                        failed += 1
                        continue

                    # Dynamically load the platform publisher
                    publisher = _get_publisher(platform)
                    if not publisher:
                        logger.error(
                            f"[Scheduler] Post {post_id}: No publisher available for platform '{platform}'"
                        )
                        post.status = ContentPublishStatus.FAILED
                        post.error_message = f"Platform '{platform}' publisher not found"
                        await db.commit()
                        failed += 1
                        continue

                    logger.info(f"[Scheduler] Post {post_id}: Uploading to {platform}...")
                    url = await publisher.upload_video(
                        video_path,
                        metadata,
                        user_id=user_id,
                        account_id=account_id,
                    )

                    if url:
                        post.status = ContentPublishStatus.PUBLISHED
                        post.published_at = datetime.datetime.now(
                            datetime.timezone.utc
                        ).replace(tzinfo=None)
                        post.error_message = None

                        history = PublishedContentDB(
                            title=metadata.title,
                            platform=platform,
                            status=ContentPublishStatus.PUBLISHED,
                            source_uri=url,
                            account_id=account_id,
                            user_id=user_id,
                            niche=getattr(metadata, "niche", None),
                        )
                        db.add(history)

                        logger.info(f"[Scheduler] ✅ Post {post_id} published successfully: {url}")
                    else:
                        post.status = ContentPublishStatus.FAILED
                        post.error_message = "Upload failed - publisher returned no URL"
                        logger.warning(f"[Scheduler] ❌ Post {post_id} upload failed (no URL returned)")
                        failed += 1

                except Exception as e:
                    logger.exception(f"[Scheduler] ❌ Post {post_id} failed with exception: {e}")
                    post.status = ContentPublishStatus.FAILED
                    post.error_message = str(e)[:500]
                    failed += 1

                await db.commit()
                processed += 1

            logger.info(f"[Scheduler] Batch complete: {processed} processed, {failed} failed out of {len(pending_posts)}")
            return {
                "processed": processed,
                "failed": failed,
                "total": len(pending_posts),
                "status": SystemJobStatus.COMPLETED,
            }
        except Exception as e:
            logger.exception(f"[Scheduler] Critical error: {e}")
            return {"error": str(e), "status": SystemJobStatus.FAILED}


@celery_app.task(
    name="optimization.check_and_post_scheduled",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def check_and_post_scheduled(self):
    """
    Periodic task wrapper to check for scheduled posts.
    Runs internal async logic with fresh loop.
    """
    from src.services.video_engine.tasks import run_async
    return run_async(_check_and_post_scheduled_internal(self))



async def _retry_failed_posts_internal():
    """Internal async logic for retrying failed posts"""
    from src.api.utils.database import get_async_session
    async with get_async_session() as db:
        retried = 0
        try:
            stmt = select(ScheduledPostDB).where(ScheduledPostDB.status == ContentPublishStatus.FAILED)
            result = await db.execute(stmt)
            failed_posts = result.scalars().all()

            for post in failed_posts:
                retry_count = getattr(post, "retry_count", 0) or 0
                max_retries = MAX_SCHEDULE_RETRIES

                if retry_count < max_retries:
                    post.status = ContentPublishStatus.PENDING
                    post.retry_count = retry_count + 1
                    post.error_message = f"Retry {retry_count + 1}/{max_retries}"
                    await db.commit()
                    retried += 1
                    logger.info(
                        f"[Scheduler] Retrying post {post.id} (attempt {retry_count + 1})"
                    )

            return {"retried": retried, "status": SystemJobStatus.COMPLETED}
        except Exception as e:
            logger.exception(f"[Scheduler] Retry internal error: {e}")
            return {"error": str(e), "status": SystemJobStatus.FAILED}


@celery_app.task(name="optimization.retry_failed_posts")
def retry_failed_posts():
    """
    Retry failed posts wrapper.
    """
    from src.services.video_engine.tasks import run_async
    return run_async(_retry_failed_posts_internal())


async def _retry_missed_schedules_internal():
    """Retry missed scheduled posts - posts that passed their scheduled time"""
    from src.services.optimization.scheduler import smart_scheduler
    from src.api.utils.database import get_async_session

    async with get_async_session() as db:
        retried = 0
        skipped = 0
        try:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

            # Find posts that missed their scheduled time
            stmt = select(ScheduledPostDB).where(
                ScheduledPostDB.status == ContentPublishStatus.PENDING,
                ScheduledPostDB.scheduled_time < now,
            )
            result = await db.execute(stmt)
            missed_posts = result.scalars().all()

            for post in missed_posts:
                retry_count = getattr(post, "retry_count", 0) or 0
                max_retries = MAX_SCHEDULE_RETRIES

                if retry_count >= max_retries:
                    logger.warning(
                        f"[Scheduler] Post {post.id} reached max retries ({retry_count}/{MAX_SCHEDULE_RETRIES})"
                    )
                    post.status = ContentPublishStatus.FAILED
                    post.error_message = f"Max retries exceeded ({retry_count})"
                    db.add(post)
                    await db.commit()
                    continue

                # Check parallel spacing rules
                parallel_allowed = getattr(post, "parallel_allowed", False)

                if not parallel_allowed:
                    # Get last post time to check spacing
                    stmt_last = (
                        select(ScheduledPostDB)
                        .where(
                            ScheduledPostDB.user_id == post.user_id,
                            ScheduledPostDB.status == ContentPublishStatus.PUBLISHED,
                        )
                        .order_by(ScheduledPostDB.published_at.desc())
                        .limit(1)
                    )
                    result_last = await db.execute(stmt_last)
                    last_post = result_last.scalar_one_or_none()

                    if last_post and not smart_scheduler.is_parallel_allowed(
                        now, last_post.published_at
                    ):
                        # Skip this iteration, not enough spacing
                        skipped += 1
                        continue

                # Retry immediately
                post.status = ContentPublishStatus.PENDING
                post.retry_count = retry_count + 1
                post.last_retry_at = now
                await db.commit()
                retried += 1
                logger.info(
                    f"[Scheduler] Retrying missed post {post.id} (attempt {retry_count + 1})"
                )

            return {"retried": retried, "skipped": skipped, "status": SystemJobStatus.COMPLETED}
        except Exception as e:
            logger.exception(f"[Scheduler] Retry missed internal error: {e}")
            return {"error": str(e), "status": SystemJobStatus.FAILED}


@celery_app.task(name="optimization.retry_missed_schedules")
def retry_missed_schedules():
    """
    Retry posts that missed their scheduled time.
    """
    from src.services.video_engine.tasks import run_async
    return run_async(_retry_missed_schedules_internal())


async def _cleanup_pending_videos_internal():
    """Internal async logic for cleaning up pending videos"""
    from src.api.utils.database import get_async_session
    async with get_async_session() as db:
        deleted_count = 0
        try:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            stmt = select(PublishedContentDB).where(
                PublishedContentDB.status == ContentPublishStatus.PENDING_AUTH
            )
            result = await db.execute(stmt)
            pending_videos = result.scalars().all()

            for video in pending_videos:
                metadata = video.metadata_json or {}
                delete_at_str = metadata.get("delete_at")

                if delete_at_str:
                    try:
                        delete_at = datetime.datetime.fromisoformat(
                            delete_at_str.replace("Z", "+00:00")
                        ).replace(tzinfo=None)

                        if now >= delete_at:
                            logger.info(
                                f"[Cleanup] Deleting video {video.id} - retention expired"
                            )

                            video_path = metadata.get("video_path")
                            if video_path and os.path.exists(video_path):
                                try:
                                    os.remove(video_path)
                                    logger.info(f"[Cleanup] Deleted file: {video_path}")
                                except Exception as e:
                                    logger.exception(
                                        f"[Cleanup] Failed to delete file: {e}"
                                    )

                            video.status = ContentPublishStatus.EXPIRED
                            metadata["deleted_at"] = now.isoformat()
                            metadata["deletion_reason"] = "retention_expired"
                            video.metadata_json = metadata

                            deleted_count += 1
                    except Exception as e:
                        logger.exception(
                            f"[Cleanup] Error processing video {video.id}: {e}"
                        )

            await db.commit()
            return {"deleted": deleted_count, "status": SystemJobStatus.COMPLETED}
        except Exception as e:
            logger.exception(f"[Cleanup] Critical internal error: {e}")
            return {"error": str(e), "status": SystemJobStatus.FAILED}


@celery_app.task(name="optimization.cleanup_pending_videos")
def cleanup_pending_videos():
    """
    Periodic task wrapper to clean up videos.
    """
    from src.services.video_engine.tasks import run_async
    return run_async(_cleanup_pending_videos_internal())


async def _cleanup_old_scheduled_internal():
    """Internal async logic for cleaning up old scheduled posts"""
    from src.api.utils.database import get_async_session
    async with get_async_session() as db:
        deleted = 0
        try:
            cutoff = datetime.datetime.now(datetime.timezone.utc).replace(
                tzinfo=None
            ) - datetime.timedelta(days=7)
            stmt = select(ScheduledPostDB).where(
                ScheduledPostDB.status == ContentPublishStatus.PENDING,
                ScheduledPostDB.scheduled_time < cutoff,
            )
            result = await db.execute(stmt)
            old_posts = result.scalars().all()

            for post in old_posts:
                logger.info(f"[Cleanup] Deleting old scheduled post {post.id}")
                await db.delete(post)
                deleted += 1

            await db.commit()
            return {"deleted": deleted, "status": SystemJobStatus.COMPLETED}
        except Exception as e:
            logger.exception(f"[Cleanup] Old scheduled internal error: {e}")
            return {"error": str(e), "status": SystemJobStatus.FAILED}


@celery_app.task(name="optimization.cleanup_old_scheduled")
def cleanup_old_scheduled():
    """
    Clean up old scheduled posts wrapper.
    """
    from src.services.video_engine.tasks import run_async
    return run_async(_cleanup_old_scheduled_internal())


@celery_app.task(name="optimization.viral_loop_compilation")
def viral_loop_compilation(niche: str = "AI Technology"):
    """
    Trigger a full Lead-to-Edit compilation cycle for a niche.
    """
    from src.services.optimization.viral_loop import base_viral_loop
    return asyncio.run(base_viral_loop.execute_compilation_cycle(niche=niche))

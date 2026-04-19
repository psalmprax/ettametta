"""
Scheduled Posts and Cleanup Tasks for Viral Forge
Celery tasks for automated posting and video cleanup
"""

from api.utils.celery import celery_app
from api.utils.database import async_session_factory
from api.utils.models import ScheduledPostDB, PublishedContentDB
from services.optimization.models import PostMetadata
from services.optimization.auth import token_manager
import datetime
import logging
import asyncio
import os
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


PLATFORM_PUBLISHERS = {
    "youtube": "services.optimization.youtube_publisher.base_youtube_publisher",
    "youtube_shorts": "services.optimization.youtube_publisher.base_youtube_publisher",
    "tiktok": "services.optimization.tiktok_publisher.base_tiktok_publisher",
    "instagram": "services.optimization.instagram_publisher.base_instagram_publisher",
    "facebook": "services.optimization.facebook_publisher.base_facebook_publisher",
    "linkedin": "services.optimization.linkedin_publisher.base_linkedin_publisher",
    "x": "services.optimization.x_publisher.base_x_publisher",
}


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
        logger.error(f"[Scheduler] Failed to load publisher {publisher_path}: {e}")
        return None


async def _check_and_post_scheduled_internal(task_self):
    """Internal async logic for posting scheduled content"""
    async with async_session_factory() as db:
        processed = 0
        failed = 0
        try:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            stmt = select(ScheduledPostDB).where(
                ScheduledPostDB.status == "PENDING",
                ScheduledPostDB.scheduled_time <= now,
            )
            result = await db.execute(stmt)
            pending_posts = result.scalars().all()

            logger.info(
                f"[Scheduler] Found {len(pending_posts)} pending posts to process"
            )

            for post in pending_posts:
                try:
                    meta_dict = post.metadata_json
                    if not meta_dict:
                        logger.error(f"[Scheduler] No metadata for post {post.id}")
                        post.status = "FAILED"
                        post.error_message = "No metadata available"
                        await db.commit()
                        failed += 1
                        continue

                    metadata = PostMetadata(**meta_dict)

                    user_tokens = await token_manager.get_token_data(
                        post.platform, post.user_id
                    )
                    if not user_tokens:
                        logger.error(
                            f"[Scheduler] No tokens for user {post.user_id} on platform {post.platform}"
                        )
                        post.status = "FAILED"
                        post.error_message = "No authentication tokens"
                        await db.commit()
                        failed += 1
                        continue

                    publisher = _get_publisher(post.platform)
                    if not publisher:
                        logger.error(
                            f"[Scheduler] No publisher for platform: {post.platform}"
                        )
                        post.status = "FAILED"
                        post.error_message = f"Platform {post.platform} not supported"
                        await db.commit()
                        failed += 1
                        continue

                    # Adjust to nearest peak window
                    import asyncio

                    peak_windows = await self._get_peak_windows_from_db(post.user_id)

                    url = await publisher.upload_video(
                        post.video_path,
                        metadata,
                        user_id=post.user_id,
                        account_id=post.account_id,
                    )

                    if url:
                        post.status = "PUBLISHED"
                        post.published_at = datetime.datetime.now(
                            datetime.timezone.utc
                        ).replace(tzinfo=None)

                        history = PublishedContentDB(
                            title=metadata.title,
                            platform=post.platform,
                            status="Published",
                            url=url,
                            account_id=post.account_id,
                            user_id=post.user_id,
                            niche=getattr(metadata, "niche", None),
                        )
                        db.add(history)

                        logger.info(
                            f"[Scheduler] Successfully published post {post.id}: {url}"
                        )
                    else:
                        post.status = "FAILED"
                        post.error_message = "Upload failed - no URL returned"
                        logger.warning(f"[Scheduler] Post {post.id} upload failed")
                        failed += 1

                except Exception as e:
                    logger.error(f"[Scheduler] Post {post.id} failed: {e}")
                    post.status = "FAILED"
                    post.error_message = str(e)[:500]
                    failed += 1
                    # In a real async task, we'd handle retries differently,
                    # but for now we follow the existing pattern of flagging as FAILED.

                await db.commit()
                processed += 1

            return {
                "processed": processed,
                "failed": failed,
                "total": len(pending_posts),
                "status": "completed",
            }
        except Exception as e:
            logger.error(f"[Scheduler] Critical error: {e}")
            return {"error": str(e), "status": "failed"}


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
    Runs internal async logic.
    """
    return asyncio.run(_check_and_post_scheduled_internal(self))


async def _retry_failed_posts_internal():
    """Internal async logic for retrying failed posts"""
    async with async_session_factory() as db:
        retried = 0
        try:
            stmt = select(ScheduledPostDB).where(ScheduledPostDB.status == "FAILED")
            result = await db.execute(stmt)
            failed_posts = result.scalars().all()

            for post in failed_posts:
                retry_count = getattr(post, "retry_count", 0)
                max_retries = getattr(post, "max_retries", 3)

                if retry_count < max_retries:
                    post.status = "PENDING"
                    post.retry_count = retry_count + 1
                    post.error_message = f"Retry {retry_count + 1}/{max_retries}"
                    await db.commit()
                    retried += 1
                    logger.info(
                        f"[Scheduler] Retrying post {post.id} (attempt {retry_count + 1})"
                    )

            return {"retried": retried, "status": "completed"}
        except Exception as e:
            logger.error(f"[Scheduler] Retry internal error: {e}")
            return {"error": str(e), "status": "failed"}


@celery_app.task(name="optimization.retry_failed_posts")
def retry_failed_posts():
    """
    Retry failed posts wrapper.
    """
    return asyncio.run(_retry_failed_posts_internal())


async def _retry_missed_schedules_internal():
    """Retry missed scheduled posts - posts that passed their scheduled time"""
    from services.optimization.scheduler import smart_scheduler

    async with async_session_factory() as db:
        retried = 0
        skipped = 0
        try:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

            # Find posts that missed their scheduled time
            stmt = select(ScheduledPostDB).where(
                ScheduledPostDB.status == "PENDING",
                ScheduledPostDB.scheduled_time < now,
            )
            result = await db.execute(stmt)
            missed_posts = result.scalars().all()

            for post in missed_posts:
                retry_count = getattr(post, "retry_count", 0) or 0
                max_retries = 3

                if retry_count >= max_retries:
                    logger.warning(f"[Scheduler] Post {post.id} reached max retries ({retry_count})")
                    post.status = "FAILED"
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
                            ScheduledPostDB.status == "PUBLISHED",
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
                post.status = "PENDING"
                post.retry_count = retry_count + 1
                post.last_retry_at = now
                await db.commit()
                retried += 1
                logger.info(
                    f"[Scheduler] Retrying missed post {post.id} (attempt {retry_count + 1})"
                )

            return {"retried": retried, "skipped": skipped, "status": "completed"}
        except Exception as e:
            logger.error(f"[Scheduler] Retry missed internal error: {e}")
            return {"error": str(e), "status": "failed"}


@celery_app.task(name="optimization.retry_missed_schedules")
def retry_missed_schedules():
    """
    Retry posts that missed their scheduled time.
    """
    return asyncio.run(_retry_missed_schedules_internal())


async def _cleanup_pending_videos_internal():
    """Internal async logic for cleaning up pending videos"""
    async with async_session_factory() as db:
        deleted_count = 0
        try:
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            stmt = select(PublishedContentDB).where(
                PublishedContentDB.status == "PENDING_AUTH"
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
                                    logger.error(
                                        f"[Cleanup] Failed to delete file: {e}"
                                    )

                            video.status = "EXPIRED"
                            metadata["deleted_at"] = now.isoformat()
                            metadata["deletion_reason"] = "retention_expired"
                            video.metadata_json = metadata

                            deleted_count += 1
                    except Exception as e:
                        logger.error(
                            f"[Cleanup] Error processing video {video.id}: {e}"
                        )

            await db.commit()
            return {"deleted": deleted_count, "status": "completed"}
        except Exception as e:
            logger.error(f"[Cleanup] Critical internal error: {e}")
            return {"error": str(e), "status": "failed"}


@celery_app.task(name="optimization.cleanup_pending_videos")
def cleanup_pending_videos():
    """
    Periodic task wrapper to clean up videos.
    """
    return asyncio.run(_cleanup_pending_videos_internal())


async def _cleanup_old_scheduled_internal():
    """Internal async logic for cleaning up old scheduled posts"""
    async with async_session_factory() as db:
        deleted = 0
        try:
            cutoff = datetime.datetime.now(datetime.timezone.utc).replace(
                tzinfo=None
            ) - datetime.timedelta(days=7)
            stmt = select(ScheduledPostDB).where(
                ScheduledPostDB.status == "PENDING",
                ScheduledPostDB.scheduled_time < cutoff,
            )
            result = await db.execute(stmt)
            old_posts = result.scalars().all()

            for post in old_posts:
                logger.info(f"[Cleanup] Deleting old scheduled post {post.id}")
                await db.delete(post)
                deleted += 1

            await db.commit()
            return {"deleted": deleted, "status": "completed"}
        except Exception as e:
            logger.error(f"[Cleanup] Old scheduled internal error: {e}")
            return {"error": str(e), "status": "failed"}


@celery_app.task(name="optimization.cleanup_old_scheduled")
def cleanup_old_scheduled():
    """
    Clean up old scheduled posts wrapper.
    """
    return asyncio.run(_cleanup_old_scheduled_internal())

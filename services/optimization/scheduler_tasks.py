"""
Scheduled Posts and Cleanup Tasks for Viral Forge
Celery tasks for automated posting and video cleanup
"""

from api.utils.celery import celery_app
from api.utils.database import SessionLocal
from api.utils.models import ScheduledPostDB, PublishedContentDB
from services.optimization.models import PostMetadata
from services.optimization.auth import token_manager
import datetime
import logging
import asyncio
import os
from typing import Optional, Dict

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


def _run_async(coro):
    """Run async coroutine in sync context (Python 3.10+ compatible)"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    else:
        return asyncio.coroutines.run(coro)


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
    Periodic task to check for scheduled posts that need to be published.
    Includes retry logic for failed posts.
    """
    db = SessionLocal()
    processed = 0
    failed = 0

    try:
        now = datetime.datetime.utcnow()
        pending_posts = (
            db.query(ScheduledPostDB)
            .filter(
                ScheduledPostDB.status == "PENDING",
                ScheduledPostDB.scheduled_time <= now,
            )
            .all()
        )

        logger.info(f"[Scheduler] Found {len(pending_posts)} pending posts to process")

        for post in pending_posts:
            try:
                meta_dict = post.metadata_json
                if not meta_dict:
                    logger.error(f"[Scheduler] No metadata for post {post.id}")
                    post.status = "FAILED"
                    post.error_message = "No metadata available"
                    db.commit()
                    failed += 1
                    continue

                metadata = PostMetadata(**meta_dict)

                user_tokens = token_manager.get_token_data(post.platform, post.user_id)
                if not user_tokens:
                    logger.error(
                        f"[Scheduler] No tokens for user {post.user_id} on platform {post.platform}"
                    )
                    post.status = "FAILED"
                    post.error_message = "No authentication tokens"
                    db.commit()
                    failed += 1
                    continue

                publisher = _get_publisher(post.platform)
                if not publisher:
                    logger.error(
                        f"[Scheduler] No publisher for platform: {post.platform}"
                    )
                    post.status = "FAILED"
                    post.error_message = f"Platform {post.platform} not supported"
                    db.commit()
                    failed += 1
                    continue

                url = _run_async(
                    publisher.upload_video(
                        post.video_path,
                        metadata,
                        user_id=post.user_id,
                        account_id=post.account_id,
                    )
                )

                if url:
                    post.status = "PUBLISHED"
                    post.published_at = datetime.datetime.utcnow()

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

                raise self.retry(exc=e)

            db.commit()
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
    finally:
        db.close()


@celery_app.task(name="optimization.retry_failed_posts")
def retry_failed_posts():
    """
    Retry failed posts that haven't exceeded max retry count
    """
    db = SessionLocal()
    retried = 0

    try:
        failed_posts = (
            db.query(ScheduledPostDB).filter(ScheduledPostDB.status == "FAILED").all()
        )

        for post in failed_posts:
            retry_count = getattr(post, "retry_count", 0)
            max_retries = 3

            if retry_count < max_retries:
                post.status = "PENDING"
                post.retry_count = retry_count + 1
                post.error_message = f"Retry {retry_count + 1}/{max_retries}"
                db.commit()
                retried += 1
                logger.info(
                    f"[Scheduler] Retrying post {post.id} (attempt {retry_count + 1})"
                )

        return {"retried": retried, "status": "completed"}
    except Exception as e:
        logger.error(f"[Scheduler] Retry task error: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="optimization.cleanup_pending_videos")
def cleanup_pending_videos():
    """
    Periodic task to clean up videos pending authentication beyond retention period.
    Default retention: 3 hours
    """
    db = SessionLocal()
    deleted_count = 0

    try:
        now = datetime.datetime.utcnow()

        pending_videos = (
            db.query(PublishedContentDB)
            .filter(PublishedContentDB.status == "PENDING_AUTH")
            .all()
        )

        for video in pending_videos:
            metadata = video.metadata or {}
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
                                logger.error(f"[Cleanup] Failed to delete file: {e}")

                        video.status = "EXPIRED"
                        metadata["deleted_at"] = now.isoformat()
                        metadata["deletion_reason"] = "retention_expired"
                        video.metadata = metadata

                        deleted_count += 1
                except Exception as e:
                    logger.error(f"[Cleanup] Error processing video {video.id}: {e}")

        db.commit()

        return {"deleted": deleted_count, "status": "completed"}
    except Exception as e:
        logger.error(f"[Cleanup] Critical error: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="optimization.cleanup_old_scheduled")
def cleanup_old_scheduled():
    """
    Clean up old scheduled posts that were never published
    """
    db = SessionLocal()
    deleted = 0

    try:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)

        old_posts = (
            db.query(ScheduledPostDB)
            .filter(
                ScheduledPostDB.status == "PENDING",
                ScheduledPostDB.scheduled_time < cutoff,
            )
            .all()
        )

        for post in old_posts:
            logger.info(f"[Cleanup] Deleting old scheduled post {post.id}")
            db.delete(post)
            deleted += 1

        db.commit()

        return {"deleted": deleted, "status": "completed"}
    except Exception as e:
        logger.error(f"[Cleanup] Old scheduled cleanup error: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()

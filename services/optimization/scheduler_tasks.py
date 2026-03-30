from api.utils.celery import celery_app
from api.utils.database import SessionLocal
from api.utils.models import ScheduledPostDB, PublishedContentDB
from services.optimization.youtube_publisher import base_youtube_publisher
from services.optimization.tiktok_publisher import base_tiktok_publisher
from services.optimization.models import PostMetadata
from services.optimization.auth import token_manager
import datetime
import logging
import asyncio


@celery_app.task(name="optimization.check_and_post_scheduled")
def check_and_post_scheduled():
    """
    Periodic task to check for scheduled posts that need to be published.
    """
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        pending_posts = db.query(ScheduledPostDB).filter(
            ScheduledPostDB.status == "PENDING",
            ScheduledPostDB.scheduled_time <= now
        ).all()
        
        for post in pending_posts:
            logging.info(f"[Scheduler] Triggering post for {post.platform}")
            try:
                # Reconstruct metadata
                meta_dict = post.metadata_json
                metadata = PostMetadata(**meta_dict)
                
                # Get user's tokens
                user_tokens = token_manager.get_tokens(post.platform, post.user_id)
                if not user_tokens:
                    logging.error(f"[Scheduler] No tokens for user {post.user_id}")
                    post.status = "FAILED"
                    db.commit()
                    continue
                
                url = None
                if post.platform == "YouTube Shorts":
                    # Run async upload in sync context
                    loop = asyncio.get_event_loop()
                    url = loop.run_until_complete(
                        base_youtube_publisher.upload_video(
                            post.video_path, 
                            metadata, 
                            account_id=post.account_id,
                            user_id=post.user_id
                        )
                    )
                elif post.platform == "TikTok":
                    loop = asyncio.get_event_loop()
                    url = loop.run_until_complete(
                        base_tiktok_publisher.upload_video(
                            post.video_path, 
                            metadata, 
                            account_id=post.account_id,
                            user_id=post.user_id
                        )
                    )
                
                if url:
                    post.status = "PUBLISHED"
                    # Add to published history
                    history = PublishedContentDB(
                        title=metadata.title,
                        platform=post.platform,
                        status="Published",
                        url=url,
                        account_id=post.account_id,
                        user_id=post.user_id,
                        niche=metadata.niche if hasattr(metadata, 'niche') else None
                    )
                    db.add(history)
                else:
                    post.status = "FAILED"
            except Exception as e:
                logging.error(f"[Scheduler] Post Failed: {e}")
                post.status = "FAILED"
            
            db.commit()
            
        return {"processed": len(pending_posts), "status": "completed"}
        
    finally:
        db.close()

@celery_app.task(name="optimization.cleanup_pending_videos")
def cleanup_pending_videos():
    """
    Periodic task to clean up videos that are pending authentication beyond their retention period.
    Deletes videos that haven't been published within the retention window (default 3 hours).
    """
    db = SessionLocal()
    try:
        now = datetime.datetime.utcnow()
        
        # Find all PENDING_AUTH videos that have passed their delete_at time
        pending_videos = db.query(PublishedContentDB).filter(
            PublishedContentDB.status == "PENDING_AUTH"
        ).all()
        
        deleted_count = 0
        for video in pending_videos:
            metadata = video.metadata or {}
            delete_at_str = metadata.get("delete_at")
            
            if delete_at_str:
                delete_at = datetime.datetime.fromisoformat(delete_at_str.replace("Z", "+00:00"))
                delete_at = delete_at.replace(tzinfo=None)  # Make naive for comparison
                
                if now >= delete_at:
                    # Video has exceeded retention - delete it
                    logging.info(f"[Cleanup] Deleting video {video.id} - retention period expired")
                    
                    # Optionally delete the video file from storage
                    video_path = metadata.get("video_path")
                    if video_path:
                        try:
                            import os
                            if os.path.exists(video_path):
                                os.remove(video_path)
                                logging.info(f"[Cleanup] Deleted video file: {video_path}")
                        except Exception as e:
                            logging.error(f"[Cleanup] Failed to delete video file: {e}")
                    
                    # Update status to EXPIRED
                    video.status = "EXPIRED"
                    metadata["deleted_at"] = now.isoformat()
                    metadata["deletion_reason"] = "retention_expired"
                    video.metadata = metadata
                    
                    deleted_count += 1
        
        db.commit()
        
        return {"deleted": deleted_count, "status": "completed"}
        
    finally:
        db.close()

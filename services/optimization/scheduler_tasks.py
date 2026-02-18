from api.utils.celery import celery_app
from api.utils.database import SessionLocal
from api.utils.models import ScheduledPostDB, PublishedContentDB
from services.optimization.youtube_publisher import base_youtube_publisher
from services.optimization.tiktok_publisher import base_tiktok_publisher
from services.optimization.models import PostMetadata
import datetime
import logging

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
                
                url = None
                if post.platform == "YouTube Shorts":
                    url = base_youtube_publisher.upload_video(post.video_path, metadata, account_id=post.account_id)
                elif post.platform == "TikTok":
                    url = base_tiktok_publisher.upload_video(post.video_path, metadata, account_id=post.account_id)
                
                if url:
                    post.status = "PUBLISHED"
                    # Add to published history
                    history = PublishedContentDB(
                        title=metadata.title,
                        platform=post.platform,
                        status="Published",
                        url=url,
                        account_id=post.account_id,
                        user_id=post.user_id
                    )
                    db.add(history)
                else:
                    post.status = "FAILED"
            except Exception as e:
                logging.error(f"[Scheduler] Post Failed: {e}")
                post.status = "FAILED"
            
            db.commit()
            
    finally:
        db.close()

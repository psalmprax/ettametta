from api.utils.celery import celery_app
from .processor import VideoProcessor
from .downloader import base_video_downloader
from services.optimization.youtube_publisher import base_youtube_publisher
from services.optimization.service import base_optimization_service
import asyncio
import os
import logging

# Bridge to use async code in synchronous Celery worker
def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def cleanup_local_files(*paths):
    """Safely removes local files to prevent disk bloat."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logging.info(f"[Cleanup] Deleted temporary file: {path}")
            except Exception as e:
                logging.error(f"[Cleanup] Failed to delete {path}: {e}")

@celery_app.task(name="video.download_and_process", bind=True)
def download_and_process_task(self, source_url: str, niche: str, platform: str):
    """
    Background task to download, process, and prepare a video.
    """
    from api.utils.database import SessionLocal
    from api.utils.models import VideoJobDB
    import uuid
    import asyncio
    
    task_id = self.request.id
    db = SessionLocal()
    
    def update_job(status=None, progress=None, output_path=None):
        job = db.query(VideoJobDB).filter(VideoJobDB.id == task_id).first()
        if job:
            if status: job.status = status
            if progress is not None: job.progress = progress
            if output_path: job.output_path = output_path
            db.commit()
            
            # Real-time WebSocket Notification
            from api.routes.ws import notify_job_update_sync
            notify_job_update_sync({
                "id": task_id,
                "status": job.status,
                "progress": job.progress,
                "output_path": job.output_path
            })

    try:
        # 1. Download
        update_job(status="Downloading", progress=10)
        video_path = run_async(base_video_downloader.download_video(source_url))
        if not video_path:
            update_job(status="Failed", progress=0)
            return {"status": "error", "message": "Download failed"}
        
        # 2. Process (Apply Dynamic AI Strategy)
        update_job(status="Strategizing", progress=30)
        
        # A. Transcribe first (needed for strategy)
        from .transcription import transcription_service
        transcript = run_async(transcription_service.transcribe_video(video_path))
        
        # B. Generate Strategy via Groq
        from services.decision_engine.service import base_strategy_service
        strategy_obj = run_async(base_strategy_service.generate_visual_strategy(transcript, niche))
        strategy = strategy_obj.dict()
        logging.info(f"[Task] AI Strategy: {strategy['vibe']} (Speed: {strategy['speed_range']}, Jitter: {strategy['jitter_intensity']})")
        
        update_job(status="Rendering", progress=50)
        
        # C. Render with Full Pipeline
        processor = VideoProcessor()
        output_name = f"{uuid.uuid4()}.mp4"
        
        # Dashboard filters (manual) + AI filters (autonomous)
        from api.utils.models import VideoFilterDB
        enabled_filters = [f.id for f in db.query(VideoFilterDB).filter(VideoFilterDB.enabled == True).all()]
        
        processed_path = run_async(processor.process_full_pipeline(
            video_path, 
            output_name, 
            enabled_filters=enabled_filters,
            strategy=strategy
        ))
        
        # 3. Generate SEO metadata/package (USING REAL SERVICE)
        update_job(status="Optimizing", progress=70)
        metadata = run_async(base_optimization_service.generate_viral_package("dummy_id", niche, platform))
        
        # 3.5 Storage (Upload to S3 or prepare local URL)
        from services.storage.service import base_storage_service
        # Upload
        storage_key = base_storage_service.upload_file(processed_path)
        # Get public URL for dashboard preview
        public_url = base_storage_service.get_public_url(storage_key)
        
        # 4. Upload to Social Platform
        update_job(status="Uploading", progress=85)
        url = ""
        if platform == "YouTube Shorts":
            url = run_async(base_youtube_publisher.upload_video(processed_path, metadata))
        elif platform == "TikTok":
             # Use Real TikTok Publisher
            from services.optimization.tiktok_publisher import base_tiktok_publisher
            update_job(status="TikTok Upload", progress=90)
            url = run_async(base_tiktok_publisher.upload_video(processed_path, metadata))
            if not url:
                url = "tiktok_upload_failed_check_logs"
        else:
            url = "platform_not_supported_yet"
            
            
        update_job(status="Completed", progress=100, output_path=public_url)
        
        # 5. Cleanup local artifacts (ONLY if cloud storage is active)
        from api.config import settings
        if settings.STORAGE_PROVIDER != "LOCAL":
            cleanup_local_files(video_path, processed_path)
        else:
            # If local, only delete the raw download
            cleanup_local_files(video_path)

        return {
            "status": "success",
            "url": url,
            "processed_file": processed_path,
            "public_url": public_url
        }
    except Exception as e:
        update_job(status="Failed")
        print(f"[Celery Task] ERROR: {e}")
        # Ensure cleanup on failure
        if 'video_path' in locals(): cleanup_local_files(video_path)
        if 'processed_path' in locals() and settings.STORAGE_PROVIDER != "LOCAL":
             cleanup_local_files(processed_path)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

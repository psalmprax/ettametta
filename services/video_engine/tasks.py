from api.utils.celery import celery_app

# Force use of system ffmpeg BEFORE importing moviepy
import os
os.environ['FFMPEG_BINARY'] = 'ffmpeg'
os.environ['IMAGEIO_FFMPEG_BINARY'] = 'ffmpeg'

from .processor import VideoProcessor
from .downloader import base_video_downloader
from services.optimization.youtube_publisher import base_youtube_publisher
from services.optimization.service import base_optimization_service
import asyncio
import logging
from api.config import settings

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
def download_and_process_task(self, source_url: str, niche: str, platform: str, preview_only: bool = False, style: str = "Default", quality_tier: str = "standard"):
    """
    Main background task to transform and publish content.
    
    Quality Tiers:
    - standard: Tier 2 basic processing (default, no changes)
    - enhanced: Tier 2 + sound design
    - premium: Tier 3 full processing (sound + motion graphics)
    """
    from api.utils.database import SessionLocal
    from api.utils.models import VideoJobDB
    import uuid
    import asyncio
    
    task_id = self.request.id
    db = SessionLocal()
    
    def update_job(status=None, progress=None, output_path=None):
        # Fresh session for each status update to avoid context leaks in prefork
        with SessionLocal() as local_db:
            job = local_db.query(VideoJobDB).filter(VideoJobDB.id == task_id).first()
            if job:
                if status: job.status = status
                if progress is not None: job.progress = progress
                if output_path: job.output_path = output_path
                local_db.commit()
                
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
        update_job(status="Validating", progress=5)
        is_valid = run_async(base_video_downloader.verify_video_asset(source_url))
        if not is_valid:
            update_job(status="Failed", progress=0)
            return {
                "status": "failed",
                "message": "Asset validation failed: Source appears to be audio-only or invalid."
            }

        update_job(status="Downloading", progress=10)
        video_path = run_async(base_video_downloader.download_video(source_url))
        if not video_path:
            update_job(status="Failed", progress=0)
            return {"status": "error", "message": "Download failed"}
        
        # B. Analyze Visuals via Gemini (VLM)
        update_job(status="Analyzing Visuals", progress=35)
        from .vlm_service import vlm_service
        visual_insights = run_async(vlm_service.analyze_video_content(video_path))
        
        # C. Generate Strategy via Groq (Integrated Scraper + VLM Intelligence)
        update_job(status="Strategizing", progress=40)
        from services.decision_engine.service import base_strategy_service
        # We need a transcript placeholder or actual extraction
        transcript = "Visual-only analysis conducted." 
        strategy_obj = run_async(base_strategy_service.generate_visual_strategy(transcript, niche, style=style, visual_insights=visual_insights))
        strategy = strategy_obj.dict()
        logging.info(f"[Task] AI Combined Strategy: {strategy['vibe']} (Style: {style}, Speed: {strategy['speed_range']}, Jitter: {strategy['jitter_intensity']})")
        if visual_insights.get("visual_mood"):
            logging.info(f"[Task] VLM Intuition: {visual_insights['visual_mood']}")
        
        update_job(status="Rendering", progress=50)
        
        # C. Render with Full Pipeline
        processor = VideoProcessor()
        output_name = f"{uuid.uuid4()}.mp4"
        
        # Dashboard filters (manual) + AI filters (autonomous)
        from api.utils.models import VideoFilterDB
        with SessionLocal() as filter_db:
             filters = filter_db.query(VideoFilterDB).filter(VideoFilterDB.enabled == True).all()
             enabled_filters = [f.id for f in filters]
        
        processed_path = run_async(processor.process_full_pipeline(
            video_path, 
            output_name, 
            enabled_filters=enabled_filters,
            strategy=strategy
        ))
        
        # ===== TIER 3 ENHANCEMENTS (Optional) =====
        if quality_tier in ("enhanced", "premium"):
            # Sound Design Enhancement
            update_job(status="Adding Sound Design", progress=55)
            from services.audio.sound_design import sound_design_service
            enhanced_path = run_async(
                sound_design_service.add_background_music(
                    processed_path, 
                    niche=niche
                )
            )
            if enhanced_path:
                processed_path = enhanced_path
                logger.info(f"[Task] Sound design applied - tier: {quality_tier}")
        
        # Premium Tier: Motion Graphics
        if quality_tier == "premium":
            update_job(status="Adding Motion Graphics", progress=60)
            from services.video_engine.motion_graphics import motion_graphics_service
            
            # Add title based on metadata
            title = f"{niche} Secrets" if niche else "Viral Content"
            mg_path = run_async(
                motion_graphics_service.add_title_sequence(
                    processed_path,
                    title=title,
                    style="cinematic"
                )
            )
            if mg_path:
                processed_path = mg_path
                logger.info(f"[Task] Motion graphics applied - tier: {quality_tier}")
        
        # 3. Generate SEO metadata/package (USING REAL SERVICE)
        update_job(status="Optimizing", progress=70)
        metadata = run_async(base_optimization_service.generate_viral_package(task_id, niche, platform))
        
        # 3.5 Storage (Upload to S3 or prepare local URL)
        from services.storage.service import base_storage_service
        # Upload
        storage_key = base_storage_service.upload_file(processed_path)
        # Get public URL for dashboard preview
        public_url = base_storage_service.get_public_url(storage_key)
        
        if preview_only:
            update_job(status="Completed", progress=100, output_path=public_url)
            # Cleanup local artifacts (ONLY if cloud storage is active)
            if settings.STORAGE_PROVIDER != "LOCAL":
                cleanup_local_files(video_path, processed_path)
            else:
                cleanup_local_files(video_path)
                
            return {
                "status": "success",
                "preview_url": public_url,
                "message": "Preview generated (Test Drive)"
            }

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
        logging.error(f"[Celery Task] ERROR: {e}")
        # Ensure cleanup on failure
        if 'video_path' in locals(): cleanup_local_files(video_path)
        if 'processed_path' in locals() and settings.STORAGE_PROVIDER != "LOCAL":
             cleanup_local_files(processed_path)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
@celery_app.task(name="video.generate", bind=True)
def generate_video_task(self, prompt: str, engine: str, style: str, aspect_ratio: str, user_id: int):
    """
    Background task for AI Video Synthesis (T2V).
    """
    from api.utils.database import SessionLocal
    from api.utils.models import VideoJobDB
    from .synthesis_service import generative_service
    import uuid
    
    task_id = self.request.id
    db = SessionLocal()
    
    def update_job(status=None, progress=None, output_path=None):
        job = db.query(VideoJobDB).filter(VideoJobDB.id == task_id).first()
        if job:
            if status: job.status = status
            if progress is not None: job.progress = progress
            if output_path: job.output_path = output_path
            db.commit()
            
            from api.routes.ws import notify_job_update_sync
            notify_job_update_sync({
                "id": task_id,
                "status": job.status,
                "progress": job.progress,
                "output_path": job.output_path
            })

    try:
        # 1. Synthesis
        update_job(status="Synthesizing", progress=10)
        video_url = run_async(generative_service.synthesize_video(prompt, engine=engine, aspect_ratio=aspect_ratio))
        
        if not video_url:
            update_job(status="Failed", progress=0)
            return {"status": "error", "message": "Synthesis failed"}

        # 2. Download generated asset (if it's a URL)
        update_job(status="Downloading Asset", progress=40)
        # For mocks, we treat the URL as the path if it's local, or download it
        if video_url.startswith("http"):
             # In a real scenario, we'd use base_video_downloader.download_video(video_url)
             # But for our current GenerativeService mocks, we'll just log it
             pass

        # 3. Refine with Transformation Engine (Optional but powerful)
        update_job(status="Refining", progress=60)
        # We can reuse the processor logic here if needed
        
        # 4. Storage & Finalization
        update_job(status="Completed", progress=100, output_path=video_url)
        
        return {
            "status": "success",
            "video_url": video_url,
            "engine": engine,
            "prompt_used": prompt
        }
    except Exception as e:
        update_job(status="Failed")
        logging.error(f"[Synthesis Task] Error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="video.generate_story", bind=True)
def generate_story_task(self, prompt: str, engine: str, style: str, user_id: int):
    """
    Orchestrates the synthesis of a multi-scene narrative story.
    """
    from api.utils.database import SessionLocal
    from api.utils.models import VideoJobDB
    from services.decision_engine.service import base_strategy_service
    from services.video_engine.synthesis_service import generative_service
    from services.video_engine.voiceover import base_voiceover_service
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
            
            from api.routes.ws import notify_job_update_sync
            notify_job_update_sync({
                "id": task_id,
                "status": job.status,
                "progress": job.progress,
                "output_path": job.output_path
            })

    try:
        # 1. Scripting Agent
        update_job(status="Scripting narrative", progress=5)
        story_script = run_async(base_strategy_service.generate_screenplay(prompt, style=style))
        scenes = [scene.dict() for scene in story_script.scenes]
        
        # 2. Parallel Synthesis: Voiceover + Visuals
        update_job(status="Synthesizing story components", progress=20)
        
        async def synthesize_full_scenes():
            # Parallel Voiceover
            voice_tasks = []
            for scene in scenes:
                voice_tasks.append(base_voiceover_service.generate_voiceover(scene["narration_text"]))
            
            # Parallel Visuals
            visual_task = generative_service.synthesize_scene_batch(scenes, engine=engine)
            
            voice_results, visual_scenes = await asyncio.gather(
                asyncio.gather(*voice_tasks),
                visual_task
            )
            
            # Merge results
            for i, scene in enumerate(visual_scenes):
                scene["audio_url"] = voice_results[i]
            
            return visual_scenes

        fully_synthesized_scenes = run_async(synthesize_full_scenes())
        
        # 3. Precision Assembly
        update_job(status="Assembling cinematic reel", progress=70)
        processor = VideoProcessor()
        output_name = f"story_{uuid.uuid4()}.mp4"
        
        final_video_path = run_async(processor.assemble_story(fully_synthesized_scenes, output_name))
        
        # 4. Storage & Finalization
        from services.storage.service import base_storage_service
        storage_key = base_storage_service.upload_file(final_video_path)
        public_url = base_storage_service.get_public_url(storage_key)
        
        update_job(status="Completed", progress=100, output_path=public_url)
        
        return {
            "status": "success",
            "title": story_script.title,
            "video_url": public_url,
            "scene_count": len(scenes)
        }
    except Exception as e:
        update_job(status="Failed")
        logging.error(f"[Story Task] Error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

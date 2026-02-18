import logging
import asyncio
from services.discovery.service import base_discovery_service
from services.video_engine.tasks import download_and_process_task
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings, ContentCandidateDB, VideoJobDB

class ViralLoopController:
    def __init__(self):
        self.logger = logging.getLogger("ViralLoop")

    async def execute_autonomous_cycle(self, niche: str, platform: str = "YouTube Shorts"):
        """
        The Master Loop: Finds trends -> Picks Winner -> Dispatches Processing.
        """
        self.logger.info(f"[ViralLoop] Starting autonomous cycle for {niche}...")
        
        db = SessionLocal()
        try:
            # 1. Discovery & Ranking
            candidates = await base_discovery_service.find_trending_content(niche)
            if not candidates:
                self.logger.warning(f"[ViralLoop] No candidates found for {niche}. Aborting cycle.")
                return

            # Top candidate is #1 after AI ranking
            winner = candidates[0]
            self.logger.info(f"[ViralLoop] Winner identified: {winner.title} ({winner.url})")

            # 2. Check if already processed
            existing_job = db.query(VideoJobDB).filter(VideoJobDB.input_url == winner.url).first()
            if existing_job:
                self.logger.info(f"[ViralLoop] Video already in pipeline ({existing_job.status}). Skipping.")
                return

            # 3. Dispatch to Video Engine
            # We trigger the Celery task directly
            task = download_and_process_task.delay(winner.url, niche, platform)
            
            # 4. Record the job entry (linked to System user or Admin)
            # Find an admin user to assign the job to
            from api.utils.user_models import UserDB
            admin = db.query(UserDB).filter(UserDB.role == "admin").first()
            
            new_job = VideoJobDB(
                id=task.id,
                title=f"AUTO: {winner.title[:40]}...",
                status="Queued",
                progress=0,
                input_url=winner.url,
                user_id=admin.id if admin else 1 # Fallback to user 1
            )
            db.add(new_job)
            db.commit()
            
            self.logger.info(f"[ViralLoop] Task {task.id} dispatched successfully for {niche}.")
            
        except Exception as e:
            self.logger.error(f"[ViralLoop] Cycle Failed: {e}")
        finally:
            db.close()

base_viral_loop = ViralLoopController()

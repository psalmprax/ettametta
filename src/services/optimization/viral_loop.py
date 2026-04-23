import logging
import asyncio
from src.services.discovery.service import base_discovery_service
from src.services.video_engine.tasks import download_and_process_task
from src.api.utils.database import async_session_factory
from sqlalchemy import select
from src.shared.enums import SystemJobStatus
from src.api.utils.models import (
    SystemSettings,
    ContentCandidateDB,
    VideoJobDB,
)


class ViralLoopController:
    def __init__(self):
        self.logger = logging.getLogger("ViralLoop")

    async def execute_autonomous_cycle(
        self, niche: str, platform: str = "YouTube Shorts"
    ):
        """
        The Master Loop: Finds trends -> Picks Winner -> Dispatches Processing.
        """
        self.logger.info(f"[ViralLoop] Starting autonomous cycle for {niche}...")

        async with async_session_factory() as db:
            try:
                # 1. Discovery & Ranking
                candidates = await base_discovery_service.find_trending_content(niche)
                if not candidates:
                    self.logger.warning(
                        f"[ViralLoop] No candidates found for {niche}. Aborting cycle."
                    )
                    return

                # Top candidate is #1 after AI ranking
                winner = candidates[0]
                self.logger.info(
                    f"[ViralLoop] Winner identified: {winner.title} ({winner.source_url})"
                )

                # 2. Check if already processed
                stmt = select(VideoJobDB).where(VideoJobDB.source_url == winner.source_url)
                result = await db.execute(stmt)
                existing_job = result.scalar_one_or_none()

                if existing_job:
                    self.logger.info(
                        f"[ViralLoop] Video already in pipeline ({existing_job.status}). Skipping."
                    )
                    return

                # 3. Dispatch to Video Engine
                task = download_and_process_task.delay(winner.source_url, niche, platform)

                # 4. Record the job entry
                from src.api.utils.user_models import UserDB, UserRole
                stmt_admin = select(UserDB).where(UserDB.role == UserRole.ADMIN)
                result_admin = await db.execute(stmt_admin)
                admin = result_admin.scalar_one_or_none()

                new_job = VideoJobDB(
                    id=task.id,
                    title=f"AUTO: {winner.title[:40]}...",
                    status=SystemJobStatus.QUEUED,
                    progress=0,
                    source_url=winner.source_url,
                    user_id=admin.id if admin else 1,  # Fallback to user 1
                )
                db.add(new_job)
                await db.commit()

                self.logger.info(
                    f"[ViralLoop] Task {task.id} dispatched successfully for {niche}."
                )

            except Exception as e:
                self.logger.error(f"[ViralLoop] Cycle Failed: {e}")
                await db.rollback()


base_viral_loop = ViralLoopController()

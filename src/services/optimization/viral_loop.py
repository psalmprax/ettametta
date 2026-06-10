import logging
from src.services.discovery.service import base_discovery_service
from src.services.video_engine.tasks import download_and_process_task
from src.services.video_engine.job_service import VideoJobService
from src.api.utils.database import async_session_factory
from sqlalchemy import select
from src.shared.enums import SystemJobStatus
from src.api.utils.models import (
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
                    f"[ViralLoop] Winner identified: {winner.title} ({winner.source_uri})"
                )

                # 2. Check if already processed
                stmt = select(VideoJobDB).where(VideoJobDB.source_uri == winner.source_uri)
                result = await db.execute(stmt)
                existing_job = result.scalar_one_or_none()

                if existing_job:
                    self.logger.info(
                        f"[ViralLoop] Video already in pipeline ({existing_job.status}). Skipping."
                    )
                    return

                # 3. Dispatch to Video Engine
                task = download_and_process_task.delay(winner.source_uri, niche, platform)

                # 4. Record the job entry via service layer
                from src.api.utils.user_models import UserDB, UserRole
                stmt_admin = select(UserDB).where(UserDB.role == UserRole.ADMIN)
                result_admin = await db.execute(stmt_admin)
                admin = result_admin.scalar_one_or_none()

                await VideoJobService(db).create_job(
                    user_id=admin.id if admin else 1,  # Fallback to user 1
                    title=f"AUTO: {winner.title[:40]}...",
                    engine="viral_loop",
                    status=SystemJobStatus.QUEUED,
                    job_id=task.id,
                    progress=0,
                    source_uri=winner.source_uri,
                )

                self.logger.info(
                    f"[ViralLoop] Task {task.id} dispatched successfully for {niche}."
                )

            except Exception as e:
                self.logger.error(f"[ViralLoop] Cycle Failed: {e}")
                await db.rollback()


    async def execute_compilation_cycle(
        self, niche: str, platforms: list = ["youtube"], max_segments: int = 3
    ):
        """
        Multi-Video Pipeline: Finds top leads -> Downloads & Normalizes -> Compiles with Transitions.
        """
        self.logger.info(f"[ViralLoop] Starting compilation cycle for {niche}...")
        
        from src.services.video_engine.processor import VideoProcessor
        from src.services.video_engine.downloader import base_downloader_service
        from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service
        import os
        import uuid

        async with async_session_factory() as db:
            try:
                # 1. Lead Generation
                leads = await base_discovery_service.discover_video_leads(
                    niche=niche,
                    platforms=platforms,
                    min_viral_score=5.0,
                    max_results=max_segments
                )
                
                if not leads or len(leads) < 2:
                    self.logger.warning(f"[ViralLoop] Insufficient leads for compilation ({len(leads) if leads else 0}).")
                    return

                # 2. Process Segments
                processor = VideoProcessor()
                processed_paths = []
                
                for lead in leads:
                    try:
                        raw_path = await base_downloader_service.download_video(lead.url)
                        if not raw_path: continue
                        
                        norm_path = os.path.join(processor.output_dir, f"loop_norm_{uuid.uuid4().hex[:8]}.mp4")
                        success = base_ffmpeg_service.apply_originality(raw_path, norm_path, mirror=True, zoom=1.03)
                        if success:
                            processed_paths.append(norm_path)
                    except Exception as e:
                        self.logger.error(f"[ViralLoop] Segment processing failed: {e}")

                if len(processed_paths) < 2:
                    self.logger.warning("[ViralLoop] Not enough segments processed for compilation.")
                    return

                # 3. Final Compilation
                final_video = os.path.join(processor.output_dir, f"loop_final_{niche.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.mp4")
                success = base_ffmpeg_service.xfade_concatenate(
                    video_paths=processed_paths,
                    output_path=final_video,
                    transition="radial",
                    trans_duration=0.6
                )

                if success:
                    # 4. Record the job via service layer
                    from src.api.utils.user_models import UserDB, UserRole
                    stmt_admin = select(UserDB).where(UserDB.role == UserRole.ADMIN)
                    result_admin = await db.execute(stmt_admin)
                    admin = result_admin.scalar_one_or_none()

                    await VideoJobService(db).create_job(
                        user_id=admin.id if admin else 1,
                        title=f"COMPILATION: {niche}",
                        engine="viral_loop",
                        status=SystemJobStatus.COMPLETED,
                        job_id=f"loop_{uuid.uuid4().hex[:8]}",
                        progress=100,
                        source_uri=final_video,
                    )
                    self.logger.info(f"[ViralLoop] Compilation cycle successful: {final_video}")
                
            except Exception as e:
                self.logger.error(f"[ViralLoop] Compilation Cycle Failed: {e}")
                await db.rollback()


base_viral_loop = ViralLoopController()

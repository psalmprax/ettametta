from src.api.utils.celery import celery_app
from src.api.utils.models import MonitoredNiche
from src.services.discovery.service import base_discovery_service
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="discovery.sentinel_watcher")
def sentinel_trend_watcher():
    """
    Background task that iterates through all active niches and triggers discovery.
    If AUTO_PILOT is enabled, it triggers the Viral Loop for autonomous processing.
    """
    from src.api.utils.models import SystemSettings
    from src.services.optimization.viral_loop import base_viral_loop
    from src.api.utils.database import async_session_factory
    from sqlalchemy import select

    async def run_watcher():
        async with async_session_factory() as db:
            # Check for Auto-Pilot setting
            stmt = select(SystemSettings).where(SystemSettings.key == "auto_pilot")
            result = await db.execute(stmt)
            auto_pilot_setting = result.scalar_one_or_none()
            is_auto_pilot = (
                auto_pilot_setting.value.lower() == "true"
                if auto_pilot_setting
                else False
            )

            stmt = select(MonitoredNiche).where(MonitoredNiche.is_active == True)
            result = await db.execute(stmt)
            niches = result.scalars().all()
            logger.info(
                f"[Sentinel] Monitoring {len(niches)} active niches (Auto-Pilot: {is_auto_pilot})..."
            )

            for n in niches:
                if is_auto_pilot:
                    # Trigger Master Viral Loop (Discovery -> Pick Winner -> Render -> Publish)
                    await base_viral_loop.execute_autonomous_cycle(n.niche)
                else:
                    # Standard Mode: Just scan trends and update DB for UI review
                    scan_trends_task.delay(n.niche)

                # Update last scanned time
                n.last_scanned_at = datetime.now()

            await db.commit()
            return len(niches), is_auto_pilot

    try:
        niche_count, is_auto_pilot = asyncio.run(run_watcher())
        return {
            "status": "dispatched",
            "niche_count": niche_count,
            "auto_pilot": is_auto_pilot,
        }
    except Exception as e:
        logger.error(f"[Sentinel] Watcher failed: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(name="discovery.scan_trends")
def scan_trends_task(niche: str, horizon: str = "30d"):
    """
    Background task for real-time trend scanning using DiscoveryService.
    """
    logger.info(f"[Discovery Task] Automated scan for: {niche} (Horizon: {horizon})")
    # DiscoveryService is async, so we use asyncio.run
    candidates = asyncio.run(
        base_discovery_service.find_trending_content(niche, horizon=horizon)
    )

    return {"status": "success", "niche": niche, "found_count": len(candidates)}


@celery_app.task(name="discovery.analyze_pattern")
def analyze_viral_pattern_task(candidate_data: dict):
    """
    Background task for deep AI deconstruction of a viral candidate.
    """
    from src.services.discovery.models import ContentCandidate

    candidate = ContentCandidate(**candidate_data)

    logger.info(f"[Discovery Task] Async analysis for: {candidate.source_uri}")
    pattern = asyncio.run(base_discovery_service.deep_analyze_viral_patterns(candidate))

    # Use model_dump(mode='json') for safe JSON serialization with datetime handling
    return {
        "status": "success",
        "candidate_id": candidate.id,
        "source_uri": candidate.source_uri,
        "pattern": pattern.model_dump(mode="json")
        if hasattr(pattern, "model_dump")
        else pattern.dict(),
    }


@celery_app.task(name="discovery.deep_scan")
def deep_scan_task(niches: list[str], tier: str = "free"):
    """
    Background task for deep, intelligent discovery scan across multiple niches.
    """
    logger.info(f"[Discovery Task] Deep Scan triggered for: {niches} (Tier: {tier})")

    all_results = []
    for niche in niches:
        try:
            candidates = asyncio.run(
                base_discovery_service.find_trending_content(
                    niche, tier=tier, deep_scan=True
                )
            )
            # Use model_dump for safe JSON serialization
            all_results.extend(
                [
                    c.model_dump(mode="json") if hasattr(c, "model_dump") else c.dict()
                    for c in candidates
                ]
            )
        except Exception as e:
            logger.error(f"[Discovery Task] Deep scan failed for {niche}: {e}")

    return {"status": "success", "niches": niches, "found_count": len(all_results)}
@celery_app.task(name="discovery.process_high_potential")
def process_high_potential_candidates():
    """
    Autonomous task that picks up high-potential content candidates
    and triggers the Nexus video generation pipeline.
    """
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import ContentCandidateDB, NexusJobDB, SystemJobStatus
    from sqlalchemy import select
    import uuid

    async def run_process():
        logger.info("[Autonomous] Checking for high-potential candidates...")
        
        async with async_session_factory() as db:
            # Find candidates that are analyzed, high potential, and not yet processed
            stmt = select(ContentCandidateDB).where(
                ContentCandidateDB.analyzed_at != None,
                ContentCandidateDB.is_processed == False
            )
            result = await db.execute(stmt)
            candidates = result.scalars().all()
            
            high_potential = []
            for c in candidates:
                results = c.analysis_results or {}
                if results.get("viral_potential") == "high":
                    high_potential.append(c)
            
            if not high_potential:
                logger.info("[Autonomous] No new high-potential candidates found.")
                return 0
                
            logger.info(f"[Autonomous] Found {len(high_potential)} high-potential candidates.")
            
            triggered_count = 0
            for candidate in high_potential:
                try:
                    # 1. Get an admin user for the job
                    from src.api.utils.user_models import UserDB, UserRole
                    stmt_admin = select(UserDB).where(UserDB.role == UserRole.ADMIN)
                    result_admin = await db.execute(stmt_admin)
                    admin = result_admin.scalar_one_or_none()
                    
                    job_id = str(uuid.uuid4())
                    
                    # 2. Create a Nexus Job entry
                    new_job = NexusJobDB(
                        id=job_id,
                        user_id=admin.id if admin else None, 
                        niche=candidate.niche or "general",
                        status=SystemJobStatus.QUEUED,
                        job_metadata={
                            "topic": candidate.title,
                            "source_content_id": candidate.id,
                            "style": "CINEMATIC_DOC",
                            "auto_triggered": True
                        }
                    )
                    db.add(new_job)
                    await db.flush() # Ensure job is in DB for foreign key
                    
                    # 3. Link candidate to job
                    candidate.nexus_job_id = job_id
                    candidate.is_processed = True
                    
                    await db.commit()
                    
                    # 3. Dispatch the Nexus task
                    from src.services.nexus_engine.tasks import create_cinema_video_task
                    create_cinema_video_task.delay(
                        job_id=job_id,
                        topic=candidate.title,
                        niche=candidate.niche or "general",
                        style="CINEMATIC_DOC"
                    )
                    
                    triggered_count += 1
                    logger.info(f"[Autonomous] Triggered Nexus job {job_id} for candidate {candidate.id}")
                    
                except Exception as e:
                    logger.error(f"[Autonomous] Failed to trigger job for {candidate.id}: {e}")
                    await db.rollback()
                    
            return triggered_count

    try:
        return asyncio.run(run_process())
    except Exception as e:
        logger.error(f"[Autonomous] Task failed: {e}")
        return 0

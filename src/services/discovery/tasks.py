from api.utils.celery import celery_app
from api.utils.models import MonitoredNiche
from services.discovery.service import base_discovery_service
from datetime import datetime
import asyncio

@celery_app.task(name="discovery.sentinel_watcher")
def sentinel_trend_watcher():
    """
    Background task that iterates through all active niches and triggers discovery.
    If AUTO_PILOT is enabled, it triggers the Viral Loop for autonomous processing.
    """
    from api.utils.models import SystemSettings
    from services.optimization.viral_loop import base_viral_loop
    from api.utils.database import async_session_factory
    from sqlalchemy import select
    
    async def run_watcher():
        async with async_session_factory() as db:
            # Check for Auto-Pilot setting
            stmt = select(SystemSettings).where(SystemSettings.key == "auto_pilot")
            result = await db.execute(stmt)
            auto_pilot_setting = result.scalar_one_or_none()
            is_auto_pilot = auto_pilot_setting.value.lower() == "true" if auto_pilot_setting else False
            
            stmt = select(MonitoredNiche).where(MonitoredNiche.is_active == True)
            result = await db.execute(stmt)
            niches = result.scalars().all()
            print(f"[Sentinel] Monitoring {len(niches)} active niches (Auto-Pilot: {is_auto_pilot})...")
            
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
        return {"status": "dispatched", "niche_count": niche_count, "auto_pilot": is_auto_pilot}
    except Exception as e:
        print(f"[Sentinel] Watcher failed: {e}")
        return {"status": "error", "error": str(e)}

@celery_app.task(name="discovery.scan_trends")
def scan_trends_task(niche: str):
    """
    Background task for real-time trend scanning using DiscoveryService.
    """
    print(f"[Discovery Task] Automated scan for: {niche}")
    # DiscoveryService is async, so we use asyncio.run
    candidates = asyncio.run(base_discovery_service.find_trending_content(niche))
    
    return {
        "status": "success", 
        "niche": niche, 
        "found_count": len(candidates)
    }

@celery_app.task(name="discovery.analyze_pattern")
def analyze_viral_pattern_task(candidate_data: dict):
    """
    Background task for deep AI deconstruction of a viral candidate.
    """
    from services.discovery.models import ContentCandidate
    candidate = ContentCandidate(**candidate_data)
    
    print(f"[Discovery Task] Async analysis for: {candidate.url}")
    pattern = asyncio.run(base_discovery_service.analyze_viral_pattern(candidate))
    
    return {
        "status": "success",
        "candidate_id": candidate.id,
        "pattern": pattern.dict()
    }

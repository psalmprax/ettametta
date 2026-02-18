from api.utils.celery import celery_app
from api.utils.database import SessionLocal
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
    
    db = SessionLocal()
    try:
        # Check for Auto-Pilot setting
        auto_pilot_setting = db.query(SystemSettings).filter(SystemSettings.key == "auto_pilot").first()
        is_auto_pilot = auto_pilot_setting.value.lower() == "true" if auto_pilot_setting else False
        
        niches = db.query(MonitoredNiche).filter(MonitoredNiche.is_active == True).all()
        print(f"[Sentinel] Monitoring {len(niches)} active niches (Auto-Pilot: {is_auto_pilot})...")
        
        for n in niches:
            if is_auto_pilot:
                # Trigger Master Viral Loop (Discovery -> Pick Winner -> Render -> Publish)
                loop = asyncio.get_event_loop()
                loop.run_until_complete(base_viral_loop.execute_autonomous_cycle(n.niche))
            else:
                # Standard Mode: Just scan trends and update DB for UI review
                scan_trends_task.delay(n.niche)
            
            # Update last scanned time
            n.last_scanned_at = datetime.utcnow()
        
        db.commit()
    finally:
        db.close()
    return {"status": "dispatched", "niche_count": len(niches), "auto_pilot": is_auto_pilot}

@celery_app.task(name="discovery.scan_trends")
def scan_trends_task(niche: str):
    """
    Background task for real-time trend scanning using DiscoveryService.
    """
    print(f"[Discovery Task] Automated scan for: {niche}")
    # DiscoveryService is async, so we run it in a loop
    loop = asyncio.get_event_loop()
    candidates = loop.run_until_complete(base_discovery_service.find_trending_content(niche))
    
    return {
        "status": "success", 
        "niche": niche, 
        "found_count": len(candidates)
    }

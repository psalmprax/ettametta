from api.utils.celery import celery_app
from services.security.service import base_security_sentinel
import asyncio

@celery_app.task(name="security.system_audit")
def system_audit_task():
    """
    Periodic background task to audit system integrity and security posture.
    """
    print("[Sentinel Task] Running scheduled logic audit...")
    report = base_security_sentinel.audit_system_integrity()
    
    # Log audit event
    base_security_sentinel.log_event(
        "SCHEDULED_AUDIT", 
        "info", 
        {"score": report["score"], "findings_count": len(report["findings"])}
    )
    
    return {
        "status": "success",
        "score": report["score"],
        "findings": report["findings"]
    }

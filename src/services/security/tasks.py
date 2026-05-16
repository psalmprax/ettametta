from src.api.utils.celery import celery_app
from src.services.security.service import base_security_service
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="security.system_audit")
def system_audit_task():
    """
    Periodic background task to audit system integrity and security posture.
    """
    logger.info("[Sentinel Task] Running scheduled logic audit...")
    report = base_security_service.audit_system_integrity()
    
    # Log audit event
    base_security_service.log_event(
        "SCHEDULED_AUDIT", 
        "info", 
        {"score": report["score"], "findings_count": len(report["findings"])}
    )
    
    return {
        "status": "success",
        "score": report["score"],
        "findings": report["findings"]
    }

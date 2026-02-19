from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from services.security.service import base_security_sentinel

router = APIRouter(prefix="/security", tags=["Security"])

@router.get("/status")
async def get_security_status():
    """
    Returns the current security health score and recent threat events.
    """
    try:
        return base_security_sentinel.get_security_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel Error: {str(e)}")

@router.post("/scan")
async def trigger_security_audit():
    """
    Manually triggers a full system integrity audit.
    """
    try:
        report = base_security_sentinel.audit_system_integrity()
        return {
            "status": "Audit Complete",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit Failure: {str(e)}")

@router.get("/events")
async def get_security_events():
    """
    Returns the raw list of security events from the sentinel.
    """
    status = base_security_sentinel.get_security_status()
    return status.get("recent_events", [])

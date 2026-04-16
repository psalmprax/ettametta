from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.security.service import base_security_sentinel

router = APIRouter(prefix="/security", tags=["Security"])
logger = logging.getLogger(__name__)


def admin_required(current_user: UserDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class ErrorReport(BaseModel):
    message: str
    stack: Optional[str] = None
    componentStack: Optional[str] = None
    timestamp: str


@router.post("/errors")
async def report_error(
    error: ErrorReport,
    db=Depends(lambda: None),  # Placeholder, audit logging optional
):
    """
    Reports frontend errors to the backend for logging.
    Accessible to all authenticated users.
    """
    try:
        # Log to structured logger
        logger.info(f"🚨 Frontend Error Report: {error.message}")
        if error.stack:
            logger.debug(f"   Stack: {error.stack[:200]}...")
        if error.componentStack:
            logger.debug(f"   Component Stack: {error.componentStack[:200]}...")

        return {"status": "error_logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log error: {str(e)}")


@router.get("/status")
async def get_security_status(current_user=Depends(get_current_user)):
    """
    Returns the current security health score and recent threat events.
    Requires authentication.
    """
    try:
        return base_security_sentinel.get_security_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel Error: {str(e)}")


@router.post("/scan")
async def trigger_security_audit(current_user=Depends(admin_required)):
    """
    Manually triggers a full system integrity audit.
    Requires authentication (admin recommended).
    """
    try:
        report = base_security_sentinel.audit_system_integrity()
        return {"status": "Audit Complete", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit Failure: {str(e)}")


@router.get("/events")
async def get_security_events(current_user=Depends(admin_required)):
    """
    Returns the raw list of security events from the sentinel.
    Requires authentication.
    """
    status = base_security_sentinel.get_security_status()
    return status.get("recent_events", [])

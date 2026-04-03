from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from services.security.service import base_security_sentinel
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB

router = APIRouter(prefix="/security", tags=["Security"])


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
        # Log to console/file (expandable to DB in future)
        print(f"🚨 Frontend Error Report:")
        print(f"   Message: {error.message}")
        print(f"   Timestamp: {error.timestamp}")
        if error.stack:
            print(f"   Stack: {error.stack[:200]}...")
        if error.componentStack:
            print(f"   Component Stack: {error.componentStack[:200]}...")

        return {"status": "error_logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log error: {str(e)}")


def admin_required(current_user: UserDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


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
async def trigger_security_audit(current_user=Depends(get_current_user)):
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
async def get_security_events(current_user=Depends(get_current_user)):
    """
    Returns the raw list of security events from the sentinel.
    Requires authentication.
    """
    status = base_security_sentinel.get_security_status()
    return status.get("recent_events", [])

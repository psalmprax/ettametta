from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.discovery.service import base_discovery_service
from services.discovery.models import ContentCandidate, ViralPattern
from typing import List

router = APIRouter(prefix="/discovery", tags=["Discovery"])

import httpx
import os

DISCOVERY_GO_URL = os.getenv("DISCOVERY_GO_URL", "http://discovery-go:8080")

from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from fastapi import APIRouter, HTTPException, Depends

@router.get("/trends", response_model=List[ContentCandidate])
async def get_trends(niche: str = "Motivation", horizon: str = "30d", user: UserDB = Depends(get_current_user)):
    try:
        trends = await base_discovery_service.find_trending_content(niche, horizon=horizon)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[ContentCandidate])
async def search_discovery(q: str, user: UserDB = Depends(get_current_user)):
    try:
        results = await base_discovery_service.search_content(q)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ScanRequest(BaseModel):
    niches: List[str] = ["AI"]

@router.post("/scan")
async def trigger_scan(request: ScanRequest):
    """
    Proxies scan requests to the high-concurrency Go engine.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{DISCOVERY_GO_URL}/scan", json={"niches": request.niches})
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Go Bridge Error: {str(e)}")

@router.post("/analyze")
async def analyze_candidate(candidate: ContentCandidate):
    """
    Asynchronous deconstruction: Dispatches deep AI analysis to Celery 
    and returns a task ID for UI polling.
    """
    from services.discovery.tasks import analyze_viral_pattern_task
    task = analyze_viral_pattern_task.delay(candidate.dict())
    return {
        "status": "Task Dispatched",
        "task_id": task.id,
        "candidate_id": candidate.id,
        "message": "AI Deconstruction in progress..."
    }

@router.get("/niche-trends/{niche}")
async def get_niche_trends(niche: str):
    try:
        trend = await base_discovery_service.aggregate_niche_trends(niche)
        if not trend:
             # If no data yet, try to scan first
             await base_discovery_service.find_trending_content(niche)
             trend = await base_discovery_service.aggregate_niche_trends(niche)
             if not trend:
                 return {"niche": niche, "top_keywords": [], "avg_engagement": 0.0}
        return trend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/niches", response_model=List[str])
async def list_monitored_niches(user: UserDB = Depends(get_current_user)):
    from api.utils.database import SessionLocal
    from api.utils.models import MonitoredNiche
    db = SessionLocal()
    try:
        niches = db.query(MonitoredNiche.niche).filter(MonitoredNiche.is_active == True).distinct().all()
        return [n[0] for n in niches]
    finally:
        db.close()

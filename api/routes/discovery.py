from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import httpx
import os
import logging
import datetime
import json

from services.discovery.service import base_discovery_service
from services.discovery.models import ContentCandidate, ViralPattern
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/discovery", tags=["Discovery"])

DISCOVERY_GO_URL = os.getenv("DISCOVERY_GO_URL", "http://discovery-go:8080")

from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from api.utils.subscription import credits_required
from services.payment.credit_service import credit_service
from api.config import settings
from api.utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@router.get("/trends", response_model=List[ContentCandidate])
@cache(expire=60)
async def get_trends(
    niche: str = "Motivation",
    horizon: str = "30d",
    page: int = 1,
    size: int = 20,
    min_viral_score: int = 0,
    exclude_shorts: bool = False,
    user: UserDB = Depends(get_current_user),
):
    try:
        trends = await base_discovery_service.find_trending_content(
            niche,
            horizon=horizon,
            tier=user.subscription.value
            if hasattr(user.subscription, "value")
            else "free",
            min_viral_score=min_viral_score,
            exclude_shorts=exclude_shorts,
        )
        # Apply pagination
        start = (page - 1) * size
        end = start + size
        return trends[start:end]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[ContentCandidate])
async def search_discovery(
    q: str = "",
    page: int = 1,
    size: int = 20,
    min_viral_score: int = 0,
    exclude_shorts: bool = False,
    user: UserDB = Depends(get_current_user),
):
    try:
        if not q.strip():
            return []
        # We pass a slightly larger limit to service and then slice for pagination
        results = await base_discovery_service.search_content(
            q, limit=100, min_viral_score=min_viral_score, exclude_shorts=exclude_shorts
        )
        start = (page - 1) * size
        end = start + size
        return results[start:end]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ScanRequest(BaseModel):
    niches: List[str] = ["AI"]
    deep: bool = False


@router.post("/scan")
async def trigger_scan(request: ScanRequest, user: UserDB = Depends(get_current_user)):
    """
    Triggers a discovery scan. If 'deep' is true, performs an exhaustive AI-powered scan.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        if request.deep:
            # Run deep scan as background task to avoid blocking
            from services.discovery.tasks import deep_scan_task

            task = deep_scan_task.delay(
                niches=request.niches,
                tier=user.subscription.value
                if hasattr(user.subscription, "value")
                else "free",
            )

            return {
                "status": "Deep Scan Queued",
                "task_id": task.id,
                "niches": request.niches,
                "message": "Deep scan started in background. Poll /analyze/{task_id} for results.",
            }
        else:
            # Proxies regular scan requests to the high-concurrency Go engine
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{DISCOVERY_GO_URL}/scan",
                        json={"niches": request.niches},
                        timeout=300.0,
                    )
                    resp.raise_for_status()
                    return resp.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning(
                    f"[Discovery] Go engine unavailable: {e}, falling back to Python service"
                )
                # Fallback to Python service if Go engine unavailable
                all_results = []
                for niche in request.niches:
                    try:
                        results = await base_discovery_service.find_trending_content(
                            niche,
                            horizon="30d",
                            tier=user.subscription.value
                            if hasattr(user.subscription, "value")
                            else "free",
                        )
                        all_results.extend(results)
                    except Exception as inner_e:
                        logger.error(
                            f"[Discovery] Fallback scan failed for {niche}: {inner_e}"
                        )

                return {
                    "status": "scan_completed",
                    "niches": request.niches,
                    "candidates": all_results[:50],
                    "count": len(all_results),
                    "source": "fallback_python",
                }
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Discovery Error: {str(e)}")


@router.post("/analyze")
async def analyze_candidate(
    candidate: ContentCandidate,
    user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("viral_analysis")),
    db: AsyncSession = Depends(get_db),
):
    """
    Asynchronous deconstruction: Dispatches deep AI analysis to Celery
    and returns a task ID for UI polling.
    """
    from services.discovery.tasks import analyze_viral_pattern_task

    # Consume credits
    await credit_service.consume_credits(
        user_id=user.id,
        amount=credits_cost,
        action="viral_analysis",
        db=db,
        reference_id=candidate.id, # Using candidate ID as reference
    )

    task = analyze_viral_pattern_task.delay(candidate.dict())
    return {
        "status": "Task Dispatched",
        "task_id": task.id,
        "candidate_id": candidate.id,
        "message": "AI Deconstruction in progress...",
    }


@router.get("/niche-trends/{niche}")
@cache(expire=300)
async def get_niche_trends(niche: str, user: UserDB = Depends(get_current_user)):
    try:
        trend = await base_discovery_service.aggregate_niche_trends(niche)
        if not trend:
            # If no data yet, try to scan first
            tier_value = (
                user.subscription.value
                if hasattr(user.subscription, "value")
                else "free"
            )
            await base_discovery_service.find_trending_content(niche, tier=tier_value)
            trend = await base_discovery_service.aggregate_niche_trends(niche)
            if not trend:
                return {"niche": niche, "top_keywords": [], "avg_engagement": 0.0}
        return trend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/niches", response_model=List[str])
async def list_monitored_niches(
    user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    from api.utils.models import MonitoredNiche

    try:
        stmt = (
            select(MonitoredNiche.niche)
            .filter(MonitoredNiche.is_active == True)
            .distinct()
        )
        result = await db.execute(stmt)
        niches = result.all()
        return [n[0] for n in niches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{task_id}")
async def get_analysis_status(task_id: str, user: UserDB = Depends(get_current_user)):
    """
    Get the status of an analysis task and return results when complete.
    """
    from api.utils.celery import celery_app
    from services.discovery.tasks import analyze_viral_pattern_task

    try:
        # Get task result
        result = celery_app.AsyncResult(task_id)

        if result.ready():
            if result.successful():
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "result": result.result,
                }
            else:
                return {
                    "status": "failed",
                    "task_id": task_id,
                    "error": str(result.info),
                }
        else:
            return {
                "status": "pending",
                "task_id": task_id,
                "message": "Analysis in progress...",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateVideoFromAnalysisRequest(BaseModel):
    task_id: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: Optional[str] = "Default"
    quality_tier: Optional[str] = "standard"


@router.post("/analyze/{task_id}/create-video")
async def create_video_from_analysis(
    task_id: str,
    request: CreateVideoFromAnalysisRequest,
    user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("video_transformation")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a video transformation from completed analysis.
    """
    from api.utils.celery import celery_app
    from services.video_engine.tasks import download_and_process_task
    from api.utils.models import VideoJobDB

    try:
        # Check if task is complete
        result = celery_app.AsyncResult(task_id)

        if not result.ready():
            raise HTTPException(status_code=400, detail="Analysis not yet complete")

        if not result.successful():
            raise HTTPException(
                status_code=400, detail=f"Analysis failed: {result.info}"
            )

        # Get analysis result
        analysis = result.result
        candidate_url = analysis.get("candidate_id", "")

        # If we have the URL from pattern, use it
        if "pattern" in analysis:
            pattern = analysis.get("pattern", {})
            candidate_url = pattern.get("source_url", "")

        if not candidate_url:
            raise HTTPException(
                status_code=400, detail="No source URL found in analysis"
            )

        # Dispatch Task
        try:
            task = download_and_process_task.delay(
                source_url=candidate_url,
                niche=request.niche,
                platform=request.platform,
                style=request.style,
                quality_tier=request.quality_tier,
            )
        except Exception as task_err:
            logger.error(f"Task dispatch failure: {task_err}")
            raise HTTPException(status_code=503, detail="Task queue unavailable")

        # Consume credits
        success, msg = await credit_service.consume_credits(
            user_id=user.id,
            amount=credits_cost,
            action="video_transformation",
            db=db,
            reference_id=task.id,
        )
        
        if not success:
            from api.utils.celery import celery_app
            celery_app.control.revoke(task.id, terminate=True)
            raise HTTPException(status_code=402, detail=f"Credit failure: {msg}")

        # Create job record
        new_job = VideoJobDB(
            id=task.id,
            title=f"From Analysis - {request.niche}",
            status="Queued",
            progress=0,
            input_url=candidate_url,
            user_id=user.id,
        )
        db.add(new_job)
        await db.commit()

        return {
            "status": "video_creation_started",
            "task_id": task.id,
            "analysis_task_id": task_id,
            "message": "Video transformation started from analysis",
        }

        return {
            "status": "video_creation_started",
            "task_id": task.id,
            "analysis_task_id": task_id,
            "message": "Video transformation started from analysis",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InsightResponse(BaseModel):
    niche: str
    recommendation: str
    confidence: float
    filters_suggested: List[str]
    target_regions: List[str]
    alpha_status: bool = True


@router.get("/insights/{niche}", response_model=InsightResponse)
@cache(expire=3600)
async def get_niche_insights(niche: str, user: UserDB = Depends(get_current_user)):
    """
    Get AI-driven insights and recommendations for a specific niche.
    Uses Groq Llama-3 to generate high-fidelity, real-time advice based on the niche.
    """
    from groq import Groq
    from api.config import settings
    import json

    # Default fallback data
    recommendation = "Use high-contrast visuals and rapid-fire segments. Maintain a high information density to maximize retention in the first 5 seconds."
    filters = ["Glitch Alpha", "Cinematic Pulse"]
    confidence = 0.85

    if settings.GROQ_API_KEY:
        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            prompt = f"""
            You are a viral growth expert for the {niche} niche on YouTube Shorts/TikTok.
            Provide a viral optimization strategy for this niche.
            
            Return ONLY a JSON object with this structure:
            {{
                "recommendation": "string (single actionable sentence, max 30 words)",
                "filters_suggested": ["string", "string"],
                "confidence": float (0.0 to 1.0)
            }}
            """

            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )

            ai_data = json.loads(chat_completion.choices[0].message.content)
            recommendation = ai_data.get("recommendation", recommendation)
            filters = ai_data.get("filters_suggested", filters)
            confidence = ai_data.get("confidence", confidence)
        except Exception as e:
            import logging

            logging.error(f"[Discovery] Groq Insight Failure: {e}")

    return InsightResponse(
        niche=niche,
        recommendation=recommendation,
        confidence=confidence,
        filters_suggested=filters,
        target_regions=["US", "GB", "DE"],
        alpha_status=False,  # No longer alpha, it's real
    )


# ─── opencli-rs Enhanced Discovery ─────────────────────────────────────
# These endpoints use the user's own Chrome sessions (via opencli-rs)
# as an alternative to global API-based discovery.


@router.get("/opencli/search")
async def opencli_search(
    platform: str,
    query: str,
    limit: int = 20,
    user: UserDB = Depends(get_current_user),
):
    """Search a platform using the user's own Chrome session (via opencli-rs).

    This is an alternative to the global API-based search. Each user
    can connect their own platform sessions via the /opencli/sessions
    endpoints, then use this to search with their authenticated session.
    """
    from api.config import settings
    from services.opencli.scanner import OpenCLIScanner

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(user.id)
    candidates = await scanner.scan_trends(query, platforms=[platform.lower()])

    # Limit results
    return candidates[:limit]


@router.get("/opencli/feed/{platform}")
async def opencli_feed(
    platform: str,
    feed_type: str = "trending",
    limit: int = 20,
    user: UserDB = Depends(get_current_user),
):
    """Get feed/trending content from a platform using the user's Chrome session.

    feed_type options: feed, trending, hot, top, explore
    """
    from api.config import settings
    from services.opencli.scanner import OpenCLIScanner

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(user.id)
    candidates = await scanner.get_platform_feed(platform.lower(), feed_type, limit)

    return candidates


@router.post("/opencli/scan")
async def opencli_scan(
    niche: str = "general",
    platforms: Optional[List[str]] = None,
    user: UserDB = Depends(get_current_user),
):
    """Deep scan all connected platforms using the user's Chrome sessions.

    This merges opencli-rs results with the standard discovery pipeline,
    giving the user content discovered through their own authenticated sessions.
    """
    from api.config import settings
    from services.opencli.scanner import OpenCLIScanner

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(user.id)
    p = [p.lower() for p in platforms] if platforms else None
    candidates = await scanner.scan_trends(niche, platforms=p)

    return {
        "candidates": candidates,
        "count": len(candidates),
        "source": "opencli-rs",
        "platforms_scanned": p or "all_connected",
    }


class InteractionRequest(BaseModel):
    candidate_id: str
    niche: str
    action: str = "handshake"


@router.post("/interact")
async def record_interaction(
    request: InteractionRequest, 
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Records a UI interaction with a discovery candidate.
    """
    from api.utils.models import DiscoveryInteractionDB
    import datetime

    try:
        new_interaction = DiscoveryInteractionDB(
            candidate_id=request.candidate_id,
            user_id=user.id,
            action=request.action,
            status=1,  # Established
            details={
                "niche": request.niche,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            },
        )
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)

        return {
            "status": "Handshake Established",
            "candidate_id": request.candidate_id,
            "interaction_id": new_interaction.id,
            "timestamp": new_interaction.created_at.isoformat(),
            "message": "Protocol established with target node.",
        }
    except Exception as e:
        logger.error(f"Interaction record failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to record interaction")

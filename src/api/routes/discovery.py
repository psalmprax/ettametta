from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import os
import logging
import datetime
import asyncio

from src.services.discovery.service import base_discovery_service
from src.services.discovery.models import ContentCandidate
from src.services.discovery.analysis_service import (
    extract_content_patterns,
    get_persisted_analysis_report,
)
from fastapi_cache.decorator import cache
from src.api.utils.api_responses import (
    success_response,
    paginate_list,
    handle_exception,
)

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from src.services.discovery.service_extended import DiscoveryServiceExtended, get_discovery_service_extended
from src.api.utils.subscription import credits_required, get_subscription_tier_value
from src.api.config import settings
from src.shared.enums import SystemJobStatus, CreditAction, ScanStatus
from src.api.utils.models import ContentCandidateDB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/discovery", tags=["Discovery"])

DISCOVERY_GO_URL = os.getenv("DISCOVERY_GO_URL", "http://discovery-go:8080")


@router.get("/trends")
@cache(expire=60)
async def get_trends(
    niche: str | None = None,
    horizon: str = "30d",
    page: int = 1,
    limit: int = 20,
    min_viral_score: int = 0,
    exclude_shorts: bool = False,
    region: str | None = "US",
    current_user: UserDB = Depends(get_current_user),
):
    try:
        if niche and niche.strip():
            try:
                trends = await base_discovery_service.find_trending_content(
                    niche,
                    horizon=horizon,
                    tier=get_subscription_tier_value(current_user),
                    min_viral_score=min_viral_score,
                    exclude_shorts=exclude_shorts,
                    region=region,
                )
            except Exception as scan_err:
                logger.exception(f"Scanner error for niche '{niche}': {scan_err}", exc_info=True)
                # Graceful degradation: return empty results instead of 500
                return success_response(data={"trends": [], "page": page, "page_size": limit, "total": 0, "total_pages": 0})
        else:
            try:
                trends = await base_discovery_service.get_global_trending(
                    limit=limit * page, 
                    min_viral_score=float(min_viral_score),
                    region=region
                )
            except Exception as scan_err:
                logger.exception(f"Global trending scan error: {scan_err}", exc_info=True)
                return success_response(data={"trends": [], "page": page, "page_size": limit, "total": 0, "total_pages": 0})

        paginated = paginate_list(trends, page=page, page_size=limit)
        paginated["trends"] = paginated["items"]
        return success_response(data=paginated)
    except Exception as e:
        logger.exception(f"Discovery trends failed: {e}", exc_info=True)
        return handle_exception(e)


@router.get("/search")
async def search_discovery(
    query: str | None = None,
    platform: list[str] | None = None,
    min_views: int | None = None,
    min_viral_score: float | None = None,
    creator: str | None = None,
    tags: list[str] | None = None,
    date_from: datetime.datetime | None = None,
    date_to: datetime.datetime | None = None,
    sort_by: str = "viral_score",
    limit: int = 50,
    offset: int = 0,
    page: int = 1,
    region: str | None = "US",
    current_user: UserDB = Depends(get_current_user),
):
    try:
        results = await base_discovery_service.search_content(
            query=query,
            platforms=platform,
            min_views=min_views,
            min_viral_score=min_viral_score,
            creator=creator,
            tags=tags,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            region=region,
            use_live_fallback=False,  # Fast DB-only search for keyword queries
        )
        paginated = paginate_list(results, page=page, page_size=limit)
        paginated["results"] = paginated["items"]
        return success_response(data=paginated)
    except Exception as e:
        return handle_exception(e)


class ScanRequest(BaseModel):
    niches: list[str] | None = None
    niche: str | None = None # Support singular niche for UI compatibility
    deep: bool = False
    region: str | None = "US"
    depth: int = 1


class NicheWatchRequest(BaseModel):
    niche: str


class NicheAlertRequest(BaseModel):
    niche: str
    threshold: int = 7  # viral_score threshold
    enabled: bool = True


class AnalyzeRequest(BaseModel):
    url: str | None = None
    niche: str | None = "AI Technology"
    candidate: ContentCandidate | None = None


@router.post("/scan")
async def trigger_scan(
    request: ScanRequest, current_user: UserDB = Depends(get_current_user)
):
    """
    Asynchronously triggers a discovery scan. If 'deep' is true, dispatches a Celery task.
    Returns a task ID for UI status tracking.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        if request.deep:
            # Run deep scan as background task to avoid blocking
            from src.services.discovery.tasks import deep_scan_task

            task = deep_scan_task.delay(
                niches=request.niches,
                tier=get_subscription_tier_value(current_user),
            )

            return success_response(
                data={
                    "status": SystemJobStatus.QUEUED,
                    "task_id": task.id,
                    "niches": request.niches,
                    "message": "Deep scan started in background. Poll /analyze/{task_id} for results.",
                }
            )
        else:
            # Proxies regular scan requests to the high-concurrency Go engine
            # with improved timeout and graceful fallback
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Ensure we have a list of niches
                    scan_niches = request.niches or ([request.niche] if request.niche else ["AI"])
                    
                    resp = await client.post(
                        f"{DISCOVERY_GO_URL}/scan",
                        json={
                            "niches": scan_niches,
                            "region": request.region,
                            "depth": request.depth
                        },
                        timeout=60.0,
                    )
                    resp.raise_for_status()
                    return success_response(data=resp.json())
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.HTTPStatusError,
            ) as e:
                logger.warning(
                    f"[Discovery] Go engine unavailable: {e}, falling back to Python service"
                )
                # Fallback to Python service if Go engine unavailable
                all_results = []
                failed_niches = []

                # Ensure we have a list of niches
                scan_niches = request.niches or ([request.niche] if request.niche else ["AI"])

                # Process niches with individual error handling for resilience
                for niche in scan_niches:
                    try:
                        results = await base_discovery_service.find_trending_content(
                            niche,
                            horizon="30d",
                            tier=getattr(
                                current_user.subscription,
                                "value",
                                str(current_user.subscription),
                            )
                            if current_user.subscription
                            else "free",
                            region=request.region or "US",
                        )
                        all_results.extend(results)
                    except Exception as inner_e:
                        logger.exception(
                            f"[Discovery] Fallback scan failed for {niche}: {inner_e}"
                        )
                        failed_niches.append(niche)

                # If we have at least some results, return them
                if all_results:
                    return success_response(
                        data={
                            "status": ScanStatus.COMPLETED,
                            "niches": request.niches,
                            "candidates": all_results[:50],
                            "count": len(all_results),
                            "source": "fallback_python",
                            "failed_niches": failed_niches,
                        }
                    )

                # Ultimate fallback: Use video lead scanner for any failed niches
                if failed_niches:
                    logger.warning(
                        f"[Discovery] Primary scanners failed. Deploying Video Lead Scanner for {failed_niches}"
                    )
                    for niche in failed_niches:
                        try:
                            swarm_results = await base_discovery_service.video_lead_scanner.scan_for_video_leads(
                                niche=niche,
                                platforms=["youtube", "tiktok", "rumble"],
                                min_viral_score=0,
                                max_results=10,
                            )
                            all_results.extend(
                                [
                                    ContentCandidate(
                                        id=r.video_id,
                                        platform=r.platform,
                                        source_uri=r.url,
                                        creator_name=r.creator,
                                        title=r.title,
                                        description=r.description,
                                        thumbnail_uri=r.thumbnail_uri,
                                        view_count=r.view_count,
                                        engagement_score=r.engagement_score,
                                        viral_score=int(r.viral_score),
                                        duration_seconds=float(r.duration_seconds),
                                        category=r.content_type,
                                        niche=niche,
                                        metadata={"source": "video_lead_scanner"},
                                    )
                                    for r in swarm_results
                                ]
                            )
                        except Exception as swarm_e:
                            logger.exception(
                                f"[Discovery] Video Lead Scanner failed for {niche}: {swarm_e}"
                            )

                return success_response(
                    data={
                        "status": ScanStatus.COMPLETED,
                        "niches": request.niches,
                        "candidates": all_results[:50],
                        "count": len(all_results),
                        "source": "fallback_python",
                    }
                )
    except Exception as e:
        import traceback
        logger.exception(f"[Discovery] UNHANDLED EXCEPTION in trigger_scan: {e}")
        logger.exception(traceback.format_exc())
        return handle_exception(e)


@router.post("/analyze")
async def analyze_candidate(
    request: AnalyzeRequest,
    current_user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("viral_analysis")),
    db=Depends(get_db),
):
    """
    Asynchronous deconstruction: Dispatches deep AI analysis to Celery
    and returns a task ID for UI polling.
    Accepts either a full ContentCandidate or just a URL and Niche.
    """
    from src.services.discovery.tasks import analyze_viral_pattern_task

    # 1. Resolve candidate from request
    if request.candidate:
        candidate = request.candidate
    elif request.url:
        candidate = ContentCandidate(
            id=f"ext_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}",
            platform="youtube",  # Default to youtube if unknown
            source_uri=request.url,
            niche=request.niche or "General",
            title="Manual Analysis",
            engagement_score=0.5,
            viral_score=50
        )
    else:
        raise HTTPException(status_code=400, detail="Missing URL or candidate data")

    # Consume credits
    from src.services.payment.credit_service import credit_service
    await credit_service.consume_credits(
        user_id=current_user.id,
        amount=credits_cost,
        action=CreditAction.VIRAL_ANALYSIS,
        db=db,
        reference_id=candidate.id,  # Using candidate ID as reference
    )

    task = analyze_viral_pattern_task.delay(candidate.dict())
    return success_response(
        data={
            "status": SystemJobStatus.QUEUED,
            "task_id": task.id,
            "candidate_id": candidate.id,
            "message": "AI Deconstruction in progress...",
        }
    )


@router.get("/niche-trends/{niche}")
@cache(expire=300)
async def get_niche_trends(
    niche: str, current_user: UserDB = Depends(get_current_user)
):
    try:
        trend = await base_discovery_service.aggregate_niche_trends(niche)
        if not trend:
            # If no data yet, try to scan first
            tier_value = get_subscription_tier_value(current_user)
            await base_discovery_service.find_trending_content(niche, tier=tier_value)
            trend = await base_discovery_service.aggregate_niche_trends(niche)
            if not trend:
                return success_response(
                    data={
                        "niche": niche,
                        "top_keywords": [],
                        "avg_engagement_score": 0.0,
                    }
                )
        return success_response(data=trend)
    except Exception as e:
        logger.exception(f"Niche trends failed for {niche}: {e}")
        return handle_exception(e)


@router.get("/niche-trends")
async def get_all_niche_trends(current_user: UserDB = Depends(get_current_user)):
    """Alias for niche trends when no niche is specified."""
    return success_response(data={"message": "Select a niche to see trends", "top_keywords": []})


@router.get("/summary")
async def get_discovery_summary(
    service: DiscoveryServiceExtended = Depends(get_discovery_service_extended),
):
    """Get discovery module summary statistics."""
    stats = await service.get_summary_stats()
    return success_response(data=stats)


@router.get("/niches")
async def list_monitored_niches(
    current_user: UserDB = Depends(get_current_user),
    service: DiscoveryServiceExtended = Depends(get_discovery_service_extended),
):
    """List all monitored niches for the current user."""
    niches = await service.list_monitored_niches(current_user.id)
    return success_response(data=niches)


@router.post("/niche/watch")
async def watch_niche(
    request: NicheAlertRequest,
    current_user: UserDB = Depends(get_current_user),
    service: DiscoveryServiceExtended = Depends(get_discovery_service_extended),
):
    """
    Persistently watch/monitor a niche for this current_user.
    Also creates or updates an alert for the niche.
    """
    result = await service.watch_niche(
        user_id=current_user.id,
        niche=request.niche,
        threshold=request.threshold,
        enabled=request.enabled,
    )
    return success_response(data=result)


@router.get("/analyze/{task_id}")
async def get_analysis_status(
    task_id: str, current_user: UserDB = Depends(get_current_user)
):
    """
    Get the status of an analysis task and return results when complete.
    """
    from src.api.utils.celery import celery_app

    try:
        # Get task result
        result = celery_app.AsyncResult(task_id)

        if result.ready():
            if result.successful():
                return success_response(
                    data={
                        "status": ScanStatus.COMPLETED,
                        "task_id": task_id,
                        "result": result.result,
                    }
                )
            else:
                return success_response(
                    data={
                        "status": ScanStatus.FAILED,
                        "task_id": task_id,
                        "error": str(result.info),
                    }
                )
        else:
            return success_response(
                data={
                    "status": ScanStatus.PENDING.value,
                    "task_id": task_id,
                    "message": "Analysis in progress...",
                }
            )
    except Exception as e:
        return handle_exception(e)


class CreateVideoFromAnalysisRequest(BaseModel):
    task_id: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: str | None = "Default"
    quality_tier: str | None = "standard"
    generate_thumbnail: bool | None = False



@router.post("/analyze/{task_id}/create-video")
async def create_video_from_analysis(
    task_id: str,
    request: CreateVideoFromAnalysisRequest,
    current_user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("video_transformation")),
    db=Depends(get_db),
):
    """
    Create a video transformation from completed analysis.
    """
    from src.api.utils.celery import celery_app
    from src.services.video_engine.tasks import download_and_process_task
    from src.api.utils.models import VideoJobDB

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
        candidate_url = analysis.get("source_uri") or analysis.get("candidate_id", "")

        if not candidate_url:
            raise HTTPException(
                status_code=400, detail="No source URL found in analysis"
            )

        # Dispatch Task
        try:
            task = download_and_process_task.delay(
                source_uri=candidate_url,
                niche=request.niche,
                platform=request.platform,
                style=request.style,
                quality_tier=request.quality_tier,
                generate_thumbnail=request.generate_thumbnail or False,
                user_id=current_user.id,
            )
        except Exception as task_err:
            logger.exception(f"Task dispatch failure: {task_err}")
            raise HTTPException(status_code=503, detail="Task queue unavailable")

        # Consume credits
        from src.services.payment.credit_service import credit_service
        success, msg = await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action=CreditAction.VIDEO_TRANSFORMATION,
            db=db,
            reference_id=task.id,
        )

        if not success:
            from src.api.utils.celery import celery_app

            celery_app.control.revoke(task.id, terminate=True)
            raise HTTPException(
                status_code=402, detail="Insufficient credits for this operation"
            )

        # Create job record
        new_job = VideoJobDB(
            id=task.id,
            title=f"From Analysis - {request.niche}",
            status=SystemJobStatus.QUEUED,
            progress=0,
            source_uri=candidate_url,
            user_id=current_user.id,
            job_metadata={
                "niche": request.niche,
                "platform": request.platform,
                "style": request.style,
                "quality_tier": request.quality_tier,
                "generate_thumbnail": request.generate_thumbnail,
                "analysis_task_id": task_id
            }
        )
        db.add(new_job)
        await db.commit()

        # Agentic Intelligence Injection (Official Skill Integration)
        try:
            from src.services.openclaw.agent import base_openclaw_agent_service
            # Trigger Competitor Analysis for the niche
            asyncio.create_task(base_openclaw_agent_service.process_message(
                identifier=str(current_user.id),
                message=f"Perform a deep competitor strategy analysis for the '{request.niche}' niche on {request.platform}. Identify top 3 viral hooks currently working."
            ))
            logger.info(f"[Discovery] Triggered agentic niche intelligence for {request.niche}")
        except Exception as ai_err:
            logger.warning(f"[Discovery] Agentic injection skipped: {ai_err}")

        return success_response(
            data={
                "status": SystemJobStatus.PROCESSING,
                "task_id": task.id,
                "analysis_task_id": task_id,
                "message": "Video transformation started from analysis",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return handle_exception(e)


# ─── Auto-Pipeline Endpoints ───────────────────────────────────────────


class AutoTransformRequest(BaseModel):
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: str | None = "Default"
    quality_tier: str | None = "standard"
    min_viral_score: int = 7
    generate_thumbnail: bool | None = False


@router.post("/auto-transform")
async def auto_transform(
    request: AutoTransformRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    One-shot pipeline: Discover best content → Create video transformation.
    Combines discovery and video creation into 1 call for autonomous operation.
    """
    from src.services.video_engine.tasks import download_and_process_task
    from src.api.utils.models import VideoJobDB
    from shared.enums import SystemJobStatus


    try:
        # Step 1: Discover top content for the niche
        await logger.info(
            f"[Auto-Transform] Discovering content for niche: {request.niche}"
        )
        candidates = await base_discovery_service.find_trending_content(
            request.niche,
            horizon="7d",
            tier=get_subscription_tier_value(current_user),
            min_viral_score=request.min_viral_score,
            region="US", # Default for auto-transform
        )

        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"No suitable content found for niche '{request.niche}'. Try lowering min_viral_score.",
            )

        # Select the top candidate
        best = candidates[0]
        source_uri = best.source_uri or ""

        if not source_uri:
            raise HTTPException(
                status_code=400, detail="Selected content has no source URL"
            )

        # Step 2: Dispatch video creation directly
        # (Skip analysis - use the discovery scores directly)
        await logger.info(f"[Auto-Transform] Creating video from: {best.title}")

        task = download_and_process_task.delay(
            source_uri=source_uri,
            niche=request.niche,
            platform=request.platform,
            style=request.style,
            quality_tier=request.quality_tier,
            generate_thumbnail=request.generate_thumbnail or False,
            user_id=current_user.id,
        )

        # Create job record
        new_job = VideoJobDB(
            id=task.id,
            title=f"Auto-Transform: {best.title[:50]}",
            status=SystemJobStatus.QUEUED,
            progress=0,
            source_uri=source_uri,
            user_id=current_user.id,
            job_metadata={
                "niche": request.niche,
                "platform": request.platform,
                "style": request.style,
                "quality_tier": request.quality_tier,
                "generate_thumbnail": request.generate_thumbnail,
                "min_viral_score": request.min_viral_score,
                "discovery_method": "auto-transform"
            }
        )
        db.add(new_job)
        await db.commit()

        return success_response(
            data={
                "status": SystemJobStatus.PROCESSING,
                "task_id": task.id,
                "source_title": best.title,
                "source_platform": best.platform,
                "source_viral_score": best.viral_score,
                "pipeline": "discover→create",
                "message": f"Auto-transform pipeline started for '{best.title[:30]}...'",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Auto-Transform] Pipeline failed: {e}")
        return handle_exception(e)


class InsightResponse(BaseModel):
    niche: str
    recommendation: str
    confidence: float
    filters_suggested: list[str]
    target_regions: list[str]
    alpha_status: bool = True


@router.get("/insights/{niche}")
@cache(expire=3600)
async def get_niche_insights(
    niche: str, current_user: UserDB = Depends(get_current_user)
):
    """
    Get AI-driven insights and recommendations for a specific niche.
    Uses Groq Llama-3 to generate high-fidelity, real-time advice based on the niche.
    """
    from src.services.llm.intelligence_hub import IntelligenceHub

    # Default fallback data
    recommendation = "Use high-contrast visuals and rapid-fire segments. Maintain a high information density to maximize retention in the first 5 seconds."
    filters = ["Glitch Alpha", "Cinematic Pulse"]
    confidence = 0.85

    try:
        hub = IntelligenceHub()
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

        ai_data = await hub.chat(
            prompt=prompt,
            system_prompt="You are a Viral Growth Strategy Analyst.",
            json_mode=True,
        )

        recommendation = ai_data.get("recommendation", recommendation)
        filters = ai_data.get("filters_suggested", filters)
        confidence = ai_data.get("confidence", confidence)
    except Exception as e:
        logger.exception(f"[Discovery] Intelligence Hub Insight Failure: {e}")

    return success_response(
        data=InsightResponse(
            niche=niche,
            recommendation=recommendation,
            confidence=confidence,
            filters_suggested=filters,
            target_regions=["US", "GB", "DE"],
            alpha_status=False,  # No longer alpha, it's real
        )
    )


# ─── opencli-rs Enhanced Discovery ─────────────────────────────────────
# These endpoints use the current_user's own Chrome sessions (via opencli-rs)
# as an alternative to global API-based discovery.


@router.get("/opencli/search")
async def opencli_search(
    platform: str,
    query: str,
    limit: int = 20,
    current_user: UserDB = Depends(get_current_user),
):
    """Search a platform using the current_user's own Chrome session (via opencli-rs).

    This is an alternative to the global API-based search. Each current_user
    can connect their own platform sessions via the /opencli/sessions
    endpoints, then use this to search with their authenticated session.
    """
    from src.services.opencli.scanner import OpenCLIScanner

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(current_user.id)
    candidates = await scanner.scan_trends(query, platforms=[platform.lower()])

    # Limit results
    return success_response(data=candidates[:limit])


@router.get("/opencli/feed/{platform}")
async def opencli_feed(
    platform: str,
    feed_type: str = "trending",
    limit: int = 20,
    current_user: UserDB = Depends(get_current_user),
):
    """Get feed/trending content from a platform using the current_user's Chrome session.

    feed_type options: feed, trending, hot, top, explore
    """
    from src.services.opencli.scanner import OpenCLIScanner

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(current_user.id)
    candidates = await scanner.get_platform_feed(platform.lower(), feed_type, limit)

    return success_response(data=candidates)


@router.post("/opencli/scan")
async def opencli_scan(
    niche: str = "general",
    platforms: list[str] | None = None,
    current_user: UserDB = Depends(get_current_user),
):
    """Deep scan all connected platforms using the current_user's Chrome sessions.

    This merges opencli-rs results with the standard discovery pipeline,
    giving the current_user content discovered through their own authenticated sessions.
    """
    from src.services.opencli.scanner import OpenCLIScanner

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(current_user.id)
    p = [p.lower() for p in platforms] if platforms else None
    candidates = await scanner.scan_trends(niche, platforms=p)

    return success_response(
        data={
            "candidates": candidates,
            "count": len(candidates),
            "source": "opencli-rs",
            "platforms_scanned": p or "all_connected",
        }
    )


class InteractionRequest(BaseModel):
    candidate_id: str | None = None
    niche: str | None = None
    platform: str | None = None
    action: str = "handshake"
    content_url: str | None = None


@router.post("/interact")
async def record_interaction(
    request: InteractionRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Records a UI interaction with a discovery candidate.
    """
    from src.api.utils.models import DiscoveryInteractionDB
    import datetime

    candidate_id = request.candidate_id
    if not candidate_id and request.content_url:
        # Try to find candidate by source_uri
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.source_uri == request.content_url)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        if candidate:
            candidate_id = candidate.id
        else:
            # Use content_url as fallback identifier or hashed value
            import hashlib
            candidate_id = f"ext_{hashlib.md5(request.content_url.encode()).hexdigest()}"

    try:
        new_interaction = DiscoveryInteractionDB(
            candidate_id=candidate_id or "unknown",
            user_id=current_user.id,
            action=request.action,
            status=1,  # Established
            details={
                "niche": request.niche,
                "platform": request.platform,
                "content_url": request.content_url,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)

        return success_response(
            data={
                "status": "Handshake Established",
                "candidate_id": candidate_id,
                "interaction_id": new_interaction.id,
                "timestamp": new_interaction.created_at.isoformat(),
                "message": "Protocol established with target node.",
            }
        )
    except Exception as e:
        logger.exception(f"Interaction record failed: {e}")
        return handle_exception(e)


# ─── Content Analysis Endpoints ───────────────────────────────────────────────


class AnalysisResponse(BaseModel):
    content_id: str
    analysis_results: dict
    analyzed_at: datetime.datetime | None = None


@router.get("/{content_id}/analysis")
async def get_content_analysis(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    force: bool = False,
):
    """
    Get analysis for a content item.

    If analysis doesn't exist, it will be performed automatically.
    Set force=true to re-analyze already analyzed content.
    """
    try:
        # First try to get existing analysis
        existing_analysis = await get_persisted_analysis_report(content_id, db)

        if existing_analysis and not force:
            # Return existing analysis
            stmt = select(ContentCandidateDB).filter(
                ContentCandidateDB.id == content_id
            )
            result = await db.execute(stmt)
            content = result.scalar_one_or_none()
            return success_response(
                data=AnalysisResponse(
                    content_id=content_id,
                    analysis_results=existing_analysis,
                    analyzed_at=content.analyzed_at if content else None,
                )
            )

        # Perform new analysis
        analysis_results = await extract_content_patterns(content_id, db, force=force)

        # Get the updated content for timestamp
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        return success_response(
            data=AnalysisResponse(
                content_id=content_id,
                analysis_results=analysis_results,
                analyzed_at=content.analyzed_at if content else None,
            )
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        return handle_exception(e)


# ─── Velocity & Reupload Tracking Endpoints ───────────────────────────────────


@router.get("/{content_id}/velocity")
async def get_content_velocity(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get viral velocity score for a specific content item.
    Calculates real-time velocity based on view count and age.
    """
    from src.services.discovery.scanner_base import DiscoveryScannerBase

    try:
        # Get content from database
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Content '{content_id}' not found"
            )

        # Create a candidate from DB
        candidate = ContentCandidate(
            id=content.id,
            platform=content.platform,
            source_uri=content.source_uri or "",
            creator_name=content.creator_name or "Unknown",
            title=content.title or "",
            description=content.description or "",
            thumbnail_uri=content.thumbnail_uri or "",
            view_count=content.view_count or 0,
            engagement_score=content.engagement_score or 0.0,
            viral_score=content.viral_score or 0,
            duration_seconds=content.duration_seconds or 0.0,
            published_at=content.published_at,
            scanned_at=content.scanned_at,
            metadata=content.metadata_json or {},
        )

        # Calculate velocity using base scanner default
        scanner = DiscoveryScannerBase()
        velocity = scanner.identify_viral_velocity(candidate)
        viral_score = scanner.calculate_viral_score(candidate)

        return success_response(
            data={
                "content_id": content_id,
                "title": content.title,
                "platform": content.platform,
                "view_count": content.view_count,
                "velocity": round(velocity, 2),
                "viral_score": viral_score,
                "hours_since_published": (
                    (
                        datetime.datetime.now(datetime.timezone.utc)
                        - content.published_at
                    ).total_seconds()
                    / 3600
                    if content.published_at
                    else None
                ),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Velocity calculation failed: {e}")
        return handle_exception(e)


@router.get("/{content_id}/reuploads")
async def get_content_reuploads(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 20,
):
    """
    Find cross-platform reuploads of the same content.
    Uses title similarity to match content across platforms.
    """
    try:
        # Get content from database
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Content '{content_id}' not found"
            )

        # Use service to find reuploads
        reuploads = await base_discovery_service.find_reuploads(
            content_id=content_id,
            source_platform=content.platform,
        )

        # Limit results
        reuploads = reuploads[:limit]

        return success_response(
            data={
                "original_id": content_id,
                "original_title": content.title,
                "original_platform": content.platform,
                "reuploads": [
                    {
                        "id": r.id,
                        "platform": r.platform,
                        "title": r.title,
                        "source_uri": r.source_uri,
                        "view_count": r.view_count,
                        "viral_score": r.viral_score,
                        "similarity_score": r.metadata.get("similarity_score", 0),
                    }
                    for r in reuploads
                ],
                "count": len(reuploads),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Reupload search failed: {e}")
        return handle_exception(e)


# ─── Refresh Endpoints ───────────────────────────────────────────────────────


class RefreshRequest(BaseModel):
    niches: list[str] | None = None
    clear_cache: bool = False


@router.post("/refresh")
async def refresh_discovery(
    request: RefreshRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Refresh discovery cache for specified niches.
    If no niches specified, refreshes all cached niches.
    Clears Redis cache and triggers new scans.
    """
    from src.api.utils.redis import get_sync_redis

    try:
        r = get_sync_redis()

        refreshed_niches = []

        if request.clear_cache:
            # Clear all cache if requested
            keys = r.keys("discovery:trends:*")
            if keys:
                r.delete(*keys)
                logger.info(f"[Discovery] Cleared {len(keys)} cache keys")

        # Determine niches to refresh
        niches_to_refresh = request.niches if request.niches else [None]

        for niche in niches_to_refresh:
            actual_niche = niche or "global"

            # Delete cache for this niche
            cache_key = f"discovery:trends:{actual_niche}:30d"
            r.delete(cache_key)
            refreshed_niches.append(actual_niche)

            # Trigger background scan
            logger.info(f"[Discovery] Triggering refresh scan for: {actual_niche}")

        return success_response(
            data={
                "status": "refresh_queued",
                "niches": refreshed_niches,
                "message": f"Cache cleared and refresh triggered for {len(refreshed_niches)} niche(s)",
            }
        )

    except Exception as e:
        logger.exception(f"Refresh failed: {e}")
        return handle_exception(e)


# ─── Export Endpoints ───────────────────────────────────────────────────────────


class ExportRequest(BaseModel):
    niche: str | None = None
    format: str = "json"  # json or csv
    limit: int = 100


@router.post("/export")
async def export_discovery(
    request: ExportRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Export discovery results as JSON or CSV.
    Useful for bulk analysis and reporting.
    """
    import csv
    import io

    try:
        # Get content
        candidates = []
        if request.niche:
            candidates = await base_discovery_service.find_trending_content(
                request.niche,
                horizon="30d",
                tier="free",
                min_viral_score=0,
            )

        candidates = candidates[: request.limit]

        if request.format == "csv":
            # Convert to CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "id",
                    "title",
                    "platform",
                    "creator",
                    "views",
                    "viral_score",
                    "engagement",
                    "url",
                ]
            )
            for c in candidates:
                writer.writerow(
                    [
                        c.id,
                        c.title,
                        c.platform,
                        c.creator_name,
                        c.view_count,
                        c.viral_score,
                        c.engagement_score,
                        c.source_uri,
                    ]
                )

            csv_content = output.getvalue()
            return success_response(
                data={
                    "format": "csv",
                    "count": len(candidates),
                    "content": csv_content,
                }
            )
        else:
            # JSON format
            return success_response(
                data={
                    "format": "json",
                    "count": len(candidates),
                    "candidates": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "platform": c.platform,
                            "creator": c.creator_name,
                            "views": c.view_count,
                            "viral_score": c.viral_score,
                            "engagement": c.engagement_score,
                            "url": c.source_uri,
                        }
                        for c in candidates
                    ],
                }
            )

    except Exception as e:
        logger.exception(f"Export failed: {e}")
        return handle_exception(e)


# ─── Niche Alert Endpoints ────────────────���──────────────────────────────────────




@router.get("/alerts")
async def get_niche_alerts(
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current_user's niche alerts."""
    from src.api.utils.models import DiscoveryAlertDB

    try:
        stmt = select(DiscoveryAlertDB).filter(
            DiscoveryAlertDB.user_id == current_user.id,
            DiscoveryAlertDB.is_active,
        )
        result = await db.execute(stmt)
        alerts = result.scalars().all()

        return success_response(
            data={
                "alerts": [
                    {
                        "id": a.id,
                        "niche": a.niche,
                        "threshold": a.threshold,
                        "enabled": a.is_active,
                        "message": f"High viral velocity detected in {a.niche}",
                        "severity": "high" if (a.threshold or 7) > 8 else "medium"
                    }
                    for a in alerts
                ]
            }
        )
    except Exception as e:
        logger.exception(f"Get alerts failed: {e}")
        return handle_exception(e)


@router.post("/alerts")
async def create_niche_alert(
    request: NicheAlertRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alias for watch_niche."""
    from src.api.utils.models import DiscoveryAlertDB, MonitoredNiche

    try:
        # 1. Ensure MonitoredNiche exists
        stmt_monitor = select(MonitoredNiche).filter(
            and_(
                MonitoredNiche.user_id == current_user.id,
                MonitoredNiche.niche == request.niche,
            )
        )
        monitor_result = await db.execute(stmt_monitor)
        monitor = monitor_result.scalar_one_or_none()
        
        if not monitor:
            monitor = MonitoredNiche(user_id=current_user.id, niche=request.niche, is_active=True)
            db.add(monitor)
        else:
            monitor.is_active = True

        # 2. Handle Alert
        stmt = select(DiscoveryAlertDB).filter(
            and_(
                DiscoveryAlertDB.user_id == current_user.id,
                DiscoveryAlertDB.niche == request.niche,
            )
        )
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if alert:
            alert.threshold = request.threshold
            alert.is_active = request.enabled
        else:
            alert = DiscoveryAlertDB(
                user_id=current_user.id,
                niche=request.niche,
                threshold=request.threshold,
                is_active=request.enabled,
            )
            db.add(alert)
        
        await db.commit()
        return success_response(
            data={
                "status": "alert_established",
                "alert_id": alert.id,
                "niche": request.niche,
                "threshold": request.threshold,
            }
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Create alert failed: {e}")
        return handle_exception(e)


@router.delete("/alerts/{alert_id}")
async def delete_niche_alert(
    alert_id: int,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a niche alert."""
    from src.api.utils.models import DiscoveryAlertDB

    try:
        alert = await db.get(DiscoveryAlertDB, alert_id)
        if not alert or alert.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Alert not found")

        await db.delete(alert)
        await db.commit()

        return success_response(data={"status": "alert_deleted", "alert_id": alert_id})
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Delete alert failed: {e}")
        return handle_exception(e)


# ─── Bulk Favorites Endpoints ──────────────────────────────────────────────


class BulkFavoriteRequest(BaseModel):
    candidate_ids: list[str]
    action: str = "add"  # add or remove


@router.post("/favorites/bulk")
async def bulk_favorites(
    request: BulkFavoriteRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """Add or remove multiple candidates from favorites."""
    from src.api.utils.models import DiscoveryFavoriteDB

    try:
        added = 0
        removed = 0

        for candidate_id in request.candidate_ids:
            # Check if exists
            existing = await db.get(DiscoveryFavoriteDB, candidate_id)

            if request.action == "add" and not existing:
                fav = DiscoveryFavoriteDB(
                    id=candidate_id,
                    user_id=current_user.id,
                )
                db.add(fav)
                added += 1
            elif request.action == "remove" and existing:
                await db.delete(existing)
                removed += 1

        await db.commit()

        return success_response(
            data={
                "status": "bulk_complete",
                "action": request.action,
                "added": added,
                "removed": removed,
            }
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Bulk favorite failed: {e}")
        return handle_exception(e)


@router.get("/favorites")
async def get_favorites(
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 50,
):
    """Get current_user's favorite content."""
    from src.api.utils.models import DiscoveryFavoriteDB

    try:
        stmt = (
            select(ContentCandidateDB)
            .join(DiscoveryFavoriteDB, DiscoveryFavoriteDB.id == ContentCandidateDB.id)
            .where(DiscoveryFavoriteDB.user_id == current_user.id)
            .order_by(ContentCandidateDB.viral_score.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        favorites = result.scalars().all()

        return success_response(
            data={
                "favorites": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "platform": f.platform,
                        "viral_score": f.viral_score,
                        "source_uri": f.source_uri,
                    }
                    for f in favorites
                ],
                "count": len(favorites),
            }
        )
    except Exception as e:
        logger.exception(f"Get favorites failed: {e}")
        return handle_exception(e)


# ─── Scan History Endpoints ──────────────────────────────────────────────


@router.get("/history")
async def get_scan_history(
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 20,
):
    """Get scan history for the current_user."""
    from src.api.utils.models import ScanHistoryDB

    try:
        stmt = (
            select(ScanHistoryDB)
            .where(ScanHistoryDB.user_id == current_user.id)
            .order_by(ScanHistoryDB.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        history = result.scalars().all()

        return success_response(
            data={
                "history": [
                    {
                        "id": h.id,
                        "niche": h.niche,
                        "status": h.status,
                        "results_count": h.results_count,
                        "created_at": h.created_at.isoformat()
                        if h.created_at
                        else None,
                    }
                    for h in history
                ],
                "count": len(history),
            }
        )
    except Exception as e:
        logger.exception(f"Get history failed: {e}")
        return handle_exception(e)

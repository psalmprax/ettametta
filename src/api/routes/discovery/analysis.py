from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
import datetime
import asyncio

from src.services.discovery.service import base_discovery_service
from src.services.discovery.models import ContentCandidate
from src.services.discovery.analysis_service import (
    extract_content_patterns,
    get_persisted_analysis_report,
)
from src.api.utils.api_responses import (
    success_response,
    handle_exception,
)

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from src.api.utils.subscription import credits_required, get_subscription_tier_value
from src.shared.enums import SystemJobStatus, CreditAction, ScanStatus
from src.api.utils.models import ContentCandidateDB
from sqlalchemy import select
from src.services.video_engine.job_service import VideoJobService, get_video_job_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    url: str | None = None
    niche: str | None = "AI Technology"
    candidate: ContentCandidate | None = None


class CreateVideoFromAnalysisRequest(BaseModel):
    task_id: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: str | None = "Default"
    quality_tier: str | None = "standard"
    generate_thumbnail: bool | None = False


class AutoTransformRequest(BaseModel):
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: str | None = "Default"
    quality_tier: str | None = "standard"
    min_viral_score: int = 7
    generate_thumbnail: bool | None = False


class InsightResponse(BaseModel):
    niche: str
    recommendation: str
    confidence: float
    filters_suggested: list[str]
    target_regions: list[str]
    alpha_status: bool = True


class AnalysisResponse(BaseModel):
    content_id: str
    analysis_results: dict
    analyzed_at: datetime.datetime | None = None


@router.post("/analyze")
async def analyze_candidate(
    request: AnalyzeRequest,
    current_user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("viral_analysis")),
    db=Depends(get_db),
):
    from src.services.discovery.tasks import analyze_viral_pattern_task

    if request.candidate:
        candidate = request.candidate
    elif request.url:
        candidate = ContentCandidate(
            id=f"ext_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}",
            platform="youtube",
            source_uri=request.url,
            niche=request.niche or "General",
            title="Manual Analysis",
            engagement_score=0.5,
            viral_score=50
        )
    else:
        raise HTTPException(status_code=400, detail="Missing URL or candidate data")

    from src.services.payment.credit_service import credit_service

    try:
        task = analyze_viral_pattern_task.delay(candidate.dict())
    except Exception as dispatch_err:
        logger.exception(f"[Discovery] Task dispatch failure: {dispatch_err}")
        raise HTTPException(
            status_code=503, detail="Task queue unavailable; credits not charged."
        )

    charged, charge_msg = await credit_service.consume_credits(
        user_id=current_user.id,
        amount=credits_cost,
        action=CreditAction.VIRAL_ANALYSIS,
        db=db,
        reference_id=candidate.id,
    )
    if not charged:
        from src.api.utils.celery import celery_app
        try:
            celery_app.control.revoke(task.id, terminate=True)
        except Exception as revoke_err:
            logger.exception(
                f"[Discovery] Failed to revoke task after credit failure: {revoke_err}"
            )
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits: {charge_msg or 'top up and retry'}",
        )

    return success_response(
        data={
            "status": SystemJobStatus.QUEUED,
            "task_id": task.id,
            "candidate_id": candidate.id,
            "message": "AI Deconstruction in progress...",
        }
    )


@router.get("/analyze/{task_id}")
async def get_analysis_status(
    task_id: str, current_user: UserDB = Depends(get_current_user)
):
    from src.api.utils.celery import celery_app

    try:
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


@router.post("/analyze/{task_id}/create-video")
async def create_video_from_analysis(
    task_id: str,
    request: CreateVideoFromAnalysisRequest,
    current_user: UserDB = Depends(get_current_user),
    credits_cost: int = Depends(credits_required("video_transformation")),
    db=Depends(get_db),
    job_service: VideoJobService = Depends(get_video_job_service),
):
    from src.api.utils.celery import celery_app
    from src.services.video_engine.tasks import download_and_process_task

    try:
        result = celery_app.AsyncResult(task_id)

        if not result.ready():
            raise HTTPException(status_code=400, detail="Analysis not yet complete")

        if not result.successful():
            raise HTTPException(
                status_code=400, detail=f"Analysis failed: {result.info}"
            )

        analysis = result.result
        candidate_url = analysis.get("source_uri") or analysis.get("candidate_id", "")

        if not candidate_url:
            raise HTTPException(
                status_code=400, detail="No source URL found in analysis"
            )

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

        await job_service.create_job(
            user_id=current_user.id,
            title=f"From Analysis - {request.niche}",
            engine="video_transform",
            niche=request.niche,
            style=request.style,
            status=SystemJobStatus.QUEUED,
            job_id=task.id,
            progress=0,
            source_uri=candidate_url,
            extra_metadata={
                "platform": request.platform,
                "quality_tier": request.quality_tier,
                "generate_thumbnail": request.generate_thumbnail,
                "analysis_task_id": task_id,
            },
        )

        try:
            from src.services.openclaw.agent import base_openclaw_agent_service
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


@router.post("/auto-transform")
async def auto_transform(
    request: AutoTransformRequest,
    current_user: UserDB = Depends(get_current_user),
    job_service: VideoJobService = Depends(get_video_job_service),
):
    from src.services.video_engine.tasks import download_and_process_task

    try:
        await logger.info(
            f"[Auto-Transform] Discovering content for niche: {request.niche}"
        )
        candidates = await base_discovery_service.find_trending_content(
            request.niche,
            horizon="7d",
            tier=get_subscription_tier_value(current_user),
            min_viral_score=request.min_viral_score,
            region="US",
        )

        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"No suitable content found for niche '{request.niche}'. Try lowering min_viral_score.",
            )

        best = candidates[0]
        source_uri = best.source_uri or ""

        if not source_uri:
            raise HTTPException(
                status_code=400, detail="Selected content has no source URL"
            )

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

        await job_service.create_job(
            user_id=current_user.id,
            title=f"Auto-Transform: {best.title[:50]}",
            engine="video_transform",
            niche=request.niche,
            style=request.style,
            status=SystemJobStatus.QUEUED,
            job_id=task.id,
            progress=0,
            source_uri=source_uri,
            extra_metadata={
                "platform": request.platform,
                "quality_tier": request.quality_tier,
                "generate_thumbnail": request.generate_thumbnail,
                "min_viral_score": request.min_viral_score,
                "discovery_method": "auto-transform",
            },
        )

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


@router.get("/insights/{niche}")
async def get_niche_insights(
    niche: str, current_user: UserDB = Depends(get_current_user)
):
    from src.services.llm.intelligence_hub import IntelligenceHub

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
            alpha_status=False,
        )
    )


@router.get("/{content_id}/analysis")
async def get_content_analysis(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    force: bool = False,
):
    try:
        existing_analysis = await get_persisted_analysis_report(content_id, db)

        if existing_analysis and not force:
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

        analysis_results = await extract_content_patterns(content_id, db, force=force)

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


@router.get("/{content_id}/velocity")
async def get_content_velocity(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.services.discovery.scanner_base import DiscoveryScannerBase

    try:
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Content '{content_id}' not found"
            )

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
    try:
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Content '{content_id}' not found"
            )

        reuploads = await base_discovery_service.find_reuploads(
            content_id=content_id,
            source_platform=content.platform,
        )

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

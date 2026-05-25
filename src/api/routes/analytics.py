import logging
import csv
import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from src.services.analytics.service import base_analytics_service
from src.services.analytics.service_extended import AnalyticsServiceExtended
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
import datetime
from fastapi_cache.decorator import cache
from src.api.utils.database import get_db
from src.api.utils.api_responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/posts")
async def list_analytics_posts(
    page: int = 1,
    size: int = 20,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    List all published posts with pagination.
    """
    try:
        analytics_service = AnalyticsServiceExtended(db)
        posts, total_items = await analytics_service.list_published_posts(
            user_id=current_user.id,
            user_role=current_user.role,
            page=page,
            size=size,
        )
        
        return success_response(
            data={
                "posts": posts,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total_items,
                    "pages": (total_items + size - 1) // size,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Content metrics failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/report")
async def get_analytics_report(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    """
    Get overall analytics report summary.
    """
    try:
        analytics_service = AnalyticsServiceExtended(db)
        report = await analytics_service.get_report_summary(
            user_id=current_user.id,
            user_role=current_user.role,
        )
        return success_response(data=report)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Analytics report failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/report/{post_id}")
@cache(expire=600)
async def get_report(
    post_id: str,
    platform: str = "youtube",
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        analytics_service = AnalyticsServiceExtended(db)
        
        # Verify user owns this content
        await analytics_service.verify_content_access(
            post_id=post_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )

        report = await base_analytics_service.get_performance_report(
            post_id, current_user.id, platform
        )

        # Real-First: Record a snapshot for history tracking whenever a report is viewed
        import asyncio

        asyncio.create_task(
            base_analytics_service.record_snapshot(
                post_id,
                report.view_count,
                report.like_count,
                report.share_count,
                report.comment_count,
                report.retention_rate,
                getattr(report, "avg_duration", 0.0),
            )
        )
        return success_response(data=report)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/insights/{post_id}")
async def get_insights(
    post_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        analytics_service = AnalyticsServiceExtended(db)
        
        # Verify user owns this content
        await analytics_service.verify_content_access(
            post_id=post_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )

        report = await base_analytics_service.get_performance_report(
            post_id,
            current_user.id,
            "youtube",  # Explicitly default to youtube for insights
        )
        return success_response(data={"insight": report.optimization_insight})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Performance analysis failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/monetization/{post_id}")
async def get_monetization_suggestions(
    post_id: str,
    niche: str = "Motivation",
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        analytics_service = AnalyticsServiceExtended(db)
        
        # Verify user owns this content
        await analytics_service.verify_content_access(
            post_id=post_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )

        report = await base_analytics_service.get_performance_report(
            post_id,
            current_user.id,
            "youtube",  # Explicitly default to youtube for monetization
        )
        suggestions = await base_analytics_service.suggest_optimal_monetization(
            report, current_user.id, niche
        )
        return success_response(data={"report": report, "suggestions": suggestions})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Comparative analysis failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/stats/summary")
@cache(expire=600)
async def get_stats_summary(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    """Get dashboard summary stats for the home page."""
    try:
        analytics_service = AnalyticsServiceExtended(db)
        stats = await analytics_service.get_stats_summary(
            user_id=current_user.id,
            user_role=current_user.role,
        )
        return success_response(data=stats)
    except Exception as e:
        logger.exception(f"Stats summary failed: {e}")
        return success_response(
            data={
                "active_trends": 0,
                "videos_processed": 0,
                "total_reach": "0",
                "success_rate": "0%",
                "recent_discovery_count": 0,
                "engine_load": "0%",
                "velocity": "Nominal",
            }
        )


@router.get("/stats/storage")
@cache(expire=3600)
async def get_storage_stats(current_user: UserDB = Depends(get_current_user)):
    """Get storage usage statistics for the outputs directory."""
    try:
        analytics_service = AnalyticsServiceExtended(None)  # DB not needed for storage stats
        stats = await analytics_service.get_storage_stats()
        return success_response(data=stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"A/B test metrics failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/ab/results/{content_id}")
async def get_ab_results(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        analytics_service = AnalyticsServiceExtended(db)
        results = await analytics_service.get_ab_test_results(content_id)
        return success_response(data=results)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"AB test results failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/report/{post_id}/history")
async def get_report_history(
    post_id: str, current_user: UserDB = Depends(get_current_user)
):
    """
    Returns time-series history for a specific post.
    In a real-first system, this replaces simulated growth curves.
    """
    try:
        history = await base_analytics_service.get_historical_performance(post_id)
        return success_response(data=history)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Dashboard metrics failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.post("/inject-pattern/{post_id}")
async def inject_pattern(
    post_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        analytics_service = AnalyticsServiceExtended(db)
        
        # Verify user owns this content
        await analytics_service.verify_content_access(
            post_id=post_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )

        # Delegate to service
        result = await base_analytics_service.inject_pattern(post_id, current_user.id)
        return success_response(data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"ROI analysis failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


@router.get("/export")
async def export_analytics(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):

    try:
        analytics_service = AnalyticsServiceExtended(db)
        posts_data = await analytics_service.export_posts(
            user_id=current_user.id,
            user_role=current_user.role,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["Post ID", "Platform", "Title", "Views", "Likes", "Shares", "Published At"]
        )

        for post_data in posts_data:
            writer.writerow(
                [
                    post_data[0],
                    post_data[1],
                    post_data[2],
                    post_data[3],
                    post_data[4],
                    post_data[5],
                    post_data[6].isoformat() if post_data[6] else "",
                ]
            )

        output.seek(0)
        filename = (
            f"ettametta_analytics_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
        )
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Export failed: {e}")
        raise HTTPException(status_code=503, detail="Export service unavailable")

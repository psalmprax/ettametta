from fastapi import APIRouter, HTTPException, Depends
from services.analytics.service import base_analytics_service
from services.analytics.models import ContentPerformance
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from typing import List
import datetime

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/posts")
async def list_analytics_posts(current_user: UserDB = Depends(get_current_user)):
    from api.utils.database import SessionLocal
    from api.utils.models import PublishedContentDB
    db = SessionLocal()
    try:
        query = db.query(PublishedContentDB).filter(PublishedContentDB.status == "Published")
        if current_user.role != "admin":
            query = query.filter(PublishedContentDB.user_id == current_user.id)
            
        posts = query.order_by(PublishedContentDB.published_at.desc()).all()
        return posts
    finally:
        db.close()

@router.get("/report/{post_id}", response_model=ContentPerformance)
async def get_report(post_id: str, current_user: UserDB = Depends(get_current_user)):
    try:
        report = await base_analytics_service.get_performance_report(post_id)
        # In a real app, verify report.user_id == current_user.id
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{post_id}")
async def get_insights(post_id: str, current_user: UserDB = Depends(get_current_user)):
    try:
        report = await base_analytics_service.get_performance_report(post_id)
        return {"insight": report.optimization_insight}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monetization/{post_id}")
async def get_monetization_suggestions(post_id: str, niche: str = "Motivation", current_user: UserDB = Depends(get_current_user)):
    try:
        report = await base_analytics_service.get_performance_report(post_id)
        suggestions = base_analytics_service.suggest_optimal_monetization(report, niche)
        return {"report": report, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_stats_summary(current_user: UserDB = Depends(get_current_user)):
    """Get dashboard summary stats for the home page."""
    from api.utils.database import SessionLocal
    from api.utils.models import PublishedContentDB, VideoJobDB
    from sqlalchemy import func
    
    db = SessionLocal()
    try:
        # Base queries
        post_query = db.query(PublishedContentDB).filter(PublishedContentDB.status == "Published")
        job_query = db.query(VideoJobDB)
        
        # User isolation
        if current_user.role != "admin":
            post_query = post_query.filter(PublishedContentDB.user_id == current_user.id)
            job_query = job_query.filter(VideoJobDB.user_id == current_user.id)

        # Count published posts
        total_posts = post_query.count()
        
        # Count total video jobs
        total_jobs = job_query.count()
        
        # Calculate success rate
        success_rate = (total_posts / total_jobs * 100) if total_jobs > 0 else 0
        
        # Get total views
        total_views = post_query.with_entities(func.sum(PublishedContentDB.view_count)).scalar() or 0
        
        # Format reach
        if total_views >= 1000000:
            reach_formatted = f"{total_views / 1000000:.1f}M"
        elif total_views >= 1000:
            reach_formatted = f"{total_views / 1000:.1f}K"
        else:
            reach_formatted = str(total_views)
        
        # Count active trends (unique niches from telemetry)
        from api.utils.models import NicheTrendDB
        active_trends_count = db.query(NicheTrendDB.niche).distinct().count() or 0
        
        # Calculate velocity (discovered in last 24h)
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        recent_count = db.query(NicheTrendDB).filter(NicheTrendDB.last_updated >= yesterday).count() or 0
        
        # Calculate engine load (Queue vs Capacity)
        pending_jobs = db.query(VideoJobDB).filter(VideoJobDB.status.in_(["Queued", "Transcribing", "Rendering"])).count()
        MAX_CAPACITY = 10 # Sample threshold
        engine_load = int((pending_jobs / MAX_CAPACITY) * 100) if MAX_CAPACITY > 0 else 0
        
        return {
            "active_trends": active_trends_count,
            "videos_processed": total_jobs,
            "total_reach": reach_formatted,
            "success_rate": f"{success_rate:.1f}%",
            "recent_discovery_count": recent_count,
            "engine_load": f"{engine_load}%",
            "velocity": "High" if recent_count > 5 else "Nominal"
        }
    finally:
        db.close()
@router.get("/ab/results/{content_id}")
async def get_ab_results(content_id: str, current_user: UserDB = Depends(get_current_user)):
    """
    Returns A/B test performance for a specific content job.
    """
    from api.utils.database import SessionLocal
    from api.utils.models import ABTestDB
    db = SessionLocal()
    try:
        test = db.query(ABTestDB).filter(ABTestDB.content_id == content_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="A/B test not found for this content")
        
        # Calculate winning variant (simplified logic)
        total_views = test.variant_a_views + test.variant_b_views
        winner = None
        if total_views > 10: # Threshold for significant data
            winner = "A" if test.variant_a_views > test.variant_b_views else "B"
            
        return {
            "test_id": test.id,
            "variant_a_title": test.variant_a_title,
            "variant_b_title": test.variant_b_title,
            "variant_a_views": test.variant_a_views,
            "variant_b_views": test.variant_b_views,
            "winner": winner,
            "created_at": test.created_at
        }
    finally:
        db.close()

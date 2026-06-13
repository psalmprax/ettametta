"""
A/B Testing API Routes for ettametta
Provides statistical A/B testing with proper significance testing
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from src.api.utils.database import get_db
from src.api.utils.models import ABTestDB, VideoJobDB, PublishedContentDB
from src.shared.enums import ABTestStatus, SystemJobStatus, ContentPublishStatus
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserRole
from pydantic import BaseModel
from datetime import datetime, timezone
import math
import logging
from src.api.utils.api_responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ab-testing", tags=["A/B Testing"])


class ABTestCreate(BaseModel):
    content_id: str
    variant_a_title: str
    variant_b_title: str
    variant_a_description: str | None = None
    variant_b_description: str | None = None
    target_metric: str | None = "views"  # views, clicks, engagement


class ABTestVariantEvent(BaseModel):
    variant: str
    event_type: str  # view, click, conversion


class VariantCreateRequest(BaseModel):
    variant_a_title: str
    variant_b_title: str
    variant_a_description: str | None = None
    variant_b_description: str | None = None
    target_metric: str | None = "views"


class VariantPublishRequest(BaseModel):
    platform: str = "YouTube Shorts"
    niche: str = "General"
    account_id: str | None = None
    inject_monetization: bool = False


class StatisticalResult(BaseModel):
    significant: bool
    confidence_level: float
    winner: str | None
    p_value: float | None
    effect_size: float


def calculate_statistics(
    views_a: int, views_b: int, conversions_a: int, conversions_b: int
) -> StatisticalResult:
    """
    Perform proper statistical testing using z-test for proportions.
    Returns statistical significance and winner.
    """
    if views_a == 0 or views_b == 0:
        return StatisticalResult(
            significant=False,
            confidence_level=0.0,
            winner=None,
            p_value=None,
            effect_size=0.0,
        )

    # Conversion rates
    rate_a = conversions_a / views_a if views_a > 0 else 0
    rate_b = conversions_b / views_b if views_b > 0 else 0

    # Pooled proportion
    pooled_rate = (
        (conversions_a + conversions_b) / (views_a + views_b)
        if (views_a + views_b) > 0
        else 0
    )

    # Standard error
    se = (
        math.sqrt(pooled_rate * (1 - pooled_rate) * (1 / views_a + 1 / views_b))
        if (views_a > 0 and views_b > 0)
        else 0
    )

    if se == 0:
        return StatisticalResult(
            significant=False,
            confidence_level=0.0,
            winner=None,
            p_value=None,
            effect_size=0.0,
        )

    # Z-score
    z_score = (rate_b - rate_a) / se

    # P-value (two-tailed)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))

    # Effect size (Cohen's h)
    effect_size = 2 * (math.asin(math.sqrt(rate_b)) - math.asin(math.sqrt(rate_a)))

    # Determine significance at 95% confidence
    significant = p_value < 0.05

    # Determine winner
    if significant:
        winner = "B" if rate_b > rate_a else "A"
    else:
        winner = None

    confidence_level = (1 - p_value) * 100 if p_value else 0

    return StatisticalResult(
        significant=significant,
        confidence_level=confidence_level,
        winner=winner,
        p_value=p_value,
        effect_size=abs(effect_size),
    )


@router.post("/test/start")
async def start_ab_test(
    request: ABTestCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Initializes an A/B test for a piece of content with proper statistical setup.
    """
    test = ABTestDB(
        content_id=request.content_id,
        user_id=current_user.id,
        variant_a_title=request.variant_a_title,
        variant_b_title=request.variant_b_title,
        variant_a_description=request.variant_a_description,
        variant_b_description=request.variant_b_description,
        target_metric=request.target_metric,
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return success_response(
        data={
            "test_id": test.id,
            "status": "started",
            "variant_a": request.variant_a_title,
            "variant_b": request.variant_b_title,
            "target_metric": request.target_metric,
            "message": "A/B test initialized. Start recording events to collect data.",
        }
    )


@router.get("/test/{test_id}")
async def get_test_results(
    test_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed test results with statistical analysis"""
    stmt = select(ABTestDB).where(
        ABTestDB.id == test_id,
        (ABTestDB.user_id == current_user.id) | (current_user.role == UserRole.ADMIN),
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get metric based on target
    if test.target_metric == "clicks":
        views_a, views_b = test.variant_a_click_count, test.variant_b_click_count
        conv_a, conv_b = test.variant_a_click_count, test.variant_b_click_count
    elif test.target_metric == "conversions":
        views_a, views_b = test.variant_a_view_count, test.variant_b_view_count
        conv_a, conv_b = (
            test.variant_a_conversion_count,
            test.variant_b_conversion_count,
        )
    else:  # views
        views_a, views_b = (test.variant_a_view_count or 0), (test.variant_b_view_count or 0)
        conv_a, conv_b = (test.variant_a_view_count or 0), (test.variant_b_view_count or 0)

    total_views = views_a + views_b

    if total_views == 0:
        return {
            "test_id": test.id,
            "content_id": test.content_id,
            "status": test.status,
            "variant_a": {
                "title": test.variant_a_title,
                "view_count": 0,
                "click_count": 0,
                "conversion_count": 0,
            },
            "variant_b": {
                "title": test.variant_b_title,
                "view_count": 0,
                "click_count": 0,
                "conversion_count": 0,
            },
            "statistics": {"significant": False, "message": "No data collected yet"},
        }

    # Calculate statistics with proper conversions
    stats = calculate_statistics(views_a, views_b, conv_a, conv_b)

    return success_response(
        data={
            "test_id": test.id,
            "content_id": test.content_id,
            "status": test.status.value if hasattr(test.status, "value") else test.status,
            "variant_a": {
                "title": test.variant_a_title,
                "description": test.variant_a_description,
                "view_count": test.variant_a_view_count,
                "click_count": test.variant_a_click_count,
                "conversion_count": test.variant_a_conversion_count,
                "conversion_rate": test.variant_a_conversion_count
                / test.variant_a_view_count
                if test.variant_a_view_count > 0
                else 0,
            },
            "variant_b": {
                "title": test.variant_b_title,
                "description": test.variant_b_description,
                "view_count": test.variant_b_view_count,
                "click_count": test.variant_b_click_count,
                "conversion_count": test.variant_b_conversion_count,
                "conversion_rate": test.variant_b_conversion_count
                / test.variant_b_view_count
                if test.variant_b_view_count > 0
                else 0,
            },
            "statistics": {
                "significant": stats.significant,
                "confidence_level": round(stats.confidence_level, 2),
                "winner": stats.winner,
                "p_value": round(stats.p_value, 4) if stats.p_value else None,
                "effect_size": round(stats.effect_size, 4),
                "interpretation": _interpret_effect_size(stats.effect_size),
            },
            "created_at": test.created_at.isoformat() if test.created_at else None,
            "completed_at": test.completed_at.isoformat()
            if test.completed_at
            else None,
            "winner_variant": test.winner_variant,
        }
    )


def _interpret_effect_size(effect_size: float) -> str:
    """Interpret Cohen's h effect size"""
    abs_effect = abs(effect_size)
    if abs_effect < 0.2:
        return "negligible"
    elif abs_effect < 0.5:
        return "small"
    elif abs_effect < 0.8:
        return "medium"
    else:
        return "large"


@router.post("/record/{test_id}/event")
async def record_variant_event(
    test_id: str, event: ABTestVariantEvent, db=Depends(get_db)
):
    """
    Records a view, click, or conversion event for a specific variant.
    """
    stmt = select(ABTestDB).where(ABTestDB.id == test_id)
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.winner_variant or test.status == ABTestStatus.COMPLETED:
        return {"status": "test_completed", "winner": test.winner_variant}

    variant = event.variant.upper()
    if variant not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Variant must be 'A' or 'B'")

    if event.event_type == "view":
        if variant == "A":
            test.variant_a_view_count += 1
        else:
            test.variant_b_view_count += 1
    elif event.event_type == "click":
        if variant == "A":
            test.variant_a_click_count += 1
        else:
            test.variant_b_click_count += 1
    elif event.event_type == "conversion":
        if variant == "A":
            test.variant_a_conversion_count += 1
        else:
            test.variant_b_conversion_count += 1

    await db.commit()
    return success_response(
        data={"status": "recorded", "variant": variant, "event_type": event.event_type}
    )


@router.post("/test/{test_id}/determine-winner")
async def determine_winner(
    test_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Determines and records the winning variant based on proper statistical significance.
    """
    stmt = select(ABTestDB).where(
        ABTestDB.id == test_id,
        (ABTestDB.user_id == current_user.id) | (current_user.role == UserRole.ADMIN),
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get the right metrics based on target
    if test.target_metric == "clicks":
        views_a, views_b = test.variant_a_click_count, test.variant_b_click_count
        conv_a, conv_b = test.variant_a_click_count, test.variant_b_click_count
    elif test.target_metric == "conversions":
        views_a, views_b = test.variant_a_view_count, test.variant_b_view_count
        conv_a, conv_b = (
            test.variant_a_conversion_count,
            test.variant_b_conversion_count,
        )
    else:
        views_a, views_b = test.variant_a_view_count, test.variant_b_view_count
        conv_a, conv_b = test.variant_a_view_count, test.variant_b_view_count

    total_views = views_a + views_b

    if total_views < 30:
        return {
            "status": "insufficient_data",
            "message": f"Need at least 30 total {test.target_metric} for statistical significance",
            "total_views": total_views,
            "minimum_required": 30,
        }

    # Use proper statistical test
    stats = calculate_statistics(views_a, views_b, conv_a, conv_b)

    if stats.significant and stats.winner:
        test.winner_variant = stats.winner
        test.confidence_level = stats.confidence_level
        test.p_value = stats.p_value
        test.status = ABTestStatus.COMPLETED
        test.completed_at = datetime.now(timezone.utc)
        winner_title = (
            test.variant_a_title if stats.winner == "A" else test.variant_b_title
        )
        await db.commit()

        return success_response(
            data={
                "status": "winner_determined",
                "winner": stats.winner,
                "winner_title": winner_title,
                "confidence": f"{stats.confidence_level:.1f}%",
                "p_value": round(stats.p_value, 4),
                "effect_size": round(stats.effect_size, 4),
                "interpretation": _interpret_effect_size(stats.effect_size),
                f"{test.target_metric}_a": views_a,
                f"{test.target_metric}_b": views_b,
            }
        )
    else:
        return success_response(
            data={
                "status": "inconclusive",
                "message": "Not enough statistical evidence to declare a winner",
                "p_value": round(stats.p_value, 4) if stats.p_value else None,
                "confidence_level": f"{stats.confidence_level:.1f}%",
                f"{test.target_metric}_a": views_a,
                f"{test.target_metric}_b": views_b,
                "recommendation": "Continue collecting data or consider that variants may have similar performance",
            }
        )


@router.get("/test/{test_id}/recommend-variant")
async def recommend_variant(test_id: str, db=Depends(get_db)):
    """
    Returns which variant should be shown based on statistical analysis.
    """
    stmt = select(ABTestDB).where(ABTestDB.id == test_id)
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.winner_variant:
        return success_response(
            data={
                "recommended_variant": test.winner_variant,
                "reason": "statistical_winner",
                "confidence": "100%",
            }
        )

    total_views = test.variant_a_view_count + test.variant_b_view_count

    if total_views < 10:
        return success_response(
            data={
                "recommended_variant": "A"
                if test.variant_a_view_count <= test.variant_b_view_count
                else "B",
                "reason": "initial_balance",
                "message": "Not enough data for recommendation",
            }
        )

    # Use statistical result
    stats = calculate_statistics(
        test.variant_a_view_count,
        test.variant_b_view_count,
        test.variant_a_view_count,
        test.variant_b_view_count,
    )

    if stats.significant and stats.winner:
        return success_response(
            data={
                "recommended_variant": stats.winner,
                "reason": "statistically_significant",
                "confidence": f"{stats.confidence_level:.1f}%",
            }
        )

    # Fall back to balanced approach
    if test.variant_a_view_count <= test.variant_b_view_count:
        return success_response(data={"recommended_variant": "A", "reason": "balanced"})
    else:
        return success_response(data={"recommended_variant": "B", "reason": "balanced"})


@router.get("/tests/active")
async def get_active_tests(
    db=Depends(get_db), current_user=Depends(get_current_user)
):
    """Get all active A/B tests with statistics"""
    stmt = select(ABTestDB).where(ABTestDB.status == ABTestStatus.ACTIVE)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(ABTestDB.user_id == current_user.id)

    stmt = stmt.order_by(ABTestDB.created_at.desc())
    result = await db.execute(stmt)
    tests = result.scalars().all()

    return success_response(
        data={
            "active_tests": [
                {
                    "id": t.id,
                    "content_id": t.content_id,
                    "status": t.status.value if hasattr(t.status, 'value') else t.status,
                    "variant_a_title": t.variant_a_title,
                    "variant_b_title": t.variant_b_title,
                    "variant_a_view_count": t.variant_a_view_count or 0,
                    "variant_b_view_count": t.variant_b_view_count or 0,
                    "target_metric": t.target_metric,
                    "total_events": (t.variant_a_view_count or 0) + (t.variant_b_view_count or 0),
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tests
            ],
            "count": len(tests),
        }
    )


@router.get("/tests/completed")
async def get_completed_tests(
    db=Depends(get_db), current_user=Depends(get_current_user)
):
    """Get all completed A/B tests with winner analysis"""
    stmt = select(ABTestDB).where(ABTestDB.status == ABTestStatus.COMPLETED)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(ABTestDB.user_id == current_user.id)

    stmt = stmt.order_by(ABTestDB.completed_at.desc()).limit(20)
    result = await db.execute(stmt)
    tests = result.scalars().all()

    return success_response(
        data={
            "completed_tests": [
                {
                    "id": t.id,
                    "content_id": t.content_id,
                    "variant_a_title": t.variant_a_title,
                    "variant_b_title": t.variant_b_title,
                    "variant_a_view_count": t.variant_a_view_count,
                    "variant_b_view_count": t.variant_b_view_count,
                    "winner_variant": t.winner_variant,
                    "confidence_level": t.confidence_level,
                    "p_value": t.p_value,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "completed_at": t.completed_at.isoformat()
                    if t.completed_at
                    else None,
                }
                for t in tests
            ],
            "count": len(tests),
        }
    )


@router.delete("/test/{test_id}")
async def delete_test(
    test_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete an A/B test (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    stmt = select(ABTestDB).where(ABTestDB.id == test_id)
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    await db.delete(test)
    await db.commit()

    return success_response(data={"status": "deleted", "test_id": test_id})


@router.post("/evolution/{parent_job_id}")
async def trigger_flywheel_evolution(
    parent_job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Triggers the 'Find Winners Fast' Flywheel Evolution (Standard 4.1).
    Calculates weighted engagement scores, kills losers, and prepares winner for iteration.
    """
    from src.services.optimization.flywheel import base_flywheel_service
    
    winner = await base_flywheel_service.run_evolution_cycle(parent_job_id)
    
    if not winner:
        raise HTTPException(status_code=404, detail="No variants found for this parent job")
    
    return success_response(data={
        "status": "evolution_complete",
        "winner_id": winner["job_id"],
        "winner_score": round(winner["score"], 4),
        "winner_metrics": winner["metrics"],
        "evolution_strategy": "Killed bottom 70%, Scaling top variant."
    })


@router.post("/evolution/global")
async def trigger_global_evolution(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Triggers a platform-wide Flywheel Evolution.
    Prunes underperforming strategies across all active niches.
    """
    from src.services.optimization.flywheel import base_flywheel_service
    
    summary = await base_flywheel_service.trigger_global_evolution()
    
    return success_response(data={
        "status": "global_evolution_initiated",
        "summary": summary,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@router.post("/variants/create/{parent_job_id}")
async def create_variant_ab_test(
    parent_job_id: str,
    request: VariantCreateRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Creates an A/B test from a multi-variant video generation parent job.

    Scans VideoJobDB for child jobs whose `job_metadata.parent_id` matches
    the given parent_job_id, extracts their output paths, and creates an
    ABTestDB entry linking both variants. Stores variant job info in
    metadata_json so the publish endpoint can look up the right video files.

    Flow: POST /video/generate {num_variants: 2}
          → returns parent_id + task_ids[0..N]
          → wait for jobs to complete
          → POST /ab-testing/variants/create/{parent_id} {titles}
          → POST /ab-testing/variants/publish/{test_id} {platform}
    """
    # 1. Locate child variant jobs
    # Variant jobs store parent_id in job_metadata JSON
    # Use SQLAlchemy JSON accessor; cast to String for cross-backend compatibility
    from sqlalchemy import cast, String as SA_String

    stmt = select(VideoJobDB).where(
        cast(VideoJobDB.job_metadata["parent_id"], SA_String) == parent_job_id,
    ).order_by(VideoJobDB.created_at.asc())
    
    result = await db.execute(stmt)
    variant_jobs = result.scalars().all()
    
    # Sort by variant_index from metadata if available
    variant_jobs.sort(key=lambda j: (j.job_metadata or {}).get("variant_index", 0))

    if not variant_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"No variant jobs found for parent {parent_job_id}. "
                   "Has the multi-variant generation completed?"
        )

    # 2. Verify ownership
    for job in variant_jobs:
        if job.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Not authorized — some variant jobs belong to another user"
            )

    # 3. Extract variant info
    variant_a_job = variant_jobs[0] if len(variant_jobs) > 0 else None
    variant_b_job = variant_jobs[1] if len(variant_jobs) > 1 else None

    variant_a_output = getattr(variant_a_job, "output_path", None) if variant_a_job else None
    variant_b_output = getattr(variant_b_job, "output_path", None) if variant_b_job else None

    # 4. Check completion
    # Safely extract status values (variant_b_job may be None)
    status_val_a = None
    status_val_b = None
    if variant_a_job:
        status_val_a = variant_a_job.status.value if hasattr(variant_a_job.status, 'value') else variant_a_job.status
    if variant_b_job:
        status_val_b = variant_b_job.status.value if hasattr(variant_b_job.status, 'value') else variant_b_job.status
    
    if not variant_a_job or status_val_a != SystemJobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Variant A job is not yet completed")
    
    if not variant_a_output:
        raise HTTPException(status_code=400, detail="Variant A has no output path")

    # 5. Create the ABTestDB entry
    test = ABTestDB(
        content_id=parent_job_id,
        user_id=current_user.id,
        variant_a_title=request.variant_a_title,
        variant_b_title=request.variant_b_title,
        variant_a_description=request.variant_a_description,
        variant_b_description=request.variant_b_description,
        target_metric=request.target_metric or "views",
        status=ABTestStatus.ACTIVE,
        metadata_json={
            "parent_job_id": parent_job_id,
            "variant_a_job_id": variant_a_job.id if variant_a_job else None,
            "variant_b_job_id": variant_b_job.id if variant_b_job else None,
            "variant_a_output_path": variant_a_output,
            "variant_b_output_path": variant_b_output,
        },
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    logger.info(
        f"[A/B Testing] Created variant test {test.id} from parent {parent_job_id}: "
        f"A='{request.variant_a_title}' B='{request.variant_b_title}'"
    )

    return success_response(
        data={
            "test_id": test.id,
            "parent_job_id": parent_job_id,
            "variant_a": {
                "title": request.variant_a_title,
                "job_id": variant_a_job.id if variant_a_job else None,
                "output_path": variant_a_output,
                "completed": status_val_a == SystemJobStatus.COMPLETED.value if status_val_a else False,
            },
            "variant_b": {
                "title": request.variant_b_title,
                "job_id": variant_b_job.id if variant_b_job else None,
                "output_path": variant_b_output,
                "completed": status_val_b == SystemJobStatus.COMPLETED.value if status_val_b else False,
            },
            "total_variants": len(variant_jobs),
            "message": f"A/B Test created with {len(variant_jobs)} variants. "
                       "Use POST /ab-testing/variants/publish/{test_id} to publish.",
        }
    )


@router.post("/variants/publish/{test_id}")
async def publish_variant_ab_test(
    test_id: str,
    request: VariantPublishRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Publishes both variants in an A/B test as separate platform posts,
    recording each variant's PublishedContentDB record for separate metric attribution.

    Flow:
      1. Looks up the ABTestDB to get variant metadata + output paths
      2. Publishes variant A with title A
      3. Publishes variant B with title B
      4. Returns both publish results with per-variant platform URLs

    Relies on existing publisher services (YouTube, TikTok, etc.) for
    actual platform upload. Skips variants without a completed output path.
    """
    # 1. Look up the test
    stmt = select(ABTestDB).where(
        ABTestDB.id == test_id,
        (ABTestDB.user_id == current_user.id) | (current_user.role == UserRole.ADMIN),
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="A/B Test not found")

    # 2. Extract variant info from metadata_json
    meta = test.metadata_json or {}
    variant_a_path = meta.get("variant_a_output_path")
    variant_b_path = meta.get("variant_b_output_path")

    # Allow fallback: if test was created via publish with variant_b_title,
    # both variants share the same video path (title/description A/B test)
    if not variant_a_path and not variant_b_path:
        # Try to look up from child published content records
        published_stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == test.content_id
        )
        pub_result = await db.execute(published_stmt)
        published = pub_result.scalar_one_or_none()
        if published:
            variant_a_path = published.source_uri
            variant_b_path = published.source_uri

    if not variant_a_path:
        raise HTTPException(
            status_code=400,
            detail="No video path found for variant A. "
                   "Create the test via POST /ab-testing/variants/create/{parent_job_id} first."
        )

    # 3. Publish each variant
    from src.api.routes.publish.common import (
        SUPPORTED_PLATFORMS,
        PLATFORM_NAME_TO_KEY,
    )
    from src.services.optimization.service import base_optimization_service
    from src.services.optimization.auth import token_manager
    from src.services.optimization.youtube_publisher import base_youtube_service

    platform_lower = request.platform.lower()
    platform_key = PLATFORM_NAME_TO_KEY.get(platform_lower, platform_lower)

    if platform_key not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Platform '{request.platform}' not supported. "
                   f"Available: {', '.join(SUPPORTED_PLATFORMS.keys())}",
        )

    # Check authentication
    has_auth = await token_manager.get_token(platform_key, user_id=current_user.id) is not None
    if not has_auth:
        raise HTTPException(
            status_code=401,
            detail=f"Platform '{platform_key}' not authenticated. Please authenticate first.",
        )

    variant_results = []

    for variant_label, variant_title, variant_desc, video_path in [
        ("A", test.variant_a_title, test.variant_a_description, variant_a_path),
        ("B", test.variant_b_title, test.variant_b_description, variant_b_path or variant_a_path),
    ]:
        if not video_path:
            variant_results.append({
                "variant": variant_label,
                "status": "skipped",
                "reason": "No video path available",
            })
            continue

        try:
            # Generate platform-optimized metadata for this variant
            content_id = f"{test_id}_{variant_label}_{datetime.now(timezone.utc).timestamp()}"
            metadata = await base_optimization_service.generate_viral_package(
                content_id, request.niche, request.platform
            )
            # Override title with variant-specific title
            metadata.title = variant_title or metadata.title

            # Upload to platform
            url = None
            if platform_key == "youtube":
                url = await base_youtube_service.upload_video(
                    video_path, metadata, user_id=current_user.id,
                    account_id=request.account_id,
                )
            elif platform_key == "tiktok":
                from src.services.optimization.tiktok_publisher import base_tiktok_service
                url = await base_tiktok_service.upload_video(
                    video_path, metadata, user_id=current_user.id,
                    account_id=request.account_id,
                )
            elif platform_key == "instagram":
                from src.services.optimization.instagram_publisher import base_instagram_service
                url = await base_instagram_service.upload_video(
                    video_path, metadata, user_id=current_user.id,
                    account_id=request.account_id,
                )
            elif platform_key == "facebook":
                from src.services.optimization.facebook_publisher import base_facebook_service
                url = await base_facebook_service.upload_video(
                    video_path, metadata, user_id=current_user.id,
                    account_id=request.account_id,
                )
            elif platform_key == "x":
                from src.services.optimization.x_publisher import base_x_service
                url = await base_x_service.upload_video(
                    video_path, metadata, user_id=current_user.id,
                    account_id=request.account_id,
                )
            elif platform_key == "linkedin":
                from src.services.optimization.linkedin_publisher import base_linkedin_service
                url = await base_linkedin_service.upload_video(
                    video_path, metadata, user_id=current_user.id,
                    account_id=request.account_id,
                )

            # Record PublishedContentDB per variant
            if url:
                published = PublishedContentDB(
                    title=variant_title or f"Variant {variant_label}",
                    platform=request.platform,
                    status=ContentPublishStatus.PUBLISHED,
                    source_uri=url,
                    user_id=current_user.id,
                    niche=request.niche,
                )
                db.add(published)
                await db.commit()

                # Track which PublishedContentDB id maps to which variant
                meta = dict(test.metadata_json or {})
                variant_posts = meta.get("published_posts", {})
                variant_posts[variant_label] = str(published.id)
                meta["published_posts"] = variant_posts
                test.metadata_json = meta
                await db.commit()

                variant_results.append({
                    "variant": variant_label,
                    "title": variant_title,
                    "status": "published",
                    "url": url,
                    "published_content_id": str(published.id),
                })
            else:
                variant_results.append({
                    "variant": variant_label,
                    "title": variant_title,
                    "status": "failed",
                    "reason": "Platform returned no URL",
                })

        except Exception as e:
            logger.exception(f"[A/B Test Publish] Variant {variant_label} failed: {e}")
            variant_results.append({
                "variant": variant_label,
                "title": variant_title,
                "status": "error",
                "reason": str(e),
            })

    # 4. Summary
    published_count = sum(1 for r in variant_results if r["status"] == "published")
    failed_count = sum(1 for r in variant_results if r["status"] in ("error", "failed", "skipped"))

    return success_response(
        data={
            "test_id": test_id,
            "platform": request.platform,
            "variants": variant_results,
            "summary": {
                "published": published_count,
                "failed": failed_count,
                "total": len(variant_results),
            },
            "statistics_url": f"/ab-testing/test/{test_id}",
            "message": f"Published {published_count}/{len(variant_results)} variants. "
                       "Use GET /ab-testing/test/{test_id} to track engagement deltas.",
        }
    )

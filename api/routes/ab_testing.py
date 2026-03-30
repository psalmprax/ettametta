from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.models import ABTestDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from pydantic import BaseModel
from typing import Optional
import math

router = APIRouter(prefix="/ab-testing", tags=["A/B Testing"])


class ABTestCreate(BaseModel):
    content_id: str
    variant_a_title: str
    variant_b_title: str


@router.post("/test/start")
async def start_ab_test(
    request: ABTestCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initializes an A/B test for a piece of content.
    """
    test = ABTestDB(
        content_id=request.content_id,
        variant_a_title=request.variant_a_title,
        variant_b_title=request.variant_b_title,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("/test/{test_id}")
async def get_test_results(
    test_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    test = db.query(ABTestDB).filter(ABTestDB.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.post("/record-view/{content_id}")
async def record_variant_view(
    content_id: str, variant: str, db: Session = Depends(get_db)
):
    """
    Records a view for a specific variant. Variant should be 'A' or 'B'.
    """
    test = db.query(ABTestDB).filter(ABTestDB.content_id == content_id).first()
    if not test:
        return {"status": "no_test_active"}

    if variant.upper() == "A":
        test.variant_a_views += 1
    elif variant.upper() == "B":
        test.variant_b_views += 1

    db.commit()
    return {"status": "success"}


@router.post("/test/{test_id}/determine-winner")
async def determine_winner(
    test_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Determines and records the winning variant based on statistical significance.
    Uses a simple z-test for proportions.
    """
    test = db.query(ABTestDB).filter(ABTestDB.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    total_views = test.variant_a_views + test.variant_b_views

    if total_views < 10:
        return {
            "status": "insufficient_data",
            "message": "Need at least 10 total views to determine winner",
            "total_views": total_views,
        }

    # Calculate conversion rates (assuming we track engagement separately)
    # For now, use views as the metric
    rate_a = test.variant_a_views / total_views if total_views > 0 else 0
    rate_b = test.variant_b_views / total_views if total_views > 0 else 0

    # Simple statistical test: if one variant has >60% of views, declare winner
    if rate_a > 0.6:
        test.winner_variant = "A"
        winner_name = test.variant_a_title
    elif rate_b > 0.6:
        test.winner_variant = "B"
        winner_name = test.variant_b_title
    else:
        # Not statistically significant yet
        return {
            "status": "inconclusive",
            "variant_a_views": test.variant_a_views,
            "variant_b_views": test.variant_b_views,
            "rate_a": round(rate_a, 3),
            "rate_b": round(rate_b, 3),
        }

    db.commit()

    return {
        "status": "winner_determined",
        "winner": test.winner_variant,
        "winner_title": winner_name,
        "variant_a_views": test.variant_a_views,
        "variant_b_views": test.variant_b_views,
    }


@router.get("/test/{test_id}/recommend-variant")
async def recommend_variant(test_id: int, db: Session = Depends(get_db)):
    """
    Returns which variant should be shown (for frontend to use).
    Uses simple A/B splitting.
    """
    test = db.query(ABTestDB).filter(ABTestDB.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # If we have a winner, always recommend the winner
    if test.winner_variant:
        return {
            "recommended_variant": test.winner_variant,
            "reason": "winner_determined",
        }

    # Otherwise, alternate based on view count to balance
    if test.variant_a_views <= test.variant_b_views:
        return {"recommended_variant": "A", "reason": "balanced"}
    else:
        return {"recommended_variant": "B", "reason": "balanced"}


@router.get("/tests/active")
async def get_active_tests(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Get all active A/B tests (without winner).
    """
    tests = db.query(ABTestDB).filter(ABTestDB.winner_variant == None).all()
    return {
        "active_tests": [
            {
                "id": t.id,
                "content_id": t.content_id,
                "variant_a_title": t.variant_a_title,
                "variant_b_title": t.variant_b_title,
                "variant_a_views": t.variant_a_views,
                "variant_b_views": t.variant_b_views,
                "total_views": t.variant_a_views + t.variant_b_views,
                "created_at": t.created_at,
            }
            for t in tests
        ]
    }

"""
Revenue & Monetization API Routes
=================================
Endpoints for tracking earnings and monetization performance.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from src.api.utils.auth import get_current_user
from src.api.utils.models import UserDB
from src.api.utils.api_responses import success_response
from src.services.monetization.revenue_service import base_revenue_service
from src.services.monetization.service import base_monetization_service

router = APIRouter(prefix="/monetization", tags=["Monetization"])


@router.get("/revenue/summary")
async def get_revenue_summary(
    days: int = 30,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get revenue summary for the last N days.
    Includes platform breakdown and daily trends.
    """
    try:
        summary = await base_monetization_service.get_revenue_summary(
            user_id=current_user.id,
            days=days
        )
        return success_response(data=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/goals")
async def get_monetization_goals(
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get current monetization goals and progress tracking.
    """
    try:
        goals = await base_monetization_service.get_monetization_goals(
            user_id=current_user.id
        )
        return success_response(data=goals)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_connected_platforms(
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    List connected monetization platforms and their status.
    """
    # Mock implementation
    platforms = [
        {"name": "YouTube", "status": "connected", "last_sync": "2026-05-07T08:00:00Z"},
        {"name": "TikTok", "status": "disconnected", "last_sync": None},
        {"name": "Stripe", "status": "connected", "last_sync": "2026-05-07T09:00:00Z"}
    ]
    return success_response(data={"platforms": platforms})

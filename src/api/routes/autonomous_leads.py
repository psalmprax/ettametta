"""
Autonomous Lead Generation API Routes
=====================================
Endpoints for AI-driven lead discovery, qualification, and outreach.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from src.api.utils.auth import get_current_user
from src.api.utils.models import UserDB
from src.api.utils.api_responses import success_response
from src.services.monetization.autonomous_lead_gen import base_autonomous_lead_gen

router = APIRouter(prefix="/leads/autonomous", tags=["Autonomous Leads"])


class LeadDiscoveryRequest(BaseModel):
    niche: str
    sources: list[str] | None = None  # social, content, newsletter
    max_results: int = 50


@router.post("/discover")
async def discover_leads(
    request: LeadDiscoveryRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Discover qualified leads from multiple sources.
    Automatically scores and qualifies each lead based on engagement signals.
    """
    try:
        leads = await base_autonomous_lead_gen.discover_leads(
            niche=request.niche,
            sources=request.sources,
            max_results=request.max_results,
        )
        return success_response(data={
            "leads": [
                {
                    "email": lead.email,
                    "name": lead.name,
                    "source": lead.source,
                    "score": lead.score,
                    "tags": lead.tags,
                }
                for lead in leads
            ],
            "total": len(leads),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead discovery failed: {str(e)}")


class OutreachRequest(BaseModel):
    lead_emails: list[str]
    sequence_name: str
    templates: list[dict]  # [{subject, body}]
    interval_hours: int = 24
    max_attempts: int = 3


@router.post("/outreach")
async def launch_outreach(
    request: OutreachRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Launch automated email/SMS outreach sequence.
    Supports A/B testing of templates and tracks engagement.
    """
    try:
        result = await base_autonomous_lead_gen.launch_outreach_sequence(
            lead_emails=request.lead_emails,
            sequence_name=request.sequence_name,
            templates=request.templates,
            interval_hours=request.interval_hours,
            max_attempts=request.max_attempts,
        )
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outreach launch failed: {str(e)}")


class ABTestRequest(BaseModel):
    name: str
    variant_a: dict
    variant_b: dict
    traffic_split: float = 0.5


@router.post("/ab-test")
async def create_ab_test(
    request: ABTestRequest,
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Set up A/B test for email templates or CTAs.
    Automatically determines winner based on engagement metrics.
    """
    try:
        result = await base_autonomous_lead_gen.run_ab_test(
            name=request.name,
            variant_a=request.variant_a,
            variant_b=request.variant_b,
            traffic_split=request.traffic_split,
        )
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A/B test creation failed: {str(e)}")


@router.get("/report")
async def get_conversion_report(
    current_user: UserDB = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get comprehensive conversion report with funnel analytics.
    Shows total leads, qualified, engaged, converted, and conversion rates.
    """
    try:
        report = await base_autonomous_lead_gen.get_conversion_report()
        return success_response(data=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

"""
Video Lead Discovery Skill for OpenClaw
========================================
Finds trending videos, analyzes performance, and identifies repurposing opportunities.
"""

from typing import Any
import logging
from services.discovery.video_lead_scanner import video_lead_scanner

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class VideoLeadSkill(OpenClawBaseSkill):
    """
    OpenClaw skill for discovering and analyzing video content leads.
    """

    def __init__(self):
        super().__init__()
        self.name = "video_lead_discovery"
        self.description = "Discover trending videos, analyze performance, and find repurposing opportunities"

    async def execute(self, action: str = "discover_leads", **kwargs) -> str:
        """
        Execute video lead discovery operations.
        """
        try:
            if action == "discover_leads":
                res = await self._discover_leads(kwargs)
            elif action == "analyze_video":
                res = await self._analyze_video(kwargs)
            elif action == "find_templates":
                res = await self._find_templates(kwargs)
            else:
                return f"⚠️ Unknown action: {action}"
                
            if isinstance(res, dict) and res.get("success"):
                return res.get("message", "Success")
            return f"⚠️ Error: {res.get('error') if isinstance(res, dict) else str(res)}"
        except Exception as e:
            logger.error(f"Video lead skill error: {e}")
            return f"⚠️ Error: {str(e)}"

    async def _discover_leads(self, params: dict[str, Any]) -> dict[str, Any]:
        """Discover high-performing video leads"""
        niche = params.get("niche", "")
        if not niche:
            return {"success": False, "error": "Niche parameter required"}

        platforms = params.get("platforms", ["youtube"])
        min_viral_score = params.get("min_viral_score", 7.0)
        max_results = params.get("max_results", 10)

        leads = await video_lead_scanner.scan_for_video_leads(
            niche=niche,
            platforms=platforms,
            min_viral_score=min_viral_score,
            max_results=max_results,
        )

        # Convert VideoLead objects to dicts
        leads_data = []
        for lead in leads:
            leads_data.append(
                {
                    "video_id": lead.video_id,
                    "platform": lead.platform,
                    "title": lead.title,
                    "creator": lead.creator,
                    "url": lead.url,
                    "view_count": lead.view_count,
                    "like_count": lead.like_count,
                    "comment_count": lead.comment_count,
                    "engagement_score": lead.engagement_score,
                    "viral_score": lead.viral_score,
                    "content_type": lead.content_type,
                    "monetization_potential": lead.monetization_potential,
                }
            )

        return {
            "success": True,
            "action": "discover_leads",
            "niche": niche,
            "leads_found": len(leads_data),
            "leads": leads_data,
            "message": f"Found {len(leads_data)} video leads for '{niche}' niche",
        }

    async def _analyze_video(self, params: dict[str, Any]) -> dict[str, Any]:
        """Analyze a specific video's performance"""
        video_url = params.get("video_url", "")
        niche = params.get("niche", "")

        if not video_url:
            return {"success": False, "error": "video_url parameter required"}

        analysis = await video_lead_scanner.evaluate_video_performance(
            video_url=video_url, niche=niche
        )

        return {
            "success": True,
            "action": "analyze_video",
            "video_url": video_url,
            "niche": niche,
            "analysis": analysis,
        }

    async def _find_templates(self, params: dict[str, Any]) -> dict[str, Any]:
        """Find successful video templates in a niche"""
        niche = params.get("niche", "")
        template_type = params.get("template_type", "viral")
        min_samples = params.get("min_samples", 10)

        if not niche:
            return {"success": False, "error": "Niche parameter required"}

        templates = await video_lead_scanner.identify_video_templates(
            niche=niche, template_type=template_type, min_samples=min_samples
        )

        return {
            "success": True,
            "action": "find_templates",
            "niche": niche,
            "template_type": template_type,
            "templates": templates,
        }


# Skill instance
video_lead_skill = VideoLeadSkill()

"""
Video Lead Discovery Skill for OpenClaw
========================================
Finds trending videos, analyzes performance, and identifies repurposing opportunities.
"""

from typing import Any
import logging
from src.services.discovery.video_lead_scanner import video_lead_scanner

logger = logging.getLogger(__name__)


class VideoLeadSkill:
    """
    OpenClaw skill for discovering and analyzing video content leads.
    """

    def __init__(self):
        self.name = "video_lead_discovery"
        self.description = "Discover trending videos, analyze performance, and find repurposing opportunities"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute video lead discovery operations.

        Supported actions:
        - discover_leads: Find high-performing video content
        - analyze_video: Deep analysis of specific video
        - find_templates: Identify successful video patterns
        """
        action = params.get("action", "discover_leads")

        try:
            if action == "discover_leads":
                return await self._discover_leads(params)
            elif action == "analyze_video":
                return await self._analyze_video(params)
            elif action == "find_templates":
                return await self._find_templates(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "discover_leads",
                        "analyze_video",
                        "find_templates",
                    ],
                }
        except Exception as e:
            logger.error(f"Video lead skill error: {e}")
            return {"success": False, "error": str(e)}

    async def _discover_leads(self, params: dict[str, Any]) -> dict[str, Any]:
        """Discover high-performing video leads"""
        niche = params.get("niche", "")
        if not niche:
            return {"success": False, "error": "Niche parameter required"}

        platforms = params.get("platforms", ["youtube"])
        min_viral_score = params.get("min_viral_score", 7.0)
        max_results = params.get("max_results", 10)

        leads = await video_lead_scanner.discover_video_leads(
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
                    "views": lead.views,
                    "likes": lead.likes,
                    "comments": lead.comments,
                    "engagement_rate": lead.engagement_rate,
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

        analysis = await video_lead_scanner.analyze_video_performance(
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

        templates = await video_lead_scanner.find_video_templates(
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

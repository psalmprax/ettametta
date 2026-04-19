"""
Intelligent Video Workflow Skill for OpenClaw
=============================================

Enables agents to perform resilient multi-platform discovery and 
produce high-fidelity narrative videos autonomously.
"""

from typing import Any
import logging
import asyncio

from engines.intelligent_video_workflow import discover_multi_platform
from services.video_engine.tasks import narrative_fusion_task
from api.utils.database import async_session_factory
from api.utils.models import VideoJobDB

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class IntelligentWorkflowSkill(OpenClawBaseSkill):
    """
    OpenClaw skill for \"Tier 10\" intelligent discovery and narrative fusion.
    """

    def __init__(self):
        super().__init__()
        self.name = "intelligent_video_workflow"
        self.description = "Perform resilient multi-platform discovery and autonomous cinematic video fusion"

    async def execute(self, action: str = "intelligent_scan", niche: str = "Motivation", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        # Merge action and niche into params for internal methods
        params = {"action": action, "niche": niche, **kwargs}
        
        try:
            if action == "intelligent_scan":
                res = await self._intelligent_scan(params)
            elif action == "autonomous_fusion":
                res = await self._autonomous_fusion(params)
            else:
                return f"⚠️ Unknown action: {action}"
            
            if isinstance(res, dict) and res.get("success"):
                return res.get("message", "Success")
            return f"⚠️ Error: {res.get('error') if isinstance(res, dict) else str(res)}"
        except Exception as e:
            logger.error(f"Intelligent workflow skill error: {e}")
            return f"⚠️ Error: {str(e)}"

    async def _intelligent_scan(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform a resilient multi-platform scan"""
        niche = params.get("niche")
        max_per_platform = params.get("max_per_platform", 3)

        logger.info(f"OpenClaw: Triggering intelligent scan for '{niche}'")
        
        results = await discover_multi_platform(niche, max_per_platform=max_per_platform)
        
        return {
            "success": True,
            "action": "intelligent_scan",
            "niche": niche,
            "count": len(results),
            "candidates": results[:15], # Return top 15 to keep context manageable
            "message": f"Discovered {len(results)} viral candidates across multiple platforms for '{niche}'."
        }

    async def _autonomous_fusion(self, params: dict[str, Any]) -> dict[str, Any]:
        """Trigger an autonomous narrative fusion production job"""
        niche = params.get("niche")
        duration = params.get("duration", 60)
        user_id = params.get("user_id")

        logger.info(f"OpenClaw: Triggering autonomous fusion for '{niche}' ({duration}s)")

        # Dispatch Celery task
        # We use .delay() to make it non-blocking
        task = narrative_fusion_task.delay(
            niche=niche,
            duration_sec=duration,
            user_id=user_id
        )

        return {
            "success": True,
            "action": "autonomous_fusion",
            "task_id": task.id,
            "status": "Queued",
            "message": f"Autonomous narrative fusion task dispatched for '{niche}'. Task ID: {task.id}"
        }

# Skill instance
intelligent_workflow_skill = IntelligentWorkflowSkill()

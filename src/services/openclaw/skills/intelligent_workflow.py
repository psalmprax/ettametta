"""
Intelligent Video Workflow Skill for OpenClaw
=============================================

Enables agents to perform resilient multi-platform discovery and 
produce high-fidelity narrative videos autonomously.
"""

from typing import Dict, Any, List
import logging
import asyncio

from engines.intelligent_video_workflow import discover_multi_platform
from services.video_engine.tasks import narrative_fusion_task
from api.utils.database import async_session_factory
from api.utils.models import VideoJobDB

logger = logging.getLogger(__name__)

class IntelligentWorkflowSkill:
    """
    OpenClaw skill for "Tier 10" intelligent discovery and narrative fusion.
    """

    def __init__(self):
        self.name = "intelligent_video_workflow"
        self.description = "Perform resilient multi-platform discovery and autonomous cinematic video fusion"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute intelligent workflow actions.

        Supported actions:
        - intelligent_scan: Resilient multi-platform search with LLM query expansion
        - autonomous_fusion: Start a multi-clip narrative video production task

        Args:
            params: Parameters for the action
                - action: 'intelligent_scan' or 'autonomous_fusion'
                - niche: Target niche/topic
                - duration: Target duration in seconds (standard: 60)
        """
        action = params.get("action", "intelligent_scan")
        niche = params.get("niche")

        if not niche:
            return {"success": False, "error": "Niche parameter is required"}

        try:
            if action == "intelligent_scan":
                return await self._intelligent_scan(params)
            elif action == "autonomous_fusion":
                return await self._autonomous_fusion(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": ["intelligent_scan", "autonomous_fusion"],
                }
        except Exception as e:
            logger.error(f"Intelligent workflow skill error: {e}")
            return {"success": False, "error": str(e)}

    async def _intelligent_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
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

    async def _autonomous_fusion(self, params: Dict[str, Any]) -> Dict[str, Any]:
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

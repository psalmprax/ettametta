"""
Video Production Assistant Skill for OpenClaw
=============================================

Generates detailed editing instructions, templates, and guides for manual video production.
Complements the automated scene-based video production system.
"""

from typing import Any
import logging
import asyncio

from .base_skill import OpenClawBaseSkill
from services.video_engine.video_production_assistant import (
    base_video_production_assistant,
)
from services.discovery.video_lead_scanner import video_lead_scanner

logger = logging.getLogger(__name__)


class VideoProductionAssistantSkill(OpenClawBaseSkill):
    """
    OpenClaw skill for generating manual video editing instructions and templates.
    Provides professional editing guidance from automated production plans.
    """

    def __init__(self):
        super().__init__()
        self.name = "base_video_production_assistant"
        self.description = "Generate detailed editing instructions, templates, and guides for manual video production"

    async def execute(self, action: str = "assist", **kwargs) -> str:
        """
        Execute video production assistance actions.
        """
        # If action is 'assist', map to 'full_production_assistance' or similar
        act = action
        if act == "assist":
            act = "full_production_assistance"
            
        params = {"action": act, **kwargs}

        try:
            if act == "generate_instructions":
                res = await self._generate_editing_instructions(params)
            elif act == "create_premiere_template":
                res = await self._create_premiere_template(params)
            elif act == "create_capcut_template":
                res = await self._create_capcut_template(params)
            elif act == "generate_ffmpeg_commands":
                res = await self._generate_ffmpeg_commands(params)
            elif act == "create_resolve_script":
                res = await self._create_resolve_script(params)
            elif act == "full_production_assistance":
                res = await self._full_production_assistance(params)
            else:
                return f"⚠️ Unknown action: {act}"
            
            if isinstance(res, dict) and res.get("success"):
                return f"✅ **Production Assistance ({act})**\n{res.get('message', '')}"
            return f"⚠️ Error: {res.get('error') if isinstance(res, dict) else str(res)}"
        except Exception as e:
            logger.error(f"Video production assistant error: {e}")
            return f"⚠️ Error: {str(e)}"

    async def _generate_editing_instructions(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate comprehensive editing instructions"""
        production_plan = params.get("production_plan")

        if not production_plan:
            # Try to create production plan from scenes and niche
            scenes = params.get("scenes", [])
            niche = params.get("niche", "")

            if scenes and niche:
                production_plan = await video_lead_scanner.create_scene_based_video(
                    scenes=scenes,
                    niche=niche,
                    target_duration=params.get("target_duration", 60),
                )
            else:
                return {
                    "success": False,
                    "error": "Either production_plan or (scenes + niche) required",
                }

        instructions = base_video_production_assistant.generate_editing_instructions(
            production_plan
        )

        return {
            "success": True,
            "action": "generate_instructions",
            "instructions": instructions,
            "niche": production_plan.get("niche", "Unknown"),
            "scene_count": len(production_plan.get("scene_videos", {})),
            "estimated_duration": production_plan.get("estimated_duration", 0),
            "message": f"Generated comprehensive editing instructions for {len(production_plan.get('scene_videos', {}))} scenes",
        }

    async def _create_premiere_template(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create Adobe Premiere project template"""
        production_plan = params.get("production_plan")

        if not production_plan:
            return {"success": False, "error": "production_plan parameter required"}

        template = base_video_production_assistant.create_premiere_template(
            production_plan
        )

        return {
            "success": True,
            "action": "create_premiere_template",
            "template": template,
            "format": "Adobe Premiere Pro project structure",
            "scene_count": len(production_plan.get("scene_videos", {})),
            "message": "Generated Adobe Premiere project template",
        }

    async def _create_capcut_template(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create CapCut project template"""
        production_plan = params.get("production_plan")

        if not production_plan:
            return {"success": False, "error": "production_plan parameter required"}

        template = base_video_production_assistant.create_capcut_template(
            production_plan
        )

        return {
            "success": True,
            "action": "create_capcut_template",
            "template": template,
            "format": "CapCut project structure",
            "scene_count": len(production_plan.get("scene_videos", {})),
            "message": "Generated CapCut project template",
        }

    async def _generate_ffmpeg_commands(self, params: dict[str, Any]) -> dict[str, Any]:
        """Generate FFmpeg command sequences"""
        production_plan = params.get("production_plan")

        if not production_plan:
            return {"success": False, "error": "production_plan parameter required"}

        commands = base_video_production_assistant.create_ffmpeg_commands(
            production_plan
        )

        return {
            "success": True,
            "action": "generate_ffmpeg_commands",
            "commands": commands,
            "command_count": len(commands),
            "scene_count": len(production_plan.get("scene_videos", {})),
            "message": f"Generated {len(commands)} FFmpeg commands for video processing",
        }

    async def _create_resolve_script(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create DaVinci Resolve automation script"""
        production_plan = params.get("production_plan")

        if not production_plan:
            return {"success": False, "error": "production_plan parameter required"}

        script = base_video_production_assistant.generate_davinci_resolve_script(
            production_plan
        )

        return {
            "success": True,
            "action": "create_resolve_script",
            "script": script,
            "format": "DaVinci Resolve Lua script",
            "scene_count": len(production_plan.get("scene_videos", {})),
            "message": "Generated DaVinci Resolve automation script",
        }

    async def _full_production_assistance(
        self, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Provide complete production assistance package"""
        production_plan = params.get("production_plan")

        if not production_plan:
            return {"success": False, "error": "production_plan parameter required"}

        # Generate all assistance materials
        instructions = base_video_production_assistant.generate_editing_instructions(
            production_plan
        )
        premiere_template = base_video_production_assistant.create_premiere_template(
            production_plan
        )
        capcut_template = base_video_production_assistant.create_capcut_template(
            production_plan
        )
        ffmpeg_commands = base_video_production_assistant.create_ffmpeg_commands(
            production_plan
        )
        resolve_script = (
            base_video_production_assistant.generate_davinci_resolve_script(
                production_plan
            )
        )

        return {
            "success": True,
            "action": "full_production_assistance",
            "package": {
                "editing_instructions": instructions,
                "premiere_template": premiere_template,
                "capcut_template": capcut_template,
                "ffmpeg_commands": ffmpeg_commands,
                "resolve_script": resolve_script,
            },
            "niche": production_plan.get("niche", "Unknown"),
            "scene_count": len(production_plan.get("scene_videos", {})),
            "estimated_duration": production_plan.get("estimated_duration", 0),
            "quality_score": production_plan.get("quality_score", 0),
            "message": "Complete production assistance package generated",
        }


# Skill instance
base_video_production_assistant_skill = VideoProductionAssistantSkill()

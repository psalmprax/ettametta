"""
Scene-Based Video Production Skill for OpenClaw
==============================================

Creates complete videos from scene descriptions with automatic video discovery,
fusion, and audio overlay for upload-ready content.
"""

from typing import Any
import logging

from src.services.video_engine.scene_orchestrator import base_scene_orchestrator_service

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class SceneBasedVideoSkill(OpenClawBaseSkill):
    """
    OpenClaw skill for producing complete videos from scene descriptions.
    Automatically finds relevant videos, fuses them, adds audio, and prepares for upload.
    """

    def __init__(self):
        super().__init__()
        self.name = "scene_based_video_production"
        self.description = "Create complete videos from scene descriptions with automatic video discovery, fusion, and audio overlay"

    async def execute(self, action: str = "produce_video", **kwargs) -> str:
        """
        Execute scene-based video production.
        """
        try:
            if action == "produce_video":
                res = await self._produce_complete_video(kwargs)
            elif action == "find_scene_videos":
                res = await self._find_scene_videos(kwargs)
            elif action == "create_production_plan":
                res = await self._create_production_plan(kwargs)
            else:
                return f"⚠️ Unknown action: {action}"
            
            if isinstance(res, dict) and res.get("success"):
                return res.get("message", "Success")
            return f"⚠️ Error: {res.get('error') if isinstance(res, dict) else str(res)}"
        except Exception as e:
            logger.exception(f"Scene-based video skill error: {e}")
            return f"⚠️ Error: {str(e)}"

    async def _produce_complete_video(self, params: dict[str, Any]) -> dict[str, Any]:
        """Produce a complete video from scene descriptions"""
        scenes = params.get("scenes", [])
        niche = params.get("niche", "")
        target_duration = params.get("target_duration", 60)
        audio_script = params.get("audio_script")
        output_filename = params.get("output_filename")

        if not scenes:
            return {"success": False, "error": "Scenes parameter is required"}

        if not niche:
            return {"success": False, "error": "Niche parameter is required"}

        logger.info(
            f"Producing scene-based video: {len(scenes)} scenes, niche='{niche}'"
        )

        # Produce the video
        result = await base_scene_orchestrator_service.produce_scene_based_video(
            scenes=scenes,
            niche=niche,
            target_duration=target_duration,
            audio_script=audio_script,
            output_filename=output_filename,
        )

        if result.get("success"):
            return {
                "success": True,
                "action": "produce_video",
                "video_path": result.get("video_path"),
                "duration": result.get("duration"),
                "file_size": result.get("file_size"),
                "quality_score": result.get("quality_score"),
                "scenes_used": result.get("scenes_used"),
                "videos_found": result.get("videos_found"),
                "platforms_used": result.get("platforms_used"),
                "upload_specs": result.get("upload_specs"),
                "monetization_plan": result.get("monetization_plan"),
                "processing_stats": result.get("processing_stats"),
                "message": f"Successfully produced {result.get('duration', 0)}s video with quality score {result.get('quality_score', 0):.1f}",
            }
        else:
            return {
                "success": False,
                "action": "produce_video",
                "error": result.get("error", "Unknown production error"),
                "niche": niche,
                "scenes_requested": len(scenes),
            }

    async def _find_scene_videos(self, params: dict[str, Any]) -> dict[str, Any]:
        """Find videos for specific scenes"""
        scenes = params.get("scenes", [])
        niche = params.get("niche", "")
        platforms = params.get("platforms", ["youtube"])
        quality_threshold = params.get("quality_threshold", 7)

        if not scenes:
            return {"success": False, "error": "Scenes parameter is required"}

        if not niche:
            return {"success": False, "error": "Niche parameter is required"}

        logger.info(f"Finding videos for {len(scenes)} scenes in '{niche}' niche")

        # Find videos for scenes
        scene_videos = (
            await base_scene_orchestrator_service.video_scanner.find_videos_for_scenes(
                scenes=scenes,
                niche=niche,
                platforms=platforms,
                quality_threshold=quality_threshold,
            )
        )

        total_videos_found = sum(len(videos) for videos in scene_videos.values())

        return {
            "success": True,
            "action": "find_scene_videos",
            "niche": niche,
            "scenes_analyzed": len(scenes),
            "total_videos_found": total_videos_found,
            "scene_videos": scene_videos,
            "platforms_used": platforms,
            "quality_threshold": quality_threshold,
            "message": f"Found {total_videos_found} videos across {len(scene_videos)} scenes",
        }

    async def _create_production_plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a production plan without executing video production"""
        scenes = params.get("scenes", [])
        niche = params.get("niche", "")
        target_duration = params.get("target_duration", 60)
        audio_script = params.get("audio_script")

        if not scenes:
            return {"success": False, "error": "Scenes parameter is required"}

        if not niche:
            return {"success": False, "error": "Niche parameter is required"}

        logger.info(
            f"Creating production plan for {len(scenes)} scenes in '{niche}' niche"
        )

        # Create production plan
        production_plan = (
            await base_scene_orchestrator_service.video_scanner.create_scene_based_video(
                scenes=scenes,
                niche=niche,
                target_duration=target_duration,
                audio_script=audio_script,
            )
        )

        if production_plan.get("production_ready"):
            return {
                "success": True,
                "action": "create_production_plan",
                "production_plan": production_plan,
                "niche": niche,
                "scenes_count": len(scenes),
                "estimated_duration": production_plan.get("estimated_duration", 0),
                "quality_score": production_plan.get("quality_score", 0),
                "videos_available": sum(
                    len(videos)
                    for videos in production_plan.get("scene_videos", {}).values()
                ),
                "message": f"Production plan created with quality score {production_plan.get('quality_score', 0):.1f}",
            }
        else:
            return {
                "success": False,
                "action": "create_production_plan",
                "error": "Unable to create viable production plan",
                "niche": niche,
                "scenes_count": len(scenes),
                "production_plan": production_plan,
            }


# Skill instance
scene_based_video_skill = SceneBasedVideoSkill()

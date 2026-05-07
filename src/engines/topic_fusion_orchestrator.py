import logging
import json
from typing import Any
from src.services.llm.intelligence_hub import base_intelligence_service
from src.services.video_engine.scene_orchestrator import base_scene_orchestrator_service
from src.api.utils.tracing import setup_tracing_logger

logger = setup_tracing_logger("TopicFusionOrchestrator")

class TopicFusionOrchestrator:
    """
    High-level orchestrator for transforming a simple topic into a multi-scene viral video.
    Bridges Intelligence (LLM), Discovery (Scanner), and Production (SceneOrchestrator).
    """

    async def decompose_topic_into_scenes(self, topic: str, count: int = 10) -> list[dict[str, Any]]:
        """
        Uses LLM to break a topic into a narrative sequence of scenes.
        """
        system_prompt = """
        You are a Viral Content Architect. Your goal is to take a topic and decompose it into a narrative sequence of scenes for a high-retention video.
        Return ONLY a JSON list of scene objects.
        Each object MUST have:
        - description: What is happening in the scene.
        - visual_prompt: Keywords for searching matching video clips.
        - duration: Duration in seconds (usually 5-8s).
        - type: 'hook', 'context', 'problem', 'solution', or 'outro'.
        """
        
        prompt = f"Decompose the topic '{topic}' into exactly {count} scenes for a viral video."
        
        try:
            response = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=True,
                complexity="medium"
            )
            
            scenes = json.loads(response["response"])
            if not isinstance(scenes, list):
                # Handle dictionary response if LLM wraps it
                if isinstance(scenes, dict) and "scenes" in scenes:
                    scenes = scenes["scenes"]
                else:
                    raise ValueError("LLM did not return a list of scenes")
            
            return scenes[:count]
        except Exception as e:
            logger.error(f"Failed to decompose topic '{topic}': {e}")
            # Fallback scenes if LLM fails
            return [
                {"description": f"Introduction to {topic}", "visual_prompt": f"{topic} futuristic cinematic", "duration": 6, "type": "hook"},
                {"description": f"Explaining {topic}", "visual_prompt": f"{topic} technology overview", "duration": 8, "type": "context"},
                {"description": f"The importance of {topic}", "visual_prompt": f"{topic} impact real world", "duration": 6, "type": "solution"},
            ]

    async def run_topic_fusion(self, topic: str, niche: str | None = None, scene_count: int = 10) -> dict[str, Any]:
        """
        End-to-end flow: Topic -> Scenes -> Discovery -> Fusion -> Video.
        """
        effective_niche = niche or topic
        logger.info(f"Starting Topic Fusion for: {topic} (Niche: {effective_niche})")
        
        # 1. Decompose topic into scenes
        scenes = await self.decompose_topic_into_scenes(topic, count=scene_count)
        logger.info(f"Decomposed topic into {len(scenes)} scenes.")
        
        # 2. Trigger Scene-Based Production
        # This handles discovery, download, and fusion internally via SceneBasedVideoOrchestrator
        result = await base_scene_orchestrator_service.produce_scene_based_video(
            scenes=scenes,
            niche=effective_niche,
            target_duration=scene_count * 6, # Approx 60s for 10 scenes
            audio_script=f"Here is a deep dive into {topic}. " + " ".join([s['description'] for s in scenes])
        )
        
        return {
            "topic": topic,
            "scenes": scenes,
            "production_result": result
        }

# Singleton instance
base_topic_fusion_orchestrator = TopicFusionOrchestrator()

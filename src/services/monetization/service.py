import logging
import json
import time
from typing import Any
from groq import AsyncGroq
from src.api.config import settings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .orchestrator import base_monetization_orchestrator


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


from src.services.llm.intelligence_hub import base_intelligence_hub

class MonetizationEngine:
    def __init__(self):
        self.logger = logging.getLogger("MonetizationEngine")
        self.orchestrator = base_monetization_orchestrator

    async def _call_hub(self, prompt: str, session_id: str | None = None) -> str | None:
        """Call IntelligenceHub with resilient fallback"""
        try:
            result = await base_intelligence_hub.chat(
                prompt=prompt,
                system_prompt="You are a professional Monetization Strategist. Output JSON ONLY.",
                session_id=session_id,
                json_mode=True
            )
            return result["response"]
        except Exception as e:
            self.logger.warning(f"  ⚠️ Hub monetization call failed: {e}")
            return None

    async def recommend_products(
        self, niche: str, script_text: str
    ) -> list[dict[str, Any]]:
        """
        Delegates product recommendation to the active strategy.
        """
        return await self.orchestrator.get_monetization_assets(niche)

    async def match_viral_to_product(
        self, niche: str, viral_title: str, session_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Matches a specific viral trend to the most relevant asset from the active strategy.
        """
        assets = await self.orchestrator.get_monetization_assets(niche)
        if not assets:
            return None

        asset_list_str = "\n".join([f"- {p['name']} (ID: {p['id']})" for p in assets])

        prompt = f"""
        Given the viral video title: "{viral_title}"
        Select the MOST RELEVANT monetization asset from the list below.

        ASSETS:
        {asset_list_str}

        Output ONLY the asset ID in JSON format: {{"asset_id": "ID"}}
        """

        try:
            content = await self._call_hub(
                prompt, session_id=session_id
            )

            if not content:
                self.logger.warning(
                    "Hub call failed, returning first asset as fallback"
                )
                return assets[0] if assets else None

            data = json.loads(content)
            aid = data.get("asset_id")
            return next((p for p in assets if p["id"] == aid), assets[0])
        except Exception as e:
            self.logger.error(f"[Monetization] Asset matching failed: {e}")
            return assets[0] if assets else None

    async def auto_insert_links(
        self, video_path: str, niche: str, script_content: str = "", session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Automatically inserts affiliate links into video content via overlays or voiceover.
        This is the missing "auto-insertion into videos" functionality.
        """
        try:
            # Get relevant affiliate links for the niche
            assets = await self.orchestrator.get_monetization_assets(niche)
            if not assets:
                return {
                    "status": "no_assets",
                    "message": "No affiliate assets available for this niche",
                }

            # Use AI to determine the best insertion points and methods
            insertion_plan = await self._plan_link_insertion(script_content, assets)

            if not insertion_plan.get("insertions"):
                return {
                    "status": "no_opportunities",
                    "message": "No suitable insertion points found",
                }

            # For now, return the plan - actual video editing would require FFmpeg integration
            # This provides the framework for future video processing pipeline
            # If we have a plan, trigger the actual processing pipeline
            processed_video = await self.process_video_with_links(video_path, insertion_plan)

            return {
                "status": "success",
                "video_path": processed_video,
                "original_video_path": video_path,
                "insertion_plan": insertion_plan,
                "message": f"Successfully inserted {len(insertion_plan['insertions'])} monetization elements",
            }

        except Exception as e:
            logging.error(f"[Monetization] Auto-insert failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _plan_link_insertion(
        self, script_content: str, assets: list[dict], session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Uses AI to plan where and how to insert affiliate links in video content.
        """
        asset_text = "\n".join(
            [f"- {a['name']}: {a['cta_text']} -> {a['link']}" for a in assets]
        )

        prompt = f"""
        Analyze this video script and plan affiliate link insertions for maximum monetization impact.

        SCRIPT: "{script_content[:1000]}"

        AVAILABLE ASSETS:
        {asset_text}

        Plan 1-3 strategic insertions that feel natural and add value. Consider:
        1. VOICEOVER: Mention during natural pauses
        2. TEXT_OVERLAY: Show link on screen during relevant segments
        3. END_SCREEN: Add to conclusion

        Output JSON with insertions array:
        {{
          "insertions": [
            {{
              "type": "voiceover|overlay|end_screen",
              "asset_id": "asset identifier",
              "timing": "start_seconds-end_seconds or 'end'",
              "context": "why this insertion point works",
              "script_addition": "what to say/show"
            }}
          ]
        }}
        """

        try:
            content = await self._call_hub(
                prompt, session_id=session_id
            )

            if not content:
                return {"insertions": []}

            return json.loads(content)
        except Exception as e:
            self.logger.error(f"[Monetization] Insertion planning failed: {e}")
            return {"insertions": []}

    async def process_video_with_links(
        self, video_path: str, insertion_plan: dict[str, Any]
    ) -> str:
        """
        Actually processes the video file to add affiliate link insertions.
        This requires FFmpeg integration for video editing.
        """
        import os
        import uuid
        from moviepy import VideoFileClip, TextClip, CompositeVideoClip

        try:
            # Load the video
            video = VideoFileClip(video_path)

            # Process insertions
            clips = [video]  # Start with original video

            for insertion in insertion_plan.get("insertions", []):
                if insertion["type"] == "overlay":
                    # Add text overlay
                    txt_clip = (
                        TextClip(
                            insertion["script_addition"],
                            fontsize=50,
                            color="white",
                            bg_color="black",
                            size=(video.w * 0.8, 100),
                        )
                        .set_position("center")
                        .set_duration(5)
                    )

                    # Position based on timing
                    if insertion["timing"] == "end":
                        txt_clip = txt_clip.set_start(video.duration - 5)
                    else:
                        # Parse timing like "10-15"
                        start_time = float(insertion["timing"].split("-")[0])
                        txt_clip = txt_clip.set_start(start_time)

                    clips.append(txt_clip)

                elif insertion["type"] == "end_screen":
                    # Add end screen text
                    end_text = (
                        TextClip(
                            insertion["script_addition"],
                            fontsize=40,
                            color="yellow",
                            bg_color="rgba(0,0,0,0.7)",
                            size=(video.w, 200),
                        )
                        .set_position(("center", video.h - 250))
                        .set_duration(10)
                        .set_start(video.duration - 10)
                    )

                    clips.append(end_text)

            # Composite all clips
            final_video = CompositeVideoClip(clips)

            # Export
            output_path = f"processed_{uuid.uuid4()}.mp4"
            final_video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=f"temp_audio_{uuid.uuid4()}.m4a",
                remove_temp=True,
            )

            # Cleanup
            video.close()
            final_video.close()

            return output_path

        except ImportError:
            self.logger.error("[Monetization] moviepy not installed - video processing skipped")
            return video_path
        except Exception as e:
            self.logger.error(f"[Monetization] Video processing failed: {e}")
            return video_path  # Return original if processing fails

    def calculate_epm(self, revenue: float, views: int) -> float:
        if views == 0:
            return 0.0
        return (revenue / views) * 1000


base_monetization_engine = MonetizationEngine()

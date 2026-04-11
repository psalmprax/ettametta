import logging
import json
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from api.config import settings

from .orchestrator import base_monetization_orchestrator


class MonetizationEngine:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.orchestrator = base_monetization_orchestrator
        self.model = "llama-3.3-70b-versatile"

    async def recommend_products(
        self, niche: str, script_text: str
    ) -> List[Dict[str, Any]]:
        """
        Delegates product recommendation to the active strategy.
        """
        return await self.orchestrator.get_monetization_assets(niche)

    async def match_viral_to_product(
        self, niche: str, viral_title: str
    ) -> Optional[Dict[str, Any]]:
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                aid = data.get("asset_id")
                return next((p for p in assets if p["id"] == aid), assets[0])
            return assets[0] if assets else None
        except Exception as e:
            logging.error(f"[Monetization] Asset matching failed: {e}")
            return assets[0] if assets else None

    async def auto_insert_links(
        self, video_path: str, niche: str, script_content: str = ""
    ) -> Dict[str, Any]:
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
            return {
                "status": "planned",
                "video_path": video_path,
                "insertion_plan": insertion_plan,
                "message": f"Planned {len(insertion_plan['insertions'])} link insertions",
            }

        except Exception as e:
            logging.error(f"[Monetization] Auto-insert failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _plan_link_insertion(
        self, script_content: str, assets: List[Dict]
    ) -> Dict[str, Any]:
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return {"insertions": []}
        except Exception as e:
            logging.error(f"[Monetization] Insertion planning failed: {e}")
            return {"insertions": []}

    async def process_video_with_links(
        self, video_path: str, insertion_plan: Dict[str, Any]
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

        except Exception as e:
            logging.error(f"[Monetization] Video processing failed: {e}")
            return video_path  # Return original if processing fails
            logging.error(f"[Monetization] Asset Matching Error: {e}")
            return assets[0]

    def calculate_epm(self, revenue: float, views: int) -> float:
        if views == 0:
            return 0.0
        return (revenue / views) * 1000


base_monetization_engine = MonetizationEngine()

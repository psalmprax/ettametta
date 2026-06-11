import logging
import json
from typing import Any
from src.api.config import settings

from .orchestrator import base_monetization_orchestrator_service
from src.services.llm.intelligence_hub import base_intelligence_service

class MonetizationEngine:
    def __init__(self):
        self.logger = logging.getLogger("MonetizationEngine")
        self.orchestrator = base_monetization_orchestrator_service

    async def _call_hub(self, prompt: str, session_id: str | None = None) -> str | None:
        """Call IntelligenceHub with resilient fallback"""
        try:
            result = await base_intelligence_service.chat(
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

        # Phase 14: support both ``link`` (DB) and ``url`` (orchestrator) field names.
        def _url(a: dict) -> str:
            return a.get("link") or a.get("url") or ""

        asset_list_str = "\n".join(
            [f"- {p['name']} (ID: {p['id']}) URL: {_url(p)}" for p in assets]
        )

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

    async def plan_monetization_strategy(
        self, niche: str, script_content: str = "", video_path: str = "", session_id: str | None = None
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
                    "video_path": None,
                    "insertion_plan": {"insertions": []}
                }

            # Use AI to determine the best insertion points and methods
            insertion_plan = await self._plan_link_insertion(script_content, assets)

            if not insertion_plan.get("insertions"):
                return {
                    "status": "no_opportunities",
                    "message": "No suitable insertion points found",
                    "video_path": None,
                    "insertion_plan": {"insertions": []}
                }

            # Trigger the actual processing pipeline
            processed_video = await self.process_video_with_links(video_path, insertion_plan)

            return {
                "status": "success",
                "video_path": processed_video,
                "original_video_path": video_path,
                "insertion_plan": insertion_plan,
                "message": f"Successfully inserted {len(insertion_plan['insertions'])} monetization elements",
            }

        except Exception as e:
            logging.exception(f"[Monetization] Auto-insert failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "video_path": None,
                "insertion_plan": {"insertions": []}
            }

    async def auto_insert_links(
        self, video_path: str, niche: str, script_content: str = ""
    ) -> dict[str, Any]:
        """Legacy alias for plan_monetization_strategy"""
        return await self.plan_monetization_strategy(niche, script_content, video_path)

    async def _plan_link_insertion(
        self, script_content: str, assets: list[dict], session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Uses AI to plan where and how to insert affiliate links in video content.

        Phase 14: rewrites every ``script_addition`` so the actual
        affiliate URL is embedded in the burned text. Without this,
        FFmpeg's ``drawtext`` would render the LLM's narrative text
        with no link visible to the viewer.
        """
        # Phase 14: support both ``link`` (DB) and ``url`` (orchestrator) field names.
        def _url(a: dict) -> str:
            return a.get("link") or a.get("url") or ""

        asset_text = "\n".join(
            [
                f"- {a.get('name', '?')}: {a.get('cta_text', 'Check it out')} -> {_url(a)}"
                for a in assets
            ]
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

            plan = json.loads(content)
        except Exception as e:
            self.logger.error(f"[Monetization] Insertion planning failed: {e}")
            return {"insertions": []}

        # Phase 14: rewrite script_addition so the URL is actually visible.
        # FFmpeg drawtext can't render clickable links, but the URL needs
        # to be readable so viewers can type it. Format:
        #   "<narrative> · <CTA>: <URL>"  (URL always last so it always renders)
        for insertion in plan.get("insertions", []):
            if insertion.get("type") not in ("overlay", "end_screen"):
                continue
            aid = insertion.get("asset_id")
            asset = next((a for a in assets if a.get("id") == aid), None)
            if not asset:
                continue
            url = _url(asset)
            if not url:
                continue
            cta = asset.get("cta_text") or "Check it out"
            llm_text = (insertion.get("script_addition") or "").strip()
            if url in llm_text:
                # LLM already included the URL; keep as-is
                insertion["script_addition"] = llm_text
            else:
                insertion["script_addition"] = (
                    f"{llm_text} \u00b7 {cta}: {url}" if llm_text else f"{cta}: {url}"
                )

        return plan

    async def process_video_with_links(
        self, video_path: str, insertion_plan: dict[str, Any]
    ) -> str:
        """
        Actually processes the video file to add affiliate link insertions.
        Uses FFmpegTransformer for robust processing.

        Phase 14: every successfully-burned insertion increments the
        linked ``AffiliateLinkDB.impression_count`` so the dashboard
        can rank links by reach. Best-effort — a DB failure does NOT
        invalidate the render.
        """
        from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service
        from src.api.utils.models import AffiliateLinkDB
        from src.api.utils.database import async_session_factory
        from sqlalchemy import update
        from datetime import datetime, timezone
        import os
        import uuid

        if not video_path or not os.path.exists(video_path):
            return video_path

        current_path = video_path
        burned_ids: list[str] = []

        try:
            for i, insertion in enumerate(insertion_plan.get("insertions", [])):
                if insertion["type"] in ("overlay", "end_screen"):
                    filename = f"monetized_{i}_{uuid.uuid4().hex[:8]}.mp4"
                    output_path = os.path.join(settings.STORAGE_OUTPUT_DIR, filename)

                    # Parse timing
                    start_time = 0.0
                    if insertion["timing"] != "end":
                        try:
                            start_time = float(insertion["timing"].split("-")[0])
                        except Exception:
                            pass
                    else:
                        start_time = 55.0  # Fallback for end of a 60s video

                    success = base_ffmpeg_service.draw_text_overlay(
                        current_path,
                        output_path,
                        insertion["script_addition"],
                        start_time=start_time,
                        duration=5.0,
                        position="bottom" if insertion["type"] == "end_screen" else "center",
                    )

                    if success:
                        # Cleanup intermediate if it's not the original
                        if current_path != video_path and os.path.exists(current_path):
                            os.remove(current_path)
                        current_path = output_path
                        aid = insertion.get("asset_id")
                        if aid:
                            burned_ids.append(aid)

            # Increment impression_count for each link that was burned.
            if burned_ids:
                try:
                    async with async_session_factory() as db:
                        await db.execute(
                            update(AffiliateLinkDB)
                            .where(AffiliateLinkDB.id.in_(burned_ids))
                            .values(
                                impression_count=AffiliateLinkDB.impression_count + 1,
                                last_impression_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            )
                        )
                        await db.commit()
                        self.logger.info(
                            f"[Monetization] Burned {len(burned_ids)} link(s) into "
                            f"{os.path.basename(current_path)}; impressions bumped."
                        )
                except Exception as imp_err:
                    self.logger.warning(
                        f"[Monetization] Failed to bump impression_count for "
                        f"{len(burned_ids)} link(s): {imp_err}"
                    )

            return current_path

        except Exception as e:
            self.logger.error(f"[Monetization] Video processing failed: {e}")
            return video_path

    def calculate_epm(self, revenue: float, views: int) -> float:
        if views == 0:
            return 0.0
        return (revenue / views) * 1000


base_monetization_service = MonetizationEngine()

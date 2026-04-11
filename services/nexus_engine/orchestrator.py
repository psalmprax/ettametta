import os
import logging
import asyncio
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from services.video_engine.processor import base_video_processor
from services.nexus_engine.audio_mixer import base_audio_mixer
from typing import List, Dict, Any, Optional


class NexusOrchestrator:
    def __init__(self, output_dir: str = "outputs/nexus"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def assemble_video(
        self,
        job_id: str,
        niche: str,
        script_segments: List[Any],
        voiceover_paths: List[str],
        visual_paths: List[str],
        music_path: Optional[str] = None,
        blueprint_id: str = "viral-reskin",
    ) -> str:
        """
        High-fidelity video assembly using Remotion React engine with node-level tracking.
        """
        from api.routes.ws import notify_nexus_job_update_sync
        from services.nexus_engine.blueprints import get_blueprint_by_id

        # Need to use async session here for get_blueprint_by_id
        from api.utils.database import async_session_factory
        async with async_session_factory() as db:
            blueprint = await get_blueprint_by_id(db, blueprint_id)
        
        logging.info(f"[Nexus] Starting {blueprint['name']} assembly for Job {job_id}")

        def update_node(node_type: str, status: str, progress: int):
            notify_nexus_job_update_sync({
                "id": str(job_id),
                "status": f"{node_type.upper()}_{status}",
                "current_node": node_type,
                "node_status": status,
                "progress": progress,
                "niche": niche,
            })

        try:
            # 1. Ingress Node
            update_node("ingress", "ACTIVE", 20)
            # HARDENED: Removed simulated network overhead sleep
            update_node("ingress", "COMPLETED", 30)

            # 2. Cognition Node
            update_node("cognition", "ACTIVE", 40)
            from services.video_engine.remotion_service import remotion_service
            import cv2 

            def get_frame_count(path: str) -> Optional[int]:
                if not os.path.exists(path):
                    return None
                try:
                    cap = cv2.VideoCapture(path)
                    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.release()
                    return count
                except Exception:
                    return None

            # Parallelize metadata extraction via threads to avoid blocking the event loop
            counts = await asyncio.gather(*[
                asyncio.to_thread(get_frame_count, v_path) for v_path in visual_paths
            ])
            
            remotion_clips = [
                {"url": v_path, "durationInFrames": count}
                for v_path, count in zip(visual_paths, counts) if count is not None
            ]
            
            update_node("cognition", "COMPLETED", 50)

            # 3. Synthesis Node
            update_node("synthesis", "ACTIVE", 60)
            
            # Detect CTAs for visual overlays
            cta_segment = next((s for s in script_segments if s.get("type") in ["engagement", "cta"]), None)
            cta_props = {}
            if cta_segment:
                cta_props = {
                    "showCtaOverlay": True,
                    "ctaType": cta_segment.get("type"),
                    "ctaText": cta_segment.get("text", "")[:50] # Keep it short for overlay
                }

            audio_url = voiceover_paths[0] if voiceover_paths else music_path
            props = {
                "title": niche.title(), # Hardened: Use real niche name
                "subtitle": "Analysis & Insights", # Less of a "template" than "Discover the Truth"
                "clips": remotion_clips,
                "audioUrl": audio_url,
                **cta_props
            }

            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            rendered_path = await remotion_service.render_video(
                composition_id="ViralClip", props=props, output_name=output_filename
            )
            update_node("synthesis", "COMPLETED", 90)

            # 4. Egress Node
            update_node("egress", "ACTIVE", 95)
            if rendered_path:
                update_node("egress", "COMPLETED", 100)
                return rendered_path
            else:
                raise Exception("Remotion render returned no path")

        except Exception as e:
            logging.error(f"[Nexus] Assembly Failed for Job {job_id}: {e}")
            notify_nexus_job_update_sync({
                "id": str(job_id),
                "status": "FAILED",
                "progress": 0,
                "error": str(e)
            })
            raise e


base_nexus_orchestrator = NexusOrchestrator()

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
        job_id: int,
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

        blueprint = get_blueprint_by_id(blueprint_id)
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
            await asyncio.sleep(1) # Simulated network/fetch overhead
            update_node("ingress", "COMPLETED", 30)

            # 2. Cognition Node
            update_node("cognition", "ACTIVE", 40)
            from services.video_engine.remotion_service import remotion_service
            import cv2 

            remotion_clips = []
            for v_path in visual_paths:
                if not os.path.exists(v_path):
                    continue
                cap = cv2.VideoCapture(v_path)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                remotion_clips.append({"url": v_path, "durationInFrames": frame_count})
            
            update_node("cognition", "COMPLETED", 50)

            # 3. Synthesis Node
            update_node("synthesis", "ACTIVE", 60)
            audio_url = voiceover_paths[0] if voiceover_paths else music_path
            props = {
                "title": f"{niche} Secrets",
                "subtitle": "Discover the Truth",
                "clips": remotion_clips,
                "audioUrl": audio_url,
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

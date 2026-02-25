import os
import logging
import asyncio
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
from services.video_engine.processor import base_video_processor
from services.nexus_engine.audio_mixer import base_audio_mixer
from typing import List, Dict, Any, Optional

class NexusOrchestrator:
    def __init__(self, output_dir: str = "outputs/nexus"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def assemble_video(self, job_id: int, niche: str, script_segments: List[Any], voiceover_paths: List[str], visual_paths: List[str], music_path: Optional[str] = None) -> str:
        """
        High-fidelity video assembly using Remotion React engine.
        Replaces legacy MoviePy for better stability and professional graphics.
        """
        logging.info(f"[Nexus] Starting Remotion assembly for Job {job_id}")
        
        try:
            from services.video_engine.remotion_service import remotion_service
            import cv2 # To get clip durations if not provided

            # 1. Prepare clips for Remotion
            # We need to calculate durationInFrames for each clip
            remotion_clips = []
            for v_path in visual_paths:
                if not os.path.exists(v_path):
                    continue
                
                # Get duration using cv2 (cheaper than moviepy for just metadata)
                cap = cv2.VideoCapture(v_path)
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                
                remotion_clips.append({
                    "url": v_path,
                    "durationInFrames": frame_count
                })

            # 2. Handle Audio
            # For MVP, we'll use the first voiceover or a merged track if we have one
            # Remotion handles background music mixing as well
            audio_url = voiceover_paths[0] if voiceover_paths else music_path

            # 3. Prepare Props
            props = {
                "title": f"{niche} Secrets",
                "subtitle": "Discover the Truth",
                "clips": remotion_clips,
                "audioUrl": audio_url
            }

            from api.routes.ws import notify_nexus_job_update_sync
            notify_nexus_job_update_sync({"id": str(job_id), "status": "RENDERING", "progress": 60, "niche": niche})

            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            rendered_path = await remotion_service.render_video(
                composition_id="ViralClip",
                props=props,
                output_name=output_filename
            )

            if rendered_path:
                notify_nexus_job_update_sync({"id": str(job_id), "status": "COMPLETED", "progress": 100, "niche": niche})
                return rendered_path
            else:
                raise Exception("Remotion render returned no path")

        except Exception as e:
            logging.error(f"[Nexus] Assembly Failed for Job {job_id}: {e}")
            raise e
        except Exception as e:
            logging.error(f"[Nexus] Assembly Failed for Job {job_id}: {e}")
            raise e

base_nexus_orchestrator = NexusOrchestrator()

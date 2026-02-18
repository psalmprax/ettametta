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
        Advanced synthesis of multiple assets into a high-quality video.
        """
        logging.info(f"[Nexus] Starting assembly for Job {job_id}")
        
        try:
            # 1. Load Visual Clips and match to durations
            clips = []
            if not visual_paths:
                 # Fallback to a placeholder black clip if no visuals provided
                 from moviepy import ColorClip
                 clips = [ColorClip(size=(1080, 1920), color=(0,0,0)).with_duration(5)]
            else:
                for v_path in visual_paths:
                    clip = VideoFileClip(v_path)
                    clips.append(clip)

            # 2. Concatenate visuals
            final_visuals = concatenate_videoclips(clips, method="compose")
            
            # 3. Handle Audio Synthesis
            if not voiceover_paths:
                 from moviepy import AudioClip
                 # 440Hz beep placeholder
                 final_voice = AudioFileClip("/usr/share/sounds/alsa/Front_Center.wav").with_duration(final_visuals.duration) if os.path.exists("/usr/share/sounds/alsa/Front_Center.wav") else None
            else:
                from moviepy import concatenate_audioclips
                voice_clips = [AudioFileClip(v) for v in voiceover_paths]
                final_voice = concatenate_audioclips(voice_clips)
            
            # 4. Mix with Music if available
            if music_path and os.path.exists(music_path):
                final_audio = base_audio_mixer.mix_tracks(
                    voiceover_path=voiceover_paths[0] if voiceover_paths else None, 
                    music_path=music_path,
                    duration=final_visuals.duration
                )
            else:
                final_audio = final_voice

            # 5. Combine and Render
            final_video = final_visuals.with_audio(final_audio)
            
            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Use premium render settings from processor logic
            final_video.write_videofile(
                output_path, 
                fps=30, 
                codec="libx264", # Fallback for compatibility
                audio_codec="aac"
            )
            
            return output_path
        except Exception as e:
            logging.error(f"[Nexus] Assembly Failed for Job {job_id}: {e}")
            raise e

base_nexus_orchestrator = NexusOrchestrator()

"""
FFmpeg Video Transformation Utilities
====================================

Professional-grade video processing using FFmpeg directly for maximum 
performance and flexibility. This replaces MoviePy for core transformations.
"""

import os
import subprocess
import logging
from pathlib import Path
from src.api.config import settings
from src.services.infrastructure.resource_governor import base_resource_governor

class FFmpegTransformer:
    def __init__(self, threads: int | None = None, preset: str | None = None):
        # 10/10 Production: Adaptive Core Management
        self.threads = threads or base_resource_governor.get_ffmpeg_threads()
        self.preset = preset or ("ultrafast" if base_resource_governor.get_degradation_mode() != "STANDARD" else "superfast")
        
        logger_name = "FFmpegTransformer"
        logging.getLogger(logger_name).info(f"🎞️ [FFmpeg] Initialized: {self.threads} threads (Mode: {base_resource_governor.get_degradation_mode()})")

    def _run_cmd(self, cmd: list) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"[FFmpeg] Command Failed: {' '.join(cmd)}")
            logging.error(f"[FFmpeg] Error: {e.stderr}")
            return False

    def apply_originality(self, input_path: str, output_path: str, mirror: bool = True, zoom: float = 1.05, contrast: float = 1.05, brightness: float = 0.0, start_offset: float = 0.0, duration: float = None, lut_path: str = None) -> bool:
        """
        Applies mirroring, zooming, color grading, and optional LUT in a single FFmpeg pass.
        This provides the cinematic 'Ascension' vibe.
        """
        # Complex Filter:
        # scale=1080:1920:force_original_aspect_ratio=increase (fill) -> crop=1080:1920 (center) -> hflip -> eq
        # This ensures all segments are IDENTICAL in resolution for -c copy concat.
        target_w, target_h = 1080, 1920
        filters = [
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}"
        ]
        
        if mirror:
            filters.append("hflip")
            
        if contrast != 1.0:
            filters.append(f"eq=contrast={contrast}")
            
        if brightness != 0.0:
            filters.append(f"eq=brightness={brightness}")

        # ELITE: LUT Support (Ascension Tier)
        if lut_path and os.path.exists(lut_path):
            filters.append(f"lut3d='{lut_path}'")
        elif lut_path:
            filters.append("curves=preset=vintage")
            
        filter_str = ",".join(filters) if filters else "copy"
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_offset),
        ]
        
        if duration:
            cmd += ["-t", str(duration)]
            
        cmd += [
            "-i", input_path,
            "-vf", filter_str,
            "-pix_fmt", "yuv420p", # Harmonize pixel format
            "-c:v", "libx264", "-preset", self.preset, "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", # Harmonize audio samplerate
            "-threads", str(self.threads),
            output_path
        ]
        
        return self._run_cmd(cmd)

    def generate_thumbnails(self, input_path: str, output_dir: str, count: int = 5) -> list[str]:
        """Extracts high-quality thumbnails for visual analysis"""
        os.makedirs(output_dir, exist_ok=True)
        thumbnails = []
        
        for i in range(count):
            thumb_path = f"{output_dir}/thumb_{i}.jpg"
            # Extract frame at different percentages
            time_at = f"{i * 20}%"
            cmd = [
                "ffmpeg", "-y", "-ss", time_at, "-i", input_path,
                "-vframes", "1", "-q:v", "2", thumb_path
            ]
            if self._run_cmd(cmd):
                thumbnails.append(thumb_path)
        
        return thumbnails

    def concatenate_videos(self, video_paths: list[str], output_path: str) -> bool:
        """Concatenates multiple video files into one"""
        if not video_paths: return False
        
        # Create temporary file list for ffmpeg
        with open("concat_list.txt", "w") as f:
            for path in video_paths:
                f.write(f"file '{Path(path).absolute()}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", "concat_list.txt", "-c", "copy", output_path
        ]
        
        success = self._run_cmd(cmd)
        if os.path.exists("concat_list.txt"):
            os.remove("concat_list.txt")
        return success

    def add_background_music(self, video_path: str, music_path: str, output_path: str, music_volume: float = 0.3) -> bool:
        """Mixes background music into the video while keeping original audio (at lower volume)"""
        # 10/10 Resilience: Handle cases where the video has no audio stream
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex", 
            f"[0:a]volume=1.0[a1];[1:a]volume={music_volume}[a2];[a1][a2]amix=inputs=2:duration=first",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", output_path
        ]
        
        # Check if video has audio stream using ffprobe
        has_audio = self._has_audio(video_path)
        
        if not has_audio:
            # If no audio, just use the music as the only audio source
            cmd = [
                "ffmpeg", "-y", "-i", video_path, "-i", music_path,
                "-filter_complex", f"[1:a]volume={music_volume}[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path
            ]
            
        return self._run_cmd(cmd)

    def _has_audio(self, path: str) -> bool:
        """Verify if a stream has audio"""
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return "audio" in result.stdout
        except:
            return False

    def mix_production_audio(self, video_path: str, voiceover_path: str, music_path: str, output_path: str, music_volume: float = 0.15) -> bool:
        """
        Elite Production Mix: Combines visuals with Voiceover and Background Music.
        Discards existing segment audio to ensure professional narration clarity.
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume=1.0[vo];[2:a]volume={music_volume}[bg];[vo][bg]amix=inputs=2:duration=first",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            output_path
        ]
        return self._run_cmd(cmd)

# Singleton Instance
base_ffmpeg_transformer = FFmpegTransformer()

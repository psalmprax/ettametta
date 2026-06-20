"""
Sound Designer Service
======================

FFmpeg-based audio mixing, background music, ambient sound generation,
and silence generation.
"""

import asyncio
import os
import subprocess
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class SoundDesigner:
    def __init__(self, output_dir: str = "data/storage/outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str | None = None,
        volume: float = 0.3,
        fade_in: float = 1.0,
        fade_out: float = 2.0,
    ) -> str | None:
        """Mix background music into a video with optional fade in/out.

        Args:
            video_path: Input video file.
            music_path: Background music file.
            output_path: Output file path (auto-generated if None).
            volume: Music volume relative to original audio (0.0-1.0).
            fade_in: Fade in duration in seconds.
            fade_out: Fade out duration in seconds.
        """
        if not os.path.exists(video_path):
            logger.error(f"[SoundDesigner] Video not found: {video_path}")
            return None
        if not os.path.exists(music_path):
            logger.error(f"[SoundDesigner] Music not found: {music_path}")
            return None

        if output_path is None:
            name = Path(video_path).stem
            output_path = os.path.join(self.output_dir, f"music_{name}_{uuid.uuid4().hex[:8]}.mp4")

        has_audio = self._has_audio(video_path)

        if has_audio:
            audio_filter = (
                f"[0:a]volume=1.0[a1];"
                f"[1:a]volume={volume}"
                f",afade=t=in:st=0:d={fade_in}"
                f",afade=t=out:st=999:d={fade_out}"
                f"[a2];"
                f"[a1][a2]amix=inputs=2:duration=first[a]"
            )
            map_args = ["-map", "0:v", "-map", "[a]"]
        else:
            audio_filter = (
                f"[1:a]volume={volume}"
                f",afade=t=in:st=0:d={fade_in}"
                f",afade=t=out:st=999:d={fade_out}"
                f"[a]"
            )
            map_args = ["-map", "0:v", "-map", "[a]", "-shortest"]

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex", audio_filter,
        ] + map_args + [
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]

        if self._run_cmd(cmd):
            logger.info(f"[SoundDesigner] Music added: {output_path}")
            return output_path

        logger.error(f"[SoundDesigner] Failed to add music to {video_path}")
        return None

    def mix_audio_tracks(
        self,
        tracks: list[dict],
        output_path: str | None = None,
        duration: float | None = None,
    ) -> str | None:
        """Mix multiple audio tracks together.

        Args:
            tracks: List of dicts with keys: path, volume (default 1.0), fade_in (default 0), fade_out (default 0).
            output_path: Output file path (auto-generated if None).
            duration: Override output duration in seconds (None = longest input).
        """
        if not tracks:
            logger.error("[SoundDesigner] No tracks provided")
            return None

        for track in tracks:
            if not os.path.exists(track.get("path", "")):
                logger.error(f"[SoundDesigner] Track not found: {track.get('path')}")
                return None

        if output_path is None:
            output_path = os.path.join(self.output_dir, f"mixed_{uuid.uuid4().hex[:8]}.mp3")

        inputs = []
        filter_parts = []
        for i, track in enumerate(tracks):
            inputs.extend(["-i", track["path"]])
            vol = track.get("volume", 1.0)
            fade_in = track.get("fade_in", 0)
            fade_out = track.get("fade_out", 0)
            chain = f"[{i}:a]volume={vol}"
            if fade_in > 0:
                chain += f",afade=t=in:st=0:d={fade_in}"
            if fade_out > 0:
                chain += f",afade=t=out:d={fade_out}"
            chain += f"[a{i}]"
            filter_parts.append(chain)

        mix_inputs = "".join(f"[a{i}]" for i in range(len(tracks)))
        duration_opt = ":duration=longest" if duration is None else ":duration=first"
        filter_parts.append(f"{mix_inputs}amix=inputs={len(tracks)}{duration_opt}[out]")

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]

        if self._run_cmd(cmd):
            logger.info(f"[SoundDesigner] Tracks mixed: {output_path}")
            return output_path

        logger.error("[SoundDesigner] Failed to mix audio tracks")
        return None

    def generate_silence(
        self,
        duration: float,
        output_path: str | None = None,
        sample_rate: int = 44100,
    ) -> str | None:
        """Generate a silent audio file of given duration.

        Args:
            duration: Duration in seconds.
            output_path: Output file path (auto-generated if None).
            sample_rate: Audio sample rate in Hz.
        """
        if duration <= 0:
            logger.error("[SoundDesigner] Duration must be positive")
            return None

        if output_path is None:
            output_path = os.path.join(self.output_dir, f"silence_{uuid.uuid4().hex[:8]}.mp3")

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r={sample_rate}:cl=stereo",
            "-t", str(duration),
            "-c:a", "aac", "-b:a", "128k",
            output_path,
        ]

        if self._run_cmd(cmd):
            logger.info(f"[SoundDesigner] Silence generated ({duration}s): {output_path}")
            return output_path

        logger.error("[SoundDesigner] Failed to generate silence")
        return None

    def generate_ambient_sound(
        self,
        duration: float,
        style: str = "ambient",
        output_path: str | None = None,
        sample_rate: int = 44100,
    ) -> str | None:
        """Generate a synthetic ambient soundscape using FFmpeg noise generators.

        Args:
            duration: Duration in seconds.
            style: Ambient style ('ambient', 'rain', 'wind', 'ocean', 'fire', 'city').
            output_path: Output file path (auto-generated if None).
            sample_rate: Audio sample rate in Hz.

        Returns:
            Path to generated audio file, or None on failure.
        """
        if duration <= 0:
            logger.error("[SoundDesigner] Duration must be positive")
            return None

        if output_path is None:
            output_path = os.path.join(
                self.output_dir, f"ambient_{style}_{uuid.uuid4().hex[:8]}.wav"
            )

        # Style-specific FFmpeg audio filter chains
        style_filters = {
            "ambient": f"anoisesrc=d={duration}:c=pink:r={sample_rate}:a=0.03,aecho=0.8:0.88:60:0.4,lowpass=f=1200",
            "rain": f"anoisesrc=d={duration}:c=white:r={sample_rate}:a=0.06,highpass=f=800,lowpass=f=4000,aecho=0.8:0.7:40:0.5",
            "wind": f"anoisesrc=d={duration}:c=brown:r={sample_rate}:a=0.05,lowpass=f=600,highpass=f=40,volume=0.7",
            "ocean": f"anoisesrc=d={duration}:c=white:r={sample_rate}:a=0.04,lowpass=f=500,aecho=0.6:0.6:100:0.5,lowpass=f=800",
            "fire": f"anoisesrc=d={duration}:c=brown:r={sample_rate}:a=0.04,lowpass=f=400,highpass=f=60,aecho=0.4:0.5:20:0.3",
            "city": f"anoisesrc=d={duration}:c=pink:r={sample_rate}:a=0.03,lowpass=f=2000,highpass=f=100,aecho=0.3:0.4:50:0.2",
        }

        filter_chain = style_filters.get(style, style_filters["ambient"])

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", filter_chain,
            "-t", str(duration),
            "-c:a", "pcm_s16le",
            output_path,
        ]

        if self._run_cmd(cmd):
            logger.info(f"[SoundDesigner] Ambient sound generated ({style}, {duration}s): {output_path}")
            return output_path

        logger.error(f"[SoundDesigner] Failed to generate ambient sound: {style}")
        return None

    async def generate_ambient_sound_async(
        self, duration: float, style: str = "ambient", **kwargs
    ) -> str | None:
        """Async wrapper for generate_ambient_sound."""
        return await asyncio.to_thread(
            self.generate_ambient_sound, duration, style=style, **kwargs
        )

    def _has_audio(self, path: str) -> bool:
        """Check if a media file has an audio stream."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "a",
                 "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
                capture_output=True, text=True,
            )
            return "audio" in result.stdout
        except Exception:
            return False

    def _run_cmd(self, cmd: list) -> bool:
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[SoundDesigner] Command failed: {' '.join(cmd)}")
            logger.error(f"[SoundDesigner] Error: {e.stderr}")
            return False
        except Exception as e:
            logger.exception(f"[SoundDesigner] Unexpected error: {e}")
            return False


base_sound_designer = SoundDesigner()

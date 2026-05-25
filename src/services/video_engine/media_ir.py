"""
Media Intermediate Representation (MediaIR)
============================================

Structured media objects used as the core data type in the DAG video compiler.
Replaces raw file paths with typed, metadata-rich media objects.

This is the foundation of the DAG architecture — every node consumes and
produces MediaIR objects instead of raw file paths.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Literal, Any

logger = logging.getLogger(__name__)

MediaType = Literal["video", "audio", "image"]


@dataclass
class MediaIR:
    """Media Intermediate Representation — structured media object.

    Replaces raw file paths throughout the pipeline with typed,
    metadata-rich objects. This enables:
    - Codec-aware node execution
    - Duration-aware scheduling
    - Metadata-backed caching
    - Type-safe media graph traversal
    """
    type: MediaType
    uri: str
    codec: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None

    @classmethod
    def from_path(cls, path: str, media_type: MediaType, **extra: Any) -> "MediaIR":
        """Create a MediaIR from a file path with optional extra metadata."""
        return cls(type=media_type, uri=path, **extra)

    @classmethod
    async def from_video_path(cls, path: str) -> "MediaIR":
        """Probe a video file and return a fully populated MediaIR.

        Uses ffprobe to extract duration, resolution, codec, and fps.
        Falls back gracefully to defaults if probing fails.
        """
        import subprocess
        ir = cls(type="video", uri=path)
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-show_entries", "stream=codec_name,width,height,r_frame_rate",
                "-of", "json",
                path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if "format" in data and data["format"].get("duration"):
                    ir.duration = float(data["format"]["duration"])
                if "streams" in data:
                    for s in data["streams"]:
                        if s.get("codec_type") == "video":
                            ir.codec = s.get("codec_name", "unknown")
                            ir.width = s.get("width")
                            ir.height = s.get("height")
                            if s.get("r_frame_rate"):
                                num, den = s["r_frame_rate"].split("/")
                                ir.fps = float(num) / float(den) if float(den) > 0 else None
                            break
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[MediaIR] ffprobe failed for {path}: {e}")
        return ir

    @classmethod
    async def from_audio_path(cls, path: str) -> "MediaIR":
        """Probe an audio file and return a fully populated MediaIR."""
        import subprocess
        ir = cls(type="audio", uri=path)
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-show_entries", "stream=codec_name",
                "-of", "json",
                path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if "format" in data and data["format"].get("duration"):
                    ir.duration = float(data["format"]["duration"])
                if "streams" in data:
                    for s in data["streams"]:
                        if s.get("codec_type") == "audio":
                            ir.codec = s.get("codec_name", "unknown")
                            break
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as e:
            logger.warning(f"[MediaIR] ffprobe failed for audio {path}: {e}")
        return ir

    def exists(self) -> bool:
        """Check if the underlying media file exists on disk."""
        return self.uri.startswith("http") or os.path.exists(self.uri)

    def __repr__(self) -> str:
        return f"MediaIR({self.type}, {os.path.basename(self.uri)}, dur={self.duration})"


# Sentinel for empty/unknown media
NULL_MEDIA = MediaIR(type="video", uri="", codec="none")

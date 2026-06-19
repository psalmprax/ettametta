"""Video quality upscaling using FFmpeg filters."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class UpscaleQuality(str, Enum):
    FAST = "fast"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class UpscaleProfile:
    scale_filter: str
    denoise: str
    sharpen: str
    description: str


PROFILES: dict[UpscaleQuality, UpscaleProfile] = {
    UpscaleQuality.FAST: UpscaleProfile(
        scale_filter="scale=1920:1080:flags=lanczos",
        denoise="hqdn3d=3:3:2:2",
        sharpen="unsharp=3:3:0.5:3:3:0.0",
        description="Fast 1080p upscale with light denoise",
    ),
    UpscaleQuality.HIGH: UpscaleProfile(
        scale_filter="scale=2560:1440:flags=lanczos",
        denoise="hqdn3d=4:3:3:3",
        sharpen="unsharp=5:5:1.0:5:5:0.0",
        description="1440p upscale with moderate denoise and sharpen",
    ),
    UpscaleQuality.ULTRA: UpscaleProfile(
        scale_filter="scale=3840:2160:flags=lanczos",
        denoise="hqdn3d=6:4:4:4",
        sharpen="unsharp=7:7:1.5:7:7:0.0",
        description="4K upscale with heavy denoise and sharpen",
    ),
}


class UpscaleService:
    def get_profile(self, quality: UpscaleQuality) -> UpscaleProfile:
        return PROFILES[quality]

    async def get_input_info(self, video_path: str) -> dict:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            video_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        import json
        return json.loads(stdout.decode()) if stdout else {}

    async def upscale_video(
        self,
        video_path: str,
        target_resolution: str = "3840x2160",
        quality: UpscaleQuality = UpscaleQuality.HIGH,
        preserve_aspect_ratio: bool = True,
    ) -> str:
        profile = PROFILES[quality]
        width, height = target_resolution.split("x")

        scale = f"scale={width}:{height}:flags=lanczos"
        if preserve_aspect_ratio:
            scale = f"scale={width}:{height}:flags=lanczos:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"

        vf_chain = ",".join([
            scale,
            profile.denoise,
            profile.sharpen,
        ])

        output_path = video_path.rsplit(".", 1)[0] + "_upscaled.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", vf_chain,
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-c:a", "copy",
            output_path,
        ]

        logger.info("Upscaling %s → %s (%s)", video_path, output_path, quality.value)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg upscale failed: {stderr.decode()}")
        return output_path

    async def enhance_video(
        self,
        video_path: str,
        denoise: bool = True,
        sharpen: bool = True,
        stabilize: bool = False,
    ) -> str:
        filters = []
        if denoise:
            filters.append("hqdn3d=3:3:2:2")
        if sharpen:
            filters.append("unsharp=3:3:0.5:3:3:0.0")
        if stabilize:
            filters.append("deshake")

        if not filters:
            return video_path

        output_path = video_path.rsplit(".", 1)[0] + "_enhanced.mp4"
        vf = ",".join(filters)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-c:a", "copy",
            output_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg enhance failed: {stderr.decode()}")
        return output_path


base_upscale_service = UpscaleService()

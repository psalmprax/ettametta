"""Shared video utilities — probe, FFmpeg execution, and helpers.

Used by processor.py, orchestrator.py, dag_nodes.py, and platform_composer.py
to eliminate duplicated OpenCV probe patterns and FFmpeg subprocess boilerplate.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Metadata extracted from a video file."""
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float
    has_audio: bool = False


def probe_video(path: str) -> VideoInfo | None:
    """Probe a video file using OpenCV. Returns VideoInfo or None on failure.

    Replaces 5 duplicated cv2.VideoCapture + property extraction + release blocks.
    """
    if path.startswith("http"):
        return None

    try:
        import cv2
    except ImportError:
        logger.warning("[video_utils] OpenCV not available for probing")
        return None

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        cap.release()
        return None

    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        return VideoInfo(
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration=duration,
        )
    except Exception as e:
        logger.warning("[video_utils] Probe failed for %s: %s", path, e)
        return None
    finally:
        cap.release()


def extract_frame(path: str, frame_index: int | None = None) -> "numpy.ndarray | None":  # type: ignore[name-defined]
    """Extract a single frame from a video. Uses middle frame if index is None.

    Replaces 3 duplicated cv2.VideoCapture + set frame + read + release blocks.
    """
    try:
        import cv2
    except ImportError:
        return None

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        cap.release()
        return None

    try:
        if frame_index is None:
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_index = total // 2 if total > 0 else 0

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        return frame if ret else None
    finally:
        cap.release()


async def run_ffmpeg_cmd(
    cmd: list[str],
    *,
    timeout: int = 300,
    label: str = "ffmpeg",
) -> tuple[bool, str]:
    """Run an FFmpeg command asynchronously with timeout and error handling.

    Replaces duplicated asyncio.create_subprocess_exec + wait + returncode blocks.
    Returns (success, error_message).
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )

        if proc.returncode == 0:
            return True, ""

        error_text = stderr.decode(errors="replace") if stderr else "unknown error"
        logger.error("[video_utils] %s failed (rc=%d): %s", label, proc.returncode, error_text[:200])
        return False, error_text

    except asyncio.TimeoutError:
        logger.error("[video_utils] %s timed out after %ds", label, timeout)
        try:
            proc.kill()
        except Exception:
            pass
        return False, f"timeout after {timeout}s"

    except Exception as e:
        logger.error("[video_utils] %s error: %s", label, e)
        return False, str(e)


async def probe_duration_ffprobe(path: str) -> float | None:
    """Get duration in seconds via ffprobe. Returns None on failure."""
    if not path or not os.path.exists(path):
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        return float(stdout.decode().strip())
    except Exception as e:
        logger.warning("[video_utils] ffprobe duration failed for %s: %s", path, e)
        return None

"""Render pipeline — thumbnail extraction, SRT export, style modulation.

Extracted from NexusOrchestrator to reduce god-class size.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _run_subprocess(
    args: list[str],
    *,
    capture_output: bool = True,
    text: bool = False,
    check: bool = True,
    cwd: str | None = None,
):
    """Run a subprocess command."""
    import subprocess
    return subprocess.run(
        args,
        capture_output=capture_output,
        text=text,
        check=check,
        cwd=cwd,
    )


def modulate_video_style(
    job_id: str,
    style: str,
    style_config: dict[str, Any],
    job_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply stochastic style modulation."""
    try:
        from src.services.video_engine.stochastic_modulator import modulate_style
        theme_preset = (job_metadata or {}).get("theme_preset")
        style_config = modulate_style(
            style_config, seed=str(job_id), theme_preset=theme_preset
        )
        logger.info(f"[Nexus] Stochastic modulation applied for style: {style}")
    except Exception as e:
        logger.warning(f"[Nexus] Stochastic modulation failed: {e}")
    return style_config


def source_music(music_path: str | None, music_keywords: list[str]) -> str | None:
    """Auto-source background music from library if not provided."""
    if music_path:
        return music_path
    from src.services.audio.sound_design import sound_design_service

    if sound_design_service.enabled:
        import random
        mood = music_keywords[0] if music_keywords else "cinematic"
        music_dir = Path(sound_design_service.library_path) / mood
        if music_dir.exists():
            tracks = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
            if tracks:
                chosen_track = str(random.choice(tracks))
                logger.info(f"[Nexus] Auto-sourced music: {chosen_track}")
                return chosen_track
    return None


async def extract_thumbnail(
    local_temp_dir: Path, job_id: str, visual_paths: list[str]
) -> str:
    """Extract a thumbnail from the first clip."""
    thumb_dir = local_temp_dir / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = str(thumb_dir / f"{job_id}.jpg")
    if visual_paths and os.path.exists(visual_paths[0]):
        try:
            logger.info("[Nexus] Extracting thumbnail from first clip...")
            await asyncio.to_thread(
                _run_subprocess,
                [
                    "ffmpeg", "-y", "-ss", "00:00:01.500",
                    "-i", visual_paths[0],
                    "-frames:v", "1", "-q:v", "2", thumbnail_path,
                ],
            )
        except Exception as e:
            logger.error(f"[Nexus] Thumbnail extraction failed: {e}")
    return thumbnail_path


def _format_srt_time(seconds: float) -> str:
    """Format a float-seconds value as an SRT timestamp ``HH:MM:SS,mmm``."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def export_srt(
    words: list[dict[str, Any]], output_path: str
) -> str | None:
    """Export word-level timestamps as an SRT subtitle sidecar file.

    Groups words into blocks of ~4 for readable subtitle chunks.
    Returns output_path on success, None if there are no words.
    """
    if not words:
        return None

    blocks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for w in words:
        current.append(w)
        if len(current) >= 4:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for i, block in enumerate(blocks, 1):
                start = block[0]["start"]
                end = block[-1]["end"]
                text = " ".join(w["word"] for w in block)
                f.write(f"{i}\n")
                f.write(
                    f"{_format_srt_time(start)} --> "
                    f"{_format_srt_time(end)}\n"
                )
                f.write(f"{text}\n\n")
        logger.info(
            "[Nexus] Exported SRT captions: %d blocks → %s",
            len(blocks), output_path,
        )
        return output_path
    except OSError as e:
        logger.error("[Nexus] Failed to write SRT file: %s", e)
        return None


import asyncio

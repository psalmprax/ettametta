"""
Video Enhancement API Routes
=============================

Standalone endpoints for applying individual enhancements to existing videos.
"""

import asyncio
import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.subscription import credits_required
from src.api.utils.limiter import limiter
from src.api.utils.audit_service import audit_service
from src.api.utils.api_responses import success_response
from src.api.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video/enhance", tags=["Video Enhancement"])

# Allowed base directories for user-supplied video/image paths
_ALLOWED_BASES = [
    "/data/storage",
    "/tmp/ettametta",
    "/var/lib/ettametta",
]


def _validate_path(path: str) -> str:
    """Validate that a file path is under an allowed directory."""
    real = os.path.realpath(path)
    for base in _ALLOWED_BASES:
        if real.startswith(base):
            return real
    raise HTTPException(
        status_code=400,
        detail=f"Path must be under an allowed directory: {', '.join(_ALLOWED_BASES)}",
    )


# ── Schemas ──────────────────────────────────────────────────────────────────


class BackgroundRemovalRequest(BaseModel):
    video_path: str
    method: str = "auto"  # auto | chromakey | colorkey | rembg
    color: str = "green"
    replace_color: str | None = None
    similarity: float = 0.3
    blend: float = 0.1


class SoundDesignRequest(BaseModel):
    video_path: str
    music_path: str | None = None
    volume: float = 0.3
    fade_in: float = 1.0
    fade_out: float = 2.0
    ambient_style: str | None = None  # ambient | rain | wind | ocean | fire | city
    ambient_duration: float | None = None


class WatermarkRequest(BaseModel):
    video_path: str
    type: str = "text"  # text | image | animated
    text: str = "Created with ettametta"
    image_path: str | None = None
    opacity: float = 0.3
    position: str = "bottom_right"
    animation: str | None = None  # pulse | fade_loop | slide_in


class BurnBrandingRequest(BaseModel):
    video_path: str
    brand_name: str = "ettametta"
    logo_path: str | None = None
    tagline: str | None = None
    website: str | None = None
    position: str = "bottom_right"
    opacity: float = 0.4


def _to_static_url(file_path: str) -> str:
    """Convert a server file path to a static URL.

    If the file is already inside STORAGE_OUTPUT_DIR, returns /static/… relative path.
    Otherwise copies the file into STORAGE_OUTPUT_DIR first so the preview works.
    """
    from src.api.config import settings

    base = os.path.realpath(settings.STORAGE_OUTPUT_DIR)
    real = os.path.realpath(file_path)
    if real.startswith(base + os.sep):
        relative = real[len(base) + 1 :]
        return f"/static/{relative}"
    # File is outside static dir — copy it in so preview works
    import shutil

    dest = os.path.join(base, os.path.basename(file_path))
    try:
        shutil.copy2(real, dest)
        return f"/static/{os.path.basename(file_path)}"
    except Exception:
        logger.warning(f"[Enhance] Could not copy {file_path} to static dir")
        return file_path


# ── Background Removal ──────────────────────────────────────────────────────


@router.post("/background")
@limiter.limit("5/minute")
async def remove_background(
    request: Request,
    body: BackgroundRemovalRequest,
    current_user: UserDB = Depends(get_current_user),
    _credits: int = Depends(credits_required("background_removal")),
    db=Depends(get_db),
):
    """Remove or replace the background of an existing video."""
    from src.services.video_engine.background_remover import base_background_remover

    video = _validate_path(body.video_path)
    if not os.path.exists(video):
        raise HTTPException(status_code=400, detail="Video file not found")

    result = await base_background_remover.remove_background_async(
        video,
        method=body.method,
        color=body.color,
        replace_color=body.replace_color,
        similarity=body.similarity,
        blend=body.blend,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Background removal failed")

    await audit_service.log(
        action="VIDEO_BG_REMOVAL",
        user_id=current_user.id,
        resource_type="VIDEO",
        resource_id=str(uuid.uuid4()),
        details={"method": body.method, "output": result},
        db=db,
    )

    output_url = _to_static_url(result)
    return success_response(data={"output_path": result, "output_url": output_url, "method": body.method})


# ── Sound Design ────────────────────────────────────────────────────────────


@router.post("/sound")
@limiter.limit("5/minute")
async def enhance_sound(
    request: Request,
    body: SoundDesignRequest,
    current_user: UserDB = Depends(get_current_user),
    _credits: int = Depends(credits_required("sound_design")),
    db=Depends(get_db),
):
    """Add background music or ambient sound to a video."""
    from src.services.video_engine.sound_designer import base_sound_designer

    video = _validate_path(body.video_path)
    if not os.path.exists(video):
        raise HTTPException(status_code=400, detail="Video file not found")

    output = None

    if body.music_path:
        # Mix in a specific music file
        music = _validate_path(body.music_path)
        if not os.path.exists(music):
            raise HTTPException(status_code=400, detail="Music file not found")
        output = await asyncio.to_thread(
            base_sound_designer.add_background_music,
            video,
            music,
            volume=body.volume,
            fade_in=body.fade_in,
            fade_out=body.fade_out,
        )
    elif body.ambient_style:
        # Generate ambient sound and mix it
        duration = body.ambient_duration
        if not duration:
            # Probe video duration
            import subprocess

            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", video],
                capture_output=True, text=True,
            )
            try:
                duration = float(probe.stdout.strip())
            except (ValueError, TypeError):
                duration = 10.0

        ambient_path = await base_sound_designer.generate_ambient_sound_async(
            duration, style=body.ambient_style,
        )
        if ambient_path:
            # Mux ambient audio onto the video (mix_audio_tracks produces audio-only)
            import subprocess as _sp

            mux_output = os.path.join(
                base_sound_designer.output_dir,
                f"ambient_mux_{uuid.uuid4().hex[:8]}.mp4",
            )
            vol_filter = f"[1:a]volume={body.volume}"
            if body.fade_in > 0:
                vol_filter += f",afade=t=in:st=0:d={body.fade_in}"
            if body.fade_out > 0:
                vol_filter += f",afade=t=out:st=999:d={body.fade_out}"

            has_audio = await asyncio.to_thread(base_sound_designer._has_audio, video)

            if has_audio:
                vol_filter += "[a2]"
                fc = f"{vol_filter};[0:a][a2]amix=inputs=2:duration=first[a]"
                map_args = ["-map", "0:v", "-map", "[a]", "-c:v", "copy"]
            else:
                fc = f"{vol_filter}[a]"
                map_args = ["-map", "0:v", "-map", "[a]", "-c:v", "copy", "-shortest"]

            mux_cmd = [
                "ffmpeg", "-y",
                "-i", video, "-i", ambient_path,
                "-filter_complex", fc,
            ] + map_args + [
                "-c:a", "aac", "-b:a", "192k",
                mux_output,
            ]
            try:
                result = await asyncio.to_thread(
                    lambda: _sp.run(mux_cmd, capture_output=True, text=True, timeout=300),
                )
                if result.returncode == 0 and os.path.exists(mux_output):
                    output = mux_output
                else:
                    logger.warning(f"[Enhance] Ambient mux failed: {result.stderr[:200]}")
            except Exception as mux_err:
                logger.warning(f"[Enhance] Ambient mux error: {mux_err}")

            # Cleanup generated ambient file
            if ambient_path and os.path.exists(ambient_path):
                os.remove(ambient_path)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either music_path or ambient_style",
        )

    if not output:
        raise HTTPException(status_code=500, detail="Sound design failed")

    await audit_service.log(
        action="VIDEO_SOUND_DESIGN",
        user_id=current_user.id,
        resource_type="VIDEO",
        resource_id=str(uuid.uuid4()),
        details={"ambient_style": body.ambient_style, "output": output},
        db=db,
    )

    output_url = _to_static_url(output)
    return success_response(data={"output_path": output, "output_url": output_url})


# ── Watermark ───────────────────────────────────────────────────────────────


@router.post("/watermark")
@limiter.limit("10/minute")
async def add_watermark(
    request: Request,
    body: WatermarkRequest,
    current_user: UserDB = Depends(get_current_user),
    _credits: int = Depends(credits_required("background_removal")),
    db=Depends(get_db),
):
    """Add a text, image, or animated watermark to a video."""
    from src.services.video_engine.motion_graphics import base_motion_graphics_service

    video = _validate_path(body.video_path)
    if not os.path.exists(video):
        raise HTTPException(status_code=400, detail="Video file not found")

    output = None

    if body.type == "image":
        if not body.image_path:
            raise HTTPException(status_code=400, detail="Image watermark file not found")
        img = _validate_path(body.image_path)
        if not os.path.exists(img):
            raise HTTPException(status_code=400, detail="Image watermark file not found")
        output = await base_motion_graphics_service.add_image_watermark(
            video,
            img,
            opacity=body.opacity,
            position=body.position,
        )
    elif body.type == "animated":
        output = await base_motion_graphics_service.add_animated_watermark(
            video,
            watermark_text=body.text,
            animation=body.animation or "pulse",
            position=body.position,
            opacity=body.opacity,
        )
    else:
        # Default: text watermark
        output = await base_motion_graphics_service.add_watermark(
            video,
            watermark_text=body.text,
            opacity=body.opacity,
            position=body.position,
        )

    if not output:
        raise HTTPException(status_code=500, detail="Watermark failed")

    await audit_service.log(
        action="VIDEO_WATERMARK",
        user_id=current_user.id,
        resource_type="VIDEO",
        resource_id=str(uuid.uuid4()),
        details={"type": body.type, "output": output},
        db=db,
    )

    output_url = _to_static_url(output)
    return success_response(data={"output_path": output, "output_url": output_url, "type": body.type})


# ── Burn Branding ───────────────────────────────────────────────────────────


@router.post("/branding")
@limiter.limit("5/minute")
async def burn_branding(
    request: Request,
    body: BurnBrandingRequest,
    current_user: UserDB = Depends(get_current_user),
    _credits: int = Depends(credits_required("sound_design")),
    db=Depends(get_db),
):
    """Burn a full brand package (logo + name + tagline + website) into a video."""
    from src.services.video_engine.motion_graphics import base_motion_graphics_service

    video = _validate_path(body.video_path)
    if not os.path.exists(video):
        raise HTTPException(status_code=400, detail="Video file not found")

    output = await base_motion_graphics_service.burn_branding(
        video,
        brand_config={
            "logo_path": _validate_path(body.logo_path) if body.logo_path else None,
            "brand_name": body.brand_name,
            "tagline": body.tagline,
            "website": body.website,
            "position": body.position,
            "opacity": body.opacity,
        },
    )

    if not output:
        raise HTTPException(status_code=500, detail="Branding failed")

    await audit_service.log(
        action="VIDEO_BRANDING",
        user_id=current_user.id,
        resource_type="VIDEO",
        resource_id=str(uuid.uuid4()),
        details={"brand_name": body.brand_name, "output": output},
        db=db,
    )

    output_url = _to_static_url(output)
    return success_response(data={"output_path": output, "output_url": output_url, "brand_name": body.brand_name})

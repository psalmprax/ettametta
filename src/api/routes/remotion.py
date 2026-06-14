import asyncio
import os
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.api.utils.auth import get_current_user
from src.services.video_engine.remotion_service import RemotionService
from src.shared.enums import SystemJobStatus

router = APIRouter(prefix="/remotion", tags=["remotion"])
logger = logging.getLogger(__name__)

# Backward compatibility: default service instance
base_remotion_service = RemotionService()

# ── Composition Registry ──────────────────────────────────────────────
# Maps every registered Remotion composition to its metadata.
# Source of truth: apps/remotion-studio/src/Root.tsx

COMPOSITION_REGISTRY: dict[str, dict[str, Any]] = {
    "ViralClip": {
        "description": "Full production engine: Ken Burns clips, kinetic captions, dynamic intros, CTA outro, 25+ video styles",
        "default_duration_frames": 18000,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (optional)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
            "words": "array of {word, start, end, confidence} (optional)",
            "clips": "array of {url, duration_in_frames} (optional)",
            "brand_name": "string (optional)",
            "primary_color": "string (optional)",
            "trademark_url": "string (optional)",
            "vignette_intensity": "number (optional)",
            "grain_opacity": "number (optional)",
            "style": "string (optional, VOX_EXPLAINER | CINEMATIC_DOC | ...)",
            "intro_style": "'brand_reveal' | 'cyberpunk' | 'iridescent' | 'portal' | 'astrolabe' | 'liquid_metal' (optional)",
            "job_metadata": "record (optional)",
            "video_duration_frames": "number (optional, max 18000)",
        }
    },
    "CinematicMinimal": {
        "description": "Minimal cinematic template: BrandReveal intro, background video, CTA outro",
        "default_duration_frames": 18000,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #00F2FE)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "HormoziStyle": {
        "description": "High-energy word-by-word kinetic typography with colored border",
        "default_duration_frames": 18000,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "text": "string (required, space-separated words)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "highlight_color": "string (optional, default #00ff00)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "Cinematic3D": {
        "description": "3D extruded text rendered in WebGL with Three.js, floating over background video",
        "default_duration_frames": 18000,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #00F2FE)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicAncient": {
        "description": "Ancient astrolabe 3D artifact with celestial rings, gold typography overlay",
        "default_duration_frames": 18000,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #FFD700)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicIridescent": {
        "description": "Iridescent glass morphing orb with iridescent border glow",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicPortal": {
        "description": "3D glowing portal ring with sparkle particles and Bloom post-processing",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicCyberpunk": {
        "description": "Cyberpunk HUD overlay with scanlines, rotating rings, and glowing text",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicLiquid": {
        "description": "3D liquid metal morphing sphere with Bloom post-processing and overlay typography",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #00F2FE)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicPrism": {
        "description": "3D prismatic light refraction with chromatic aberration, textual content rendered in WebGL",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #FF10F0)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicLidar": {
        "description": "3D lidar point cloud scanner with Glitch and Bloom post-processing, monospace typography",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #00FF00)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
    "CinematicKinetic": {
        "description": "Kinetic typography animation with bouncing, rotating, and scaling motion for each character",
        "default_duration_frames": 120,
        "fps": 30,
        "width": 1080,
        "height": 1920,
        "props_schema": {
            "title": "string (required)",
            "subtitle": "string (required)",
            "video_url": "string (optional)",
            "audio_url": "string (optional)",
            "primary_color": "string (optional, default #FFFF00)",
            "show_cta_overlay": "boolean (optional)",
            "cta_type": "'engagement' | 'cta' (optional)",
            "cta_text": "string (optional)",
        }
    },
}

# ── Preview Defaults ───────────────────────────────────────────────────
# Sensible default props for each composition when rendering a quick
# test/preview.  Mirrors the defaultProps from Root.tsx.

PREVIEW_DEFAULTS: dict[str, dict[str, Any]] = {
    "ViralClip": {
        "title": "Preview Mode",
        "subtitle": "Viral Template Preview",
        "show_cta_overlay": False,
        "style": "CINEMATIC_DOC",
        "brand_name": "ettametta",
        "primary_color": "#8b5cf6",
    },
    "CinematicMinimal": {
        "title": "Preview Mode",
        "subtitle": "Minimal Template Preview",
        "primary_color": "#00F2FE",
        "show_cta_overlay": False,
    },
    "HormoziStyle": {
        "text": "Results Discipline Money Freedom Legacy",
        "highlight_color": "#00ff00",
        "show_cta_overlay": False,
    },
    "Cinematic3D": {
        "title": "3D PREVIEW",
        "subtitle": "Extruded Text Demo",
        "primary_color": "#00F2FE",
        "show_cta_overlay": False,
    },
    "CinematicAncient": {
        "title": "ANCIENT",
        "subtitle": "Astrolabe Preview",
        "primary_color": "#FFD700",
        "show_cta_overlay": False,
    },
    "CinematicIridescent": {
        "title": "AURORA",
        "subtitle": "COLLECTION",
        "show_cta_overlay": False,
    },
    "CinematicPortal": {
        "title": "ANCIENT",
        "subtitle": "MYSTERY",
        "show_cta_overlay": False,
    },
    "CinematicCyberpunk": {
        "title": "SYSTEM",
        "subtitle": "ONLINE",
        "show_cta_overlay": False,
    },
    "CinematicLiquid": {
        "title": "LIQUID",
        "subtitle": "METAL",
        "show_cta_overlay": False,
    },
    "CinematicPrism": {
        "title": "OPTICAL",
        "subtitle": "PRISM",
        "show_cta_overlay": False,
    },
    "CinematicLidar": {
        "title": "LIDAR",
        "subtitle": "SCANNER",
        "show_cta_overlay": False,
    },
    "CinematicKinetic": {
        "title": "KINETIC",
        "subtitle": "ENERGY",
        "show_cta_overlay": False,
    },
}

# Ordered list of composition IDs (matches Root.tsx registration order)
COMPOSITION_IDS: list[str] = [
    "ViralClip",
    "CinematicMinimal",
    "HormoziStyle",
    "Cinematic3D",
    "CinematicAncient",
    "CinematicIridescent",
    "CinematicPortal",
    "CinematicCyberpunk",
    "CinematicLiquid",
    "CinematicPrism",
    "CinematicLidar",
    "CinematicKinetic",
]


class RenderRequest(BaseModel):
    composition_id: str = Field(
        default="ViralClip",
        description="Registered Remotion composition ID. Use GET /remotion/compositions for available IDs.",
        examples=["ViralClip", "CinematicPortal", "CinematicLiquid"],
    )
    props: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible props dict passed to the composition. Required fields depend on composition_id.",
    )
    output_name: str | None = Field(
        default=None,
        description="Optional output filename. Auto-generated if not provided.",
    )


async def run_render_task(composition_id: str, props: dict[str, Any], output_name: str | None, job_id: str):
    """Background task to execute Remotion render for any composition."""
    try:
        final_output = output_name or f"render_{job_id}.mp4"
        result = await base_remotion_service.render_video(
            composition_id, props, final_output
        )
        if result:
            logger.info(f"Successfully rendered {composition_id} for job {job_id}")
        else:
            logger.error(f"Render task returned no output for job {job_id}")
    except Exception as e:
        logger.exception(f"Error in background render task for {composition_id}: {e}")


@router.get("/compositions")
async def list_compositions(current_user=Depends(get_current_user)):
    """
    Returns the full registry of available Remotion compositions.
    Each entry includes metadata, default dimensions, and the expected props schema.
    """
    return {
        "compositions": COMPOSITION_IDS,
        "registry": {
            cid: {
                "description": meta["description"],
                "default_duration_frames": meta["default_duration_frames"],
                "fps": meta["fps"],
                "width": meta["width"],
                "height": meta["height"],
                "props_schema": meta["props_schema"],
            }
            for cid, meta in COMPOSITION_REGISTRY.items()
        },
    }


@router.get("/compositions/{composition_id}/preview")
async def preview_composition(
    composition_id: str,
    current_user=Depends(get_current_user),
):
    """
    Renders a quick test preview (4 seconds, 25% scale) of any registered
    Remotion composition and returns the MP4 video file inline.

    - **composition_id**: One of the IDs returned by `GET /remotion/compositions`

    Useful for previewing how a composition looks before committing to a
    full pipeline render.  Short-form compositions (CinematicPortal,
    CinematicCyberpunk, etc.) render all 120 frames; long-form compositions
    render only the first 120 frames for a rapid draft.
    """
    if composition_id not in COMPOSITION_REGISTRY:
        available = ", ".join(COMPOSITION_IDS)
        raise HTTPException(
            status_code=422,
            detail=f"Unknown composition_id '{composition_id}'. Available: {available}",
        )

    # Build preview props from sensible defaults
    props: dict[str, Any] = dict(PREVIEW_DEFAULTS.get(composition_id, {
        "title": "Preview",
        "subtitle": "Preview Mode",
        "show_cta_overlay": False,
    }))

    # Fast draft render: low scale, short duration
    props["job_metadata"] = {"remotion_scale": 0.25}
    # Cap at 60 frames (--frames 0-59) for a fast 2-second preview.
    # 3D compositions (CinematicPortal, Cinematic3D, etc.) are especially
    # slow in headless Chromium without GPU — shorter duration helps.
    props["duration_in_frames"] = 59

    output_name = f"preview_{composition_id}_{uuid.uuid4().hex[:8]}.mp4"

    try:
        result = await asyncio.wait_for(
            base_remotion_service.render_video(composition_id, props, output_name),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        logger.error(f"Preview render timed out for {composition_id} (120s limit)")
        raise HTTPException(
            status_code=504,
            detail=f"Preview render timed out after 120 seconds for composition '{composition_id}'. "
            f"3D compositions (CinematicPortal, Cinematic3D, etc.) may need more time "
            f"on headless Chromium. Try a simpler composition like CinematicMinimal.",
        )
    except Exception as e:
        logger.exception(f"Preview render failed for {composition_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Remotion preview render failed: {e}",
        )

    if not result or not os.path.exists(result):
        raise HTTPException(
            status_code=500,
            detail="Preview render completed but output file is missing",
        )

    return FileResponse(
        path=result,
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename=preview_{composition_id}.mp4",
            "Accept-Ranges": "bytes",
        },
    )


@router.post("/render")
async def trigger_render(
    req: RenderRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """
    Triggers a programmatic Remotion render for any registered composition.
    Requires authentication.

    - `composition_id`: One of the IDs returned by GET /remotion/compositions
    - `props`: Dict of props to pass to the composition. Required fields depend on the composition.
    - `output_name`: Optional output filename (default: auto-generated)

    Example: render a CinematicPortal video
    ```json
    {
        "composition_id": "CinematicPortal",
        "props": {
            "title": "ANCIENT",
            "subtitle": "MYSTERY",
            "show_cta_overlay": false
        }
    }
    ```
    """
    cid = req.composition_id

    # Validate composition_id against registry
    if cid not in COMPOSITION_REGISTRY:
        available = ", ".join(COMPOSITION_IDS)
        raise HTTPException(
            status_code=422,
            detail=f"Unknown composition_id '{cid}'. Available: {available}",
        )

    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_render_task, cid, req.props, req.output_name, job_id)

    meta = COMPOSITION_REGISTRY[cid]
    return {
        "status": SystemJobStatus.QUEUED.value,
        "job_id": job_id,
        "composition_id": cid,
        "composition_description": meta["description"],
        "message": f"Render task for {cid} queued in background.",
    }

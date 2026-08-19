"""
Video Preview and Download API Routes
======================================
Endpoints for previewing and downloading generated videos.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB

router = APIRouter(prefix="/video", tags=["Video Preview/Download"])


@router.get("/preview/{job_id}")
async def preview_video(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Preview a generated video by streaming it to the browser.
    Returns the video file with appropriate headers for inline playback.
    """
    # Look for video in output directories
    output_dirs = [
        Path("data/storage/outputs/remix"),
        Path("data/storage/outputs/edited"),
        Path("data/storage/outputs"),
    ]

    video_path = None
    for output_dir in output_dirs:
        potential_path = output_dir / f"{job_id}.mp4"
        if potential_path.exists():
            video_path = potential_path
            break

        # Also check for files that contain job_id in their name
        if output_dir.exists():
            for f in output_dir.glob(f"*{job_id}*.mp4"):
                video_path = f
                break

    if not video_path or not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Video not found for job {job_id}")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename=video_{job_id}.mp4",
            "Accept-Ranges": "bytes",
        }
    )


@router.get("/download/{job_id}")
async def download_video(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Download a generated video as an attachment.
    Forces browser to download rather than play inline.
    """
    # Look for video in output directories
    output_dirs = [
        Path("data/storage/outputs/remix"),
        Path("data/storage/outputs/edited"),
        Path("data/storage/outputs"),
    ]

    video_path = None
    for output_dir in output_dirs:
        potential_path = output_dir / f"{job_id}.mp4"
        if potential_path.exists():
            video_path = potential_path
            break

        # Also check for files that contain job_id in their name
        if output_dir.exists():
            for f in output_dir.glob(f"*{job_id}*.mp4"):
                video_path = f
                break

    if not video_path or not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Video not found for job {job_id}")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"remix_{job_id}.mp4",
        headers={
            "Content-Disposition": f"attachment; filename=remix_{job_id}.mp4",
        }
    )

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.utils.database import SessionLocal
from api.utils.models import VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.video_engine.tasks import download_and_process_task

router = APIRouter(prefix="/video", tags=["Video Engine"])

class TransformationRequest(BaseModel):
    input_url: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"


@router.post("/transform")
async def start_transformation(request: TransformationRequest, current_user: UserDB = Depends(get_current_user)):
    """
    Triggers a background Celery task to download, process, and upload a video.
    """
    db = SessionLocal()
    try:
        task = download_and_process_task.delay(request.input_url, request.niche, request.platform)
        
        # Create Job Entry in Database
        new_job = VideoJobDB(
            id=task.id,
            title=f"Viral Transform - {request.niche}",
            status="Queued",
            progress=0,
            input_url=request.input_url,
            user_id=current_user.id
        )
        db.add(new_job)
        db.commit()
        
        return {
            "message": "Transformation started in background", 
            "task_id": task.id,
            "status": "Queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/jobs")
async def list_jobs(current_user: UserDB = Depends(get_current_user)):
    """
    Lists all video processing jobs from the database for the current user.
    """
    db = SessionLocal()
    try:
        # User isolation: Only see their own jobs unless admin
        query = db.query(VideoJobDB)
        if current_user.role != "admin":
            query = query.filter(VideoJobDB.user_id == current_user.id)
            
        jobs = query.order_by(VideoJobDB.created_at.desc()).all()
        return jobs
    finally:
        db.close()

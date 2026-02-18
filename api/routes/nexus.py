from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.models import NexusJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.nexus_engine.orchestrator import base_nexus_orchestrator
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/nexus", tags=["Nexus Composition"])

class NexusComposeRequest(BaseModel):
    niche: str
    topic: Optional[str] = None
    visual_paths: Optional[List[str]] = []
    voiceover_paths: Optional[List[str]] = []
    music_path: Optional[str] = None
    script_segments: Optional[List[dict]] = []
    generate_thumbnail: bool = False
    cinema_mode: bool = False

async def run_nexus_composition(job_id: int, request: NexusComposeRequest, db: Session):
    from services.nexus_engine.thumbnail_service import base_thumbnail_generator
    from services.nexus_engine.auto_creator import base_auto_creator
    job = db.query(NexusJobDB).filter(NexusJobDB.id == job_id).first()
    try:
        job.status = "COMPOSING"
        db.commit()
        
        output_path = None
        
        if request.cinema_mode and request.topic:
            # 1. Autonomous Cinema Mode
            output_path = await base_auto_creator.create_cinema_video(
                job_id=job_id,
                topic=request.topic,
                niche=request.niche
            )
        else:
            # 2. Manual Nexus Assembly
            # Thumbnail Generation (if requested)
            if request.generate_thumbnail:
                script_text = " ".join([s.get("text", "") for s in request.script_segments])
                thumbnail_url = await base_thumbnail_generator.generate_thumbnail(script_text)
                logging.info(f"[Nexus] Generated Thumbnail: {thumbnail_url}")

            output_path = await base_nexus_orchestrator.assemble_video(
                job_id=job_id,
                niche=request.niche,
                script_segments=request.script_segments,
                voiceover_paths=request.voiceover_paths,
                visual_paths=request.visual_paths,
                music_path=request.music_path
            )
        
        job.status = "COMPLETED"
        job.output_path = output_path
        job.progress = 100
    except Exception as e:
        import traceback
        logging.error(f"[Nexus] Error: {e}\n{traceback.format_exc()}")
        job.status = "FAILED"
        job.error_log = str(e)
    finally:
        db.commit()

@router.post("/compose")
async def compose_video(request: NexusComposeRequest, background_tasks: BackgroundTasks, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Triggers the high-fidelity video assembly pipeline.
    """
    new_job = NexusJobDB(
        niche=request.niche,
        user_id=current_user.id,
        status="PENDING"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    background_tasks.add_task(run_nexus_composition, new_job.id, request, db)
    
    return {"status": "accepted", "job_id": new_job.id}

@router.get("/job/{job_id}")
async def get_nexus_job(job_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(NexusJobDB).filter(NexusJobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

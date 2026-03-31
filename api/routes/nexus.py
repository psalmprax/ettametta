import logging
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
    blueprint_id: Optional[str] = "viral-reskin"

async def run_nexus_composition(job_id: int, request: NexusComposeRequest, db: Session):
    from services.nexus_engine.thumbnail_service import base_thumbnail_generator
    from services.nexus_engine.auto_creator import base_auto_creator
    job = db.query(NexusJobDB).filter(NexusJobDB.id == job_id).first()
    try:
        job.status = "COMPOSING"
        db.commit()
        from api.routes.ws import notify_nexus_job_update_sync
        notify_nexus_job_update_sync({"id": str(job.id), "status": job.status, "progress": 10, "niche": job.niche})
        
        output_path = None
        
        if request.cinema_mode:
            # 1. Autonomous Cinema Mode
            # Use topic if provided, otherwise fallback to niche as topic
            target_topic = request.topic or f"Viral trends in {request.niche}"
            output_path = await base_auto_creator.create_cinema_video(
                job_id=job_id,
                topic=target_topic,
                niche=request.niche
            )
        elif request.blueprint_id == "story-factory":
             # 2. Strategy for Storytelling Blueprint
             # For now, route to auto creator with a storytelling prompt
             output_path = await base_auto_creator.create_cinema_video(
                job_id=job_id,
                topic="The future of AI Automation", # Example
                niche=request.niche
            )
        else:
            # 3. Manual Nexus Assembly or Viral Reskin (Default)
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
        from api.routes.ws import notify_nexus_job_update_sync
        notify_nexus_job_update_sync({"id": str(job.id), "status": job.status, "progress": 100, "niche": job.niche})
    except Exception as e:
        import traceback
        logging.error(f"[Nexus] Error: {e}\n{traceback.format_exc()}")
        job.status = "FAILED"
        job.error_log = str(e)
        from api.routes.ws import notify_nexus_job_update_sync
        notify_nexus_job_update_sync({"id": str(job.id), "status": job.status, "progress": 0, "niche": job.niche, "error": str(e)})
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

@router.get("/blueprints")
async def list_nexus_blueprints(current_user = Depends(get_current_user)):
    """
    Returns the available Nexus production recipes/blueprints.
    """
    from services.nexus_engine.blueprints import get_blueprints
    return get_blueprints()

@router.get("/jobs")
async def list_nexus_jobs(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the latest production jobs for the Nexus matrix.
    """
    return db.query(NexusJobDB).filter(NexusJobDB.user_id == current_user.id).order_by(NexusJobDB.created_at.desc()).limit(10).all()

@router.get("/job/{job_id}")
async def get_nexus_job(job_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(NexusJobDB).filter(NexusJobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/telemetry")
async def get_nexus_telemetry(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns real-time health and performance metrics for the Nexus cluster.
    """
    from api.utils.models import VideoJobDB
    import time
    import os
    
    start_time = time.time()
    
    # 1. Database Access Metrics (Real Job Count)
    active_nexus_jobs = db.query(NexusJobDB).filter(NexusJobDB.status.in_(["PENDING", "COMPOSING"])).count()
    active_video_jobs = db.query(VideoJobDB).filter(VideoJobDB.status.in_(["Queued", "Downloading", "Processing", "Rendering"])).count()
    
    db_query_time_ms = int((time.time() - start_time) * 1000)
    
    # 2. System Load (Real OS load avg)
    try:
        load_1, _, _ = os.getloadavg()
    except:
        load_1 = 0.0 # Fallback for non-unix or restricted envs
        
    # 3. Real Latency Measurement (Synthetic RTT)
    # We'll use the DB query time as our proxy for cluster responsiveness
    latency_ms = max(db_query_time_ms, 5)
    
    return {
        "status": "OPERATIONAL",
        "cluster_node": os.getenv("NEXUS_NODE_ID", "Global-Master-01"),
        "active_jobs": active_nexus_jobs + active_video_jobs,
        "nexus_active": active_nexus_jobs,
        "video_active": active_video_jobs,
        "latency_ms": latency_ms,
        "timestamp": time.time(),
        "load_avg": round(load_1, 2),
        "signals": [
            {"id": "Signal_01", "status": "ACTIVE" if active_nexus_jobs > 0 else "STANDBY", "offset": f"{latency_ms}ms"},
            {"id": "Signal_02", "status": "READY", "offset": "0ms"}
        ]
    }

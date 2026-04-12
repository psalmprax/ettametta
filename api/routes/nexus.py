import logging
import socket
import os
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.utils.database import get_db, async_session_factory
from api.utils.models import NexusJobDB, BlueprintDB, VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.nexus_engine.orchestrator import base_nexus_orchestrator
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

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


async def run_nexus_composition(job_id: str, request: NexusComposeRequest):
    from services.nexus_engine.thumbnail_service import base_thumbnail_generator
    from services.nexus_engine.auto_creator import base_auto_creator
    from services.nexus_engine.blueprints import execute_blueprint, get_blueprint_by_id
    from api.routes.ws import notify_nexus_job_update_sync

    async with async_session_factory() as db:
        try:
            stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            
            if not job:
                logging.error(f"[Nexus] Job {job_id} not found")
                return

            job.status = "COMPOSING"
            await db.commit()
            await db.refresh(job)

            notify_nexus_job_update_sync(
                {
                    "id": str(job.id),
                    "status": job.status,
                    "progress": 10,
                    "niche": job.niche,
                }
            )

            # Check if this is a blueprint execution
            if hasattr(request, "blueprint_id") and request.blueprint_id:
                blueprint = await get_blueprint_by_id(db, request.blueprint_id)
                if blueprint:
                    # Execute custom blueprint
                    blueprint_inputs = {
                        "niche": request.niche,
                        "topic": getattr(request, "topic", None),
                        "visual_paths": getattr(request, "visual_paths", []),
                        "voiceover_paths": getattr(request, "voiceover_paths", []),
                        "music_path": getattr(request, "music_path", None),
                        "script_segments": getattr(request, "script_segments", []),
                        "job_id": job_id,
                    }

                    execution_result = await execute_blueprint(
                        blueprint, blueprint_inputs, job_id
                    )

                    if execution_result["status"] == "success":
                        job.status = "COMPLETED"
                        job.output_path = (
                            execution_result.get("results", {})
                            .get("egress", {})
                            .get("output_path")
                        )
                        await db.commit()
                        notify_nexus_job_update_sync(
                            {
                                "id": str(job.id),
                                "status": job.status,
                                "progress": 100,
                                "output_path": job.output_path,
                                "niche": job.niche,
                            }
                        )
                        return
                    else:
                        job.status = "FAILED"
                        job.error_log = execution_result.get("error", "Blueprint execution failed")
                        await db.commit()
                        notify_nexus_job_update_sync(
                            {
                                "id": str(job.id),
                                "status": job.status,
                                "progress": 0,
                                "error": job.error_log,
                                "niche": job.niche,
                            }
                        )
                        return

            output_path = None

            if request.cinema_mode:
                # 1. Autonomous Cinema Mode
                target_topic = request.topic or f"Viral trends in {request.niche}"
                output_path = await base_auto_creator.create_cinema_video(
                    job_id=job_id, topic=target_topic, niche=request.niche
                )
            elif request.blueprint_id == "story-factory":
                # 2. Strategy for Storytelling Blueprint
                target_topic = request.topic or f"Viral trends in {request.niche}"
                output_path = await base_auto_creator.create_cinema_video(
                    job_id=job_id, topic=target_topic, niche=request.niche
                )
            else:
                # 3. Manual Nexus Assembly or Viral Reskin (Default)
                if request.generate_thumbnail:
                    script_text = " ".join(
                        [s.get("text", "") for s in request.script_segments]
                    )
                    thumbnail_url = await base_thumbnail_generator.generate_thumbnail(
                        script_text
                    )
                    logging.info(f"[Nexus] Generated Thumbnail: {thumbnail_url}")

                output_path = await base_nexus_orchestrator.assemble_video(
                    job_id=job_id,
                    niche=request.niche,
                    script_segments=request.script_segments,
                    voiceover_paths=request.voiceover_paths,
                    visual_paths=request.visual_paths,
                    music_path=request.music_path,
                )

            job.status = "COMPLETED"
            job.output_path = output_path
            job.progress = 100
            await db.commit()

            notify_nexus_job_update_sync(
                {
                    "id": str(job.id),
                    "status": job.status,
                    "progress": 100,
                    "niche": job.niche,
                }
            )
        except Exception as e:
            import traceback
            logging.error(f"[Nexus] Error in background task: {e}\n{traceback.format_exc()}")
            try:
                # Refresh session and update job status
                stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    job.status = "FAILED"
                    job.error_log = str(e)
                    await db.commit()
                    notify_nexus_job_update_sync(
                        {
                            "id": str(job_id),
                            "status": "FAILED",
                            "progress": 0,
                            "niche": job.niche,
                            "error": str(e),
                        }
                    )
            except Exception as inner_e:
                logging.error(f"[Nexus] Failed to update job error status: {inner_e}")


@router.post("/compose")
async def compose_video(
    request: NexusComposeRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers the high-fidelity video assembly pipeline.
    """
    new_job = NexusJobDB(niche=request.niche, user_id=current_user.id, status="PENDING")
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    background_tasks.add_task(run_nexus_composition, new_job.id, request)

    return {"status": "accepted", "job_id": new_job.id}


@router.get("/blueprints")
async def list_nexus_blueprints(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Returns the available Nexus production recipes/blueprints.
    """
    from services.nexus_engine.blueprints import get_blueprints
    return await get_blueprints(db)


class BlueprintCreate(BaseModel):
    id: str
    name: str
    description: str
    nodes: List[dict]


@router.post("/blueprints")
async def create_nexus_blueprint(
    blueprint: BlueprintCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new custom Nexus blueprint.
    """
    from api.utils.models import BlueprintDB

    # Check if ID exists
    stmt = select(BlueprintDB).where(BlueprintDB.id == blueprint.id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Blueprint ID already exists")

    new_bp = BlueprintDB(
        id=blueprint.id,
        name=blueprint.name,
        description=blueprint.description,
        nodes=blueprint.nodes,
    )
    db.add(new_bp)
    await db.commit()
    await db.refresh(new_bp)

    return new_bp


@router.get("/jobs")
async def list_nexus_jobs(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Returns the latest production jobs for the Nexus matrix.
    """
    stmt = (
        select(NexusJobDB)
        .where(NexusJobDB.user_id == current_user.id)
        .order_by(NexusJobDB.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/job/{job_id}")
async def get_nexus_job(
    job_id: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/telemetry")
async def get_nexus_telemetry(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Returns real-time health and performance metrics for the Nexus cluster.
    """
    start_time = time.time()

    # 1. Database Access Metrics (Real Job Count)
    nexus_active_stmt = select(func.count(NexusJobDB.id)).where(NexusJobDB.status.in_(["PENDING", "COMPOSING"]))
    video_active_stmt = select(func.count(VideoJobDB.id)).where(VideoJobDB.status.in_(["Queued", "Downloading", "Processing", "Rendering"]))
    
    active_nexus_jobs = (await db.execute(nexus_active_stmt)).scalar() or 0
    active_video_jobs = (await db.execute(video_active_stmt)).scalar() or 0

    db_query_time_ms = int((time.time() - start_time) * 1000)

    # 2. System Load (Real OS load avg)
    try:
        load_1, _, _ = os.getloadavg()
    except:
        load_1 = 0.0  # Fallback for non-unix or restricted envs

    # 3. Real Latency Measurement (Synthetic RTT)
    latency_ms = max(db_query_time_ms, 5)
    node_id = os.getenv("NEXUS_NODE_ID", socket.gethostname())

    return {
        "status": "OPERATIONAL",
        "cluster_node": node_id,
        "hostname": node_id,
        "active_jobs": active_nexus_jobs + active_video_jobs,
        "nexus_active": active_nexus_jobs,
        "video_active": active_video_jobs,
        "latency_ms": latency_ms,
        "timestamp": time.time(),
        "load_avg": round(load_1, 2),
        "signals": [
            {
                "id": "Primary_Node",
                "status": "ACTIVE" if active_nexus_jobs > 0 else "IDLE",
                "offset": f"{latency_ms}ms",
            },
            {
                "id": "Neural_Mesh",
                "status": "SYNCED" if active_video_jobs > 0 else "STANDBY",
                "offset": "2ms",
            },
        ],
    }

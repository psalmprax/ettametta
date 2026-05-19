from typing import Any
import logging
import socket
import os
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.api.utils.database import get_db, async_session_factory
from src.shared.enums import SystemJobStatus
from src.api.utils.models import NexusJobDB, BlueprintDB, VideoJobDB
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.services.nexus_engine.orchestrator import base_nexus_service
from pydantic import BaseModel, Field
from src.api.utils.api_responses import success_response
from datetime import datetime, timedelta

router = APIRouter(prefix="/nexus", tags=["Nexus Composition"])


class NexusComposeRequest(BaseModel):
    niche: str = Field(..., description="The high-level market segment (e.g., 'AI', 'Motivation')")
    topic: str | None = Field(None, description="The specific subject of the content. Defaults to 'Viral trends in [niche]' if omitted.")
    visual_paths: list[str] | None = None
    voiceover_paths: list[str] | None = None
    music_path: str | None = None
    script_segments: list[dict] | None = None
    automation_mode: str = Field("manual", description="Automation level: manual, partial, or full")
    generate_thumbnail: bool = False
    cinema_mode: bool = False
    blueprint_id: str | None = Field("viral-reskin", description="The Nexus blueprint to execute.")
    job_metadata: dict | None = None


async def run_nexus_composition(job_id: str, request: NexusComposeRequest):
    from src.services.nexus_engine.thumbnail_service import base_thumbnail_service
    from src.services.nexus_engine.auto_creator import base_creator_service
    from src.services.nexus_engine.blueprints import (
        execute_blueprint,
        get_blueprint_by_id,
    )
    from src.api.routes.ws import notify_nexus_job_update_sync

    async with async_session_factory() as db:
        try:
            stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

            if not job:
                logging.error(f"[Nexus] Job {job_id} not found")
                return

            job.status = SystemJobStatus.COMPOSING
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
                        job.status = SystemJobStatus.COMPLETED
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
                        job.status = SystemJobStatus.FAILED
                        job.error_log = execution_result.get(
                            "error", "Blueprint execution failed"
                        )
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
                output_path = await base_creator_service.create_cinema_video(
                    job_id=job_id, topic=target_topic, niche=request.niche
                )
            elif request.blueprint_id == "story-factory":
                # 2. Strategy for Storytelling Blueprint
                target_topic = request.topic or f"Viral trends in {request.niche}"
                output_path = await base_creator_service.create_cinema_video(
                    job_id=job_id, topic=target_topic, niche=request.niche
                )
            else:
                # 3. Manual Nexus Assembly or Viral Reskin (Default)
                if request.generate_thumbnail:
                    script_text = " ".join(
                        [s.get("text", "") for s in request.script_segments]
                    )
                    thumbnail_uri = await base_thumbnail_service.generate_thumbnail(
                        script_text
                    )
                    logging.info(f"[Nexus] Generated Thumbnail: {thumbnail_uri}")

                output_path = await base_nexus_service.assemble_video(
                    job_id=job_id,
                    niche=request.niche,
                    script_segments=request.script_segments,
                    voiceover_paths=request.voiceover_paths,
                    visual_paths=request.visual_paths,
                    music_path=request.music_path,
                )

            if not output_path:
                job.status = SystemJobStatus.FAILED
                job.error_log = "Pipeline completed but produced no output file"
                await db.commit()
                notify_nexus_job_update_sync({
                    "id": str(job.id),
                    "status": job.status,
                    "progress": 0,
                    "error": job.error_log,
                    "niche": job.niche,
                })
                return

            job.status = SystemJobStatus.COMPLETED
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

            logging.error(
                f"[Nexus] Error in background task: {e}\n{traceback.format_exc()}"
            )
            try:
                # Refresh session and update job status
                stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    job.status = SystemJobStatus.FAILED
                    job.error_log = str(e)
                    await db.commit()
                    notify_nexus_job_update_sync(
                        {
                            "id": str(job_id),
                            "status": SystemJobStatus.FAILED,
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
    db=Depends(get_db),
):
    """
    Triggers the high-fidelity video assembly pipeline.
    """
    # Initialize job with metadata for persistence and studio visibility
    new_job = NexusJobDB(
        niche=request.niche,
        user_id=current_user.id,
        status=SystemJobStatus.QUEUED,
        job_metadata={
            "blueprint_id": request.blueprint_id,
            "cinema_mode": request.cinema_mode,
            **(request.job_metadata or {}),
        },
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    background_tasks.add_task(run_nexus_composition, new_job.id, request)

    return success_response(data={"status": "accepted", "job_id": new_job.id})


@router.get("/blueprints")
async def list_nexus_blueprints(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns the available Nexus production recipes/blueprints.
    """
    from src.services.nexus_engine.blueprints import get_blueprints

    blueprints = await get_blueprints(db)
    return success_response(data=blueprints)


class BlueprintCreate(BaseModel):
    id: str
    name: str
    description: str
    composition_id: str = Field("ViralClip", description="The composition/template to use for rendering")
    nodes: list[dict]


@router.post("/blueprints")
async def create_nexus_blueprint(
    blueprint: BlueprintCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Creates a new custom Nexus blueprint.
    """
    from src.api.utils.models import BlueprintDB

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
        composition_id=blueprint.composition_id,
        nodes=blueprint.nodes,
    )
    db.add(new_bp)
    await db.commit()
    await db.refresh(new_bp)

    return success_response(data=new_bp)


@router.get("/jobs")
async def list_nexus_jobs(
    current_user=Depends(get_current_user), db=Depends(get_db)
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
    return success_response(data=result.scalars().all())


@router.delete("/jobs")
async def clear_nexus_jobs(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Clears the production job history for the current user.
    """
    from sqlalchemy import delete
    stmt = delete(NexusJobDB).where(NexusJobDB.user_id == current_user.id)
    await db.execute(stmt)
    await db.commit()
    return success_response(data={"status": "cleared", "message": "Nexus job history purged."})


@router.get("/stats")
async def get_nexus_stats(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns Nexus performance statistics.
    """
    from sqlalchemy import func

    # Count by status
    total_result = await db.execute(
        select(func.count(NexusJobDB.id)).where(NexusJobDB.user_id == current_user.id)
    )
    total = total_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(NexusJobDB.id)).where(
            NexusJobDB.user_id == current_user.id, NexusJobDB.status == SystemJobStatus.COMPLETED
        )
    )
    completed = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(NexusJobDB.id)).where(
            NexusJobDB.user_id == current_user.id, NexusJobDB.status == SystemJobStatus.FAILED
        )
    )
    failed = failed_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(NexusJobDB.id)).where(
            NexusJobDB.user_id == current_user.id, NexusJobDB.status == SystemJobStatus.QUEUED
        )
    )
    pending = pending_result.scalar() or 0

    return success_response(
        data={
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
        }
    )


@router.get("/jobs/{job_id}/preview")
async def get_job_preview(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Returns the scene breakdown and discovered assets for a Nexus job.
    Used for previewing the narrative structure before final rendering.
    """
    stmt = select(NexusJobDB).where(
        NexusJobDB.id == job_id,
        NexusJobDB.user_id == current_user.id
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    metadata = job.job_metadata or {}
    scenes = metadata.get("preview_scenes", [])
    
    return success_response(data={
        "job_id": job_id,
        "status": job.status,
        "scenes": scenes,
        "scene_count": len(scenes),
        "message": "Preview data retrieved successfully"
    })


@router.get("/queue")
async def get_nexus_queue(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns current job queue status.
    """
    from sqlalchemy import func

    # Get pending/processing jobs
    stmt = (
        select(NexusJobDB)
        .where(
            NexusJobDB.user_id == current_user.id,
            NexusJobDB.status.in_([SystemJobStatus.QUEUED, SystemJobStatus.COMPOSING, SystemJobStatus.ANALYZING]),
        )
        .order_by(NexusJobDB.created_at.asc())
    )
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return success_response(
        data={
            "queue_length": len(jobs),
            "jobs": [
                {
                    "id": j.id,
                    "niche": j.niche,
                    "status": j.status,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                }
                for j in jobs
            ],
        }
    )


@router.get("/job/{job_id}")
async def get_nexus_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return success_response(data=job)


@router.delete("/jobs/{job_id}")
async def delete_nexus_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    from sqlalchemy import delete
    stmt = delete(NexusJobDB).where(
        NexusJobDB.id == job_id, NexusJobDB.user_id == current_user.id
    )
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")
        
    return success_response(data={"status": "deleted", "id": job_id})


@router.get("/telemetry")
async def get_nexus_telemetry(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns real-time health and performance metrics for the Nexus cluster.
    """
    start_time = time.time()

    # 1. Database Access Metrics (Real Job Count)
    nexus_active_stmt = select(func.count(NexusJobDB.id)).where(
        NexusJobDB.status.in_([SystemJobStatus.QUEUED, SystemJobStatus.COMPOSING])
    )
    video_active_stmt = select(func.count(VideoJobDB.id)).where(
        VideoJobDB.status.in_(
            [
                SystemJobStatus.QUEUED,
                SystemJobStatus.PROCESSING,
                SystemJobStatus.RENDERING,
            ]
        )
    )

    active_nexus_jobs = (await db.execute(nexus_active_stmt)).scalar() or 0
    active_video_jobs = (await db.execute(video_active_stmt)).scalar() or 0

    db_query_time_ms = int((time.time() - start_time) * 1000)

    # 2. System Load (Real OS load avg)
    try:
        load_1, _, _ = os.getloadavg()
    except:
        load_1 = 0.0  # Fallback for non-unix or restricted envs

    # 3. Dynamic Hardware Signals (Live Reports)
    node_id = os.getenv("NEXUS_NODE_ID", socket.gethostname())

    # Lazily import services to avoid circular dependencies
    from src.services.video_engine.synthesis_service import base_generative_service
    from src.services.llm.service import unified_llm_service

    gen_report = base_generative_service.get_dependency_report()
    llm_report = unified_llm_service.get_intelligence_report()

    signals = []

    # Synthesis & GPU Signals
    signals.append(
        {
            "id": "GPU_Cluster",
            "status": gen_report.get("circuit_status", "CLOSED"),
            "offset": f"{db_query_time_ms}ms",
        }
    )

    # Driver-level signals (Sample 2 key ones)
    for driver in gen_report.get("drivers", [])[:2]:
        signals.append(
            {
                "id": driver["name"].replace(" ", "_"),
                "status": "HEALTHY"
                if driver.get("status") == "Healthy" or driver.get("installed")
                else "DEGRADED",
                "offset": "0ms",
            }
        )

    # Intelligence Framework Signals
    for fw in llm_report.get("frameworks", []):
        signals.append(
            {
                "id": f"Neural_{fw['name']}",
                "status": fw["status"].upper(),
                "offset": "1ms",
            }
        )

    return success_response(
        data={
            "status": "OPERATIONAL" if gen_report["healthy"] else "DEGRADED",
            "cluster_node": node_id,
            "hostname": node_id,
            "active_jobs": active_nexus_jobs + active_video_jobs,
            "nexus_active": active_nexus_jobs,
            "video_active": active_video_jobs,
            "latency_ms": db_query_time_ms,
            "timestamp": time.time(),
            "load_avg": round(load_1, 2),
            "signals": signals,
        }
    )

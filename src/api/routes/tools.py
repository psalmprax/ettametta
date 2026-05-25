from fastapi import APIRouter, Depends
from pydantic import BaseModel
import os
import logging
from src.api.utils.api_responses import success_response
import sys
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.database import get_db, async_session_factory
from src.shared.enums import SystemJobStatus
from src.api.utils.models import NexusJobDB
from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from src.services.openclaw.skills.external import (
    popular_skills,
    clawhub_loader,
    langchain_service,
    prompt_manager,
    crewai_service,
    ettametta_crew,
    interpreter_service,
    blog_seo_service,
)
from src.services.openclaw.skills.research import research_skill
from src.services.openclaw.skills.analytics import AnalyticsSkill
from src.services.openclaw.skills.ingestion import data_ingestion_skill

social_metrics_skill = AnalyticsSkill()

router = APIRouter(prefix="/tools", tags=["Tools & Skills"])


class ResearchRequest(BaseModel):
    query: str
    limit: int = 5


class IngestionRequest(BaseModel):
    action: str
    subreddit: str | None = None
    feed_url: str | None = None
    language: str | None = None
    sources: list[str] | None = None


class MetricsRequest(BaseModel):
    platform: str
    handle: str


class ClawHubSearchRequest(BaseModel):
    query: str
    category: str | None = None


class PromptTemplateRequest(BaseModel):
    template: str
    variables: dict[str, str] | None = None




class CrewRequest(BaseModel):
    crew_type: str
    topic: str
    worker_id: str | None = None


@router.post("/research")
async def search_academic_papers(request: ResearchRequest):
    """Search academic papers via OpenAlex API (free, no API key)"""
    return success_response(
        data={"result": research_skill.search_papers(request.query, request.limit)}
    )


@router.post("/ingestion")
async def ingest_data(request: IngestionRequest):
    """Multi-source data ingestion (Reddit, RSS, GitHub)"""
    action = request.action

    if action == "reddit":
        return success_response(
            data={
                "result": data_ingestion_skill.reddit_hot(
                    request.subreddit or "technology", 5
                )
            }
        )
    elif action == "rss":
        return success_response(
            data={"result": data_ingestion_skill.fetch_rss(request.feed_url or "")}
        )
    elif action == "github":
        return success_response(
            data={
                "result": data_ingestion_skill.github_trending(request.language or "")
            }
        )
    elif action == "multi":
        return success_response(
            data={
                "result": data_ingestion_skill.ingest_multi_source(
                    request.sources or []
                )
            }
        )
    return success_response(data={"error": f"Unknown action: {action}"})


@router.post("/metrics")
async def get_social_metrics(request: MetricsRequest):
    """Get social media metrics"""
    platform = request.platform
    handle = request.handle

    if platform == "x":
        return success_response(
            data={"result": social_metrics_skill.get_x_followers(handle)}
        )
    elif platform == "reddit":
        return success_response(
            data={"result": social_metrics_skill.get_reddit_stats(handle)}
        )
    elif platform == "github":
        return success_response(
            data={"result": social_metrics_skill.get_github_stats(handle)}
        )
    elif platform == "instagram":
        return success_response(
            data={"result": social_metrics_skill.get_instagram_profile(handle)}
        )
    return success_response(data={"error": f"Unknown platform: {platform}"})


@router.get("/skills/popular")
async def get_popular_skills():
    """Get popular ClawHub skills relevant to ettametta"""
    return success_response(
        data={
            "skills": popular_skills.get_all_skills(),
            "high_priority": popular_skills.get_skills_by_priority("high"),
            "enabled": os.getenv("ENABLE_CREWAI", "false").lower() == "true",
        }
    )


@router.post("/skills/search")
async def search_clawhub_skills(request: ClawHubSearchRequest):
    """Search skills from ClawHub GitHub repository"""
    results = clawhub_loader.search_skills(request.query, request.category)
    return success_response(data={"results": results, "count": len(results)})


@router.get("/skills/categories")
async def get_skill_categories():
    """Get available skill categories from ClawHub"""
    categories = clawhub_loader.list_categories()
    return success_response(data={"categories": categories})


@router.post("/prompt/template")
async def use_prompt_template(request: PromptTemplateRequest):
    """Use a predefined prompt template"""
    template = prompt_manager.get_template(request.template)
    if not template:
        return {"error": f"Template '{request.template}' not found"}

    variables = request.variables or {}
    rendered = prompt_manager.render_template(request.template, **variables)
    return success_response(
        data={
            "template": request.template,
            "system": rendered["system"],
            "human": rendered["human"],
        }
    )


@router.get("/prompt/templates")
async def list_prompt_templates():
    """list all available prompt templates"""
    return success_response(data={"templates": prompt_manager.list_templates()})


@router.get("/langchain/status")
async def langchain_status():
    """Check LangChain integration status"""
    return success_response(
        data={
            "enabled": langchain_service.enabled,
            "message": "LangChain integration active"
            if langchain_service.enabled
            else "Set ENABLE_LANGCHAIN=true to enable",
        }
    )


@router.post("/crew/run")
async def run_crewai_crew(
    request: CrewRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Run a CrewAI crew for content creation as a persistent Nexus Job."""
    from src.api.routes.ws import notify_nexus_job_update_sync

    # Initialize job for visualization
    new_job = NexusJobDB(
        niche=request.topic,
        user_id=current_user.id,
        status=SystemJobStatus.QUEUED,
        job_metadata={
            "crew_type": request.crew_type,
            "worker_id": request.worker_id,
            "agent_deployment": True,
        },
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    async def execute_crew_task(job_id: str, req: CrewRequest):
        async with async_session_factory() as local_db:
            try:
                stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
                res = await local_db.execute(stmt)
                job = res.scalar_one_or_none()
                if not job: return

                job.status = SystemJobStatus.STRATEGIZING
                await local_db.commit()
                notify_nexus_job_update_sync({"id": str(job.id), "status": job.status, "progress": 20})

                if req.crew_type == "content":
                    result = await ettametta_crew.run_content_team(req.topic)
                elif req.crew_type == "affiliate":
                    result = await ettametta_crew.run_affiliate_campaign(req.topic)
                else:
                    result = f"Unknown crew type: {req.crew_type}"

                job.status = SystemJobStatus.COMPLETED
                job.progress = 100
                job.error_log = str(result)[:1000] # Save summary
                await local_db.commit()
                notify_nexus_job_update_sync({"id": str(job.id), "status": job.status, "progress": 100})
            except Exception as e:
                logging.exception(f"[Crew] Deployment failed: {e}")
                # Update job to failed
                stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
                res = await local_db.execute(stmt)
                job = res.scalar_one_or_none()
                if job:
                    job.status = SystemJobStatus.FAILED
                    job.error_log = str(e)
                    await local_db.commit()
                    notify_nexus_job_update_sync({"id": str(job.id), "status": "FAILED", "error": str(e)})

    background_tasks.add_task(execute_crew_task, new_job.id, request)

    return success_response(data={
        "status": "accepted",
        "job_id": new_job.id,
        "crew_type": request.crew_type,
        "worker_id": request.worker_id
    })


@router.get("/crewai/status")
async def crewai_status():
    """Check CrewAI integration status"""
    return success_response(
        data={
            "enabled": crewai_service.enabled,
            "message": "CrewAI integration active"
            if crewai_service.enabled
            else "Set ENABLE_CREWAI=true to enable",
        }
    )




@router.get("/interpreter/status")
async def interpreter_status():
    """Check Open Interpreter status"""
    return success_response(
        data={
            "enabled": interpreter_service.enabled,
            "message": "Open Interpreter active"
            if interpreter_service.enabled
            else "Set ENABLE_INTERPRETER=true to enable",
        }
    )


@router.post("/interpreter/execute")
async def execute_code(request: dict):
    """Execute code in sandbox"""
    code = request.get("code", "")
    language = request.get("language", "python")
    timeout = request.get("timeout", 60)

    result = interpreter_service.execute_code(code, language, timeout)
    return success_response(data=result)


@router.post("/seo/content")
async def generate_seo_content(request: dict):
    """Generate SEO-optimized blog content"""
    topic = request.get("topic", "")
    content_type = request.get("content_type", "blog")
    word_count = request.get("word_count", 500)

    result = blog_seo_service.generate_seo_content(topic, content_type, word_count)
    return success_response(data=result)


@router.get("/nexus/workforce/status")
async def nexus_workforce_status():
    """Unified status check for Workforce Hub services"""
    return success_response(
        data={
            "crewai": {
                "enabled": crewai_service.enabled,
                "status": "ONLINE" if crewai_service.enabled else "OFFLINE",
                "message": "CrewAI integration active" if crewai_service.enabled else "Set ENABLE_CREWAI=true to enable",
            },
            "interpreter": {
                "enabled": interpreter_service.enabled,
                "status": "SECURE" if interpreter_service.enabled else "OFFLINE",
                "message": "Open Interpreter active" if interpreter_service.enabled else "Set ENABLE_INTERPRETER=true to enable",
            },
            "timestamp": os.getloadavg()[0] # Example health metric
        }
    )

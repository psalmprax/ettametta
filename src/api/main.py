from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.api.utils.database import engine, Base  # noqa: F401 — imported to register models

from src.api.config import settings
import os
import asyncio
from src.services.infrastructure.recovery_service import base_recovery_service
from src.services.analytics.consistency_sentinel import base_consistency_sentinel
from src.api.utils.limiter import limiter

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.middleware.tracing import (
    TracingMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from src.api.exception_handlers import register_exception_handlers
from src.api.routes.chaos import router as chaos_router
from src.shared.observability import setup_observability, get_logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

setup_observability("ettametta-api")
logger = get_logger(__name__)

app = FastAPI(
    title="ettametta API",
    description="""## Overview
ettametta is an AI-powered content creation and monetization platform.

## Features
- **Discovery**: Find trending content across platforms
- **Video Generation**: Create videos using AI models
- **Publishing**: Multi-platform publishing (YouTube, TikTok, etc.)
- **Analytics**: Performance tracking and insights
- **Monetization**: Affiliate links, empire building

## Authentication
Most endpoints require JWT authentication. Get token from `/api/v1/auth/login`.

## Rate Limits
- Free tier: 5 requests/hour
- Basic tier: 50 requests/hour
- Sovereign tier: 500 requests/hour

## Errors
All errors follow this format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "timestamp": "ISO timestamp"
  }
}
```
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
Instrumentator().instrument(app).expose(app)
FastAPIInstrumentor.instrument_app(app)

# Middleware stack (order matters: outermost first)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TracingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Exception handlers (registered from extracted module)
register_exception_handlers(app)

# Route imports
from src.api.routes import (
    video_jobs,
    discovery,
    auth,
    video_generate,
    health,
    ws,
    proxy,
    internal,
    video_transform,
    content_editor,
    analytics,
    monetization,
    billing,
    settings as route_settings,
    nexus,
    security,
    persona,
    webhooks,
    admin,
    no_face,
    ab_testing,
    remotion,
    agent,
    knowledge_base,
    credits,
    autonomous_video,
    autonomous_leads,
    autonomous_remix,
    video_preview,
    publishing,
    monetization_dashboard,
    zero,
    opencli,
    tools,
    llm,
    reasoning,
    notifications,
)
from src.api.routes.publish import router as publish_router

from fastapi.staticfiles import StaticFiles

os.makedirs(settings.STORAGE_OUTPUT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.STORAGE_OUTPUT_DIR), name="static")

# Rate Limiter setup
app.state.limiter = limiter

# CORS
cors_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0)(\.sslip\.io)?(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def seed_monitored_niches():
    from src.api.utils.database import AsyncSessionLocal
    from src.api.utils.models import MonitoredNiche
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(func.count()).select_from(MonitoredNiche))
            count = result.scalar()

            if count == 0:
                logger.info("[Startup] Seeding default monitored niches...")
                default_niches = [
                    "Motivation",
                    "AI Technology",
                    "Stoic Wisdom",
                    "Market Trends",
                ]
                for n in default_niches:
                    db.add(MonitoredNiche(niche=n, is_active=True))
                await db.commit()
        except Exception as e:
            logger.error(f"[Startup] Error seeding niches: {e}")
            await db.rollback()


@app.on_event("startup")
async def startup_event():
    # Initialize Redis Cache
    redis_instance = aioredis.from_url(
        settings.REDIS_URL, encoding="utf8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis_instance), prefix="fastapi-cache")
    await seed_monitored_niches()

    # Start Hot-Reload Listener
    from src.api.utils.hot_reload import start_hot_reload_listener

    asyncio.create_task(start_hot_reload_listener())

    # Standard: Stateful Recovery - Distributed System Correctness
    await base_recovery_service.sync_all_vitals()

    # Standard: Autonomous Enforcement - ConsistencySentinel
    asyncio.create_task(base_consistency_sentinel.start())
    logger.info("🛡️ [Startup] ConsistencySentinel enforcement loop activated.")

    # Agent Zero Auto-Resume
    from src.services.agent_zero.agent import base_agent_zero_service

    asyncio.create_task(base_agent_zero_service.load_and_resume())
    logger.info("🤖 [Startup] Agent Zero state recovery initiated.")


# API Versioning: v1
from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1")

# Each router defines its own prefix — do NOT add duplicate prefixes here
v1_router.include_router(auth.router, tags=["Authentication"])
v1_router.include_router(discovery.router, tags=["Discovery"])
v1_router.include_router(video_transform.router, tags=["Video Engine"])
v1_router.include_router(video_generate.router, tags=["Video Engine"])
v1_router.include_router(content_editor.router, tags=["Content Editor"])
v1_router.include_router(video_jobs.router, tags=["Video Engine"])
v1_router.include_router(publish_router, tags=["Publishing"])
v1_router.include_router(analytics.router, tags=["Analytics"])
v1_router.include_router(monetization.router, tags=["Monetization"])
v1_router.include_router(billing.router, tags=["Billing"])
v1_router.include_router(route_settings.router, tags=["Settings"])
v1_router.include_router(nexus.router, tags=["Nexus Agent"])
v1_router.include_router(security.router, tags=["Security"])
v1_router.include_router(persona.router, tags=["Persona"])
v1_router.include_router(webhooks.router, tags=["Webhooks"])
v1_router.include_router(admin.router, tags=["Admin"])
v1_router.include_router(no_face.router, tags=["Automation"])
v1_router.include_router(ab_testing.router, tags=["Growth"])
v1_router.include_router(remotion.router, tags=["Remotion"])
v1_router.include_router(agent.router, tags=["AI Agents"])
v1_router.include_router(credits.router, tags=["Credits & Billing"])
v1_router.include_router(zero.router, tags=["Agent Zero"])
v1_router.include_router(opencli.router, tags=["opencli-rs"])
v1_router.include_router(tools.router, tags=["Free Tools"])
v1_router.include_router(llm.router, tags=["LLM - Multi-Provider"])
v1_router.include_router(reasoning.router)
v1_router.include_router(knowledge_base.router, tags=["Knowledge Base"])
v1_router.include_router(ws.router, tags=["WebSockets"])
v1_router.include_router(health.router, tags=["Health"])
v1_router.include_router(proxy.router, tags=["Proxy"])
v1_router.include_router(internal.router, tags=["Internal"])
v1_router.include_router(autonomous_video.router, tags=["Autonomous Video"])
v1_router.include_router(autonomous_leads.router, tags=["Autonomous Leads"])
v1_router.include_router(autonomous_remix.router, tags=["Autonomous Remix"])
v1_router.include_router(video_preview.router, tags=["Video Preview/Download"])
v1_router.include_router(publishing.router, tags=["Publishing"])
v1_router.include_router(monetization_dashboard.router, tags=["Monetization Dashboard"])
v1_router.include_router(notifications.router, tags=["Notifications"])

app.include_router(v1_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} is running",
        "env": settings.ENV,
        "version": "v1",
    }


@app.post("/api/v1/errors")
async def report_frontend_error(request: Request):
    """Receives frontend error reports from GlobalErrorBoundary."""
    try:
        body = await request.json()
        logger.error(
            f"[Frontend Error] {body.get('message', 'Unknown')} | "
            f"Stack: {body.get('stack', 'N/A')[:500]} | "
            f"Component: {body.get('componentStack', 'N/A')[:200]}"
        )
    except Exception as e:
        logger.error(f"Failed to parse frontend error report: {e}")
    return {"status": "logged"}


# Health endpoint is now in routes/health.py with DB/Redis dependency checks
# Keep /health for Docker healthcheck compatibility
@app.get("/health")
async def health_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/health")


# Chaos Engineering endpoints (extracted to routes/chaos.py)
app.include_router(chaos_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request, APIRouter, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from src.api.utils.database import engine, Base, AsyncSessionLocal
from src.api.utils.models import SystemSettings, ContentCandidateDB, MonitoredNiche
from src.api.utils.user_models import UserDB
from src.api.utils import credit_models  # Import to register credit models with SQLAlchemy
from sqlalchemy import select, func


# Tables should be managed via Alembic in production.

from src.services.security.service import base_security_service
from src.api.config import settings
import os
import time
import logging
import asyncio
from src.services.infrastructure.chaos_utility import base_chaos_service
import asyncio
from src.services.infrastructure.recovery_service import base_recovery_service
from src.services.analytics.consistency_sentinel import base_consistency_sentinel
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from src.api.utils.limiter import limiter, get_user_rate_limit, get_remote_address

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.utils.tracing import set_request_id, get_request_id, setup_tracing_logger
import uuid
from typing import Any

logger = setup_tracing_logger(__name__)

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


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if settings.ENV == "production":
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.scope["type"] == "websocket":
            return await call_next(request)
            
        # Extract or generate Request-ID
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(rid)
        
        response = await call_next(request)
        
        # Propagate back to client
        response.headers["X-Request-ID"] = rid
        return response

app.add_middleware(TracingMiddleware)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.scope["type"] == "websocket":
            return await call_next(request)
            
        start_time = time.time()
        rid = get_request_id()
        response = await call_next(request)
        process_time = time.time() - start_time
        if settings.ENV == "production" or settings.DEBUG:
            logger.info(
                f"[{rid}] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
            )
        response.headers["X-Process-Time"] = str(process_time)
        return response


app.add_middleware(RequestLoggingMiddleware)

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
    publish,
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
    zero,
    opencli,
    tools,
    llm,
    reasoning,
)

from fastapi.staticfiles import StaticFiles

os.makedirs(settings.STORAGE_OUTPUT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.STORAGE_OUTPUT_DIR), name="static")

# Rate Limiter setup
app.state.limiter = limiter


from src.api.utils.api_responses import error_response, api_error_response, APIError
@app.exception_handler(StarletteHTTPException)
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: Any):
    """Normalize HTTPException to standard nested error format."""
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "An error occurred")
    
    if status_code == 404:
        return error_response(
            code="NOT_FOUND",
            message=f"Endpoint '{request.url.path}' not found.",
            status_code=404,
        )
        
    return error_response(
        code="HTTP_ERROR",
        message=detail if isinstance(detail, str) else "An error occurred",
        status_code=status_code,
        details=detail if isinstance(detail, dict) else {"detail": detail},
    )


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Please slow down.",
        status_code=429,
        details={"retry_after": exc.detail if hasattr(exc, "detail") else "60s"},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    message = "An internal database error occurred."
    if settings.DEBUG:
        message = f"Database Error: {str(exc)}"

    return error_response(
        code="DB_ERROR",
        message=message,
        status_code=500,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    details = []
    for err in exc.errors():
        cleaned = {}
        for k, v in err.items():
            if isinstance(v, Exception):
                cleaned[k] = str(v)
            elif isinstance(v, dict):
                cleaned[k] = {
                    sk: str(sv) if isinstance(sv, Exception) else sv
                    for sk, sv in v.items()
                }
            else:
                cleaned[k] = v
        details.append(cleaned)

    return error_response(
        code="VALIDATION_ERROR",
        message="Invalid data provided.",
        status_code=422,
        details={"errors": details},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    logger.warning(f"Value error: {exc}")
    return error_response(
        code="VALUE_ERROR",
        message=str(exc),
        status_code=400,
    )


@app.exception_handler(APIError)
async def api_error_exception_handler(request: Request, exc: APIError):
    """Handler for custom APIError types."""
    return api_error_response(exc, request.url.path, request.method)


import traceback
from src.api.utils.models import SelfHealingAuditDB



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Standard: Hardening Observability - Fault Persistence
    try:
        async with AsyncSessionLocal() as db:
            audit = SelfHealingAuditDB(
                path=request.url.path,
                method=request.method,
                exception_type=type(exc).__name__,
                message=str(exc),
                traceback=traceback.format_exc(),
            )
            db.add(audit)
            await db.commit()
            
            # Standard 3.12: Compliance Hardening (EU AI Act Article 71)
            # Notify external surveillance authorities of serious incidents
            from src.services.infrastructure.incident_reporting import base_incident_service
            await base_incident_service.report_incident(
                incident_type="SYSTEM_CRASH",
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "audit_id": audit.id
                },
                severity="CRITICAL"
            )
    except Exception as db_exc:
        logger.error(f"Failed to persist fault audit or report incident: {db_exc}")

    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Our engineers have been notified.",
        status_code=500,
    )



app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

cors_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

# Standard 1.2: Permissive CORS with credential support
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|[0-9\.]+)(\.sslip\.io)?(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def seed_monitored_niches():
    async with AsyncSessionLocal() as db:
        try:
            # Async-compatible count check
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
v1_router = APIRouter(prefix="/v1")

# Each router defines its own prefix - do NOT add duplicate prefixes here
v1_router.include_router(auth.router, tags=["Authentication"])
v1_router.include_router(discovery.router, tags=["Discovery"])
v1_router.include_router(video_transform.router, tags=["Video Engine"])
v1_router.include_router(video_generate.router, tags=["Video Engine"])
v1_router.include_router(content_editor.router, tags=["Content Editor"])
v1_router.include_router(video_jobs.router, tags=["Video Engine"])
v1_router.include_router(publish.router, tags=["Publishing"])
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

# Include versioned router under /api
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


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "v1",
        "services": {"ai_video": settings.AI_VIDEO_PROVIDER, "cache": "redis"},
    }


# ─── Chaos Engineering Endpoints (Reality Run Protocol) ───────────
chaos_router = APIRouter(prefix="/v1/chaos", tags=["Chaos"])


@chaos_router.post("/latency")
async def inject_latency(service: str, delay_ms: int):
    """Adds artificial delay to a service."""
    await base_chaos_service.inject_latency(service, delay_ms)
    return {"status": "injected", "service": service, "delay": f"{delay_ms}ms"}


@chaos_router.post("/crash")
async def simulate_crash():
    """Simulates a worker crash notification."""
    await base_chaos_service.simulate_worker_crash()
    return {"status": "crash_simulated"}


@chaos_router.post("/exhaustion")
async def induce_exhaustion(platform: str):
    """Fakes a 429/403 for a specific platform API."""
    await base_chaos_service.induce_api_exhaustion(platform)
    return {"status": "exhaustion_active", "platform": platform}


@chaos_router.post("/scenario")
async def run_chaos_scenario(name: str):
    """Executes an orchestrated Killer Combo scenario (blackout/cascade/storm)."""
    report = await base_chaos_service.run_scenario(name)
    return report


@chaos_router.post("/continuous/start")
async def start_continuous_chaos(intensity: str = "medium", duration_minutes: int = 30):
    """Starts a background continuous chaos injection loop."""
    result = await base_chaos_service.start_continuous_chaos(
        intensity, duration_minutes
    )
    return result


@chaos_router.post("/continuous/stop")
async def stop_continuous_chaos():
    """Stops continuous chaos and clears all active faults."""
    result = await base_chaos_service.stop_continuous_chaos()
    return result


@chaos_router.post("/clear")
async def clear_all_faults():
    """Emergency: removes all active chaos faults from the system."""
    await base_chaos_service.clear_all_faults()
    return {"status": "all_faults_cleared"}


@chaos_router.get("/report")
async def get_chaos_report():
    """Returns current chaos state, sentinel health, and recovery status."""
    from src.services.infrastructure.recovery_service import base_recovery_service

    return {
        "chaos": base_chaos_service.get_chaos_report(),
        "sentinel": base_consistency_sentinel.get_status(),
        "recovery": base_recovery_service.get_status(),
    }


app.include_router(chaos_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

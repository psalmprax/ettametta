from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.exceptions import RequestValidationError
from api.utils.database import engine, Base, SessionLocal
from api.utils.models import SystemSettings, ContentCandidateDB, MonitoredNiche
from api.utils.user_models import UserDB
from api.utils import credit_models  # Import to register credit models with SQLAlchemy

# Ensure tables are created before importing routes/services that might query them at module level
Base.metadata.create_all(bind=engine)

from services.security.service import base_security_sentinel
from api.config import settings
import os
import time
import logging
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from api.utils.limiter import limiter, get_user_rate_limit, get_remote_address

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

app = FastAPI(title=settings.APP_NAME)
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


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        if settings.ENV == "production" or settings.DEBUG:
            logger.info(
                f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
            )
        response.headers["X-Process-Time"] = str(process_time)
        return response


app.add_middleware(RequestLoggingMiddleware)

from api.routes import (
    discovery,
    video,
    publish,
    analytics,
    auth,
    settings as settings_router,
    ws,
    no_face,
    monetization,
    nexus,
    ab_testing,
    security,
    billing,
    remotion,
    admin,
    trading,
    agent,
    credits,
    persona,
    webhooks,
    zero,
    opencli,
)

from fastapi.staticfiles import StaticFiles

os.makedirs("outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="outputs"), name="static")

# Rate Limiter setup
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please slow down.",
            "retry_after": exc.detail if hasattr(exc, "detail") else "60s",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "message": "An internal database error occurred. Please try again later.",
            "code": "DB_ERROR",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid data provided.",
            "details": exc.errors(),
            "code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Our engineers have been notified.",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )


app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

cors_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def seed_monitored_niches():
    db = SessionLocal()
    try:
        count = db.query(MonitoredNiche).count()
        if count == 0:
            print("[Startup] Seeding default monitored niches...")
            default_niches = [
                "Motivation",
                "AI Technology",
                "Stoic Wisdom",
                "Market Trends",
            ]
            for n in default_niches:
                db.add(MonitoredNiche(niche=n, is_active=True))
            db.commit()
    except Exception as e:
        print(f"[Startup] Error seeding niches: {e}")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    # Initialize Redis Cache
    redis_instance = aioredis.from_url(
        settings.REDIS_URL, encoding="utf8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis_instance), prefix="fastapi-cache")
    await seed_monitored_niches()


# API Versioning: v1
v1_router = APIRouter(prefix="/v1")

# Each router defines its own prefix - do NOT add duplicate prefixes here
v1_router.include_router(auth.router, tags=["Authentication"])
v1_router.include_router(discovery.router, tags=["Discovery"])
v1_router.include_router(video.router, tags=["Video Engine"])
v1_router.include_router(publish.router, tags=["Publishing"])
v1_router.include_router(analytics.router, tags=["Analytics"])
v1_router.include_router(monetization.router, tags=["Monetization"])
v1_router.include_router(billing.router, tags=["Billing"])
v1_router.include_router(settings_router.router, tags=["Settings"])
v1_router.include_router(nexus.router, tags=["Nexus Agent"])
v1_router.include_router(security.router, tags=["Security"])
v1_router.include_router(persona.router, tags=["Persona"])
v1_router.include_router(webhooks.router, tags=["Webhooks"])
v1_router.include_router(admin.router, tags=["Admin"])
v1_router.include_router(no_face.router, tags=["Automation"])
v1_router.include_router(ab_testing.router, tags=["Growth"])
v1_router.include_router(remotion.router, tags=["Remotion"])
v1_router.include_router(trading.router, tags=["Trading"])
v1_router.include_router(agent.router, tags=["AI Agents"])
v1_router.include_router(credits.router, tags=["Credits & Billing"])
v1_router.include_router(zero.router, tags=["Agent Zero"])
v1_router.include_router(opencli.router, tags=["opencli-rs"])

# Include versioned router under /api
app.include_router(v1_router, prefix="/api")

# WebSocket routes (non-versioned for stability)
app.include_router(ws.router)


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

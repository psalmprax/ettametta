from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from api.routes import discovery, video, publish, analytics, auth, settings as settings_router, ws, no_face, monetization, nexus, ab_testing, security, billing, remotion, admin
from services.security.service import base_security_sentinel
from api.config import settings
import os
import time
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Only add security headers in production
        if settings.ENV == "production":
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Gzip compression for performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request Logging Middleware (Production)
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Log in production or when debug is enabled
        if settings.ENV == "production" or settings.DEBUG:
            logger.info(
                f"{request.method} {request.url.path} "
                f"- Status: {response.status_code} "
                f"- Time: {process_time:.3f}s"
            )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

app.add_middleware(RequestLoggingMiddleware)

from api.utils.models import SystemSettings, ContentCandidateDB
from api.utils.database import engine, Base

# Initialize Database Tables
from api.utils.user_models import UserDB
Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles
os.makedirs("outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="outputs"), name="static")

@app.on_event("startup")
async def seed_monitored_niches():
    """
    Seeds default niches to monitor if none exist.
    """
    from api.utils.database import SessionLocal
    from api.utils.models import MonitoredNiche
    
    db = SessionLocal()
    try:
        count = db.query(MonitoredNiche).count()
        if count == 0:
            print("[Startup] Seeding default monitored niches...")
            default_niches = ["Motivation", "AI Technology", "Stoic Wisdom", "Market Trends"]
            for n in default_niches:
                db.add(MonitoredNiche(niche=n, is_active=True))
            db.commit()
    except Exception as e:
        print(f"[Startup] Error seeding niches: {e}")
    finally:
        db.close()

# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://130.61.26.105:3000",
        "http://130.61.26.105:8080",
        "http://130.61.26.105",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],

    allow_origin_regex="http://130\\.61\\.26\\.105(:\\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Removed log_requests middleware to prevent interference with WebSocket handshakes.


# Router Includes
app.include_router(auth.router)

app.include_router(discovery.router)
app.include_router(video.router)
app.include_router(publish.router)
app.include_router(analytics.router)
app.include_router(settings_router.router)
app.include_router(ws.router)
app.include_router(no_face.router)
app.include_router(monetization.router)
app.include_router(nexus.router)
app.include_router(ab_testing.router)
app.include_router(security.router)
app.include_router(billing.router)
app.include_router(remotion.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running", "env": settings.ENV}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "debug": settings.DEBUG,
        "env": settings.ENV,
        "services": {
            "sound_design": settings.ENABLE_SOUND_DESIGN,
            "motion_graphics": settings.ENABLE_MOTION_GRAPHICS,
            "ai_video": settings.AI_VIDEO_PROVIDER,
            "langchain": settings.ENABLE_LANGCHAIN,
            "crewai": settings.ENABLE_CREWAI
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

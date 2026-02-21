from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import discovery, video, publish, analytics, auth, settings as settings_router, ws, no_face, monetization, nexus, ab_testing, security
from services.security.service import base_security_sentinel
from api.config import settings
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI(title=settings.APP_NAME)

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
app.include_router(persona.router)

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running", "env": settings.ENV}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "debug": settings.DEBUG}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

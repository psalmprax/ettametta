from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import discovery, video, publish, analytics, auth, settings as settings_router, ws, no_face, monetization, nexus, ab_testing
from api.config import settings
import os

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

@app.on_event("startup")
async def seed_default_user():
    """
    Ensures a default admin user exists for recovery purposes.
    """
    from api.utils.database import SessionLocal
    from api.utils.user_models import UserDB, UserRole, SubscriptionTier
    from api.utils.security import get_password_hash
    
    db = SessionLocal()
    try:
        user_count = db.query(UserDB).count()
        if user_count == 0:
            print("[Startup] Seeding default admin user...")
            admin = UserDB(
                username="psalmprax",
                email="psalmprax@example.com",
                hashed_password=get_password_hash("viral_forge_pass"),
                role=UserRole.ADMIN,
                subscription=SubscriptionTier.PREMIUM
            )
            db.add(admin)
            db.commit()
    except Exception as e:
        print(f"[Startup] Error seeding admin: {e}")
    finally:
        db.close()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 401:
        print(f"[DEBUG AUTH] 401 at {request.url.path} | Headers: {dict(request.headers)}")
    return response

from fastapi import Request

from fastapi.staticfiles import StaticFiles

# Ensure outputs directory exists
os.makedirs("outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="outputs"), name="static")

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

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running", "env": settings.ENV}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "debug": settings.DEBUG}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

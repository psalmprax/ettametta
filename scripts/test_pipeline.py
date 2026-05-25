import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_full_pipeline():
    print("🚀 Starting ettametta End-to-End Pipeline Test...")
    
    # Initialize Database Tables
    from api.utils.database import engine, Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database Tables Initialized.")
    
    api_url = "http://localhost:8001"
    
    # 1. Check AI Health (Groq)
    print("\n[Step 1] Checking AI Brain (Groq)...")
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        print("❌ FAILED: GROQ_API_KEY not found in .env. Please add it to run the real brain.")
        # We can continue with a mock check if needed, but for E2E we want the real thing
    else:
        print("✅ Groq Key Detected.")

    # 2. Trigger Go Scanner via Python Proxy
    print("\n[Step 2] Triggering High-Concurrency Go Scanner proxy...")
    try:
        async with httpx.AsyncClient() as client:
            # We assume niche "Motivation"
            resp = await client.post(f"{api_url}/discovery/scan", json={"niches": ["Motivation", "AI"]})
            if resp.status_code == 200:
                print(f"✅ Scanner triggered. Response: {resp.json().get('message')}")
            else:
                print(f"❌ Scanner Bridge Failed: {resp.text}")
    except Exception:
        print("⚠️ API not running locally? (This test assumes uvicorn is running on port 8000)")

    # 4. Check Monetization (Auto-Merch & Affiliate)
    print("\n[Step 4] Verifying Monetization (Hardened)...")
    from services.monetization.auto_merch import AutoMerchService
    from services.affiliate.service import AffiliateService
    
    merch = AutoMerchService()
    affiliate = AffiliateService()
    
    print("✅ AutoMerch initialized. Ready for Printful pushing.")
    if affiliate.is_enabled():
        print("✅ Affiliate service enabled.")
    else:
        print("⚠️ Affiliate service disabled (ENABLE_AFFILIATE_API=false)")

    # 5. Check Audio Engine (Sound Design)
    print("\n[Step 5] Checking Audio Engine (Sound Design)...")
    from services.audio.sound_design import SoundDesignService
    sound = SoundDesignService()
    if sound.enabled:
        print("✅ Sound Design enabled with MoviePy mixing.")
    else:
        print("⚠️ Sound Design disabled (ENABLE_SOUND_DESIGN=false)")

    # 6. Check Database Persistence
    print("\n[Step 6] Checking Persistence Layer...")
    from api.utils.database import SessionLocal
    from services.discovery.db_models import DBContentCandidate
    db = SessionLocal()
    count = db.query(DBContentCandidate).count()
    print(f"📊 Items in Database: {count}")
    db.close()

    print("\n🏁 Test Summary complete. Next step: Run 'uvicorn api.main:app' and provide your GROQ key to see the live brain in action!")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

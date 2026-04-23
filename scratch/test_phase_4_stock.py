import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("src"))

from services.video_engine.stock_service import StockService
from api.config import settings

async def test_phase_4_stock():
    print("🚀 Testing Phase 4: Stock Synthesis...")
    
    stock_service = StockService()
    
    # Check if PEXELS_API_KEY is available
    if not settings.PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY not found in config. Testing fallback behavior.")
    else:
        print(f"✅ PEXELS_API_KEY found: {settings.PEXELS_API_KEY}. Testing real API pull.")

    niche = "cyberpunk city street"
    print(f"🔍 Searching for B-roll: '{niche}'")
    
    try:
        # fetch_b_roll is async in some versions, let's check
        import inspect
        if inspect.iscoroutinefunction(stock_service.fetch_b_roll):
            results = await stock_service.fetch_b_roll(niche, count=2)
        else:
            results = stock_service.fetch_b_roll(niche, count=2)
            
        print(f"📊 Results: {len(results)} clips found.")
        for i, clip in enumerate(results):
            print(f"  Clip {i+1}: {clip.get('url', 'No URL')} (Duration: {clip.get('duration', 'N/A')}s)")
            
        if len(results) == 0:
            print("❌ No stock clips found. Check API key or search term.")
        else:
            print("✅ Phase 4 Test PASSED (Discovery).")
            
    except Exception as e:
        print(f"❌ Phase 4 Test FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_phase_4_stock())

import asyncio
import os
from services.discovery.service import base_discovery_service

async def test_discovery():
    print("🚀 Starting Intelligence-Driven Discovery Test...")
    niche = "motivation"
    
    # We'll skip real caching into Redis for the local test if it's not running
    # but we'll see the scanner outputs
    print(f"🔍 Searching for high-potential '{niche}' content across YouTube and TikTok...")
    
    candidates = await base_discovery_service.find_trending_content(niche)
    
    print(f"\n✅ Found {len(candidates)} total candidates.")
    print("-" * 50)
    
    for i, c in enumerate(candidates[:10]):
        duration = c.metadata.get("duration", "N/A")
        print(f"Rank {i+1} [{c.platform}] ({duration}): {c.title}")
        print(f"   URL: {c.source_url}")
        print(f"   Author: {c.creator_name}")
        print(f"   Engagement: {c.engagement_score:.2%}")
        print("-" * 30)

if __name__ == "__main__":
    # Ensure we have access to the correct python path
    import sys
    sys.path.append(os.getcwd())
    
    asyncio.run(test_discovery())

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.engines.intelligent_video_workflow import discover_multi_platform

async def test_discovery():
    print("Testing Phase 1: Intelligent Discovery...")
    topic = "AI productivity tools viral 2026"
    leads = await discover_multi_platform(topic, max_per_platform=1, session_id="test_session")
    
    if leads:
        print(f"✅ Success! Found {len(leads)} leads.")
        for lead in leads:
            print(f"  - [{lead['platform']}] {lead['title']}")
    else:
        print("❌ Failed: No leads found.")

if __name__ == "__main__":
    asyncio.run(test_discovery())

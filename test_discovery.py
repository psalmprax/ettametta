import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.engines.intelligent_video_workflow import discover_multi_platform

async def test():
    topic = "AI productivity tools 2026"
    print(f"Testing discovery for: {topic}")
    leads = await discover_multi_platform(topic, max_per_platform=3)
    print(f"Found {len(leads)} leads")
    for i, lead in enumerate(leads):
        print(f"{i+1}. {lead.get('title')} ({lead.get('platform')})")

if __name__ == "__main__":
    asyncio.run(test())

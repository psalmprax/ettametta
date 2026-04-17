import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.discovery.public_domain_scanner import base_public_domain_scanner

async def test_scanner():
    logging.basicConfig(level=logging.INFO)
    queries = ["Space Exploration", "Mars colonization", "NASA discoveries"]
    for q in queries:
        print(f"\n🔍 Testing query: {q}")
        results = await base_public_domain_scanner.scan_trends(q)
        print(f"✅ Found {len(results)} results")
        for r in results[:2]:
            print(f"  - [{r.platform}] {r.title}: {r.url}")

if __name__ == "__main__":
    asyncio.run(test_scanner())

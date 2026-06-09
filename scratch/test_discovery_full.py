import asyncio
import sys
sys.path.insert(0, "/app")

from src.services.discovery.service import base_discovery_service

print("=== Scanner registration ===")
for s in base_discovery_service.scanners:
    p = getattr(s, "default_platform", "?")
    print(f"  {type(s).__name__} (platform={p})")
for s in base_discovery_service.global_scanners:
    p = getattr(s, "default_platform", "?")
    print(f"  {type(s).__name__} (global, platform={p})")
print(f"_scraper_url: {getattr(base_discovery_service, '_scraper_url', 'NOT DEFINED')}")

async def test():
    print("\n=== Testing find_trending_content for 'AI' ===")
    results = await base_discovery_service.find_trending_content(
        "AI", horizon="30d", tier="free", deep_scan=False, region="US"
    )
    print(f"Results: {len(results)}")
    for c in results[:10]:
        src = (c.metadata_json or {}).get("source", "none")
        print(f"  [{c.platform}] {c.title[:60]} views={c.view_count} src={src}")
    return results

asyncio.run(test())
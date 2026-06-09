#!/usr/bin/env python3
"""Test discovery pipeline on remote."""
import asyncio
import sys
sys.path.insert(0, "/app")

from src.services.discovery.service import base_discovery_service

print("=== SCANNER REGISTRATION ===")
print(f"_scraper_url: {base_discovery_service._scraper_url}")
print("Main scanners:")
for s in base_discovery_service.scanners:
    plat = getattr(s, "default_platform", getattr(s, "platform", "?"))
    print(f"  {type(s).__name__} (platform={plat})")
print("Global scanners:")
for s in base_discovery_service.global_scanners:
    print(f"  {type(s).__name__}")

print("\n=== TESTING find_trending_content ===")
async def test():
    results = await base_discovery_service.find_trending_content(
        "AI", horizon="30d", tier="free", deep_scan=False, region="US"
    )
    print(f"Total results: {len(results)}")
    for r in results[:10]:
        src = (r.metadata_json or {}).get("source", "none")
        print(f"  [{r.platform}] {r.title[:55]} | views={r.view_count} | src={src}")

asyncio.run(test())
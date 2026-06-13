#!/usr/bin/env python3
import asyncio
import sys
import logging

logging.basicConfig(level=logging.WARNING)
sys.path.insert(0, "/app")

from src.services.discovery.service import base_discovery_service

async def main():
    print("=== SCANNERS ===")
    for s in base_discovery_service.scanners:
        p = getattr(s, "default_platform", "?")
        n = type(s).__name__
        url = getattr(s, "scraper_url", "?")
        print(f"  {n} platform={p} scraper_url={url}")

    print("\n=== GLOBAL SCANNERS ===")
    for s in base_discovery_service.global_scanners:
        n = type(s).__name__
        url = getattr(s, "scraper_url", "?")
        print(f"  {n} scraper_url={url}")

    print("\n=== TEST find_trending_content ===")
    r = await base_discovery_service.find_trending_content(
        "AI", horizon="30d", tier="free", deep_scan=False, region="US"
    )
    print("RESULT COUNT:", len(r))
    for c in r[:10]:
        src = (c.metadata_json or {}).get("source", "none")
        print(f"  [{c.platform}] {c.title[:60]} views={c.view_count} src={src}")

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from services.discovery.service import base_discovery_service

async def test_search():
    query = "Gothic Architecture"
    print(f"Searching for: {query}")
    results = await base_discovery_service.search_content(query)
    print(f"Found {len(results)} results:")
    for r in results:
        thumb = "HAS_THUMB" if r.thumbnail_url else "MISSING_THUMB"
        print(f"- [{r.platform}] {r.title} ({thumb}) (Views: {r.views})")

if __name__ == "__main__":
    asyncio.run(test_search())

#!/usr/bin/env python3
"""
Direct test of OpenCLAW skills - runs inside the openclaw container
"""

import asyncio
import sys
import os

sys.path.insert(0, "/app")
os.chdir("/app")


async def test_discovery_skill():
    """Test Discovery skill"""
    print("\n" + "=" * 50)
    print("Testing Discovery Skill")
    print("=" * 50)

    try:
        from skills.discovery import discovery_skill

        # Test search trends
        result = discovery_skill.search_trends("motivation", limit=3, analyze=False)
        print(f"Search result: {result[:200]}...")

        return True
    except Exception as e:
        print(f"❌ Discovery skill error: {e}")
        return False


async def test_content_editor_skill():
    """Test Content Editor skill"""
    print("\n" + "=" * 50)
    print("Testing Content Editor Skill")
    print("=" * 50)

    try:
        from skills.content_editor import content_editor_skill

        # Test find content
        result = await content_editor_skill.find_content(
            source="youtube", query="motivation", niche="motivation", limit=3
        )
        print(f"Find content result: {result.get('status')}")
        print(f"Videos found: {len(result.get('videos', []))}")

        return True
    except Exception as e:
        print(f"❌ Content Editor skill error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_video_providers():
    """Test video generation skills"""
    print("\n" + "=" * 50)
    print("Testing Video Generation Skills")
    print("=" * 50)

    from services.video_engine.free_video_providers import free_video_provider

    # List providers
    providers = free_video_provider.PROVIDERS
    print(f"Total providers: {len(providers)}")
    for name, config in providers.items():
        print(f"  - {name}: {config.get('free_credits', '?')} credits/day")

    return True


async def main():
    print("🔬 OpenCLAW Skills Direct Test")

    results = []

    # Test each skill category
    results.append(("Providers", await test_video_providers()))
    results.append(("Discovery", await test_discovery_skill()))
    results.append(("Content Editor", await test_content_editor_skill()))

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")


if __name__ == "__main__":
    asyncio.run(main())

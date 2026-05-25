#!/usr/bin/env python3
"""
Auto Mode: Discovery -> Video Generation
Runs fully automated test on remote
"""

import asyncio
import requests

API_URL = "http://api:8000"
DISCOVERY_GO_URL = "http://discovery-go:8080"


async def auto_discovery_and_generate():
    """Full automated flow"""
    print("🚀 AUTO MODE: Discovery + Video Generation")
    print("=" * 50)

    # Step 1: Discovery
    print("\n📡 Step 1: Finding trending content...")
    try:
        response = requests.get(
            f"{DISCOVERY_GO_URL}/trending",
            params={"niche": "motivation", "size": 3},
            timeout=10,
        )
        if response.status_code == 200:
            trends = response.json()
            print(f"✅ Found {len(trends)} trending items")
            for i, t in enumerate(trends[:3]):
                print(f"  {i + 1}. {t.get('title', 'N/A')[:50]}...")
            topic = (
                trends[0].get("title", "motivation video") if trends else "motivation"
            )
        else:
            print(f"⚠️ Discovery returned: {response.status_code}")
            topic = "motivation speech"
    except Exception as e:
        print(f"⚠️ Discovery error: {e}")
        topic = "motivation speech"

    # Step 2: Video Generation via API
    print(f"\n🎬 Step 2: Generating video for: {topic[:30]}...")
    print("NOTE: Video generation requires auth and credits.")
    print("      Skipping actual generation in auto mode.")

    # Show available providers
    print("\n📹 Available Video Providers:")
    providers = [
        ("kling", "Kling AI", "66 credits/day"),
        ("pika", "Pika", "150 credits/mo"),
        ("runway", "Runway", "Free tier"),
        ("leonardo", "Leonardo", "Free tier"),
        ("frameloop", "Frameloop", "No watermark"),
        ("wavespeed", "WaveSpeedAI", "Multiple models"),
        ("ltx", "LTX Studio", "4K output"),
    ]
    for pid, name, credits in providers:
        print(f"  - {name} ({credits})")

    print("\n✅ Auto mode complete!")
    return True


def main():
    asyncio.run(auto_discovery_and_generate())


if __name__ == "__main__":
    main()

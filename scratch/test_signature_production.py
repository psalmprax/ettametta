import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add project root and src to path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

# Set Keys (set GROQ_API_KEY in your environment before running)
if "GROQ_API_KEY" not in os.environ:
    raise ValueError("Please set GROQ_API_KEY environment variable")
os.environ["DEBUG"] = "false"

from src.engines.real_video_fusion_engine import RealVideoFusionEngine


async def test_signature_production():
    print("💎 SIGNATURE QUALITY TEST: MULTI-LEAD FUSION + ELITE OVERLAYS")
    print("=" * 60)

    niche = "SpaceX Starship"
    topic = "The Absolute Future: SpaceX Starship Mars Colonization"
    print(f"📡 Searching for real trending content in: {niche}")

    # 1. LIVE DISCOVERY (Find 10 real URLs for maximum diversity)
    search_query = f"ytsearch10:{niche} shorts"
    print(f"🔍 Querying YouTube: {search_query}")

    cmd = [
        "yt-dlp",
        "--quiet",
        "--flat-playlist",
        "--print",
        "%(title)s",
        "--print",
        "%(id)s",
        search_query,
    ]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [
            line.strip() for line in process.stdout.strip().split("\n") if line.strip()
        ]

        discovered_videos = []
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                title = lines[i]
                vid_id = lines[i + 1]
                discovered_videos.append(
                    {
                        "id": vid_id,
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "platform": "YouTube",
                        "relevance": 1.0,
                        "viral_score": 95,
                    }
                )

        if not discovered_videos:
            print("❌ FAILED to find real content.")
            return

        print(f"✅ Found {len(discovered_videos)} REAL RELEVANT videos.")

        # 2. Initialize Engine
        engine = RealVideoFusionEngine(output_dir="outputs/signature_tests")

        # 3. Create Video
        print(f"\n🎬 Creating SIGNATURE production for topic: {topic}")

        result = await engine.create_real_video_content(
            discovered_videos=discovered_videos,
            content_topic=topic,
            duration_sec=30,
            session_id="signature_production_001",
        )

        print("\n" + "=" * 40)
        print("📊 SIGNATURE PRODUCTION REPORT")
        print("=" * 40)
        print(f"Success: {result.get('success')}")
        print(f"Video Path: {result.get('video_path')}")

        if result.get("success") and os.path.exists(result["video_path"]):
            print(f"\n✅ SIGNATURE PRODUCTION COMPLETE: {result['video_path']}")

            # Verify Diversity
            unique_assets = set(
                [s["file_path"] for s in result["fusion_plan"].get("segments", [])]
            )
            print(f"Unique Assets Used: {len(unique_assets)}")

            if len(unique_assets) > 1:
                print("🏆 MULTI-LEAD SUCCESS: Fusion is diverse.")
            else:
                print("⚠️  SINGLE-LEAD: Diversity penalty might not have been enough.")

            # Verify Overlays
            temp_dir = Path("outputs/signature_tests/temp_neural")
            if (temp_dir / "production.ass").exists():
                print("🏆 SIGNATURE OVERLAYS SUCCESS: Styled .ass file generated.")

        else:
            print(f"\n❌ Production failed: {result.get('error')}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_signature_production())

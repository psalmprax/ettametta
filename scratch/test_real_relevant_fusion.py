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


async def test_real_relevant_fusion():
    print("🚀 REAL RELEVANT TEST: LIVE DISCOVERY + NEURAL FUSION")
    print("=" * 60)

    niche = "SpaceX Starship"
    topic = "How SpaceX Starship will change space travel"
    print(f"📡 Searching for real trending content in: {niche}")

    # 1. LIVE DISCOVERY (Using yt-dlp to find real URLs)
    # This ensures we are NOT using "useless" or unrelated videos.
    search_query = f"ytsearch5:{niche} shorts"
    print(f"🔍 Querying YouTube: {search_query}")

    # We use --print to get title and id reliably
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
                        "relevance": 1.0,  # High relevance by definition
                        "viral_score": 90,
                    }
                )

        if not discovered_videos:
            print("❌ FAILED to find real content. Please check internet connection.")
            return

        print(f"✅ Found {len(discovered_videos)} REAL RELEVANT videos.")
        for v in discovered_videos:
            print(f"  - [{v['id']}] {v['title']}")

        # 2. Initialize Engine
        engine = RealVideoFusionEngine(output_dir="outputs/real_relevant")

        # 3. Create Video
        print(f"\n🎬 Creating production for topic: {topic}")

        result = await engine.create_real_video_content(
            discovered_videos=discovered_videos,
            content_topic=topic,
            duration_sec=30,
            session_id="real_relevant_session_001",
        )

        print("\n" + "=" * 40)
        print("📊 FINAL PRODUCTION REPORT")
        print("=" * 40)
        print(f"Success: {result.get('success')}")
        print(f"Video Path: {result.get('video_path')}")

        if result.get("success") and os.path.exists(result["video_path"]):
            print(f"\n✅ PRODUCTION COMPLETE: {result['video_path']}")
            print(
                f"📁 Video Size: {os.path.getsize(result['video_path']) / 1024 / 1024:.2f} MB"
            )

            if "fusion_plan" in result:
                print(
                    f"Unique Assets Used: {len(set([s['file_path'] for s in result['fusion_plan'].get('segments', [])]))}"
                )
        else:
            print(f"\n❌ Production failed: {result.get('error')}")

    except Exception as e:
        print(f"\n❌ ERROR during real-world test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_relevant_fusion())

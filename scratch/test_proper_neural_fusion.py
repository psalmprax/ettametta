import asyncio
import os
import sys
from pathlib import Path

# Add project root and src to path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

# Set Groq key (set GROQ_API_KEY in your environment before running)
if "GROQ_API_KEY" not in os.environ:
    raise ValueError("Please set GROQ_API_KEY environment variable")
os.environ["DEBUG"] = "false"

from src.engines.real_video_fusion_engine import RealVideoFusionEngine


async def test_proper_neural_fusion():
    print("🚀 PROPER TEST: HIGH-FIDELITY NEURAL FUSION")
    print("=" * 60)
    print("🧠 Using Real LLM (Groq) for narrative orchestration.")
    print("🎬 Using 10+ discovered assets for Neural Tournament selection.")

    # 1. Initialize Engine
    engine = RealVideoFusionEngine(output_dir="outputs/proper_tests")

    # 2. Mock a realistic Discovered Pool from local files
    raw_dir = root / "local_downloads/raw"
    local_files = list(raw_dir.glob("*.mp4"))

    if not local_files:
        print(
            "❌ ERROR: No local assets found in local_downloads/raw. Please run the previous test first."
        )
        return

    discovered_videos = []
    # We create a diverse pool to test the "Neural Tournament" logic.
    # The engine will rank these by relevance and motion score for each scripted scene.
    for i, f in enumerate(local_files[:12]):
        discovered_videos.append(
            {
                "id": f.stem,
                "url": f"https://youtube.com/watch?v={f.stem}",
                "file_path": str(f),
                "relevance": 0.4 + (i * 0.05),  # Some high, some low relevance
                "motion_score": 0.2 + (i * 0.07),  # Different motion dynamics
                "viral_score": 70 + i,
            }
        )

    topic = "The Rise of AGI: A Blueprint for Human Evolution"

    print(f"📝 Topic: {topic}")
    print(f"📊 Discovered Assets in Pool: {len(discovered_videos)}")

    # 3. Create Video
    try:
        # This will trigger:
        # - Script generation via Groq
        # - Scene analysis via CLIP (CPU)
        # - Neural selection of assets
        # - Cinematic rendering via FFmpeg
        result = await engine.create_real_video_content(
            discovered_videos=discovered_videos,
            content_topic=topic,
            duration_sec=30,  # 30 seconds
            session_id="proper_test_session_001",
        )

        print("\n" + "=" * 40)
        print("📊 FINAL PRODUCTION REPORT:")
        print("=" * 40)
        print(f"Success: {result.get('success', 'N/A')}")
        print(f"Video Path: {result.get('video_path')}")

        if "script" in result:
            print(f"Title: {result['script'].get('title')}")
            print(f"Narrative Segments: {len(result['script'].get('segments', []))}")

        if "fusion_plan" in result:
            segments = result["fusion_plan"].get("segments", [])
            print(f"Fusion Segments: {len(segments)}")
            # Check for asset diversity in the plan
            used_assets = set([s["file_path"] for s in segments])
            print(
                f"Unique Assets Selected: {len(used_assets)} / {len(discovered_videos)}"
            )

            print("\n🎬 Scene Selection Detail:")
            for i, seg in enumerate(segments):
                asset_name = Path(seg["file_path"]).name
                print(
                    f"  [{i}] {seg['role']} ({seg['emotion']}) -> {asset_name} ({seg['duration']}s)"
                )

        if result.get("success") and os.path.exists(result["video_path"]):
            print(f"\n✅ PRODUCTION COMPLETE: {result['video_path']}")
            print(
                f"📁 Size: {os.path.getsize(result['video_path']) / 1024 / 1024:.2f} MB"
            )
        else:
            print("\n❌ Production failed.")
            if "error" in result:
                print(f"Error: {result['error']}")

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_proper_neural_fusion())

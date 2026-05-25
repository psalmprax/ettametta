import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engines.real_video_fusion_engine import RealVideoFusionEngine
from src.engines.intelligent_video_workflow import discover_multi_platform

async def test_intelligent_production():
    print("\n🚀 INITIATING INTELLIGENT NEURAL PRODUCTION")
    print("============================================")
    
    topic = "The Future of Human Life on Mars"
    niche = "Space/Science"
    
    engine = RealVideoFusionEngine(output_dir="data/storage/outputs/intelligent_edits")
    
    # Step 1: Intelligent Discovery (Multi-Platform)
    print(f"\n[1/5] 🔍 Discovering high-intent assets for: {topic}")
    candidates = await discover_multi_platform(topic, max_per_platform=3)
    
    if not candidates:
        print("❌ No candidates found. Aborting.")
        return

    print(f"   ✅ Found {len(candidates)} candidate leads.")

    # Step 2: Intelligent Production (Narrative Planning + Neural Fusion)
    print("\n[2/5] 🧠 Orchestrating Narrative Reasoning & Neural Fusion...")
    print("      (This includes: Scripting, CLIP Analysis, Beat-Snapping, and Emotional Mapping)")
    
    # We use a 30s duration for a fast test cycle
    result = await engine.create_real_video_content(
        discovered_videos=candidates,
        content_topic=topic,
        duration_sec=30,
        quality="ELITE"
    )
    
    if result.get("success"):
        print("\n" + "=" * 60)
        print("✨ PRODUCTION SUCCESSFUL!")
        print("=" * 60)
        print(f"🎬 Title: {result.get('script', {}).get('title', 'Unknown')}")
        print(f"📂 Output: {result.get('video_path')}")
        print(f"📝 Script Segments: {len(result.get('script', {}).get('segments', []))}")
        print(f"📊 Narrative Score: {result.get('fusion_plan', {}).get('quality', 'N/A')}")
        
        # Create a preview link in the current directory for easy access
        preview_path = os.path.join(os.getcwd(), "intelligent_preview.mp4")
        if os.path.exists(result["video_path"]):
            import shutil
            shutil.copy(result["video_path"], preview_path)
            print(f"🔗 Preview ready: {preview_path}")
    else:
        print(f"\n❌ Production failed: {result.get('error', 'Unknown Error')}")

if __name__ == "__main__":
    asyncio.run(test_intelligent_production())

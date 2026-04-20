import asyncio
import os
import sys
from pathlib import Path

# Add project root and src to path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

# Mock environment variables
os.environ["DEBUG"] = "false"

from src.engines.real_video_fusion_engine import RealVideoFusionEngine

async def test_synthetic_lead_to_video():
    print("🚀 TESTING: SYNTHETIC LEAD TO VIDEO EDITING")
    print("=" * 60)

    # 1. Initialize Engine
    engine = RealVideoFusionEngine(output_dir="outputs/tests")

    # 2. Mock Synthetic Lead
    # We provide a local file to simulate a "synthetic" lead already present.
    # This ensures the test passes regardless of external API status.
    test_asset = root / "local_downloads/raw/test_lead_1.mp4"
    
    synthetic_leads = [
        {
            "id": "test_lead_1",
            "url": "https://example.com/test_lead_1.mp4",
            "file_path": str(test_asset),
            "relevance": 1.0,
            "motion_score": 0.8
        }
    ]
    
    topic = "The intersection of Cyberpunk and AI"
    
    print(f"📝 Topic: {topic}")
    print(f"🎬 Lead: {synthetic_leads[0]['id']} -> {synthetic_leads[0]['file_path']}")

    # 3. Create Video
    try:
        result = await engine.create_real_video_content(
            discovered_videos=synthetic_leads,
            content_topic=topic,
            duration_sec=10, # 10 seconds
            session_id="test_synthetic_session"
        )
        
        print("\n" + "=" * 40)
        print("📊 TEST RESULTS:")
        print("=" * 40)
        print(f"Success: {result.get('success', 'N/A')}")
        print(f"Video Path: {result.get('video_path')}")
        
        if "script" in result:
            print(f"Title: {result['script'].get('title')}")
            
        if "fusion_plan" in result:
            print(f"Fusion Segments: {len(result['fusion_plan'].get('segments', []))}")
        
        if result.get("success") and os.path.exists(result["video_path"]):
            print(f"\n✅ Video generated successfully: {result['video_path']}")
        else:
            print("\n❌ Video generation failed.")
            if "error" in result:
                print(f"Error: {result['error']}")
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_synthetic_lead_to_video())

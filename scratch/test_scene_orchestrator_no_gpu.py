import asyncio
import os
import sys
from pathlib import Path

# Add project root and src to path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

from src.services.video_engine.scene_orchestrator import SceneBasedVideoOrchestrator

async def test_scene_orchestrator():
    print("=" * 60)
    print("🚀 TESTING SCENE-BASED VIDEO ORCHESTRATOR (NO-GPU)")
    print("=" * 60)

    orchestrator = SceneBasedVideoOrchestrator()
    
    # Use Case: Create a 2-scene video from local clips
    local_video = str(root / "outputs" / "no_gpu_test.mp4")
    scenes = [
        {
            "scene": "Introduction",
            "visual_prompt": "Cinematic shot of a modern city at night",
            "video_path": local_video,
            "duration": 3
        },
        {
            "scene": "Ettametta Logo",
            "visual_prompt": "Futuristic AI interface glowing",
            "video_path": local_video,
            "duration": 2
        }
    ]
    
    print(f"\n🎬 Dispatching production for {len(scenes)} scenes...")
    
    try:
        # We manually trigger produce_scene_based_video
        # Note: it will try to download the assets
        result = await orchestrator.produce_scene_based_video(
            scenes=scenes,
            niche="Technology",
            target_duration=5,
            audio_script="Ettametta is revolutionizing content creation with AI."
        )
        
        if result.get("success"):
            print(f"\n✅ Production Successful!")
            print(f"   Video Path: {result['video_path']}")
            print(f"   Duration: {result['duration']}s")
            print(f"   File Size: {result['file_size']} bytes")
        else:
            print(f"\n❌ Production Failed: {result.get('error')}")
            if "fusion_error" in result:
                print(f"   Fusion Error: {result['fusion_error']}")
                
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scene_orchestrator())

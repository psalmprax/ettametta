#!/usr/bin/env python3
"""
Create Scene-Based Video Demo
============================

Demonstrates the enhanced video editor by fusing existing videos
with audio overlay to create uploadable content.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# Fix environment
os.environ["DEBUG"] = "false"

from services.video_engine.scene_orchestrator import scene_based_orchestrator
from services.discovery.video_lead_scanner import video_lead_scanner


async def create_scene_based_demo_video():
    """Create a demo video by fusing existing test videos"""

    print("CREATING SCENE-BASED DEMO VIDEO")
    print("=" * 40)

    # Use existing videos as source material
    existing_videos = [
        "test_videos/gen_1775226095.mp4",
        "test_videos/gen_1775213381.mp4",
        "test_videos/cogvideo_5b_sync.mp4",
    ]

    # Check if videos exist
    available_videos = [v for v in existing_videos if Path(v).exists()]
    print(f"Found {len(available_videos)} existing videos to fuse")

    # Create scenes based on available videos
    scenes = []
    for i, video_path in enumerate(available_videos[:2]):  # Use up to 2 videos
        scenes.append(
            {
                "description": f"Scene {i + 1} from existing video content",
                "visual_prompt": f"Content from {Path(video_path).name}",
                "duration": 5,  # Short duration for demo
                "source_video": video_path,
            }
        )

    print(f"Created {len(scenes)} scenes for fusion")

    # Create production plan manually since discovery requires API keys
    production_plan = {
        "production_ready": True,
        "niche": "AI content creation",
        "estimated_duration": 10,
        "quality_score": 8.5,
        "scene_videos": {
            f"scene_{i + 1}": [
                {
                    "platform": "local",
                    "url": scene["source_video"],
                    "title": f"Demo video {i + 1}",
                    "duration": 5,
                    "quality": "high",
                }
            ]
            for i, scene in enumerate(scenes)
        },
        "fusion_plan": {
            "segments": [
                {
                    "scene": scene["description"],
                    "start_time": i * 5,
                    "duration": 5,
                    "source_video": scene["source_video"],
                    "transition": "fade" if i > 0 else "none",
                }
                for i, scene in enumerate(scenes)
            ],
            "total_duration": len(scenes) * 5,
            "frame_rate": 30,
            "resolution": "1920x1080",
        },
        "audio_plan": {
            "voice_over": True,
            "audio_segments": [
                {
                    "text": f"This is scene {i + 1} demonstrating video fusion",
                    "start_time": i * 5,
                    "duration": 5,
                }
                for i, scene in enumerate(scenes)
            ],
            "background_music": True,
        },
        "upload_specs": {
            "platforms": ["youtube", "tiktok", "instagram"],
            "seo_tags": ["AI", "content creation", "demo"],
            "metadata": {"hashtags": ["#AI #ContentCreation #Demo"]},
        },
    }

    # Execute video fusion directly
    fusion_result = await scene_based_orchestrator._execute_video_fusion(
        production_plan
    )
    if not fusion_result.get("success"):
        print(f"Fusion failed: {fusion_result.get('error')}")
        return fusion_result

    # Add audio overlay
    audio_result = await scene_based_orchestrator._add_audio_overlay(
        fusion_result["video_path"], production_plan["audio_plan"]
    )

    # Finalize for upload
    final_video_path = (
        audio_result["video_path"]
        if audio_result.get("success")
        else fusion_result["video_path"]
    )
    final_result = await scene_based_orchestrator._finalize_for_upload(
        final_video_path, production_plan["upload_specs"], "scene_based_demo"
    )

    result = {
        "success": final_result.get("success", False),
        "video_path": final_result.get("final_path"),
        "duration": production_plan.get("estimated_duration", 0),
        "scenes_used": len(scenes),
        "quality_score": production_plan.get("quality_score", 0),
        "processing_stats": {
            "video_fusion_time": fusion_result.get("processing_time", 0),
            "audio_overlay_time": audio_result.get("processing_time", 0)
            if audio_result.get("success")
            else 0,
            "total_processing_time": fusion_result.get("processing_time", 0)
            + (
                audio_result.get("processing_time", 0)
                if audio_result.get("success")
                else 0
            ),
        },
    }

    # Create scenes based on available videos
    scenes = []
    for i, video_path in enumerate(available_videos[:2]):  # Use up to 2 videos
        scenes.append(
            {
                "description": f"Scene {i + 1} from existing video content",
                "visual_prompt": f"Content from {Path(video_path).name}",
                "duration": 10 + i * 5,  # Vary durations
                "source_video": video_path,
            }
        )

    print(f"Created {len(scenes)} scenes for fusion")

    # Produce the video
    result = await scene_based_orchestrator.produce_scene_based_video(
        scenes=scenes,
        niche="AI content creation",
        target_duration=25,
        audio_script="Discover how AI tools can enhance your content creation workflow.",
        output_filename="fused_scene_demo",
    )

    print("\nVideo Production Result:")
    print(f"Success: {result.get('success', False)}")
    if result.get("video_path"):
        print(f"Video Path: {result['video_path']}")
        print(f"Duration: {result.get('duration', 0)} seconds")
        print(f"Scenes Used: {result.get('scenes_used', 0)}")
        print(f"Quality Score: {result.get('quality_score', 0)}/10")

        # Check if file exists
        if Path(result["video_path"]).exists():
            size = Path(result["video_path"]).stat().st_size
            print(f"File Size: {size} bytes")
            print("✅ Video file created successfully!")
        else:
            print("❌ Video file was not created")

    return result


async def main():
    """Main demo function"""
    try:
        result = await create_scene_based_demo_video()

        if result and result.get("success"):
            print("\n🎉 SUCCESS: Scene-based video created!")
            print(f"Review the video at: {result.get('video_path')}")
        else:
            print("\n❌ Demo completed but no video was created")
            print("This is expected behavior when no source videos are available")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

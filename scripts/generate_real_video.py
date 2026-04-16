#!/usr/bin/env python3
"""
Generate Real Videos with Docker Container
==========================================

This script shows how to generate actual MP4 video files using the video processor container.
Run this after starting the video processor container with dependencies installed.
"""

import asyncio
import os
import sys

# Add project root
sys.path.insert(0, str(os.path.dirname(__file__)))

async def generate_real_video():
    """Generate a real video using the video processor"""

    print("🎬 GENERATING REAL VIDEO WITH VIDEO PROCESSOR CONTAINER")
    print("=" * 65)

    # Check if we're in the container environment
    in_container = os.path.exists('/app/outputs') and os.path.exists('/app/services')

    if not in_container:
        print("⚠️  Not running in video processor container!")
        print("   Start the container first:")
        print("   docker-compose --profile video up video_processor")
        print("   Then run this script inside the container")
        return

    print("✅ Running in video processor container")

    # Check dependencies
    dependencies_ok = True
    try:
        import moviepy
        import cv2
        print("✅ MoviePy available")
        print("✅ OpenCV available")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        dependencies_ok = False

    if not dependencies_ok:
        print("❌ Dependencies not installed - install with:")
        print("   pip install moviepy opencv-python torch faster-whisper")
        return

    print("\\n🎯 STARTING VIDEO GENERATION PROCESS")

    # Define test scenes
    test_scenes = [
        {
            "description": "Introduction to AI productivity tools and their impact on modern work",
            "visual_prompt": "Modern workspace with computer screen, productivity charts, clean office environment",
            "duration_estimate": 15
        },
        {
            "description": "Demonstration of ChatGPT for workflow automation and content creation",
            "visual_prompt": "Split screen showing user typing prompts and AI generating responses, productivity metrics",
            "duration_estimate": 20
        },
        {
            "description": "Overview of specialized AI tools for different professional workflows",
            "visual_prompt": "Collage of different AI tool interfaces, workflow diagrams, efficiency metrics",
            "duration_estimate": 15
        }
    ]

    test_niche = "AI productivity tools"
    test_audio_script = """
    Welcome to our comprehensive guide on AI productivity tools that are revolutionizing how we work in the modern era.

    In this video, we'll explore the latest AI tools that can dramatically boost your productivity and transform your workflow.

    First, let's look at ChatGPT and how it can automate repetitive tasks and generate high-quality content quickly. You'll see real examples of prompts and responses that save hours of work each day.

    Next, we'll explore specialized AI tools designed for different workflows, from coding assistants to design tools. Each tool has unique strengths that can supercharge specific aspects of your professional work.

    Finally, we'll share expert tips for maximizing your AI productivity while avoiding common pitfalls that many users encounter.

    These strategies will help you get the most out of your AI investment and stay ahead in an increasingly competitive landscape.
    """

    print("📋 PRODUCTION PARAMETERS:")
    print(f"   • Niche: {test_niche}")
    print(f"   • Scenes: {len(test_scenes)}")
    print(f"   • Target Duration: 50 seconds")
    print(f"   • Audio Script: {len(test_audio_script.split())} words")
    print()

    try:
        # Import the video orchestrator
        print("🔧 Initializing video orchestrator...")
        from services.video_engine.scene_orchestrator import scene_based_orchestrator

        print("🎬 Starting video production...")

        # Generate the video
        result = await scene_based_orchestrator.produce_scene_based_video(
            scenes=test_scenes,
            niche=test_niche,
            target_duration=50,
            audio_script=test_audio_script,
            output_filename="real_ai_productivity_tutorial"
        )

        print("\\n🎉 VIDEO GENERATION RESULTS")
        print("-" * 35)

        if result.get("success"):
            print("✅ Video production completed successfully!")
            print(f"   📁 Video Path: {result.get('video_path')}")
            print(f"   ⏱️  Duration: {result.get('duration', 0)} seconds")
            print(f"   📏 File Size: {result.get('file_size', 0) // 1024 // 1024} MB")
            print(".1f"            print(f"   🎯 Quality Score: {result.get('quality_score', 0):.1f}/10")
            print(f"   🎬 Scenes Used: {result.get('scenes_used', 0)}")
            print(f"   📊 Videos Found: {result.get('videos_found', 0)}")

            # Check if file actually exists
            video_path = result.get("video_path")
            if video_path and os.path.exists(video_path):
                print(f"   ✅ FILE EXISTS: {os.path.basename(video_path)}")
                print("   🎉 REAL MP4 VIDEO FILE GENERATED!")
            else:
                print("   ⚠️  File path returned but file not found")

            # Show platform readiness
            platforms = result.get("platforms_used", [])
            if platforms:
                print(f"   🌐 Platforms Ready: {', '.join(platforms)}")

        else:
            print(f"❌ Video production failed: {result.get('error', 'Unknown error')}")

        print("\\n📂 OUTPUT DIRECTORY CONTENTS:")
        print("-" * 35)

        output_dir = "/app/outputs/scene_based_videos"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print("Files in output directory:")
                for file in files:
                    file_path = os.path.join(output_dir, file)
                    size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                    print(f"   • {file} ({size} bytes)")
            else:
                print("   (No files in output directory)")
        else:
            print("   Output directory not found")

    except Exception as e:
        print(f"❌ Video generation failed with error: {e}")
        import traceback
        traceback.print_exc()

    print("\\n" + "=" * 65)
    print("🎯 VIDEO GENERATION COMPLETE")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(generate_real_video())
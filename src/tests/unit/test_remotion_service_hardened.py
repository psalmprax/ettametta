#!/usr/bin/env python3
import asyncio
import os
import sys

PROJECT_DIR = "/app" if os.path.exists("/app") else "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

from src.services.video_engine.remotion_service import RemotionService

async def main():
    print("=== HARDENED REMOTION SERVICE TEST ===")

    # Initialize service with concurrency limit 1 to verify semaphore queuing
    service = RemotionService(concurrency_limit=1)

    props1 = {
        "title": "Hardened Pipeline Render 1",
        "subtitle": "Isolate concurrent sandbox 1",
        "duration_in_frames": 20,
    }

    props2 = {
        "title": "Hardened Pipeline Render 2",
        "subtitle": "Isolate concurrent sandbox 2",
        "duration_in_frames": 20,
    }

    print("\nTriggering 2 concurrent renders...")
    task1 = service.render_video("CinematicMinimal", props1, "sandboxed_render_1.mp4")
    task2 = service.render_video("CinematicMinimal", props2, "sandboxed_render_2.mp4")

    results = await asyncio.gather(task1, task2, return_exceptions=True)

    for idx, res in enumerate(results, 1):
        if isinstance(res, Exception):
            print(f"❌ Render {idx} failed with: {res}")
        else:
            print(f"✅ Render {idx} success: {res}")
            if os.path.exists(res):
                print(f"  - Verified file exists: {res} (size: {os.path.getsize(res) / 1024:.1f} KB)")

if __name__ == "__main__":
    asyncio.run(main())

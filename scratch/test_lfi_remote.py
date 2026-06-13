import os
import asyncio
os.environ["PYTHONPATH"] = "/app"
os.environ["ENV"] = "production"

async def test():
    from src.services.video_engine.remotion_service import base_remotion_service
    test_clip = "/app/temp/test_clip.mp4"
    print(f"exists: {os.path.exists(test_clip)}")
    print(f"size: {os.path.getsize(test_clip)/1024/1024:.1f} MB")
    props = {"title": "LFI", "subtitle": "Test", "vibe": "Energetic", "clips": [{"url": test_clip, "start": 0, "duration": 5}]}
    print("Calling render_video...")
    result = await base_remotion_service.render_video(
        composition_id="ViralClip",
        props=props,
        output_filename="lfi_fix_test.mp4",
        fps=30
    )
    print(f"result: {result}")

asyncio.run(test())
import asyncio
import os
import logging
from src.services.video_engine.remotion_service import base_remotion_service
logging.basicConfig(level=logging.DEBUG)

async def test():
    props = {
        "title": "ETTAMETTA PRESENTS",
        "subtitle": "Test Title",
        "duration_in_frames": 90,
        "show_cta_overlay": False
    }
    try:
        path = await base_remotion_service.render_video("CinematicMinimal", props, "test_intro.mp4")
        print(f"Success: {path}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())

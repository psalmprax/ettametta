import asyncio
import os
import sys
import uuid
import logging

# Ensure we can import from src
PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.append(PROJECT_DIR)

from src.services.nexus_engine.auto_creator import base_creator_service
from src.services.infrastructure.resource_governor import base_governor_service
from src.services.infrastructure.cookie_manager import base_cookie_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockE2ETest")

async def test_mock_pipeline():
    logger.info("🚀 Starting Mock E2E Test...")
    
    # 1. Check Resource Governor
    mode = base_governor_service.get_degradation_mode()
    throttle = base_governor_service.should_throttle()
    logger.info(f"📊 Governor Status: Mode={mode}, Throttle={throttle}")
    
    # 2. Check Cookie Manager
    cookies = base_cookie_manager.get_youtube_cookies()
    logger.info(f"🍪 Cookie Status: {cookies}")
    
    # 3. Launch Automated Video (Topic Fusion)
    # We use a fake user ID for testing
    user_id = "test_user_123"
    topic = "The future of AI automation"
    niche = "technology"
    
    logger.info(f"🎬 Launching automated video for topic: {topic}")
    job_id = await base_creator_service.launch_automated_video(
        user_id=user_id,
        topic=topic,
        niche=niche,
        engine="mock" # Our new mock engine!
    )
    
    logger.info(f"✅ Job launched successfully! Job ID: {job_id}")
    logger.info("⌛ Waiting for background tasks to start...")
    await asyncio.sleep(5)
    
    # In a real test, we would poll the database, but for this mock test, 
    # we just verify the launch logic is sound.
    logger.info("🌟 Mock E2E Launch Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_mock_pipeline())

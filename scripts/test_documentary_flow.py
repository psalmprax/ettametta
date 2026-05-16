import asyncio
import logging
import sys
import os
import uuid
from typing import Dict, Any

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.services.nexus_engine.auto_creator import base_creator_service
from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DocumentaryFlow")

async def test_documentary_flow():
    """
    Tests the FULL AI-driven documentary creation flow.
    This uses AutoCreator to generate the script, source assets, and assemble the video.
    """
    job_id = str(uuid.uuid4())
    topic = "The Rise of Artificial General Intelligence"
    niche = "Technology"
    style = "CINEMATIC_DOC"
    
    logger.info(f"🏁 Starting Full AI Documentary Flow for job: {job_id}")
    logger.info(f"Topic: '{topic}' | Niche: '{niche}' | Style: '{style}'")

    # Create dummy job in DB to satisfy orchestrator updates
    async with async_session_factory() as db:
        job = NexusJobDB(
            id=job_id,
            user_id=None,
            status="CREATED",
            job_metadata={
                "topic": topic,
                "niche": niche,
                "style": style
            },
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(job)
        await db.commit()

    try:
        # Run the full pipeline
        # Note: This will generate script via IntelligenceHub, source visuals via StockService, 
        # and generate voiceovers via VoiceoverService.
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic="The Future of AI Robotics",
            niche="Technology & Science",
            duration_seconds=15,
            style="CINEMATIC_DOC"
        )
        
        logger.info("✅ Full Pipeline Completed!")
        logger.info(f"Output: {output_path}")
        
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"📊 VERIFIED: Output file exists and is {size_mb:.2f} MB")
        else:
            logger.error(f"❌ ERROR: Output file not found at {output_path}")

    except Exception as e:
        logger.exception(f"💥 Full Pipeline Failed: {e}")
    finally:
        logger.info("🎬 Test Finished.")

if __name__ == "__main__":
    asyncio.run(test_documentary_flow())

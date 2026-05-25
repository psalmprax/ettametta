import asyncio
import os
import sys
import uuid
import logging

# Add project root to path
PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("VideoLeadTest")

# Imports
from src.services.discovery.video_lead_scanner import VideoLeadScanner
from src.services.nexus_engine.auto_creator import base_creator_service
from src.services.llm.intelligence_hub import base_intelligence_service
from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB

# Monkeypatch IntelligenceHub to force provider if requested
original_chat = base_intelligence_service.chat
async def forced_chat(*args, **kwargs):
    if os.getenv("FORCE_PROVIDER"):
        kwargs["provider"] = os.getenv("FORCE_PROVIDER")
    # Increase timeout for slow remote providers (Ollama/Dify)
    kwargs["timeout_seconds"] = 600
    return await original_chat(*args, **kwargs)

base_intelligence_service.chat = forced_chat

async def test_lead_to_video_flow(niche: str = "Technology", style: str = "EASY"):
    logger.info(f"🔍 [Discovery] Scanning for video leads in niche: {niche}")
    scanner = VideoLeadScanner()
    
    # 1. Discover Leads
    leads = await scanner.scan_for_video_leads(niche=niche, platforms=["youtube"], max_results=3)
    
    if not leads:
        logger.error("❌ No video leads found! Falling back to manual topic.")
        lead_topic = f"The evolution of {niche}"
        lead_desc = "An automated deep dive into modern trends."
    else:
        best_lead = leads[0]
        lead_topic = best_lead.title
        lead_desc = best_lead.description
        logger.info(f"✅ Lead Found: '{lead_topic}' (Platform: {best_lead.platform})")

    # 2. Setup Nexus Job
    job_id = str(uuid.uuid4())
    logger.info(f"🎫 [Nexus] Creating job {job_id} for topic: {lead_topic}")
    
    async with async_session_factory() as db:
        new_job = NexusJobDB(
            id=job_id,
            niche=niche,
            status="QUEUED",
            job_metadata={
                "topic": lead_topic,
                "description": lead_desc,
                "style": style,
                "source": "lead_scanner_test"
            }
        )
        db.add(new_job)
        await db.commit()

    # 3. Trigger Creation
    logger.info(f"🎬 [Nexus] Starting creation pipeline for style: {style}")
    try:
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=lead_topic,
            niche=niche,
            style=style,
            duration_seconds=30
        )
        
        logger.info(f"🎉 [Success] Video generated at: {output_path}")
        
        # Verify file
        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / (1024*1024)
            logger.info(f"✅ [Verified] File size: {size:.2f} MB")
        else:
            # Check relative
            abs_path = os.path.join(PROJECT_DIR, output_path)
            if os.path.exists(abs_path):
                 size = os.path.getsize(abs_path) / (1024*1024)
                 logger.info(f"✅ [Verified] File size (abs): {size:.2f} MB")
            else:
                logger.error("❌ [Error] Output file reported but not found on disk.")
                
    except Exception:
        logger.exception("💥 [Critical] Flow failed")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", type=str, default="Technology")
    parser.add_argument("--style", type=str, default="EASY")
    args = parser.parse_args()
    
    asyncio.run(test_lead_to_video_flow(args.niche, args.style))

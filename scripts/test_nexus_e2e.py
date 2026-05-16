import asyncio
import os
import sys
import uuid
import time
import datetime
from sqlalchemy import select

# Ensure we can import from src
PROJECT_DIR = os.getenv("PYTHONPATH", "/app")
sys.path.append(PROJECT_DIR)

# Set environment
os.environ["DEBUG"] = "true"
os.environ["USE_OS_MODELS"] = "true"

import logging
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("NexusE2E")

async def poll_job_status(job_id: str):
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import NexusJobDB
    
    start_time = time.time()
    timeout = 600  # 10 minutes timeout
    
    logger.info(f"⏳ Polling status for Job {job_id}...")
    
    while time.time() - start_time < timeout:
        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"❌ Job {job_id} not found in database!")
                return None
            
            status = job.status or "QUEUED"
            progress = job.progress or 0
            current_node = getattr(job, 'current_node', 'N/A')
            
            logger.info(f"🔄 Job Status: {status} | Progress: {progress}% | Node: {current_node}")
            
            if status == "COMPLETED" or progress == 100:
                logger.info(f"✅ Job {job_id} COMPLETED successfully!")
                logger.info(f"📹 Output Path: {job.output_path}")
                return job.output_path
            
            if status == "FAILED":
                logger.error(f"❌ Job {job_id} FAILED!")
                logger.error(f"📜 Error Log: {job.error_log}")
                return None
        
        await asyncio.sleep(10)
    
    logger.error(f"❌ Job {job_id} timed out after {timeout}s")
    return None

async def main():
    logger.info("🏁 Starting Nexus E2E Test...")
    
    from src.services.nexus_engine.auto_creator import base_creator_service
    
    # Define test parameters
    test_user_id = "4e8c3e12-ad08-48bc-9672-448d0ce83baa" # Existing user on test server
    test_topic = "The Future of AI and Robotics"
    test_niche = "Technology"
    
    # Hardcoded script to bypass LLM generation hang
    test_script = [
        {
            "text": "The future of AI is here, and it is autonomous.",
            "visual_prompt": "Cinematic shot of a neural network",
            "mood": "Cinematic"
        },
        {
            "text": "Ettametta is scaling the nexus orchestration.",
            "visual_prompt": "Abstract digital connection lines",
            "mood": "Energetic"
        }
    ]
    
    logger.info(f"🚀 Launching Nexus job for topic: '{test_topic}' in niche: '{test_niche}' (with manual script)")
    
    # Use existing assets from the server to guarantee rendering test
    # These paths exist on disk for Python validation and are sanitized by RemotionService
    visual_asset = "/app/apps/remotion-studio/public/temp/stock_15529708_360_640_30fps.mp4.mp4"
    voice_asset = "/app/outputs/audio/voiceover_984233.mp3"
    
    from src.services.nexus_engine.orchestrator import base_nexus_service
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import NexusJobDB
    
    job_id = str(uuid.uuid4())
    
    # 1. Create Job Entry
    async with async_session_factory() as db:
        new_job = NexusJobDB(
            id=job_id,
            user_id=test_user_id,
            niche=test_niche,
            current_node="ingress",
            status="QUEUED",
            progress=0,
            job_metadata={
                "topic": test_topic,
                "manual_test": True
            }
        )
        db.add(new_job)
        await db.commit()
    
    logger.info(f"🎫 Job Created: {job_id}")
    
    # 2. Trigger Assembly Directly with existing assets
    logger.info(f"🎬 Triggering direct assembly with assets: {visual_asset}, {voice_asset}")
    
    async def notify_db(node, status, progress):
        async with async_session_factory() as db:
            from sqlalchemy import update
            stmt = (
                update(NexusJobDB)
                .where(NexusJobDB.id == job_id)
                .values(
                    status=f"{node.upper()}_{status}",
                    current_node=node,
                    node_status=status,
                    progress=progress,
                    updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                )
            )
            await db.execute(stmt)
            await db.commit()

    try:
        # Simulate the API behavior
        await notify_db("synthesis", "ACTIVE", 60)
        
        # Call the assembly directly
        rendered_path = await base_nexus_service.assemble_video(
            job_id=job_id,
            niche=test_niche,
            script_segments=test_script,
            voiceover_paths=[voice_asset, voice_asset],
            visual_paths=[visual_asset, visual_asset],
            music_path=None
        )
        
        if rendered_path:
            await notify_db("synthesis", "COMPLETED", 90)
            await notify_db("egress", "COMPLETED", 100)
            
            # Update output path in DB
            async with async_session_factory() as db:
                from sqlalchemy import update
                stmt = (
                    update(NexusJobDB)
                    .where(NexusJobDB.id == job_id)
                    .values(
                        output_path=rendered_path,
                        status="COMPLETED"
                    )
                )
                await db.execute(stmt)
                await db.commit()

            if os.path.exists(rendered_path):
                file_size = os.path.getsize(rendered_path) / (1024 * 1024)
                logger.info(f"✅ VERIFIED: Output file exists and is {file_size:.2f} MB")
                print(f"RESULT: SUCCESS | JOB_ID: {job_id} | PATH: {rendered_path} | SIZE: {file_size:.2f}MB")
            else:
                # Try relative to app dir
                abs_path = os.path.join(PROJECT_DIR, rendered_path)
                if os.path.exists(abs_path):
                     file_size = os.path.getsize(abs_path) / (1024 * 1024)
                     logger.info(f"✅ VERIFIED (abs): Output file exists and is {file_size:.2f} MB")
                     print(f"RESULT: SUCCESS | JOB_ID: {job_id} | PATH: {abs_path} | SIZE: {file_size:.2f}MB")
                else:
                    logger.error(f"❌ ERROR: Output path {rendered_path} reported but file not found on disk!")
                    print(f"RESULT: FILE_NOT_FOUND | JOB_ID: {job_id} | PATH: {rendered_path}")
        else:
            logger.error("❌ E2E Test Failed: No output path returned.")
            print(f"RESULT: FAILED | JOB_ID: {job_id}")
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR during E2E test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"RESULT: CRASHED | ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

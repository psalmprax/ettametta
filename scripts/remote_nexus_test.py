"""
Remote Nexus Engine E2E Test
Runs on the remote server via docker exec, using available assets on disk.
"""
import asyncio
import os
import sys
import uuid
import datetime
import logging
from sqlalchemy import select, update

# Ensure we can import from /app
sys.path.insert(0, "/app")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("RemoteNexusTest")

# Available assets on this server
VISUAL_ASSETS = [
    "/app/apps/remotion-studio/out/nexus_2c780d21-5090-462b-9bc5-e2079820535d_AI.mp4",
    "/app/apps/remotion-studio/out/nexus_e0e0b69c-f5a0-4ca1-8f99-c197204ae0a0_Tech.mp4",
]

VOICEOVER_ASSETS = [
    "/app/outputs/audio/voiceover_105408.mp3",
    "/app/outputs/audio/voiceover_107010.mp3",
]

TEST_USER_ID = "4e8c3e12-ad08-48bc-9672-448d0ce83baa"  # Existing user on test server

async def main():
    logger.info("=" * 60)
    logger.info("🏁 Starting Remote Nexus Engine E2E Test")
    logger.info("=" * 60)

    # Verify assets exist
    for path in VISUAL_ASSETS + VOICEOVER_ASSETS:
        if not os.path.exists(path):
            logger.warning(f"⚠️ Asset not found: {path}")
        else:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            logger.info(f"✅ Asset OK: {path} ({size_mb:.2f} MB)")

    test_script = [
        {
            "text": "The future of AI is here, and it's transforming every industry.",
            "visual_prompt": "Cinematic shot of a neural network",
            "mood": "Cinematic"
        },
        {
            "text": "Ettametta is scaling the nexus orchestration for autonomous content.",
            "visual_prompt": "Abstract digital connection lines",
            "mood": "Energetic"
        }
    ]

    from src.services.nexus_engine.orchestrator import base_nexus_service
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import NexusJobDB

    job_id = str(uuid.uuid4())
    niche = "Technology"

    # 1. Create Job Entry
    async with async_session_factory() as db:
        new_job = NexusJobDB(
            id=job_id,
            user_id=TEST_USER_ID,
            niche=niche,
            current_node="ingress",
            status="QUEUED",
            progress=0,
            job_metadata={
                "topic": "The Future of AI and Robotics",
                "remote_test": True,
                "source": "remote_nexus_test"
            }
        )
        db.add(new_job)
        await db.commit()

    logger.info(f"🎫 Job Created: {job_id}")
    logger.info(f"🎬 Assembling video with {len(VISUAL_ASSETS)} visual and {len(VOICEOVER_ASSETS)} voiceover assets...")

    try:
        rendered_path = await base_nexus_service.assemble_video(
            job_id=job_id,
            niche=niche,
            script_segments=test_script,
            voiceover_paths=VOICEOVER_ASSETS,
            visual_paths=VISUAL_ASSETS,
            music_path=None,
            style="CINEMATIC_DOC"
        )

        if rendered_path:
            logger.info(f"✅ Assembly returned path: {rendered_path}")

            # Update job status
            async with async_session_factory() as db:
                stmt = (
                    update(NexusJobDB)
                    .where(NexusJobDB.id == job_id)
                    .values(
                        output_path=rendered_path,
                        status="COMPLETED",
                        progress=100
                    )
                )
                await db.execute(stmt)
                await db.commit()

            # Check if the file exists
            resolved_path = rendered_path
            if not os.path.exists(resolved_path):
                # Try relative to /app
                resolved_path = os.path.join("/app", rendered_path.lstrip("/"))

            if os.path.exists(resolved_path):
                file_size = os.path.getsize(resolved_path) / (1024 * 1024)
                logger.info(f"✅ VERIFIED: Output file exists at {resolved_path} ({file_size:.2f} MB)")
                print(f"RESULT: SUCCESS | JOB_ID: {job_id} | PATH: {resolved_path} | SIZE: {file_size:.2f}MB")
            else:
                logger.error(f"❌ File not found at {resolved_path}")
                print(f"RESULT: FILE_NOT_FOUND | JOB_ID: {job_id} | PATH: {rendered_path}")
        else:
            logger.error("❌ No output path returned from assemble_video")
            print(f"RESULT: FAILED | JOB_ID: {job_id}")

    except Exception as e:
        logger.exception("💥 CRITICAL ERROR during Nexus assembly")
        import traceback
        traceback.print_exc()
        print(f"RESULT: CRASHED | ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

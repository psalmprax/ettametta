#!/usr/bin/env python3
"""
Nexus Engine Style Pipeline Test Script
Runs the full pipeline for a given style, one at a time.
Usage: python3 test_style_pipeline.py <STYLE_NAME> [duration_seconds]
"""
import sys
import os
import asyncio
import uuid
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Ensure CHROMIUM_PATH is set for Remotion rendering
if not os.environ.get("CHROMIUM_PATH"):
    potential_paths = [
        "/app/apps/remotion-studio/node_modules/.remotion/chrome-headless-shell/linux64/chrome-headless-shell-linux64/chrome-headless-shell",
        "/root/ettametta/apps/remotion-studio/node_modules/.remotion/chrome-headless-shell/linux64/chrome-headless-shell-linux64/chrome-headless-shell",
    ]
    for path in potential_paths:
        if os.path.exists(path):
            os.environ["CHROMIUM_PATH"] = path
            logger.info(f"Set CHROMIUM_PATH to {path}")
            break


async def test_style(style: str, topic: str, niche: str, duration_seconds: int = 20):
    """Run the full Nexus pipeline for a single style."""
    from src.services.nexus_engine.auto_creator import base_creator_service
    from src.api.utils.database import async_session_factory
    from src.api.utils.models import NexusJobDB
    from src.services.llm.intelligence_hub import base_intelligence_service

    # Reset all LLM circuit breakers before starting
    base_intelligence_service.reset_all_circuits()
    logger.info("Reset all LLM circuit breakers")

    # Create a job in the database first
    job_id = str(uuid.uuid4())

    async with async_session_factory() as db:
        job = NexusJobDB(
            id=job_id,
            niche=niche,
            user_id="cfaf0a32-02ee-40a8-824c-f4b0a774f0ab",
            status="QUEUED",
            job_metadata={
                "style": style,
                "test_run": True,
                "topic": topic,
                "niche": niche,
            },
            progress=0,
        )
        db.add(job)
        await db.commit()
        logger.info(f"Created job {job_id} in database")

    logger.info(f"[{style}] ===== Starting full pipeline =====")
    logger.info(f"[{style}] Topic: {topic}")
    logger.info(f"[{style}] Niche: {niche}")
    logger.info(f"[{style}] Duration: {duration_seconds}s")

    try:
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche=niche,
            style=style,
            duration_seconds=duration_seconds,
            blueprint_id="story-factory",
            engine="cloud",
            use_gpu=False,
            batch_count=1,
        )
        logger.info(f"[{style}] Pipeline completed successfully!")
        logger.info(f"[{style}] Output path: {output_path}")

        # Verify the output file exists and has content
        if output_path and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"[{style}] Output file size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")

            # Copy to a predictable download location
            download_dir = "/tmp/ettametta_style_tests"
            os.makedirs(download_dir, exist_ok=True)
            download_path = os.path.join(download_dir, f"{style.lower()}.mp4")
            shutil.copy2(output_path, download_path)
            logger.info(f"[{style}] Copied to: {download_path}")
            print(f"RESULT_PATH:{download_path}")
            return download_path
        else:
            logger.error(f"[{style}] Output path is None or file doesn't exist: {output_path}")
            print("RESULT_PATH:None")
            return None

    except Exception as e:
        logger.exception(f"[{style}] Pipeline FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("RESULT_PATH:None")
        return None


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_style_pipeline.py <STYLE_NAME> [duration_seconds]")
        print("Example: python3 test_style_pipeline.py CINEMATIC_DOC 20")
        sys.exit(1)

    style = sys.argv[1].upper()
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    # Style-specific topics and niches
    STYLE_CONFIGS = {
        "CINEMATIC_DOC": {
            "topic": "The future of artificial intelligence in healthcare",
            "niche": "Technology & Innovation",
        },
        "REDDIT_STORY": {
            "topic": "My AI startup failed after raising 10 million dollars",
            "niche": "Startup Stories",
        },
        "TOP_LISTICLE": {
            "topic": "Top 5 programming languages for AI development in 2025",
            "niche": "Software Engineering",
        },
        "HEARTFELT_NARRATIVE": {
            "topic": "What I learned after 10 years as a software engineer",
            "niche": "Life Lessons",
        },
        "BROADCAST_NEWS": {
            "topic": "Breaking: AI regulation bill passes through Congress",
            "niche": "Breaking News",
        },
    }

    config = STYLE_CONFIGS.get(style)
    if not config:
        # Use generic config for arbitrary styles
        config = {
            "topic": f"A complete guide to {style.lower().replace('_', ' ')}",
            "niche": style.lower().replace("_", " ").title(),
        }

    result = await test_style(
        style=style,
        topic=config["topic"],
        niche=config["niche"],
        duration_seconds=duration,
    )

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

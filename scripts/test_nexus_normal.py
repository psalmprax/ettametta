import asyncio
import os
import sys
import logging

# Ensure we can import from src
PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.append(PROJECT_DIR)

# Mock environment to bypass database/redis if needed
os.environ["DEBUG"] = "true"
os.environ["USE_OS_MODELS"] = "true"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusNormalTest")

async def test_normal_fusion():
    logger.info("🏁 Starting Normal Nexus Fusion Test...")
    
    # Define a simple scene list
    scenes = [
        {
            "scene": "Introduction",
            "text": "The world's greatest tournament is coming to America.",
            "visual_prompt": "Soccer stadium in USA packed with fans cinematic wide shot",
            "duration": 5
        },
        {
            "scene": "Capability",
            "text": "Get ready for the Football World Cup across the United States.",
            "visual_prompt": "World cup soccer ball on pitch slow motion cinematic",
            "duration": 5
        }
    ]
    
    # This will trigger the REAL Topic Fusion synthesis handler
    # which now includes our NEW additions:
    # 1. Normalization
    # 2. Audio Ducking
    # 3. Vision QC
    # 4. AI Video Gen Fallback
    
    from src.services.nexus_engine.blueprints import TopicFusionSynthesisHandler
    handler = TopicFusionSynthesisHandler()
    
    inputs = {"topic": "Football World Cup in America", "niche": "Sports"}
    # Mock previous results (Cognition phase)
    previous_results = {
        "cognition": {
            "scenes": scenes
        }
    }
    
    logger.info("🎬 Executing TopicFusionSynthesisHandler...")
    result = await handler.execute(inputs, previous_results, job_id="test_normal_001")
    
    if result.get("output_generated"):
        logger.info(f"✅ Success! Video Path: {result['video_path']}")
        logger.info(f"🛠️ Method used: {result.get('method', 'standard_fusion')}")
        if "fusion_details" in result:
             logger.info(f"📋 QC Report: {result['fusion_details'].get('qc_report')}")
    else:
        logger.error("❌ Failed to generate output")

if __name__ == "__main__":
    asyncio.run(test_normal_fusion())

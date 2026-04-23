import os
import sys
import asyncio
import logging
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root and src to path
PROJECT_ROOT = Path("/home/psalmprax/ALL_PROJECTS/ettametta")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import the Elite Components
from src.engines.intelligent_video_workflow import discover_multi_platform, analyze_content_type, expand_query_intelligently
from src.engines.real_video_fusion_engine import RealVideoFusionEngine
from src.services.video_engine.remotion_service import base_remotion_service
from src.services.optimization.viral_critic import base_viral_critic
from src.services.monetization.service import base_monetization_engine
from src.services.video_engine.video_production_assistant import base_video_production_assistant

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestElitePhases")

async def test_phase_1_discovery(topic: str):
    logger.info(f"--- Testing Phase 1: Discovery for topic '{topic}' ---")
    leads = await discover_multi_platform(topic, max_per_platform=1)
    if leads:
        leads = leads[:3] # Keep only 3 leads for slow CPU tests
    if not leads:
        logger.error("❌ Phase 1 Failed: No leads found.")
        return None
    logger.info(f"✅ Phase 1 Success: Found {len(leads)} leads.")
    for lead in leads:
        logger.info(f"Lead: {lead.get('title')} ({lead.get('platform')})")
    return leads

async def test_phase_2_analysis_and_critic(leads, topic: str):
    logger.info(f"--- Testing Phase 2: Analysis & Quality Gate for topic '{topic}' ---")
    if not leads:
        logger.error("❌ Phase 2 skipped: No leads provided.")
        return None
    
    # Analysis (Sequential for slow CPU)
    analyses = []
    for v in leads:
        analysis = await analyze_content_type(v)
        analyses.append(analysis)
    for i, lead in enumerate(leads): 
        lead["analysis"] = analyses[i]
    
    eligible_leads = [v for v in leads if v["analysis"].get("usable", True)]
    logger.info(f"Eligible leads after analysis: {len(eligible_leads)}")
    
    # Critic Review
    mock_metadata = {"duration": 30, "segments_used": len(eligible_leads)}
    mock_script = {"segments": [{"text": lead['title']} for lead in eligible_leads[:5]]}
    
    audit_report = await base_viral_critic.review_production(topic, mock_script, mock_metadata)
    logger.info(f"Audit Score: {audit_report.get('overall_score')}/10")
    logger.info(f"Feedback: {audit_report.get('improvement_suggestions')}")
    
    return eligible_leads, audit_report

async def test_phase_3_monetization(topic: str):
    logger.info(f"--- Testing Phase 3: Monetization for topic '{topic}' ---")
    mock_script = "This is a video about " + topic
    monetization_plan = await base_monetization_engine.auto_insert_links("", topic, mock_script)
    logger.info(f"Monetization Plan: {monetization_plan.get('insertion_plan')}")
    return monetization_plan

async def test_phase_4_neural_fusion(leads, topic: str, quality: str = "ELITE"):
    logger.info(f"--- Testing Phase 4: Neural Fusion for topic '{topic}' (Quality: {quality}) ---")
    if not leads:
        logger.error("❌ Phase 4 skipped: No leads provided.")
        return None
    
    engine = RealVideoFusionEngine()
    try:
        fusion_result = await engine.create_real_video_content(
            discovered_videos=leads,
            content_topic=topic,
            duration_sec=30,
            quality=quality
        )
        video_path = fusion_result.get("video_path")
        if video_path and os.path.exists(video_path):
            logger.info(f"✅ Phase 4 Success: Video created at {video_path}")
            return fusion_result
        else:
            logger.error(f"❌ Phase 4 Failed: Video path invalid or not found: {video_path}")
            return None
    except Exception as e:
        logger.error(f"❌ Phase 4 Crashed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    topic = "cyberpunk future city"
    
    # Step 1
    leads = await test_phase_1_discovery(topic)
    
    # Step 2
    if leads:
        eligible_leads, audit_report = await test_phase_2_analysis_and_critic(leads, topic)
    else:
        eligible_leads = None
        audit_report = None
        
    # Step 3
    monetization_plan = await test_phase_3_monetization(topic)
    
    # Step 4
    if eligible_leads:
        fusion_result = await test_phase_4_neural_fusion(eligible_leads, topic, quality="FAST")
    else:
        logger.warning("Skipping Phase 4 because Phase 1/2 failed to provide leads.")

if __name__ == "__main__":
    asyncio.run(main())

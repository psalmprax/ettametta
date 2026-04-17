import os
import sys
import asyncio
import logging
import shutil
import uuid
import json
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the Elite Components
from src.engines.intelligent_video_workflow import discover_multi_platform, analyze_content_type, expand_query_intelligently
from src.engines.real_video_fusion_engine import RealVideoFusionEngine
from src.services.video_engine.base_remotion_service import base_remotion_service
from src.services.optimization.viral_critic import base_viral_critic
from src.services.monetization.service import base_monetization_engine
from src.services.video_engine.base_video_production_assistant import base_video_production_assistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("EliteCycle")

async def run_elite_production_cycle(topic: str, duration: int = 60, download_path: str = "local_downloads", session_id: str | None = None):
    """
    Executes the unified Tier 10 production flow.
    Includes Quality Gates, Monetization Injection, and Autonomous Pivoting.
    """
    
    # 0. Setup
    request_id = session_id or str(uuid.uuid4())
    download_dir = Path(download_path)
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Tier 10 State
    current_topic = topic
    attempts = 0
    MAX_ATTEMPTS = 3
    final_eligible_leads = []
    audit_report = None

    print("\n" + "="*80)
    print(f"🚀 INITIATING TIER 10 PRODUCTION CYCLE: '{topic}' [ID: {request_id}]")
    print("="*80)

    # --- PHASE 1 & 2: DISCOVERY & QUALITY GATE (PIVOT LOOP) ---
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        logger.info(json.dumps({
            "event": "cycle_attempt",
            "attempt": attempts,
            "topic": current_topic,
            "request_id": request_id
        }))
        
        # Discovery
        leads = await discover_multi_platform(current_topic, max_per_platform=3, session_id=request_id)
        if not leads:
            logger.warning(f"⚠️ No leads for '{current_topic}'. Expanding search...")
            swarm = await expand_query_intelligently(current_topic, session_id=request_id)
            current_topic = swarm[0] if swarm else current_topic
            continue

        # Curation & Analysis
        analysis_tasks = [analyze_content_type(v, session_id=request_id) for v in leads]
        analyses = await asyncio.gather(*analysis_tasks)
        for i, lead in enumerate(leads): lead["analysis"] = analyses[i]
        
        eligible_leads = [v for v in leads if v["analysis"].get("usable", True)]
        eligible_leads.sort(key=lambda x: x["analysis"].get("score", 0), reverse=True)
        
        if not eligible_leads:
            logger.warning("⚠️ Discovery found no 'Elite' leads. Pivoting...")
            current_topic = f"trending {current_topic}"
            continue

        # CRITIC AUDIT (TIER 10 HARD GATE)
        logger.info(f"🧐 [Quality Gate] Performing ViralCritic Audit for {request_id}...")
        # We simulate a "Production Package" for the critic to review before fusion
        mock_metadata = {"duration": duration, "segments_used": len(eligible_leads)}
        mock_script = {"segments": [{"text": lead['title']} for lead in eligible_leads[:5]]}
        
        audit_report = await base_viral_critic.review_production(current_topic, mock_script, mock_metadata, session_id=request_id)
        
        if audit_report.get("overall_score", 0) >= 6.0:
            logger.info(f"✅ Quality Score {audit_report['overall_score']}/10. PROCEEDING TO FUSION.")
            final_eligible_leads = eligible_leads
            break
        else:
            logger.warning(f"❌ [Rejected] Score {audit_report['overall_score']}/10. '{current_topic}' is too weak.")
            logger.info(f"🧠 [Pivot] Applying feedback: {audit_report.get('improvement_suggestions', [])}")
            # Intelligent Pivot
            swarm = await expand_query_intelligently(current_topic, session_id=request_id)
            current_topic = swarm[attempts % len(swarm)] if swarm else current_topic

    if not final_eligible_leads:
        logger.error(f"❌ Elite Production Failed for {request_id}: Max attempts reached.")
        return None

    # --- PHASE 3: MONETIZATION INJECTION (TIER 10) ---
    logger.info(f"[Step 3/6] MONETIZATION: Matching assets for {request_id}...")
    # Inject monetization assets based on the winning topic
    monetization_plan = await base_monetization_engine.auto_insert_links("", current_topic, str(mock_script), session_id=request_id)
    
    # --- PHASE 4: NEURAL FUSION ---
    logger.info(f"[Step 4/6] FUSION: Assembling cinematic sequence for {request_id}...")
    engine = RealVideoFusionEngine()
    fusion_result = await engine.create_real_video_content(
        discovered_videos=final_eligible_leads,
        content_topic=current_topic,
        duration_sec=duration,
        session_id=request_id
    )
    
    fused_video_path = fusion_result.get("video_path")
    if not fused_video_path or not os.path.exists(fused_video_path):
        logger.error("❌ Fusion failed.")
        return None

    # --- PHASE 5: REMOTION POLISH (POLISHING & MONETIZATION) ---
    logger.info("[Step 5/6] POLISHING: Rendering captions & monetization overlays...")
    
    # Convert critic report into actionable edit commands
    production_actions = base_video_production_assistant.transform_critic_report_to_actions(audit_report)
    
    # NEW: SCENE-AWARE TIMELINE (Director's Cut)
    timeline = []
    current_time = 0
    for seg in fusion_result.get("fusion_plan", {}).get("segments", []):
        timeline.append({
            "text": seg["text"],
            "role": seg.get("role", "BODY"),
            "start": current_time,
            "duration": seg["duration"],
            "style": "high_impact" if seg.get("role") == "HOOK" else "standard"
        })
        current_time += seg["duration"]

    remotion_props = {
        "videoUrl": os.path.abspath(fused_video_path),
        "title": fusion_result.get("script", {}).get("title", f"The {current_topic} Story"),
        "subtitle": f"A ViralForge Production ID: {request_id[:8]}",
        "timeline": timeline,
        "branding": {"name": "ettametta", "handle": "@viral_forge"},
        "monetization": {
            "cta": monetization_plan.get("insertion_plan", {}).get("insertions", [{}])[0].get("script_addition", "Check Bio!"),
            "url": "https://ettametta.ai/shop"
        },
        "showCtaOverlay": True,
        "editorial_notes": production_actions,
        "style": fusion_result.get("fusion_plan", {}).get("editorial_style", "Cinematic")
    }
    
    final_master_path = await base_remotion_service.render_video(
        composition_id="ViralClip",
        props=remotion_props,
        output_name=f"director_cut_{uuid.uuid4().hex[:8]}.mp4"
    )
    
    if not final_master_path:
        final_master_path = fused_video_path
        logger.warning("⚠️ Remotion polish failed. Exporting raw fusion.")

    # --- PHASE 6: EXPORT ---
    logger.info("[Step 6/6] EXPORT: Saving hardened master to local system...")
    final_local_path = download_dir / os.path.basename(final_master_path)
    shutil.copy2(final_master_path, final_local_path)
    
    print("\n" + "="*80)
    print(f"🎉 TIER 10 PRODUCTION COMPLETE!")
    print(f"📍 Final Video Location: {final_local_path}")
    print(f"💰 Monetization status: Assets injected")
    print(f"⭐️ Final Quality Score: {audit_report.get('overall_score', 0)}/10")
    print("="*80 + "\n")
    
    return final_local_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the Hardened ViralForge Elite Cycle")
    parser.add_argument("topic", type=str, help="Viral topic")
    parser.add_argument("--duration", type=int, default=30, help="Seconds")
    
    args = parser.parse_args()
    asyncio.run(run_elite_production_cycle(args.topic, args.duration))

import asyncio
import logging
import json
import os
import sys
from pathlib import Path

# This is a script-style verification (run via `python test_ettametta_cycle.py`),
# not a pytest test suite. Skip it during pytest collection so it doesn't block
# collection when its optional engine imports are missing.
import pytest
pytest.skip("script-style E2E verification; run directly, not via pytest", allow_module_level=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engines.intelligent_video_workflow import discover_multi_platform
from src.engines.real_video_fusion_engine import RealVideoFusionEngine

# Configure logging to show the cinematic events clearly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WorkflowTest")

async def run_e2e_workflow():
    """
    End-to-End Workflow Verification:
    Discovery -> Analysis -> Procurement -> Neural Fusion
    """
    print("\n" + "="*60)
    print("🚀 ETTAMETTA E2E WORKFLOW TEST STARTING")
    print("="*60)

    topic = "AI productivity tools 2026"
    duration = 30

    # Initialize Engine
    engine = RealVideoFusionEngine(output_dir="output/vids/test_run")

    # 1. DISCOVERY PHASE
    cache_file = Path("src/engines/temp_leads.json")

    if cache_file.exists():
        print(f"\n[PHASE 1] Loading cached discovery results from {cache_file}")
        with open(cache_file, 'r') as f:
            videos = json.load(f)
    else:
        print(f"\n[PHASE 1] Multi-Platform Discovery: '{topic}'")
        # We use a smaller limit for the test to ensure speed
        videos = await discover_multi_platform(topic, max_per_platform=2)

        if videos:
            with open(cache_file, 'w') as f:
                json.dump(videos, f)

    if not videos:
        print("❌ FAILED: No videos discovered. Check API keys or network.")
        return

    print(f"✅ Success: Found {len(videos)} potential leads.")
    for v in videos[:3]:
        print(f"   - [{v['platform']}] {v['title'][:50]}...")

    # 2. SELECTION & ANALYSIS (Handled inside Fusion Engine)
    # We pass the raw discovered leads to the fusion engine 10.0
    print(f"\n[PHASE 2] Neural Production & Asset Procurement (Target: {duration}s)")
    try:
        result = await engine.create_real_video_content(
            discovered_videos=videos,
            content_topic=topic,
            duration_sec=duration,
            session_id="test_e2e_001"
        )

        if result.get("success"):
            print("\n" + "="*60)
            print("🏆 WORKFLOW SUCCESS")
            print("="*60)
            print(f"🎬 Video Generated: {result['video_path']}")
            print(f"📝 Script Title: {result.get('script', {}).get('title')}")
            print(f"📦 Distribution Package: {result.get('distribution_package', {}).get('package_path', 'N/A')}")

            # Verify file exists
            if os.path.exists(result['video_path']):
                print(f"📁 Verification: File exists and size is {os.path.getsize(result['video_path'])} bytes.")
            else:
                print("❌ Verification Error: Video path returned but file not found on disk.")
        else:
            print(f"❌ FAILED: Production error - {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.exception("Workflow execution crashed")
        print(f"❌ CRITICAL FAILURE: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_e2e_workflow())

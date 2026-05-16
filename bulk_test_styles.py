import asyncio
import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)

from src.services.nexus_engine.auto_creator import base_creator_service
from src.services.nexus_engine.style_library import NexusStyle
from src.services.llm.intelligence_hub import base_intelligence_service

# Force Ollama as it's the most reliable on this setup
original_chat = base_intelligence_service.chat
async def forced_chat(*args, **kwargs):
    kwargs["provider"] = os.getenv("FORCE_PROVIDER", "ollama")
    return await original_chat(*args, **kwargs)

base_intelligence_service.chat = forced_chat

async def run_style_test(style_name: str, results: dict):
    print(f"\n🎬 [BATCH] Testing Style: {style_name}")
    topic = f"The fascinating world of {style_name.replace('_', ' ').lower()}"
    job_id = f"bulk_{style_name.lower()}_{int(time.time())}"
    
    start_time = time.time()
    try:
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche="General",
            style=style_name,
            duration_seconds=15 # Shorter duration for bulk testing
        )
        
        duration = time.time() - start_time
        file_exists = os.path.exists(output_path)
        file_size = os.path.getsize(output_path) if file_exists else 0
        
        results[style_name] = {
            "status": "SUCCESS" if file_exists else "FAILED_FILE_MISSING",
            "job_id": job_id,
            "output_path": output_path,
            "duration_sec": round(duration, 2),
            "file_size_bytes": file_size,
            "error": None
        }
        print(f"✅ {style_name} completed in {round(duration, 2)}s")
        
    except Exception as e:
        duration = time.time() - start_time
        results[style_name] = {
            "status": "FAILED",
            "job_id": job_id,
            "duration_sec": round(duration, 2),
            "error": str(e)
        }
        print(f"❌ {style_name} failed: {e}")

async def main():
    styles = [s.value for s in NexusStyle]
    results = {}
    
    print(f"🚀 Starting bulk style test for {len(styles)} styles...")
    
    # Save partial results after each run
    results_file = "bulk_test_results.json"
    
    for style in styles:
        await run_style_test(style, results)
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        # Small cooldown
        await asyncio.sleep(2)

    print("\n🏁 Bulk test complete!")
    print(f"📊 Results saved to {results_file}")

if __name__ == "__main__":
    asyncio.run(main())

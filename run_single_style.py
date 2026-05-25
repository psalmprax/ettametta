import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)

from src.services.nexus_engine.auto_creator import base_creator_service
from src.services.llm.intelligence_hub import base_intelligence_service

# Force Ollama as it's the most reliable on this setup
original_chat = base_intelligence_service.chat
async def forced_chat(*args, **kwargs):
    kwargs["provider"] = os.getenv("FORCE_PROVIDER", "ollama")
    return await original_chat(*args, **kwargs)

base_intelligence_service.chat = forced_chat

async def run_style_test(style_name: str):
    print(f"\n🎬 Testing Style: {style_name}")
    topic = f"The fascinating world of {style_name.replace('_', ' ').lower()}"
    job_id = f"single_{style_name.lower()}_{int(time.time())}"
    
    start_time = time.time()
    try:
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche="General",
            style=style_name,
            duration_seconds=15 # Shorter duration for testing
        )
        
        duration = time.time() - start_time
        file_exists = os.path.exists(output_path)
        
        if file_exists:
            print(f"✅ {style_name} completed in {round(duration, 2)}s. Output: {output_path}")
            return True
        else:
            print(f"❌ {style_name} failed: File missing at {output_path}")
            return False
        
    except Exception as e:
        print(f"❌ {style_name} failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_single_style.py <style_name>")
        sys.exit(1)
    
    style = sys.argv[1]
    success = asyncio.run(run_style_test(style))
    sys.exit(0 if success else 1)

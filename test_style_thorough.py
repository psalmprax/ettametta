import asyncio
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)

from src.services.nexus_engine.auto_creator import base_creator_service
from src.services.nexus_engine.style_library import NexusStyle
from src.services.llm.intelligence_hub import base_intelligence_service

# Monkeypatch IntelligenceHub to force provider if requested
original_chat = base_intelligence_service.chat
async def forced_chat(*args, **kwargs):
    if os.getenv("FORCE_PROVIDER"):
        kwargs["provider"] = os.getenv("FORCE_PROVIDER")
    return await original_chat(*args, **kwargs)

base_intelligence_service.chat = forced_chat

async def test_creation(topic: str, style: str):
    print(f"\n🚀 Testing Creation: Style='{style}' | Topic='{topic}'")
    try:
        job_id = f"test_{style.lower()}_{int(asyncio.get_event_loop().time())}"
        niche = "Education"
        
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche=niche,
            style=style,
            duration_seconds=30
        )
        
        print(f"✅ Creation Successful!")
        print(f"🎬 Video Path: {output_path}")
        if os.path.exists(output_path):
            print(f"📁 Verification: File exists ({os.path.getsize(output_path)} bytes)")
        else:
            print(f"❌ Verification Error: File not found at {output_path}")
            
    except Exception as e:
        print(f"❌ Creation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Ettametta Style Creation")
    parser.add_argument("--style", type=str, default="CINEMATIC_DOC", help="Nexus style to use")
    parser.add_argument("--topic", type=str, default="A thorough look into AI", help="Topic to use")
    
    args = parser.parse_args()
    
    asyncio.run(test_creation(args.topic, args.style))

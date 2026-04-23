import asyncio
import os
import json
import logging
from src.services.hermes.service import base_hermes_service

# Setup logging to see output
logging.basicConfig(level=logging.INFO)

async def test_hermes_reflection():
    print("🚀 Starting Hermes Reflection Test...")
    
    # Mock data for a successful video job
    job_data = {
        "job_id": "test_verification_001",
        "niche": "Technology",
        "script": {
            "title": "Why AI is changing everything",
            "hook": "Stop scrolling! AI just solved its biggest problem.",
            "body": "For years, we thought X was impossible. But a new breakthrough shows..."
        },
        "user_id": "admin"
    }
    
    metrics = {
        "views": 7500,
        "retention_p50": 0.65,
        "shares": 120
    }
    
    print(f"📡 Sending reflection request to local Hermes (hermes3)...")
    
    # This will trigger _call_llm which should hit the local Ollama
    skill = await base_hermes_service.reflect_and_crystallize(job_data, metrics)
    
    if skill:
        print("\n✅ SUCCESS! Hermes reflected and crystallized a new skill:")
        print(json.dumps(skill, indent=4))
    else:
        print("\n❌ FAILED. No skill was crystallized. Check Ollama logs.")

if __name__ == "__main__":
    asyncio.run(test_hermes_reflection())

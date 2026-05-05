import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.llm.intelligence_hub import base_intelligence_service

async def test_ollama_direct():
    print("Testing Ollama via IntelligenceHub...")
    try:
        # Force ollama provider
        result = await base_intelligence_service.chat(
            prompt="say hi",
            provider="ollama"
        )
        print(f"Success! Provider: {result['provider']}")
        print(f"Response: {result['response']}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_ollama_direct())

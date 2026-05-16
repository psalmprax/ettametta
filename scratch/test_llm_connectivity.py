
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

load_dotenv()

from src.services.llm.service import unified_llm_service, LLMProvider

async def test_providers():
    print("--- LLM Provider Connectivity Test ---")
    providers = [LLMProvider.GROQ, LLMProvider.OPENAI, LLMProvider.GEMINI]
    
    for provider in providers:
        print(f"\nTesting {provider.value}...")
        try:
            response = await unified_llm_service.complete(
                prompt="Say 'Hello World' in 2 words.",
                provider=provider
            )
            if "error" in response:
                print(f"❌ {provider.value} failed: {response['error']}")
            else:
                print(f"✅ {provider.value} success: {response['content']}")
        except Exception as e:
            print(f"💥 {provider.value} exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_providers())

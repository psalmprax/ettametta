import asyncio
import sys
import os
PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv
load_dotenv()

from src.services.llm.intelligence_hub import base_intelligence_service

async def test_groq():
    print(f"Testing Groq... Key: {os.getenv('GROQ_API_KEY')[:10]}...")
    try:
        res = await base_intelligence_service.chat(
            prompt="Say hello from Groq!",
            provider="groq"
        )
        print(f"Success: {res['response']}")
    except Exception as e:
        print(f"Failure: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())

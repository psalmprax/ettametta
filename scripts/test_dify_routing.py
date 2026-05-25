import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.llm.intelligence_hub import base_intelligence_service
from src.api.config import settings

async def test_dify_routing():
    print("Testing Dify Routing via IntelligenceHub...")
    
    # Temporarily set dummy keys for testing routing
    settings.DIFY_API_KEY = "dummy-key"
    
    try:
        # This will trigger _call_dify but fail with 401/404 because the key is dummy
        # We want to see if it reaches the 'dify' provider in the logs
        print("Calling chat with complexity='high'...")
        response = await base_intelligence_service.chat(
            prompt="Hello Dify",
            complexity="high"
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Caught Expected Exception: {e}")
        # If it reached Dify, the error should mention Dify
        if "Dify" in str(e) or "dify" in str(e):
            print("SUCCESS: Request routed to Dify provider!")
        else:
            print("FAILURE: Request did not route to Dify provider.")

if __name__ == "__main__":
    asyncio.run(test_dify_routing())

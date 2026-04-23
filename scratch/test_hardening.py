import asyncio
import json
import logging
from src.services.llm.intelligence_hub import base_intelligence_hub

async def test_hub_hardening():
    print("🧪 Testing ettametta Intelligence Hub Hardening...")
    
    # Test 1: Successful OpenAI call with RequestID
    print("\n[Test 1] OpenAI Primary Call...")
    try:
        res = await base_intelligence_hub.chat(
            prompt="Tell me a joke about AI video production.",
            session_id="test-session-123"
        )
        print(f"✅ Success via {res['provider'].upper()}")
        print(f"Request ID: {res['request_id']}")
        print(f"Latency: {res['latency_sec']:.2f}s")
        # print(f"Response: {res['response'][:100]}...")
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")

    # Test 2: Structured Logging Check (Manual verification in stdout)
    print("\n[Test 2] JSON Mode check...")
    try:
        res = await base_intelligence_hub.chat(
            prompt="Generate a list of 3 viral niches. Return JSON: {'niches': []}",
            session_id="test-session-456",
            json_mode=True
        )
        data = json.loads(res["response"])
        print(f"✅ JSON Parsed: {data.get('niches', [])}")
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_hub_hardening())

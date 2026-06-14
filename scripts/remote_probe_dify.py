"""
Inspect the Dify app configuration by probing its response behavior.
Tests with and without json_mode, and inspects response structure.
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, "/app")

async def main():
    print("=" * 60)
    print("Dify App Configuration Probe")
    print("=" * 60)

    from src.services.llm.dify_client import base_dify_client

    # Test 1: Without json_mode — basic prompt
    print("\n📡 Test 1: Basic chat (no json_mode)")
    try:
        resp = await base_dify_client.chat_messages(
            query="Reply with exactly: HELLO_FROM_DIFY",
            user_id="ettametta_probe",
            inputs={}
        )
        print(f"   Status: Connected")
        print(f"   Answer: {resp.get('answer', '')[:200]}")
        print(f"   Conversation ID: {resp.get('conversation_id', 'N/A')}")
        meta = resp.get("metadata", {})
        usage = meta.get("usage", {})
        print(f"   Usage: {json.dumps(usage)[:200]}")
        print(f"   All keys: {list(resp.keys())}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 2: With json_mode=true
    print("\n📡 Test 2: With json_mode=true")
    try:
        resp = await base_dify_client.chat_messages(
            query="Reply with a JSON: {\"message\": \"hello\", \"status\": \"ok\"}",
            user_id="ettametta_probe",
            inputs={"json_mode": True}
        )
        print(f"   Status: Connected")
        print(f"   Answer: {resp.get('answer', '')[:300]}")
        print(f"   Conversation ID: {resp.get('conversation_id', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 3: Check what app this API key points to
    print("\n📡 Test 3: App info via conversation list")
    try:
        # Try listing conversations to see what's configured
        from httpx import AsyncClient
        from src.api.config import settings
        headers = {
            "Authorization": f"Bearer {settings.DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        async with AsyncClient(timeout=10) as client:
            # Try the conversations endpoint
            url = f"{settings.DIFY_API_URL.rstrip('/')}/conversations"
            resp = await client.get(url, headers=headers)
            print(f"   Conversations endpoint: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   Data: {json.dumps(data)[:300]}")
            else:
                print(f"   Response: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 4: Try parameters endpoint
    print("\n📡 Test 4: App parameters")
    try:
        from httpx import AsyncClient
        from src.api.config import settings
        headers = {
            "Authorization": f"Bearer {settings.DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        async with AsyncClient(timeout=10) as client:
            url = f"{settings.DIFY_API_URL.rstrip('/')}/parameters"
            resp = await client.get(url, headers=headers)
            print(f"   Parameters endpoint: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   Data: {json.dumps(data)[:500]}")
            else:
                print(f"   Response: {resp.text[:300]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n" + "=" * 60)
    print("Probe complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

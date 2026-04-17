import os
from dotenv import load_dotenv
import httpx
import asyncio

async def test():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("❌ No OPENAI_API_KEY found in environment")
        return
    
    print(f"🔑 Key found (length {len(key)})")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key.strip()}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hi"}]
            }
        )
        print(f"📡 Status: {resp.status_code}")
        print(f"📄 Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test())

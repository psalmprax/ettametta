import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_keys():
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    print(f"Testing OpenAI Key: {openai_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}
            )
            print(f"OpenAI Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"OpenAI Error: {resp.text}")
    except Exception as e:
        print(f"OpenAI Exception: {e}")

    print(f"\nTesting Groq Key: {groq_key[:10]}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "hi"}]}
            )
            print(f"Groq Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Groq Error: {resp.text}")
    except Exception as e:
        print(f"Groq Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_keys())

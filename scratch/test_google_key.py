import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_google_key():
    google_key = os.getenv("GOOGLE_API_KEY")
    print(f"Testing Google Key: {google_key[:10]}...")
    
    # Gemini 1.5 Flash is great for vision
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={google_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": "hi"}]
        }]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            print(f"Google Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Google Error: {resp.text}")
            else:
                print("Google Key is WORKING!")
    except Exception as e:
        print(f"Google Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_google_key())

import os
import asyncio
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

from services.discovery.youtube_scanner import YouTubeShortsScanner
from services.discovery.tiktok_scanner import TikTokScanner
from services.discovery.youtube_long_scanner import YouTubeLongScanner
from groq import Groq

async def test_groq():
    print("🧠 Testing Groq (AI Brain)...")
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("❌ FAIL: GROQ_API_KEY is missing in .env")
        return False
    
    try:
        client = Groq(api_key=key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Verification check. Reply with 'OK'."}],
        )
        response = completion.choices[0].message.content
        if "OK" in response:
            print("✅ PASS: Groq is responding correctly.")
            return True
        else:
            print(f"⚠️  WARNING: Groq responded but output was unexpected: {response}")
            return True
    except Exception as e:
        print(f"❌ FAIL: Groq error: {e}")
        return False

async def test_youtube():
    print("\n📺 Testing YouTube Data API...")
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        print("❌ FAIL: YOUTUBE_API_KEY is missing in .env")
        return False
    
    try:
        scanner = YouTubeShortsScanner()
        results = await scanner.scan_trends("motivation")
        if results:
            print(f"✅ PASS: Found {len(results)} videos. API is working.")
            return True
        else:
            print("⚠️  WARNING: YouTube API connected but returned 0 results. Check if quota is hit.")
            return False
    except Exception as e:
        print(f"❌ FAIL: YouTube error: {e}")
        return False

async def test_tiktok():
    print("\n🎵 Testing TikTok Discovery (Scraper)...")
    try:
        scanner = TikTokScanner()
        results = await scanner.scan_trends("crypto")
        if results:
            print(f"✅ PASS: Found {len(results)} TikToks. Network/Parser is active.")
            return True
        else:
            print("❌ FAIL: TikTok scraper returned 0 results. TikTok may have changed their layout.")
            return False
    except Exception as e:
        print(f"❌ FAIL: TikTok error: {e}")
        return False

async def main():
    print("""
    =========================================
    🚀 ViralForge API Diagnostic Utility
    =========================================
    """)
    
    results = await asyncio.gather(
        test_groq(),
        test_youtube(),
        test_tiktok()
    )
    
    print("\n=========================================")
    if all(results):
        print("🎉 ALL SYSTEMS GO! Your ViralForge engine is fully powered.")
    else:
        print("⚠️  DIAGNOSTIC INCOMPLETE: Please review the failures above.")
    print("=========================================\n")

if __name__ == "__main__":
    asyncio.run(main())

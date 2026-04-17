#!/usr/bin/env python3
"""
E2E Test: Download and Process Video
=====================================
"""

import asyncio
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DEBUG to avoid pydantic bool parsing issue
os.environ["DEBUG"] = "true"

from dotenv import load_dotenv

load_dotenv()

# Ensure DEBUG is explicitly set to boolean
os.environ["DEBUG"] = "true"

from src.services.video_engine.downloader import base_video_downloader


async def test_download():
    """Test downloading a video from discovered content"""

    # From our discovery, we found these eligible videos:
    # - "5 AI Tools That Will Blow Your Mind in 2026" - 3 days old (YouTube)
    # - "【自动AI】12分钟招到24小时不下班AI员工" - new (Bilibili)

    # Use a working YouTube video URL
    test_url = (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - reliable test
    )

    print("\n[1/5] DOWNLOADING video...")
    print(f"  URL: {test_url}")

    video_path = await base_video_downloader.download_video(test_url)

    if not video_path:
        print("  ❌ Download failed!")
        return None

    print(f"  ✅ Downloaded: {video_path}")
    print(f"  Size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")

    return video_path


async def main():
    video_path = await test_download()

    if video_path:
        print(f"\n✅ DOWNLOAD TEST PASSED")
        print(f"  Video saved to: {video_path}")
    else:
        print("\n❌ DOWNLOAD TEST FAILED")

    return video_path


if __name__ == "__main__":
    result = asyncio.run(main())

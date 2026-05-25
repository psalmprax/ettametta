#!/usr/bin/env python3
"""
Remote E2E Test - Steps 3 & 4 (Transcription + VLM)
================================================
Run this on the remote server after uploading the video.
"""

import os
import sys

# Setup environment
os.environ["DEBUG"] = "true"
os.environ["USE_OS_MODELS"] = "true"

from dotenv import load_dotenv

load_dotenv()

import asyncio


async def run_transcription(video_path: str):
    """Step 3: Transcribe video audio"""
    print(f"\n[STEP 3] TRANSCRIBING: {video_path}")

    try:
        # Try faster-whisper first
        from src.api.utils.os_worker import ai_worker

        result = await ai_worker.transcribe(video_path)

        if result:
            print(f"  ✅ Transcript: {len(result)} segments")
            for seg in result[:3]:
                print(f"    - {seg.get('text', '')[:60]}...")
            return result
    except ImportError:
        print("  ⚠️ faster-whisper not installed")
    except Exception as e:
        print(f"  ⚠️ Transcription error: {e}")

    return []


async def run_vlm_analysis(video_path: str):
    """Step 4: Analyze video with VLM"""
    print(f"\n[STEP 4] VLM ANALYSIS: {video_path}")

    try:
        from src.services.video_engine.base_vlm_service import base_vlm_service

        result = await base_vlm_service.analyze_video_content(video_path)

        if result:
            print("  ✅ VLM Analysis:")
            print(f"    - Visual mood: {result.get('visual_mood', 'unknown')}")
            print(f"    - Content type: {result.get('content_type', 'unknown')}")
            print(f"    - Key moments: {len(result.get('key_moments', []))}")
            return result
    except ImportError as e:
        print(f"  ⚠️ VLM module import error: {e}")
    except Exception as e:
        print(f"  ⚠️ VLM analysis error: {e}")

    return {}


async def main():
    # Use video from local test or accept as argument
    video_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "temp/downloads/39b79e32-0d84-4609-b9e1-9d1a9b7db56c.mp4"
    )

    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        print("Usage: python3 remote_e2e_test.py <video_path>")
        return

    print(f"Testing with: {video_path}")
    print(f"File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")

    # Step 3: Transcription
    transcript = await run_transcription(video_path)

    # Step 4: VLM Analysis
    vlm_result = await run_vlm_analysis(video_path)

    # Summary
    print("\n" + "=" * 50)
    print("REMOTE E2E RESULTS")
    print("=" * 50)
    print(f"Video: {video_path}")
    print(f"Transcript segments: {len(transcript)}")
    print(f"VLM Analysis: {'Success' if vlm_result else 'Failed/Skipped'}")

    if vlm_result:
        print(f"  - Visual mood: {vlm_result.get('visual_mood')}")
        print(f"  - Content type: {vlm_result.get('content_type')}")


if __name__ == "__main__":
    asyncio.run(main())

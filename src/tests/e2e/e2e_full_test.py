#!/usr/bin/env python3
"""
E2E Test: Full Video Processing Pipeline
=========================================
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

from src.services.video_engine.downloader import base_downloader_service
from src.services.video_engine.transcription import base_transcription_service


async def test_full_pipeline():
    """Test full pipeline: download -> transcribe -> analyze -> process"""

    # Use our downloaded video or download new
    test_video = "temp/downloads/39b79e32-0d84-4609-b9e1-9d1a9b7db56c.mp4"

    if not os.path.exists(test_video):
        print("\n[1/5] DOWNLOADING video...")
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print(f"  URL: {test_url}")
        test_video = await base_downloader_service.download_video(test_url)
        if not test_video:
            print("  ❌ Download failed!")
            return None
        print(f"  ✅ Downloaded: {test_video}")
    else:
        print(f"\n[1/5] USING EXISTING: {test_video}")

    # Step 2: Transcribe
    print("\n[2/5] TRANSCRIBING audio...")
    try:
        transcript = await base_transcription_service.transcribe_video(test_video)
        if transcript:
            print(f"  ✅ Transcript: {len(transcript)} segments")
            for seg in transcript[:3]:
                print(f"    - {seg.get('text', '')[:60]}...")
        else:
            print("  ⚠️ No transcript (may be music-only video)")
    except Exception as e:
        print(f"  ⚠️ Transcription error: {e}")
        transcript = []

    # Step 3: VLM Analysis (if available)
    print("\n[3/5] ANALYZING video content (VLM)...")
    try:
        from src.services.video_engine.vlm_service import base_vlm_service

        visual_analysis = await base_vlm_service.analyze_video_content(test_video)
        if visual_analysis:
            print("  ✅ VLM Analysis:")
            print(f"    - Visual mood: {visual_analysis.get('visual_mood', 'unknown')}")
            print(
                f"    - Content type: {visual_analysis.get('content_type', 'unknown')}"
            )
            print(f"    - Key moments: {len(visual_analysis.get('key_moments', []))}")
        else:
            print("  ⚠️ VLM analysis unavailable")
            visual_analysis = {}
    except Exception as e:
        print(f"  ⚠️ VLM error: {e}")
        visual_analysis = {}

    # Step 4: Video Processing Pipeline
    print("\n[4/5] PROCESSING video through pipeline...")
    try:
        from src.services.video_engine.processor import VideoProcessor

        processor = VideoProcessor()
        output_name = f"e2e_test_output_{os.path.basename(test_video)}"

        # Process with basic strategy
        strategy = {
            "vibe": "energetic",
            "speed_range": (1.2, 1.5),
            "jitter_intensity": 0.3,
            "transitions": "smooth",
        }

        processed = await processor.process_full_pipeline(
            test_video, output_name, strategy=strategy
        )

        if processed and os.path.exists(processed):
            size_mb = os.path.getsize(processed) / 1024 / 1024
            print(f"  ✅ Processed: {processed} ({size_mb:.2f} MB)")
        else:
            print("  ⚠️ Processing returned no output")
            processed = None
    except Exception as e:
        print(f"  ❌ Processing error: {e}")
        import traceback

        traceback.print_exc()
        processed = None

    # Step 5: Review
    print("\n[5/5] REVIEW OUTPUT...")
    if processed and os.path.exists(processed):
        print(f"  ✅ Final video: {processed}")
        print(f"  Size: {os.path.getsize(processed) / 1024 / 1024:.2f} MB")
    else:
        print("  ❌ No output to review")

    return {
        "original": test_video,
        "transcript": transcript,
        "visual_analysis": visual_analysis,
        "processed": processed,
    }


async def main():
    result = await test_full_pipeline()

    print("\n" + "=" * 60)
    if result:
        print("✅ E2E PIPELINE COMPLETE!")
        print(f"  Original: {result['original']}")
        print(f"  Transcript segments: {len(result.get('transcript', []))}")
        print(f"  Processed: {result['processed']}")
    else:
        print("❌ E2E PIPELINE FAILED")

    return result


if __name__ == "__main__":
    asyncio.run(main())

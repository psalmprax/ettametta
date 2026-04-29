#!/usr/bin/env python3
"""
Standalone Remote E2E Test - Steps 3 & 4
=========================================
"""

import os
import sys
import asyncio
import subprocess
import base64

PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

os.environ["DEBUG"] = "true"
os.environ["USE_OS_MODELS"] = "true"

from dotenv import load_dotenv

load_dotenv("/tmp/.env")

# Also set explicitly
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")


async def test_step3_transcription(video_path: str):
    """Step 3: Transcribe video using faster-whisper"""
    print(f"\n[STEP 3] TRANSCRIBING: {video_path}")

    try:
        from faster_whisper import WhisperModel

        print("  Loading tiny model (CPU)...")
        model = WhisperModel("tiny", device="cpu", download_root="/tmp/whisper")

        segments, info = model.transcribe(video_path, beam_size=1, vad_filter=True)

        result = []
        for seg in segments:
            result.append({"start": seg.start, "end": seg.end, "text": seg.text})

        print(f"  ✅ Transcript: {len(result)} segments")
        print(f"    Language: {info.language}")
        for seg in result[:3]:
            print(f"    - {seg['text'][:60]}...")

        return result
    except ImportError:
        print("  ⚠️ faster-whisper not installed")
    except Exception as e:
        print(f"  ⚠️ Transcription error: {e}")

    return []


async def test_step4_vlm_analysis(video_path: str):
    """Step 4: Analyze video with VLM using OpenAI Vision"""
    print(f"\n[STEP 4] VLM ANALYSIS: {video_path}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("  ⚠️ No OPENAI_API_KEY")
        return {}

    try:
        import httpx

        # Extract first frame as thumbnail
        thumb_path = "/tmp/video_thumb.jpg"
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-ss",
                "00:00:01",
                "-vframes",
                "1",
                thumb_path,
            ],
            capture_output=True,
            timeout=30,
        )

        if not os.path.exists(thumb_path):
            print("  ⚠️ Could not extract thumbnail")
            return {}

        with open(thumb_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        print("  📤 Analyzing with OpenAI Vision...")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this video frame. Describe: 1) What's happening 2) The visual mood 3) Key content type (talking head, demo, music video, etc)",
                                },
                                {
                                    "type": "image_uri",
                                    "image_uri": {
                                        "url": f"data:image/jpeg;base64,{img_b64}"
                                    },
                                },
                            ],
                        }
                    ],
                    "max_tokens": 300,
                },
            )

        if resp.status_code == 200:
            data = resp.json()
            description = data["choices"][0]["message"]["content"]

            result = {
                "visual_mood": "analyzed",
                "content_type": "video_analysis",
                "description": description,
                "key_moments": [],
            }

            print(f"  ✅ VLM: {description[:150]}...")

            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            return result
        else:
            print(f"  ⚠️ OpenAI error: {resp.status_code}")

    except Exception as e:
        print(f"  ⚠️ VLM error: {e}")

    return {}


async def main():
    video_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_video.mp4"

    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return

    print(f"=== REMOTE E2E TEST ===")
    print(f"Video: {video_path}")
    print(f"Size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")

    transcript = await test_step3_transcription(video_path)
    vlm = await test_step4_vlm_analysis(video_path)

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Transcript: {len(transcript)} segments")
    print(f"VLM: {'✅ Success' if vlm else '❌ Failed'}")


if __name__ == "__main__":
    asyncio.run(main())

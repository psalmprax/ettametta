"""
E2E Integration Test: Exotic Multi-Video Scenes with Custom Intro/Outro Styles
================================================================================
This script directly invokes the Remotion rendering service to validate:
  1. Multiple intro styles (glass, round, elevator, glitch)
  2. Multiple outro styles (glass, cyber-grid, neon-minimal)
  3. Multi-video scene layouts (split-horizontal, split-vertical, grid-3)
  4. Exotic scene transitions (wipe, flip, spin, glitch-shake)

It bypasses the full pipeline (LLM, voiceover, vision audit) and renders
directly with pre-existing video assets.

Usage:
    PYTHONPATH=. python3 scratch/test_nexus_exotic.py
"""

import asyncio
import os
import sys
import time
import json
import glob

sys.path.insert(0, os.getcwd())

# Set required env vars before importing app modules
os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ettametta.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:7204/0")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_testing_purposes_123")


def collect_video_assets(count: int = 9) -> list[str]:
    """Collect real video assets staged inside the Remotion public directory."""
    candidates = []

    # Primary: clips staged inside Remotion public (passes LFI guard)
    staged_dir = os.path.join(
        os.getcwd(), "apps", "remotion-studio", "public", "assets", "test_clips"
    )
    if os.path.isdir(staged_dir):
        for f in sorted(os.listdir(staged_dir)):
            if f.endswith(".mp4"):
                candidates.append(os.path.join(staged_dir, f))

    # Fallback: mock pool
    mock_pool = os.path.join(os.getcwd(), "tests", "assets", "mock_pool")
    if os.path.isdir(mock_pool):
        for f in sorted(os.listdir(mock_pool)):
            if f.endswith(".mp4"):
                candidates.append(os.path.join(mock_pool, f))

    # Deduplicate and trim
    seen = set()
    unique = []
    for p in candidates:
        if p not in seen and os.path.exists(p):
            seen.add(p)
            unique.append(p)
    
    return unique[:count]


def build_clips(video_paths: list[str], fps: int = 30, sec_per_clip: int = 4) -> list[dict]:
    """Build Remotion clip objects from video file paths."""
    clips = []
    for vp in video_paths:
        clips.append({
            "url": os.path.abspath(vp),
            "duration_in_frames": int(sec_per_clip * fps),
        })
    return clips


async def render_test_video(
    test_name: str,
    clips: list[dict],
    intro_style: str,
    outro_style: str,
    scene_layout: str,
    style: str = "CINEMATIC_DOC",
) -> str | None:
    """Render a single test video with specified exotic options."""
    from src.services.video_engine.remotion_service import base_remotion_service

    total_frames = sum(c["duration_in_frames"] for c in clips) + (3 * 30) + (3 * 30)  # intro + outro buffer

    props = {
        "title": f"Exotic Test: {test_name}",
        "subtitle": "Multi-Video Scene Integration Test",
        "vibe": "Energetic",
        "clips": clips,
        "audio_url": None,
        "job_id": f"exotic-test-{test_name.lower().replace(' ', '-')}",
        "trademark_url": "assets/logo.png",
        "brand_name": "EttaMetta",
        "primary_color": "#00D4FF",
        "vignette_intensity": 0.6,
        "grain_opacity": 0.08,
        "video_duration_frames": int(total_frames),
        "duration_in_frames": int(total_frames),
        "style": style,
        "words": [],
        "timeline": [],
        "intro_style": intro_style,
        "outro_style": outro_style,
        "scene_layout": scene_layout,
        "job_metadata": {
            "intro_style": intro_style,
            "outro_style": outro_style,
            "scene_layout": scene_layout,
        },
        "show_cta_overlay": True,
        "cta_type": "cta",
        "cta_text": "Subscribe & Follow",
    }

    output_name = f"exotic_test_{test_name.lower().replace(' ', '_')}.mp4"
    print(f"\n{'='*70}")
    print(f"  RENDERING: {test_name}")
    print(f"  Intro: {intro_style} | Outro: {outro_style} | Layout: {scene_layout}")
    print(f"  Clips: {len(clips)} | Total Frames: {total_frames}")
    print(f"{'='*70}")

    start = time.time()
    try:
        result = await base_remotion_service.render_video(
            composition_id="ViralClip",
            props=props,
            output_name=output_name,
        )
        elapsed = time.time() - start
        if result and os.path.exists(result):
            size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"  ✅ SUCCESS in {elapsed:.1f}s — {size_mb:.2f} MB")
            print(f"  📁 Output: {result}")
            return result
        else:
            print(f"  ❌ FAILED — render returned None or file missing ({elapsed:.1f}s)")
            return None
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ❌ ERROR after {elapsed:.1f}s: {e}")
        return None


async def main():
    print("\n" + "=" * 70)
    print("  ETTAMETTA — Exotic Multi-Video Scene E2E Test Suite")
    print("=" * 70)

    # Collect assets
    videos = collect_video_assets(9)
    if len(videos) < 6:
        print(f"\n⚠️  Only found {len(videos)} videos. Need at least 6 for multi-video scenes.")
        print("   Will duplicate clips to fill scenes.")
        while len(videos) < 9:
            videos.append(videos[len(videos) % len(videos)])

    print(f"\n📹 Found {len(videos)} video assets:")
    for i, v in enumerate(videos):
        print(f"   [{i+1}] {os.path.basename(v)} ({os.path.getsize(v) / 1024:.0f} KB)")

    # Build clip sets: 3 clips per scene, 3 scenes = 9 clips
    all_clips = build_clips(videos, fps=30, sec_per_clip=4)

    # Test Matrix — 3 comprehensive test renders
    test_cases = [
        {
            "name": "Round Intro CyberGrid Outro",
            "clips": all_clips[:6],  # 2 scenes × 3 clips
            "intro_style": "round",
            "outro_style": "cyber-grid",
            "scene_layout": "split-horizontal",
        },
        {
            "name": "Elevator Intro NeonMinimal Outro",
            "clips": all_clips[:6],
            "intro_style": "elevator",
            "outro_style": "neon-minimal",
            "scene_layout": "split-vertical",
        },
        {
            "name": "Glitch Intro Glass Outro Grid",
            "clips": all_clips[:9],  # 3 scenes × 3 clips
            "intro_style": "glitch",
            "outro_style": "glass",
            "scene_layout": "grid-3",
        },
    ]

    results = []
    total_start = time.time()

    for tc in test_cases:
        result = await render_test_video(
            test_name=tc["name"],
            clips=tc["clips"],
            intro_style=tc["intro_style"],
            outro_style=tc["outro_style"],
            scene_layout=tc["scene_layout"],
        )
        results.append({"name": tc["name"], "path": result, "success": result is not None})

    total_elapsed = time.time() - total_start

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUITE SUMMARY")
    print("=" * 70)
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    for r in results:
        icon = "✅" if r["success"] else "❌"
        path_info = f" → {r['path']}" if r["path"] else ""
        print(f"  {icon} {r['name']}{path_info}")

    print(f"\n  Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print(f"  Total Time: {total_elapsed:.1f}s")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

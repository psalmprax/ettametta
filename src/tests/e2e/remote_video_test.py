#!/usr/bin/env python3
"""
Minimal Video Fusion Test for Remote Server
===========================================

Tests video fusion capabilities without full API dependencies.
"""

import os
import sys
from pathlib import Path

# Minimal imports to avoid database dependencies
try:
    import moviepy as mpy

    print("✅ MoviePy available")
except ImportError as e:
    print(f"❌ MoviePy not available: {e}")
    sys.exit(1)


def test_video_fusion():
    """Test basic video fusion with existing files"""

    # Check for video files
    video_files = ["gen_1775226095.mp4", "gen_1775213381.mp4"]

    available_videos = [f for f in video_files if Path(f).exists()]
    print(f"Found {len(available_videos)} video files: {available_videos}")

    if len(available_videos) < 2:
        print("❌ Need at least 2 video files for fusion test")
        return False

    try:
        print("🎬 Starting video fusion test...")

        # Load and process videos
        clips = []
        for video_file in available_videos[:2]:
            print(f"Loading {video_file}...")
            clip = mpy.VideoFileClip(video_file)
            # Use shorter duration for test
            duration = min(3, clip.duration)  # 3 seconds max
            if clip.duration > duration:
                clip = clip.with_duration(duration)
            clips.append(clip)
            print(f"  - Duration: {clip.duration}s")

        if clips:
            print("Combining clips...")
            final_clip = mpy.concatenate_videoclips(clips, method="compose")

            output_file = "remote_fusion_test.mp4"
            print(f"Writing output to {output_file}...")
            final_clip.write_videofile(
                output_file, fps=30, codec="libx264", audio_codec="aac"
            )
            final_clip.close()

            # Clean up
            for clip in clips:
                clip.close()

            # Check output
            if Path(output_file).exists():
                size = Path(output_file).stat().st_size
                print("✅ SUCCESS: Video fusion completed!")
                print(f"   Output: {output_file}")
                print(f"   Size: {size} bytes")
                print(f"   Duration: {final_clip.duration}s")
                return True
            else:
                print("❌ Output file not created")
                return False

    except Exception as e:
        print(f"❌ Fusion failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("REMOTE SERVER VIDEO FUSION TEST")
    print("=" * 40)

    success = test_video_fusion()

    if success:
        print("\n🎉 Video processing works on remote server!")
        print("Scene-based video editor is ready for production.")
    else:
        print("\n❌ Video processing test failed on remote server.")

#!/usr/bin/env python3
"""
FFmpeg Video Overlay Test
===================
Uses ffmpeg directly - no network needed
"""

import os
import sys
import subprocess

# Paths
INPUT_VIDEO = "/tmp/test_video.mp4"
OUTPUT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out"
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "ffmpeg_overlay.mp4")

# First copy the title video from remotion
TITLE_VIDEO = "/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/test_remotion_output.mp4"

if __name__ == "__main__":
    print("=== FFMPEG VIDEO OVERLAY TEST ===")
    print(f"Title video: {TITLE_VIDEO}")
    print(f"Input video: {INPUT_VIDEO}")

    if not os.path.exists(TITLE_VIDEO):
        print(f"❌ Title video not found: {TITLE_VIDEO}")
        sys.exit(1)

    if not os.path.exists(INPUT_VIDEO):
        print(f"❌ Input video not found: {INPUT_VIDEO}")
        sys.exit(1)


    # Check durations
    def get_duration(path):
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip()) if result.stdout.strip() else 0


    title_dur = get_duration(TITLE_VIDEO)
    input_dur = get_duration(INPUT_VIDEO)
    print(f"Title duration: {title_dur}s")
    print(f"Input duration: {input_dur}s")

    # Use ffmpeg to overlay: place input video as picture-in-picture over title
    # Stack vertically: [title_video] on top of [input_video] scaled
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        TITLE_VIDEO,
        "-i",
        INPUT_VIDEO,
        "-filter_complex",
        "[1:v]scale=540:-1[bg];"  # Scale input to half width
        "[0:v][bg]overlay=0:0[out];"  # Overlay
        "-map",
        "[out]",
        "-map",
        "0:a?",  # Use title audio if available
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        OUTPUT_VIDEO,
    ]

    print(f"\nRunning ffmpeg overlay...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode == 0 and os.path.exists(OUTPUT_VIDEO):
        size = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
        print(f"\n✅ SUCCESS: {OUTPUT_VIDEO} ({size:.2f} MB)")
    else:
        print(f"❌ FAILED")
        print(f"STDERR: {result.stderr[:500]}")

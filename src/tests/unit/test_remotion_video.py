#!/usr/bin/env python3
"""
Test Remotion with Video Overlay via HTTP
=========================================
"""

import os
import sys
import subprocess
import json

PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/viral_forge"
sys.path.insert(0, PROJECT_DIR)
os.environ["DEBUG"] = "true"

STUDIO_PATH = "/home/psalmprax/ALL_PROJECTS/viral_forge/apps/remotion-studio"
OUTPUT_DIR = os.path.join(STUDIO_PATH, "out")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_video_overlay():
    """Test remotion with video via HTTP URL"""

    # Use HTTP URL to serve video
    video_url = "http://172.16.1.37:3001/test_video.mp4"

    print("=== REMOTION VIDEO OVERLAY TEST ===")
    print(f"Video URL: {video_url}")

    # Test ViralClip with videoUrl via HTTP
    props = {
        "title": "AI Tools That Will Change Everything",
        "subtitle": "2026 Viral Trends",
        "videoUrl": video_url,
    }
    composition_id = "ViralClip"

    props_path = "/tmp/remotion_props.json"
    with open(props_path, "w") as f:
        json.dump(props, f)

    output_path = os.path.join(OUTPUT_DIR, "test_video_overlay.mp4")

    print(f"\nRendering {composition_id} with video overlay...")
    cmd = [
        "npx",
        "remotion",
        "render",
        "src/index.ts",
        composition_id,
        output_path,
        "--props",
        props_path,
        "--concurrency",
        "2",
    ]

    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd, cwd=STUDIO_PATH, capture_output=True, text=True, timeout=180
    )

    print(f"\nReturn code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout[:1200]}")
    if result.stderr:
        stderr_lines = result.stderr.split("\n")[:10]
        print(f"STDERR:\n{chr(10).join(stderr_lines)}")

    if result.returncode == 0 and os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024 / 1024
        print(f"\n✅ SUCCESS: {output_path} ({size:.2f} MB)")
        return output_path
    else:
        print(f"\n❌ FAILED")
        return None


if __name__ == "__main__":
    test_video_overlay()

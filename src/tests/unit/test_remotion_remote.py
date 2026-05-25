#!/usr/bin/env python3
"""
Test Remotion Service on Remote
=============================
"""

import os
import sys
import subprocess
import json

PROJECT_DIR = "/app" if os.path.exists("/app") else "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

os.environ["DEBUG"] = "true"

STUDIO_PATH = os.path.join(PROJECT_DIR, "apps/remotion-studio")
OUTPUT_DIR = os.path.join(STUDIO_PATH, "out")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_remotion():
    """Test remotion rendering"""

    video_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_video.mp4"

    if not os.path.exists(video_path):
        print(f"Input video not found: {video_path}")

    print("=== REMOTION TEST ===")
    print(f"Using: {video_path}")

    # Test CinematicMinimal composition (no video needed, just titles)
    props = {
        "title": "AI Productivity Tools",
        "subtitle": "Viral Video Test",
    }
    composition_id = "CinematicMinimal"

    props_path = "/tmp/remotion_props.json"
    with open(props_path, "w") as f:
        json.dump(props, f)

    print(f"Props: {props_path}")

    output_path = os.path.join(OUTPUT_DIR, "test_remotion_output.mp4")

    print(f"\nRendering {composition_id} with Remotion...")
    cmd = [
        "npx",
        "remotion",
        "render",
        "src/index.ts",
        composition_id,
        output_path,
        "--props",
        props_path,
        "--quality",
        "1",
        "--frames",
        "0-100",
    ]

    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd, cwd=STUDIO_PATH, timeout=600
    )
    print(f"\nReturn code: {result.returncode}")

    if result.returncode == 0 and os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024 / 1024
        print(f"\n✅ SUCCESS: {output_path} ({size:.2f} MB)")
        return output_path
    else:
        print("\n❌ FAILED")
        return None


if __name__ == "__main__":
    test_remotion()

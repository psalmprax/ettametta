#!/usr/bin/env python3
"""
Simple Real Video Creator - Direct Fusion
========================================

Creates real video by directly concatenating downloaded YouTube videos.
"""

import asyncio
from pathlib import Path


async def create_simple_real_video():
    """Create a real video by directly fusing downloaded videos"""

    print("🎬 SIMPLE REAL VIDEO CREATOR")
    print("=" * 40)

    # Check for downloaded videos
    download_dir = Path("downloads/video_sources")
    if not download_dir.exists():
        print("❌ No downloaded videos found")
        return False

    video_files = list(download_dir.glob("*.mp4"))
    if not video_files:
        print("❌ No MP4 files found in downloads")
        return False

    print(f"Found {len(video_files)} downloaded videos:")
    for vf in video_files:
        size = vf.stat().st_size
        print(f"  - {vf.name}: {size} bytes")

    # Create output directory
    output_dir = Path("outputs/real_videos")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = (
        output_dir / f"simple_fusion_{int(asyncio.get_event_loop().time())}.mp4"
    )

    # Create concat file
    concat_file = output_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for video_file in video_files[:3]:  # Use up to 3 videos
            abs_path = video_file.resolve()
            f.write(f"file '{abs_path}'\n")

    print(f"Created concat file: {concat_file}")

    # Run FFmpeg concatenation
    cmd = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",  # Copy streams without re-encoding (fastest)
        "-y",
        str(output_file),
    ]

    print("Running FFmpeg concatenation...")
    print(f"Command: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            if output_file.exists():
                file_size = output_file.stat().st_size
                print("✅ SUCCESS: Real video created!")
                print(f"   File: {output_file}")
                print(f"   Size: {file_size} bytes")
                print("\n🎉 VIDEO READY FOR REVIEW!")
                return True
            else:
                print("❌ Output file not created")
        else:
            error = stderr.decode()[-300:]
            print(f"❌ FFmpeg failed: {error}")

    except Exception as e:
        print(f"❌ Error: {e}")

    return False


if __name__ == "__main__":
    asyncio.run(create_simple_real_video())

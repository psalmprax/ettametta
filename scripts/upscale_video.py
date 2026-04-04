#!/usr/bin/env python3
"""
Standalone Video Upscaler - Run on GPU Server
==============================================
Uses Real-ESRGAN for upscaling and GFPGAN for face enhancement
"""

import os
import sys
import time
import argparse
import subprocess


def load_enhancers(upscale_factor=4):
    """Load GFPGAN and Real-ESRGAN models"""
    print(f"📥 Loading enhancers (upscale_factor={upscale_factor})...", flush=True)

    try:
        from gfpgan import GFPGANer

        face_enhancer = GFPGANer(
            model_path="https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth",
            upscale=1,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=None,
        )
        print("✅ GFPGAN loaded")
    except Exception as e:
        print(f"⚠️ GFPGAN failed: {e}")
        face_enhancer = None

    try:
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdb_arch import RRDBNet

        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        upscaler_model = RealESRGANer(
            scale=4,
            model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            model=model,
            tile=400,
            tile_pad=10,
            pre_pad=0,
            half=True,
        )
        print("✅ Real-ESRGAN loaded")
    except Exception as e:
        print(f"⚠️ Real-ESRGAN failed: {e}")
        upscaler_model = None

    return face_enhancer, upscaler_model


def upscale_video(input_path, output_path, upscale_factor=4, enhance_face=True):
    """Upscale and enhance a video"""
    import cv2
    import numpy as np

    face_enhancer, upscaler_model = load_enhancers(upscale_factor)

    print(f"🎬 Processing: {input_path}", flush=True)

    # Read video
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"   Frames: {total_frames}, FPS: {fps}", flush=True)

    # Get output writer
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * upscale_factor
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * upscale_factor

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Upscale frame
        if upscaler_model:
            print(f"   Frame {frame_idx + 1}/{total_frames} - Upscaling...", flush=True)
            try:
                _, upscaled = upscaler_model.process(frame, scale=upscale_factor)
                frame = upscaled
            except Exception as e:
                print(f"   Upscale error: {e}")

        # Face enhancement
        if enhance_face and face_enhancer:
            try:
                _, enhanced = face_enhancer.process(frame, 1)
                frame = enhanced
            except Exception as e:
                print(f"   Face enhance error: {e}")

        # Write frame
        out.write(frame)
        frame_idx += 1

        if frame_idx % 10 == 0:
            print(f"   Progress: {frame_idx}/{total_frames}", flush=True)

    cap.release()
    out.release()

    print(f"✅ Upscaled video saved: {output_path}", flush=True)
    return output_path


def upscale_with_ffmpeg(input_path, output_path, scale=4):
    """Simpler upscale using ffmpeg with super resolution filter"""
    print(f"🎬 Upscaling with FFmpeg: {input_path}", flush=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vf",
        f"scale={scale}:flags=lanczos,unsharp=5:5:0.8:3:3:0.4",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-c:a",
        "copy",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        return None

    print(f"✅ Upscaled: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Upscale video with AI enhancement")
    parser.add_argument("input", help="Input video file")
    parser.add_argument("-o", "--output", help="Output video file")
    parser.add_argument(
        "-s", "--scale", type=int, default=4, help="Upscale factor (2 or 4)"
    )
    parser.add_argument(
        "--no-face", action="store_true", help="Disable face enhancement"
    )
    parser.add_argument(
        "--ffmpeg-only", action="store_true", help="Use only FFmpeg upscale (no AI)"
    )

    args = parser.parse_args()

    if not args.output:
        name, ext = os.path.splitext(args.input)
        args.output = f"{name}_upscaled{ext}"

    if args.ffmpeg_only:
        upscale_with_ffmpeg(args.input, args.output, args.scale)
    else:
        upscale_video(args.input, args.output, args.scale, not args.no_face)


if __name__ == "__main__":
    main()

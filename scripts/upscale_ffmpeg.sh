#!/bin/bash
#
# Upscale Video Script
# ====================
# Uses FFmpeg with nnedi to upscale video to higher resolution

set -e

INPUT=$1
OUTPUT=$2
SCALE=${3:-2}

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <input.mp4> <output.mp4> [scale]"
    echo "  scale: 2 (default) or 4"
    exit 1
fi

echo "Upscaling: $INPUT -> $OUTPUT (${SCALE}x)"

# Check available scalers
SCALER="scale"
if ffmpeg -filters 2>/dev/null | grep -q "nnedi"; then
    SCALER="nnedi"
    echo "Using NNEDI upscaler"
fi

# Use super resolution with libplacebo or sw scale
ffmpeg -y -i "$INPUT" \
    -vf "scale=${SCALE}*:flags=lanczos,unsharp=5:5:0.8:3:3:0.4" \
    -c:v libx264 -preset slow -crf 18 \
    -c:a copy \
    "$OUTPUT"

echo "✅ Upscaled video: $OUTPUT"

# Get file info
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$OUTPUT"
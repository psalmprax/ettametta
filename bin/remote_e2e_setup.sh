#!/bin/bash
# Remote E2E Setup Script
# Run this on the remote server to install dependencies

set -e

echo "=== Installing Python dependencies for E2E steps 3 & 4 ==="

# Install faster-whisper for step 3 (transcription - CPU based)
echo "[1/4] Installing faster-whisper..."
pip3 install faster-whisper --quiet || echo "  Note: May need more RAM, trying alternative..."

# Install google-generativeai for step 4 (VLM - uses cloud API, not local GPU)
echo "[2/4] Installing google-generativeai..."
pip3 install google-generativeai --quiet || echo "  Note: API key needed"

# Install other dependencies
echo "[3/4] Installing utilities..."
pip3 install httpx aiohttp --quiet

echo "[4/4] Checking installations..."
pip3 list | grep -iE "faster-whisper|google-generative|httpx|aiohttp" || echo "Check installed packages manually"

echo "=== Setup complete ==="
echo "Now copy the video and run: python3 remote_e2e_test.py <video_path>"
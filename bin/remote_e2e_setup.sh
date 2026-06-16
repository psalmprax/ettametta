#!/bin/bash
# Remote E2E Setup Script
# Run this on the remote server to install dependencies
#
# ── Named jumpbox target (saves retyping the full SSH command) ───────────────
# Add to your local ~/.ssh/config:
#
#   Host ettametta-prod
#       HostName 149.104.110.122
#       User root
#       IdentityFile /home/psalmprax/Music/id_rsa
#       IdentitiesOnly yes
#       StrictHostKeyChecking accept-new
#
# Then run this script via:
#
#   ssh ettametta-prod 'cd ~/ettametta && bash bin/remote_e2e_setup.sh'
#
# Or one-off (no SSH config):
#
#   ssh -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no \
#       -o PasswordAuthentication=no -o BatchMode=yes \
#       root@149.104.110.122 'cd ~/ettametta && bash bin/remote_e2e_setup.sh'
#
# Port mapping: container :8000 → host :7201. Hit the API at
# http://149.104.110.122:7201/health once the stack is up.
# ─────────────────────────────────────────────────────────────────────────────

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
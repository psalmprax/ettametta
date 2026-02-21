#!/bin/bash
# Setup script for ettametta OS AI Requirements

echo "[ettametta] Installing system-level OS AI dependencies..."
# For Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y ffmpeg

echo "[ettametta] Installing Python OS AI libraries..."
pip install faster-whisper httpx piper-tts

echo "[ettametta] Checking for Ollama (Llama-3)..."
if command -v ollama &> /dev/null
then
    echo "[ettametta] Ollama found. Pre-pulling Llama-3..."
    ollama pull llama3
else
    echo "[ettametta] WARNING: Ollama not found. Please install it to use Llama-3 locally (https://ollama.com)."
fi

echo "[ettametta] OS AI Setup Complete (Zero API Costs Mode enabled)."

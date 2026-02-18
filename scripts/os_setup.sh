#!/bin/bash
# Setup script for ViralForge OS AI Requirements

echo "[ViralForge] Installing system-level OS AI dependencies..."
# For Linux (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y ffmpeg

echo "[ViralForge] Installing Python OS AI libraries..."
pip install faster-whisper httpx piper-tts

echo "[ViralForge] Checking for Ollama (Llama-3)..."
if command -v ollama &> /dev/null
then
    echo "[ViralForge] Ollama found. Pre-pulling Llama-3..."
    ollama pull llama3
else
    echo "[ViralForge] WARNING: Ollama not found. Please install it to use Llama-3 locally (https://ollama.com)."
fi

echo "[ViralForge] OS AI Setup Complete (Zero API Costs Mode enabled)."

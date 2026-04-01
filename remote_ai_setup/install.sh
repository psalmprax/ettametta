#!/bin/bash
# ettametta Universal Remote AI Installer
# Supports: Ubuntu, RHEL, macOS
# Hardware: NVIDIA, AMD, Apple, Intel, CPU

set -e

echo "🚀 Starting Universal Remote AI Setup..."

# 1. OS Detection and System Dependencies
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                echo "📦 [System] Detected Ubuntu/Debian. Ensuring build chain..."
                sudo apt-get update
                sudo apt-get install -y build-essential cmake git python3-dev \
                    ffmpeg libx265-dev libnuma-dev libsm6 libxext6 libgl1 libglib2.0-0 \
                    libsndfile1 libfftw3-dev sox
                ;;
            fedora|rhel|centos)
                echo "📦 [System] Detected RHEL/Fedora. Ensuring build chain..."
                sudo dnf groupinstall -y "Development Tools"
                sudo dnf install -y cmake python3-devel ffmpeg ffmpeg-devel libnuma \
                    mesa-libGL glib2 sox
                ;;
        esac
    fi
fi

# 2. Python Environment Setup
if [ ! -d "venv" ]; then
    echo "🐍 [Python] Creating production virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip "setuptools<82" wheel cython numpy

# 3. Hardware-Specific PyTorch Installation
echo "🔍 [Hardware] Detecting optimal compute backend..."
TORCH_CMD=$(python3 check_hardware.py --pip)
echo "⚡ [Hardware] Installing: $TORCH_CMD"
eval $TORCH_CMD

# 4. Manual Stable Installations (Problematic Packages)
echo "🛠️  [Build] Installing stable fairseq from source..."
if [ ! -d "fairseq" ]; then
    git clone https://github.com/facebookresearch/fairseq.git
    cd fairseq && pip install -e . && cd ..
fi

echo "🛠️  [Build] Installing stable basicsr..."
pip install basicsr --no-build-isolation

# 5. Global Dependencies
echo "📚 [Main] Installing remaining requirements..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pip install -r "$SCRIPT_DIR/requirements.txt"

# 6. Final Validation
echo "🎨 [Summary] Hardware Activation Report:"
python3 check_hardware.py
echo "✅ Viral Forge AI Engine is ready for production."

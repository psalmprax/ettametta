#!/bin/bash
# ettametta Universal Remote AI Installer
# Supports: Ubuntu, RHEL, macOS
# Hardware: NVIDIA, AMD, Apple, Intel, CPU

set -e

echo "🚀 Starting Universal Remote AI Setup..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 0. Smart Storage Discovery (High-Disk Allocation)
echo "🔍 [Storage] Discovering optimal high-capacity writable disk..."
BEST_DISK=$(python3 storage_helper.py 2>/dev/null || echo ".")
echo "💾 [Storage] Allocated: $BEST_DISK"

# Ensure required directories exist and are symlinked if needed
# We want models in .cache and outputs in ai_content
mkdir -p "$BEST_DISK/.cache/huggingface"
mkdir -p "$BEST_DISK/ai_content"

# Set persistent HF_HOME for this session
export HF_HOME="$BEST_DISK/.cache/huggingface"
export AI_CONTENT_DIR="$BEST_DISK/ai_content"

# 1. OS Detection and System Dependencies
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                echo "📦 [System] Detected Ubuntu/Debian. Ensuring build chain..."
                apt-get update
                # System updates & PATH hardening
                export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                echo "🌐 [System] Path: $PATH"

                apt-get update && apt-get install -y build-essential cmake git python3-dev python3-venv ffmpeg libx265-dev libnuma-dev libsm6 libxext6 libgl1 libglib2.0-0 libsndfile1 libfftw3-dev sox rsync
                ;;
            fedora|rhel|centos)
                echo "📦 [System] Detected RHEL/Fedora. Ensuring build chain..."
                dnf groupinstall -y "Development Tools"
                dnf install -y cmake python3-devel ffmpeg ffmpeg-devel libnuma \
                    mesa-libGL glib2 sox
                ;;
        esac
    fi
fi

# 2. Base Environment (Always fresh for provision)
echo "📦 [System] Standardizing virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️ [System] Stale environment detected. Purging for clean provision..."
    rm -rf venv
fi

echo "📦 [System] Creating isolated virtual environment..."
python3 -W ignore -m venv --clear venv || echo "⚠️ [System] Virtual environment creation failed. Attempting global install fallback."
rm -f .install_complete # Reset status

# Define PIP_CMD based on absolute environment path
PIP_BIN="$SCRIPT_DIR/venv/bin/pip"
PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"

if [ -x "$PIP_BIN" ] && "$PIP_BIN" --version > /dev/null 2>&1; then
    PIP_CMD="$PIP_BIN"
else
    # Fallback for Global Install
    PIP_CMD="python3 -m pip"
    PIP_FLAGS="--break-system-packages"
fi

$PIP_CMD install $PIP_FLAGS --no-cache-dir --upgrade pip "setuptools<82" wheel cython numpy

# 3. Hardware-Specific PyTorch Installation
echo "🔍 [Hardware] Detecting optimal compute backend..."
RAW_TORCH_CMD=$("$PYTHON_BIN" "$SCRIPT_DIR/check_hardware.py" --pip || python3 "$SCRIPT_DIR/check_hardware.py" --pip)
if [[ $RAW_TORCH_CMD == pip* ]]; then
    # Inject flags into the command
    TORCH_CMD="${RAW_TORCH_CMD/pip install/ $PIP_CMD install $PIP_FLAGS --no-cache-dir }"
else
    TORCH_CMD="$RAW_TORCH_CMD"
fi

echo "⚡ [Hardware] Installing: $TORCH_CMD"
eval "$TORCH_CMD"

# 4. Manual Stable Installations (Problematic Packages)
echo "🛠️  [Build] Installing stable fairseq from source..."
if [ ! -d "fairseq" ]; then
    git clone --depth 1 https://github.com/facebookresearch/fairseq.git
    cd fairseq && "$PIP_CMD" install $PIP_FLAGS --no-cache-dir -e . && cd ..
fi

echo "🛠️  [Build] Installing stable basicsr..."
# Use --no-deps to skip complex resolution loops for aux libraries
"$PIP_CMD" install $PIP_FLAGS basicsr --no-cache-dir --no-build-isolation --no-deps

# 5. Global Dependencies
echo "📚 [Main] Installing remaining requirements..."
"$PIP_CMD" install $PIP_FLAGS --no-cache-dir -r "$SCRIPT_DIR/requirements.txt"

# 6. Final Validation
echo "🎨 [Summary]# Global variables
LOG_FILE="/var/log/viral_forge_setup.log"
PYTHON_VERSION="3.12"
NODE_VERSION="20"

# --- REMOTION AND NODE.JS SETUP ---
echo "⚙️ Installing Node.js ${NODE_VERSION} for Remotion and Programmatic Tools..."
curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g npx

# Install OpenClaw agent skills for remote AI gaps
echo "🧠 Installing OpenClaw agent skills..."
mkdir -p "$BEST_DISK/.skills"
export SKILLS_DIR="$BEST_DISK/.skills"

# Memory persistence (addresses long-term memory gap)
npx skills add anthropics/skills/memory -g -y || echo "⚠️ Memory skill install failed, continuing..."

# Notification routing (Slack/Discord/email alerting)
npx skills add openclaw/skills/notification-routing -g -y || echo "⚠️ Notification skill install failed, continuing..."

# Workflow automation (n8n-style chaining)
npx skills add composiohq/composio/workflow-automation -g -y || echo "⚠️ Workflow automation skill install failed, continuing..."

# Self-healing watchdog (AlphaClaw pattern)
npx skills add openclaw/skills/self-healing-watchdog -g -y || echo "⚠️ Self-healing skill install failed, continuing..."

# Install Chromium for Remotion (Headless rendering)
echo "🌐 Installing Chromium for Headless Video Rendering..."
sudo apt-get install -y chromium-browser libgbm-dev
$SCRIPT_DIR/check_hardware.py" || python3 "$SCRIPT_DIR/check_hardware.py"
echo "✅ Viral Forge AI Engine is ready for production."

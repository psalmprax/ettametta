#!/bin/bash
# Optimized GPU Server Deployment Script
# ettametta "Real-First" Production Engine

set -e

# --- CONFIGURATION (Zero-Hardcode Agnostic Config) ---
REMOTE_HOST=${1}
REMOTE_PORT=${2:-22}
REMOTE_USER=${3:-"root"}
SSH_KEY=${SSH_KEY:-"/home/psalmprax/Music/id_rsa"}
REMOTE_DIR="/workspace/ettametta_ai"
LOCAL_DIR="$(pwd)/remote_ai_setup"


# Allow override via environment variables
REMOTE_HOST=${1:-$REMOTE_HOST}
REMOTE_PORT=${2:-$REMOTE_PORT}

echo "🚀 [Deploy] Preparing migration to GPU Server: $REMOTE_HOST (Port: $REMOTE_PORT)"

# 1. Test SSH Connection & Ensure rsync is installed remotely
echo "📡 [Deploy] Testing connectivity and ensuring dependencies..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    mkdir -p $REMOTE_DIR && 
    if ! command -v rsync >/dev/null 2>&1; then 
        echo '📦 Installing rsync on remote host...'; 
        apt-get update && apt-get install -y rsync; 
    fi &&
    uptime
"

# 2. Sync Files (Using rsync for efficiency)
echo "📤 [Deploy] Syncing AI Engine components..."
rsync -avz --delete -e "ssh -i $SSH_KEY -p $REMOTE_PORT -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15" \
    "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# 3. Remote Initialization & Hardware Check
echo "🛠️ [Deploy] Initializing remote environment..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    cd $REMOTE_DIR && 
    chmod +x install.sh && 
    ./install.sh --auto-gpu
"

# 4. Start Engine Process
echo "🔥 [Deploy] Starting AI Engine processes..."
# Use a unified, hardened command to minimize SSH session-reuse context errors
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    # Atomic Cleanup: Avoid killing the current SSH session's bash
    pgrep -f main.py | grep -v \$\$ | xargs kill -9 2>/dev/null || true
    
    cd $REMOTE_DIR && 
    export AI_CLUSTER_SECRET=\"$AI_CLUSTER_SECRET\" &&
    export AI_GATEWAY_URL=\"${AI_GATEWAY_URL:-http://localhost:8133}\" &&
    export AI_NODE_PUBLIC_URL=\"http://$REMOTE_HOST:8122\" &&
    
    # Precise Python Discovery: Prioritize the local venv over system Ghost-Pythons
    PYTHON_BIN=\"./venv/bin/python3\"
    if [ ! -x \"\$PYTHON_BIN\" ]; then PYTHON_BIN=\"/opt/miniforge3/bin/python3\"; fi
    if [ ! -x \"\$PYTHON_BIN\" ]; then PYTHON_BIN=\"python3\"; fi
    
    echo \"📡 Launching via: \$PYTHON_BIN\"
    # Explicitly use nohup with double-forking and full descriptor isolation
    # We add a 2s delay and 'exit 0' to ensure the SSH session closes cleanly after the fork
    (nohup \$PYTHON_BIN -u main.py > server_out.log 2>&1 &) && sleep 2 && echo \"✅ Launch initiated.\" && exit 0
" || echo "⚠️ [Deploy] Session closed (255), verifying process persistence..."

echo "⏳ [Deploy] Waiting for model warm-up (Hunyuan/LTX)..."
sleep 20

# 5. Final Health Verification
echo "🏥 [Deploy] Verifying Health Endpoint..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    curl -s http://localhost:8122/health || curl -s http://localhost:8000/health
"

echo "✅ [Deploy] GPU Migration Complete!"

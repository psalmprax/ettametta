#!/bin/bash
# Optimized GPU Server Deployment Script
# Viral Forge "Real-First" Production Engine

set -e

# --- CONFIGURATION (Defaulting to the RTX 8000 Node) ---
REMOTE_HOST="220.135.0.171"
REMOTE_PORT="45672"
REMOTE_USER="root"
SSH_KEY=${SSH_KEY:-"/home/psalmprax/Music/id_rsa"}
REMOTE_DIR="/workspace/viral_forge_ai"
LOCAL_DIR="$(pwd)/remote_ai_setup"

# Allow override via environment variables
REMOTE_HOST=${1:-$REMOTE_HOST}
REMOTE_PORT=${2:-$REMOTE_PORT}

echo "🚀 [Deploy] Preparing migration to GPU Server: $REMOTE_HOST (Port: $REMOTE_PORT)"

# 1. Test SSH Connection
echo "📡 [Deploy] Testing connectivity..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR && uptime"

# 2. Sync Files (Using rsync for efficiency)
echo "📤 [Deploy] Syncing AI Engine components..."
rsync -avz -e "ssh -i $SSH_KEY -p $REMOTE_PORT -o StrictHostKeyChecking=no" \
    "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# 3. Remote Initialization & Hardware Check
echo "🛠️ [Deploy] Initializing remote environment..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    cd $REMOTE_DIR && 
    chmod +x install.sh && 
    ./install.sh --auto-gpu
"

# 4. Start Engine Process
echo "🔥 [Deploy] Starting AI Engine processes with Cluster Secret..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    cd $REMOTE_DIR && 
    export AI_CLUSTER_SECRET=\"$AI_CLUSTER_SECRET\" &&
    nohup ./venv/bin/python3 -u main.py > server_out.log 2>&1 &
"

echo "⏳ [Deploy] Waiting for model warm-up (Hunyuan/LTX)..."
sleep 20

# 5. Final Health Verification
echo "🏥 [Deploy] Verifying Health Endpoint..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "
    curl -s http://localhost:8122/health || curl -s http://localhost:8000/health
"

echo "✅ [Deploy] GPU Migration Complete!"

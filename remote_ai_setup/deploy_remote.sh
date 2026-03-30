#!/bin/bash
# Remote Server Restart & Deploy Script
# Automates syncing code and restarting the AI engine

set -e

# Configuration
REMOTE_HOST="220.135.0.171"
REMOTE_PORT="45672"
REMOTE_USER="root"
SSH_KEY="/home/psalmprax/Music/id_rsa"
REMOTE_DIR="/workspace/remote_ai_group"
LOCAL_DIR="/home/psalmprax/viral_forge/remote_ai_setup"

echo "🚀 Starting remote deployment..."

# 1. Sync code to remote
echo "📤 Syncing code to remote server..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -P "$REMOTE_PORT" \
    "$LOCAL_DIR/main.py" \
    "$LOCAL_DIR/hunyuan_inference.py" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# 2. Kill existing server processes
echo "🛑 Killing existing server processes..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o PasswordAuthentication=no -p "$REMOTE_PORT" \
    "$REMOTE_USER@$REMOTE_HOST" \
    "pids=\$(pgrep -f 'python3.*main.py'); if [ -n \"\$pids\" ]; then kill -9 \$pids; fi; fuser -k 8122/tcp || true; sleep 2"

# 3. Start new server
echo "🚀 Starting AI engine on port 8122..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o PasswordAuthentication=no -p "$REMOTE_PORT" \
    "$REMOTE_USER@$REMOTE_HOST" \
    "cd $REMOTE_DIR && nohup ./venv/bin/python3 -u main.py > server_out.log 2>&1 &"

# 4. Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 15

# 5. Check health
echo "🏥 Checking server health (Port 8122)..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o PasswordAuthentication=no -p "$REMOTE_PORT" \
    "$REMOTE_USER@$REMOTE_HOST" \
    "curl -s http://localhost:8122/health"

echo "✅ Deployment complete!"

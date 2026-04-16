#!/bin/bash
# Multi-Model AI Engine Bootstrap Script (Hardened with Correct Gateway Path)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.12/dist-packages/nvidia/cu13/lib/

# Cluster Connectivity
# Note: Engine appends '/pulse' to this URL
export AI_GATEWAY_URL="http://149.104.110.122.sslip.io:7200/ai-gateway"
export AI_NODE_PUBLIC_URL="http://175.155.64.174:19675"
export AI_CLUSTER_SECRET="2aa8f7102fc81c6ee2fe28fa60f9e6bd012034bba8c601467aee61460b9aade8"

cd /workspace/viral_forge_ai
echo "🛑 [Bootstrap] Killing old processes..."
pkill -f "python3 -u main.py" || true
sleep 2

echo "🚀 [Bootstrap] Starting Viral Forge AI Engine on Port 8080 (Mapped to 19675)..."
nohup python3 -u main.py > server_out.log 2>&1 &
PID=$!
echo $PID > engine.pid

echo "✅ [Bootstrap] Engine started with PID: $PID"
echo "💓 [Bootstrap] Should report as: $AI_NODE_PUBLIC_URL to $AI_GATEWAY_URL/pulse"
sleep 5
ps -p $PID

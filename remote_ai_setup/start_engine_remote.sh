#!/bin/bash
export HF_HOME=/workspace/.cache
cd /workspace/remote_ai_group
nohup ./venv/bin/python3 -u main.py > /workspace/remote_ai_group/server_out.log 2>&1 &
echo $! > /workspace/remote_ai_group/engine.pid
echo "Engine started with PID $(cat /workspace/remote_ai_group/engine.pid)"

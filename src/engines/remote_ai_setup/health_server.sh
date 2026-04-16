#!/bin/bash
# Simple health endpoint server for AI cluster

echo "🚀 Starting simple health server on port 8122..."

while true; do
  # Listen on port 8122 and respond to health requests
  {
    echo -e "HTTP/1.1 200 OK\r"
    echo -e "Content-Type: application/json\r"
    echo -e "\r"
    echo '{"status": "healthy", "busy": false, "current_model": "minimal", "hardware": {"gpu": "unknown", "cpu": "available", "memory": "available"}}'
  } | nc -l -p 8122 -q 1
done
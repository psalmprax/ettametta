#!/bin/bash
# ettametta Remote AI Installer
# Target: Ubuntu/Debian VPS with GPU

echo "🚀 Starting ettametta Remote AI Setup..."

# 1. System Updates
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv ffmpeg libsm6 libxext6 libgl1 libglib2.0-0 git

# 2. Python Environment
python3 -m venv venv
source venv/bin/activate

# 3. Core Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Opening Firewall (assuming ufw)
sudo ufw allow 8000/tcp
echo "✅ Firewall port 8000 opened."

echo "🎉 Installation Complete! Run 'source venv/bin/activate && python3 main.py' to start."

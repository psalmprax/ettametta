#!/bin/bash

echo "🚀 Initializing Viral Content Automation System..."

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

# Build docker containers
echo "📦 Building services..."
docker-compose build

echo "✨ Initialization complete!"
echo "Run 'docker-compose up' to start the system."

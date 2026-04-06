FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install skills CLI globally
RUN npm install -g npx

# Install Python dependencies
COPY services/openclaw/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenClaw agent skills for gaps
# Memory persistence (addresses long-term memory gap)
RUN npx skills add anthropics/skills/memory -g -y || echo "Memory skill install failed, continuing..."

# Notification routing (Slack/Discord/email alerting)
RUN npx skills add openclaw/skills/notification-routing -g -y || echo "Notification skill install failed, continuing..."

# Workflow automation (n8n-style chaining)
RUN npx skills add composiohq/composio/workflow-automation -g -y || echo "Workflow automation skill install failed, continuing..."

# Self-healing watchdog (AlphaClaw pattern)
RUN npx skills add openclaw/skills/self-healing-watchdog -g -y || echo "Self-healing skill install failed, continuing..."

# Create skills directory for persistence
RUN mkdir -p /app/.skills

# Copy openclaw code
COPY services/openclaw /app

# Copy necessary sibling services for integration
COPY services/agent_zero /app/services/agent_zero
COPY api /app/api
# Ensure __init__.py exists in services to make it a package
RUN touch /app/services/__init__.py

# Set PYTHONPATH to include /app so 'services.agent_zero' works
ENV PYTHONPATH=/app

# Expose port for health checks/webhooks
EXPOSE 3001

# Command to run the service
CMD ["python", "main.py"]

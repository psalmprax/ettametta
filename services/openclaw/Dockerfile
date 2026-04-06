FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Fix npm CVE-2024-22017 issue
ENV NPM_CONFIG_UNSAFE_PERM=true

# Install skills CLI globally
RUN npm install -g npx

# Install Python dependencies
COPY services/openclaw/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenClaw agent skills for gaps via git clone
RUN git clone https://github.com/vercel-labs/agent-skills.git /tmp/agent-skills && \
    cp -r /tmp/agent-skills/* /app/.skills/ 2>/dev/null || echo "Skill copy failed, continuing..." && \
    rm -rf /tmp/agent-skills

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

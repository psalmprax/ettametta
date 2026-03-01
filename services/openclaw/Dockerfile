FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/openclaw/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy openclaw code
COPY services/openclaw /app

# Copy necessary sibling services for integration
COPY services/agent_zero /app/services/agent_zero
# Ensure __init__.py exists in services to make it a package
RUN touch /app/services/__init__.py

# Set PYTHONPATH to include /app so 'services.agent_zero' works
ENV PYTHONPATH=/app

# Expose port for health checks/webhooks
EXPOSE 3001

# Command to run the service
CMD ["python", "main.py"]

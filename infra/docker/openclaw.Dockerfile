FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    git \
    # Playwright browser dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    libatspi2.0-0 \
    libxshmfence1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Fix npm CVE-2024-22017 issue
ENV NPM_CONFIG_UNSAFE_PERM=true

# Install skills CLI globally
RUN npm install -g npx

# Install Python dependencies
COPY src/api/requirements.txt api/requirements.txt
COPY src/services/openclaw/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r api/requirements.txt && \
    pip uninstall -y langchain langchain-community langchain-core crewai duckduckgo-search && \
    pip install --no-cache-dir --force-reinstall \
        "langchain==0.1.20" \
        "langchain-community==0.0.38" \
        "langchain-core==0.1.52" \
        "crewai==1.14.4" \
        "duckduckgo-search>=5.3.0" && \
    pip install --no-cache-dir \
        "open-interpreter==0.4.3" \
        "litellm==1.80.0" && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium || true
RUN playwright install-deps chromium || true

# Install OpenClaw agent skills for gaps via git clone
RUN git clone https://github.com/vercel-labs/agent-skills.git /tmp/agent-skills && \
    cp -r /tmp/agent-skills/* /app/.skills/ 2>/dev/null || echo "Skill copy failed, continuing..." && \
    rm -rf /tmp/agent-skills

# Create skills directory for persistence
RUN mkdir -p /app/.skills

# Copy openclaw code
COPY src /app/src
RUN touch /app/src/services/__init__.py

# Set PYTHONPATH to include /app so 'src' and 'services' works
ENV PYTHONPATH=/app:/app/src

# Expose port for health checks/webhooks
EXPOSE 3001

# Command to run the service
CMD ["python", "-m", "services.openclaw.main"]

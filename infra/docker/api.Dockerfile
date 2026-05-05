ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

WORKDIR /app

# Install System Dependencies (FFmpeg, Image processing libs, and JS runtime for yt-dlp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    nodejs \
    npm \
    tesseract-ocr \
    libtesseract-dev \
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
    libasound2 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno for yt-dlp JavaScript runtime support
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

# Install opencli-rs binary
RUN curl -fsSL https://raw.githubusercontent.com/nashsu/opencli-rs/main/scripts/install.sh | sh && \
    ln -sf /usr/local/bin/opencli-rs /usr/local/bin/opencli

ENV PYTHONPATH=/app
# Core Requirements
COPY src/api/requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --default-timeout=100 --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt && \
    pip uninstall -y langchain langchain-community langchain-core && \
    pip install --no-cache-dir --force-reinstall "langchain==0.1.20" "langchain-community==0.0.38" "langchain-core==0.1.52"

# Agentic Requirements (Hardened Suite)
COPY src/api/requirements-agents.txt ./requirements-agents.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --default-timeout=100 -r requirements-agents.txt

# Utilities
RUN pip install --no-cache-dir psutil && \
    pip install --no-cache-dir -U yt-dlp

# Install Remotion dependencies for Tier 3 Motion Graphics
COPY apps/remotion-studio /app/apps/remotion-studio
WORKDIR /app/apps/remotion-studio
RUN npm install
COPY src /app/src
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


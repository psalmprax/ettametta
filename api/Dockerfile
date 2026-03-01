ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

WORKDIR /app

# Install System Dependencies (FFmpeg, Image processing libs, and JS runtime for yt-dlp)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    nodejs \
    npm \
    tesseract-ocr \
    libtesseract-dev \
    chromium \
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
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

# Install Remotion dependencies for Tier 3 Motion Graphics
COPY apps/remotion-studio /app/apps/remotion-studio
WORKDIR /app/apps/remotion-studio
RUN npm install
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


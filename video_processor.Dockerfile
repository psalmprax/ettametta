# Video Processor Dockerfile with Multi-Stage Build
# Optimized for efficient video processing deployment

ARG BASE_IMAGE=python:3.10

# Build stage: Install all dependencies and compile native extensions
FROM ${BASE_IMAGE} as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies with caching
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Install video processing dependencies with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    moviepy \
    opencv-python \
    torch \
    torchvision \
    torchaudio \
    faster-whisper \
    pydub \
    librosa \
    soundfile \
    pillow \
    numpy \
    scipy \
    remotion \
    nodejs \
    npm

# Runtime stage: Minimal image for execution
FROM ${BASE_IMAGE}-slim as runtime

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p outputs/scene_based_videos inputs cache

# Set environment variables for video processing
ENV PYTHONPATH=/app
ENV TORCH_USE_CUDA_DSA=1
ENV CUDA_VISIBLE_DEVICES=all

# Default command
CMD ["python", "-c", "print('Video Processor Container Ready')"]
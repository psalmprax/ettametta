# Video Processor Dockerfile
# Includes all dependencies for video editing and processing

ARG BASE_IMAGE=python:3.10

FROM ${BASE_IMAGE} as base

# Install system dependencies for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    build-essential \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install video processing dependencies
RUN pip install --no-cache-dir \
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

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p outputs/scene_based_videos inputs cache

# Set environment variables for video processing
ENV PYTHONPATH=/app
ENV TORCH_USE_CUDA_DSA=1
ENV CUDA_VISIBLE_DEVICES=""

# Default command
CMD ["python", "-c", "print('Video Processor Container Ready')"]
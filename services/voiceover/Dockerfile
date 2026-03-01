FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Fish Speech dependencies
# Note: In a real scenario, we would clone the repo and install from requirements.txt
# Here we prepare the service wrapper dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy service code
COPY . .

# Environment variables for model paths
ENV MODEL_PATH=/app/models/fish-speech-1.5
ENV DEVICE=cpu 

EXPOSE 8080

# Auto-download models then start the app
CMD ["sh", "-c", "python download_models.py && python main.py"]

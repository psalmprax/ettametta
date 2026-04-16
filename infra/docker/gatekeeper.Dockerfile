FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for AI processing and networking
RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping \
    openssh-client \
    rsync \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Mirror the requirements for the gateway
RUN pip install --no-cache-dir fastapi uvicorn httpx

EXPOSE 8133

# Create persistent state directory
RUN mkdir -p /workspace

CMD ["python", "gateway.py"]

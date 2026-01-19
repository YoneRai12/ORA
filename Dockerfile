# Base Image
FROM python:3.11-slim

# Env Vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System Dependencies (Git for pip git install, FFmpeg for Audio)
RUN apt-get update && \
    apt-get install -y git ffmpeg build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Common Python Dependencies FIRST (Caching)
COPY requirements.txt ./

# Install PyTorch (Linux CUDA 12.1 default)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Project Requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy Source Code
COPY . .

# Default Command (Can be overridden by Compose)
CMD ["python", "main.py"]

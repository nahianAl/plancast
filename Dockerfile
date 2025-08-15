# PlanCast Fallback Dockerfile
# Uses Python 3.9 and PyTorch 1.12.1 for maximum compatibility

FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install only essential system dependencies for OpenCV and other libs
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libgthread-2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install CPU-only PyTorch first (overrides the one in requirements.txt)
RUN pip install --no-cache-dir --timeout=100 \
    torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements (skipping torch/torchvision since we just installed them)
RUN pip install --no-cache-dir --timeout=100 \
    $(grep -v "^torch" requirements.txt | grep -v "^torchvision" | grep -v "^#" | grep -v "^$")

# Copy application code
COPY . .

# Expose port (Railway will override this with PORT env var)
EXPOSE 8000

# Use Railway's PORT environment variable
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}

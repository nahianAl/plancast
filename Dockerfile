# PlanCast Fallback Dockerfile
# Uses Python 3.9 and PyTorch 1.12.1 for maximum compatibility

FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Create a temporary requirements file without torch/torchvision
RUN grep -v "^torch" requirements.txt | grep -v "^torchvision" > requirements-no-torch.txt

# Install CPU-only PyTorch first
RUN pip install --no-cache-dir --timeout=100 \
    torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir --timeout=100 -r requirements-no-torch.txt

# Copy application code
COPY . .

# Expose port (Railway will override this with PORT env var)
EXPOSE 8000

# Use Railway's PORT environment variable
CMD python start.py

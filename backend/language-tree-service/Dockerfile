# Single-stage Dockerfile for development mode
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure pip doesn't cache wheels (saves space)
ENV PIP_NO_CACHE_DIR=1

# Upgrade pip and install uv tool
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY uv.lock ./

# Pre-install PyTorch CPU version to prevent CUDA downloads
RUN uv pip install --index-url https://download.pytorch.org/whl/cpu torch

# Install remaining dependencies (excluding torch since it's already installed)
RUN uv sync --frozen --all-extras

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Run with auto-reload for development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

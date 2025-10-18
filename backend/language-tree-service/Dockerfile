# Single-stage Dockerfile for development mode
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

    # Ensure pip doesn't cache wheels (saves space) and add pytorch CPU wheel index
ENV PIP_NO_CACHE_DIR=1
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# Upgrade pip and install uv tool
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir uv


# Copy project files
COPY pyproject.toml ./
COPY uv.lock ./

# Install all dependencies (including dev dependencies)
RUN uv sync --frozen --all-extras

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Run with auto-reload for development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

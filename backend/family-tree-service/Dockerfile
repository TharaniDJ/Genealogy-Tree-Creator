# Single-stage Dockerfile for development mode
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY uv.lock ./

# Install all dependencies (including dev dependencies)
RUN uv sync --frozen --all-extras

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run with auto-reload for development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

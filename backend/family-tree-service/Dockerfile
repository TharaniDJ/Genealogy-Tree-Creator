# Multi-stage Dockerfile for development and production modes
FROM python:3.11-slim AS base

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

# Development stage
FROM base AS development

# Install all dependencies (including dev dependencies)
RUN uv sync --frozen --all-extras

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run with auto-reload for development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS production

# Install only production dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

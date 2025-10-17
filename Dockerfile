FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY requirements.lock ./

# Install Python dependencies from lock file (skip -e file:. line for Docker)
RUN grep -v "^-e file:" requirements.lock > requirements-docker.txt && \
    uv pip install --system -r requirements-docker.txt

# Copy application code
COPY main.py ./
COPY src/ ./src/
COPY configs/ ./configs/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port 8322
EXPOSE 8322

# Command to run the application with streamable-http transport
CMD ["python", "main.py", "--transport", "streamable-http", "--port", "8322"]

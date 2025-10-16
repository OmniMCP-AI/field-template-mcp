FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN uv pip install --system --no-cache \
    fastmcp>=2.3.3 \
    python-dotenv>=1.1.1 \
    uvicorn>=0.34.2

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port 8321
EXPOSE 8321

# Command to run the application
CMD ["python", "main.py", "--transport", "streamable-http", "--port", "8321"]

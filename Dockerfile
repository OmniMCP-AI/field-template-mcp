FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml requirements.txt* ./

# Install Python dependencies from requirements.txt if it exists, otherwise from pyproject.toml
RUN if [ -f requirements.txt ]; then \
        uv pip install --system --no-cache -r requirements.txt; \
    else \
        uv pip install --system --no-cache \
            fastmcp>=2.3.3 \
            python-dotenv>=1.1.1 \
            openai>=2.4.0 \
            anthropic>=0.39.0 \
            mcp>=1.1.2 \
            jsonschema>=4.25.1 \
            pydantic>=2.0.0; \
    fi

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

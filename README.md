# MCP Template

A template for building Model Context Protocol (MCP) servers using FastMCP.

## Features

- 🚀 FastMCP-based server implementation
- 🐳 Docker and Docker Compose support
- 📦 Python package configuration with pyproject.toml
- 🔧 Environment variable configuration
- 📁 Well-organized folder structure
- 🤖 Built-in AI text summarization tool using OpenAI/OpenRouter
- 🧪 Comprehensive test suite with SSE client support

## Project Structure

```
.
├── docs/           # Documentation files
├── tests/          # Test files
├── src/            # Source code
├── main.py         # Main entry point
├── pyproject.toml  # Python project configuration
├── Dockerfile      # Docker configuration
├── docker-compose.yml
├── .env            # Environment variables
├── .gitignore      # Git ignore rules
└── README.md       # This file
```

## Installation

### Using pip

```bash
pip install -e .
```

### Using Docker

```bash
docker-compose up --build
```

## Usage

### Running locally

```bash
# stdio mode (default)
python main.py

# HTTP mode (default port: 8322)
python main.py --transport streamable-http --port 8322
```

### Running with Docker

```bash
# Build and run
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop the container
docker-compose down
```

The server will be available at `http://localhost:8322`

## Configuration

Create a `.env` file from the example:

```bash
cp env.example .env
```

Edit the `.env` file to configure your API keys:

```bash
# OpenAI Configuration (Required for summarize_text tool)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Custom base URL for OpenRouter or other OpenAI-compatible endpoints
# For OpenRouter: https://openrouter.ai/api/v1
OPENAI_BASE_URL=

# Optional: Model to use for summarization (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini
```

### OpenRouter Configuration

If you want to use [OpenRouter](https://openrouter.ai/) for accessing multiple LLM providers:

```bash
OPENAI_API_KEY=sk-or-v1-your-openrouter-api-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
# Or use other models like: anthropic/claude-3-opus, google/gemini-pro, etc.
```

## Available Tools

### 1. hello
A simple greeting tool to test the MCP connection.

**Parameters:**
- `name` (str): The name to greet

**Example:**
```python
result = await session.call_tool("hello", {"name": "World"})
# Returns: "Hello, World!"
```

### 2. summarize_text
Summarize text using OpenAI/OpenRouter LLM to generate concise summaries.

**Parameters:**
- `text` (str): The text to summarize
- `max_words` (int, optional): Maximum number of words for the summary (default: 50)

**Example:**
```python
result = await session.call_tool(
    "summarize_text",
    {
        "text": "Long text here...",
        "max_words": 30
    }
)
# Returns: A concise summary
```

## Testing

The project includes comprehensive tests for all MCP tools.

### Running Tests

```bash
# Make sure the server is running first
python main.py --transport streamable-http --port 8321

# In another terminal, run the tests
# Run all tests
python test/test_mcp_client.py --env=local --test=all

# Run specific test
python test/test_mcp_client.py --env=local --test=hello
python test/test_mcp_client.py --env=local --test=summarize

# Test against a remote server
python test/test_mcp_client.py --env=remote --url=https://your-server.com --test=all
```

### Test Requirements

For the `summarize_text` test to work, you need to:
1. Set `OPENAI_API_KEY` in your `.env` file
2. Optionally configure `OPENAI_BASE_URL` for OpenRouter

## Development

### Project Setup

1. Clone this repository
2. Install dependencies: `pip install -e .`
3. Configure environment variables in `.env`
4. Start developing in the `src/` directory

### Adding Tools

Add your MCP tools in `main.py` or create separate modules in the `src/` directory:

```python
@mcp.tool()
def your_tool(param: str) -> str:
    """
    Description of your tool.
    
    Args:
        param: Parameter description
    
    Returns:
        Result description
    """
    # Your implementation
    return result
```

## Docker Support

The template includes:

- **Dockerfile**: Multi-stage build with security best practices
- **docker-compose.yml**: Easy container orchestration
- **Non-root user**: Runs as unprivileged user for security
- **Health checks**: Built-in health monitoring

## Requirements

- Python >= 3.11
- FastMCP >= 2.3.3
- Docker (optional)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

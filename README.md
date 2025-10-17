# AI Field Template

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


### OpenRouter Configuration

If you want to use [OpenRouter](https://openrouter.ai/) for accessing multiple LLM providers:


## Available Tools

### 1. classify_by_llm
Classify each input into exactly ONE best-matching category using LLM.

**Parameters:**
- `input` (list): Items to classify
- `categories` (list[str]): Possible categories (mutually exclusive, min 2)
- `prompt` (str, optional): Custom classification instructions
- `args` (dict, optional): Additional config (model, temperature, etc.)

**Example:**
```python
result = await session.call_tool(
    "classify_by_llm",
    {
        "input": ["Apple releases iPhone", "Lakers win game"],
        "categories": ["tech", "sports", "politics"]
    }
)
# Returns: [{"id": 0, "result": "tech"}, {"id": 1, "result": "sports"}]
```

### 2. tag_by_llm
Apply multiple relevant tags from a predefined set to each input.

**Parameters:**
- `input` (list): Items to tag
- `tags` (list[str]): Possible tags (non-mutually exclusive)
- `prompt` (str, optional): Custom tagging instructions
- `args` (dict, optional): Additional config (max_tags, min_relevance, etc.)

**Example:**
```python
result = await session.call_tool(
    "tag_by_llm",
    {
        "input": ["Python REST API", "React app"],
        "tags": ["python", "javascript", "backend", "frontend"]
    }
)
# Returns: [{"id": 0, "result": ["python", "backend"]}, ...]
```

### 3. extract_by_llm
Extract specific fields from unstructured text using LLM.

**Parameters:**
- `input` (list): Items to extract from
- `fields` (list[str], optional): Field names to extract
- `response_format` (dict, optional): JSON Schema for structured output
- `args` (dict, optional): Additional config (model, temperature, etc.)

**Example:**
```python
result = await session.call_tool(
    "extract_by_llm",
    {
        "input": ["Article by Wade on 2025-10-12"],
        "fields": ["author", "date"]
    }
)
# Returns: [{"id": 0, "result": {"author": "Wade", "date": "2025-10-12"}}]
```

## Testing

The project includes comprehensive tests for all MCP tools.

### Running Tests

```bash
# Make sure the server is running first
python main.py --transport streamable-http --port 8322

# In another terminal, run the tests
# Run all tests
rye run python tests/test_mcp_client.py --env=local --test=all

# Run specific test
rye run python tests/test_mcp_client.py --env=local --test=classify
rye run python tests/test_mcp_client.py --env=local --test=tag
rye run python tests/test_mcp_client.py --env=local --test=extract

# Test against a remote server
rye run python tests/test_mcp_client.py --env=remote --url=https://your-server.com --test=all
```

### Test Requirements

For the LLM tools tests to work, you need to:
1. Set `OPENAI_API_KEY` in your `.env` file (refer to env.example)
2. Optionally configure `OPENAI_BASE_URL` for OpenRouter
3. Ensure the server is running on port 8322

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

# MCP Template

A template for building Model Context Protocol (MCP) servers using FastMCP.

## Features

- 🚀 FastMCP-based server implementation
- 🐳 Docker and Docker Compose support
- 📦 Python package configuration with pyproject.toml
- 🔧 Environment variable configuration
- 📁 Well-organized folder structure

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

# HTTP mode
python main.py --transport streamable-http --port 8321
```

### Running with Docker

```bash
docker-compose up
```

The server will be available at `http://localhost:8321`

## Configuration

Edit the `.env` file to configure your environment variables:

```bash
# Add your configuration here
API_KEY=your_api_key_here
```

## Development

### Project Setup

1. Clone this repository
2. Install dependencies: `pip install -e .`
3. Configure environment variables in `.env`
4. Start developing in the `src/` directory

### Adding Tools

Add your MCP tools in the `src/` directory and import them in `main.py`.

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

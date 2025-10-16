# Quick Start Guide

This guide will help you get started with the MCP Template Server and test the AI summarization tool.

## Prerequisites

- Python 3.11 or higher
- OpenAI API key or OpenRouter API key

## Installation

### 1. Install the Package

```bash
# Clone the repository (if not already done)
cd field-template-mcp

# Install the package and dependencies
pip install -e .
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your API key
# For OpenAI:
OPENAI_API_KEY=sk-your-openai-api-key-here

# OR for OpenRouter:
OPENAI_API_KEY=sk-or-v1-your-openrouter-api-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
```

## Running the Server

### Start the Server

```bash
# Start the server with streamable-http transport
python main.py --transport streamable-http --port 8321
```

You should see output like:
```
🚀 MCP Template Server
=========================
📋 Server Information:
   📦 Version: 1.0.0
   🌐 Transport: streamable-http
   🔗 URL: http://0.0.0.0:8321
   🐍 Python: 3.11.0

🚀 Starting server on http://0.0.0.0:8321
```

## Testing the Tools

### Quick Test - Using the Test Suite

Open a new terminal and run:

```bash
# Test all tools
python test/test_mcp_client.py --env=local --test=all

# Test only the hello tool
python test/test_mcp_client.py --env=local --test=hello

# Test only the summarize_text tool
python test/test_mcp_client.py --env=local --test=summarize
```

### Manual Testing - Using Python

You can also test manually using Python:

```python
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_summarize():
    url = "http://127.0.0.1:8321/mcp"
    
    async with streamablehttp_client(url=url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test summarize_text
            text = """
            Artificial Intelligence has transformed how we work and live.
            Machine learning enables computers to learn from data without
            explicit programming. Deep learning has achieved breakthroughs
            in image recognition and natural language processing.
            """
            
            result = await session.call_tool(
                "summarize_text",
                {"text": text, "max_words": 20}
            )
            
            if not result.isError:
                summary = json.loads(result.content[0].text)
                print(f"Summary: {summary}")

asyncio.run(test_summarize())
```

## Example Usage

### 1. Hello Tool

The simplest tool to test connectivity:

```python
result = await session.call_tool("hello", {"name": "World"})
# Returns: "Hello, World!"
```

### 2. Summarize Text Tool

Summarize any text to a concise version:

```python
long_text = """
The Model Context Protocol (MCP) is an open protocol that enables 
seamless integration between LLM applications and external data sources 
and tools. Whether you're building an AI-powered IDE, enhancing a chat 
interface, or creating custom AI workflows, MCP provides a standardized 
way to connect LLMs with the context they need.
"""

result = await session.call_tool(
    "summarize_text",
    {
        "text": long_text,
        "max_words": 30
    }
)
# Returns a ~30 word summary of the text
```

### 3. Different Word Limits

You can control summary length:

```python
# Very short summary (20 words)
result = await session.call_tool(
    "summarize_text",
    {"text": long_text, "max_words": 20}
)

# Medium summary (default 50 words)
result = await session.call_tool(
    "summarize_text",
    {"text": long_text}
)

# Longer summary (100 words)
result = await session.call_tool(
    "summarize_text",
    {"text": long_text, "max_words": 100}
)
```

## Using with Different LLM Providers

### OpenAI (Default)

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### OpenRouter (Multiple Providers)

```bash
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Choose from various models:
OPENAI_MODEL=openai/gpt-4o-mini
# OPENAI_MODEL=anthropic/claude-3-opus
# OPENAI_MODEL=google/gemini-pro
# OPENAI_MODEL=meta-llama/llama-3.1-70b-instruct
```

Get your OpenRouter API key at: https://openrouter.ai/keys

## Troubleshooting

### "OpenAI client not initialized" Error

Make sure you have set `OPENAI_API_KEY` in your `.env` file:
```bash
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Port Already in Use

If port 8321 is already in use, specify a different port:
```bash
python main.py --transport streamable-http --port 8322
```

Then update your test command:
```bash
python test/test_mcp_client.py --env=remote --url=http://127.0.0.1:8322 --test=all
```

### Import Errors

Make sure you've installed the package:
```bash
pip install -e .
```

## Next Steps

- Add your own MCP tools in `main.py`
- Customize the summarization prompt in the `summarize_text` function
- Integrate with your favorite MCP client (Claude Desktop, Cursor, etc.)
- Deploy the server with Docker

For more information, see the main [README.md](../README.md).


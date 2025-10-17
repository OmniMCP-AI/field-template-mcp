import argparse
import logging
import os
import sys
from importlib import metadata

from dotenv import load_dotenv
from fastmcp import FastMCP
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("AI Field Template MCP Server")

# Initialize OpenAI client (kept for backward compatibility, tools use their own LLM client)
openai_client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")  # Optional, for OpenRouter or custom endpoints

    if api_key:
        if base_url:
            openai_client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
    else:
        logger.info("OPENAI_API_KEY not found. Tools will use ANTHROPIC_API_KEY if available.")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")


# Import tools - using compatibility wrappers that work with dynamic registry
from src.tools import classify_by_llm, extract_by_llm, tag_by_llm

# Register tools with FastMCP using the old-style decorators
# These now use the dynamic registry under the hood
@mcp.tool()
async def classify_by_llm_tool(
    input: list,
    categories: list,
    prompt: str = None,
    args: dict = None
) -> list:
    """Classify each input into exactly ONE best-matching category from predefined options using LLM"""
    return await classify_by_llm(input, categories, prompt, args)

@mcp.tool()
async def tag_by_llm_tool(
    input: list,
    tags: list,
    prompt: str = None,
    args: dict = None
) -> list:
    """Apply multiple relevant tags from a predefined set to each input (non-mutually exclusive)"""
    return await tag_by_llm(input, tags, prompt, args)

@mcp.tool()
async def extract_by_llm_tool(
    input: list,
    fields: list = None,
    response_format: dict = None,
    args: dict = None
) -> list:
    """Extract specific fields from unstructured text using LLM semantic understanding"""
    return await extract_by_llm(input, fields, response_format, args)


def main():
    """
    Main entry point for the AI Field Template MCP server.
    Uses FastMCP's native streamable-http transport.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI Field Template MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="streamable-http",
        help="Transport mode: stdio (default) or streamable-http",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8322,
        help="Port for streamable-http transport (default: 8322)",
    )
    args = parser.parse_args()

    print("🚀 AI Field Template MCP Server")
    print("=" * 35)
    print("📋 Server Information:")
    try:
        version = metadata.version("field-template-mcp")
    except metadata.PackageNotFoundError:
        version = "dev"
    print(f"   📦 Version: {version}")
    print(f"   🌐 Transport: {args.transport}")
    if args.transport == "streamable-http":
        print(f"   🔗 URL: http://0.0.0.0:{args.port}")
    print(f"   🐍 Python: {sys.version.split()[0]}")
    # Dynamically list loaded tools
    print(f"   🛠️  Tools: classify_by_llm_tool, tag_by_llm_tool, extract_by_llm_tool")
    print("")

    try:
        if args.transport == "streamable-http":
            print(f"🚀 Starting server on http://0.0.0.0:{args.port}")
            mcp.run(transport="streamable-http", port=args.port, host="0.0.0.0")
        else:
            print("🚀 Starting server in stdio mode")
            mcp.run()

    except KeyboardInterrupt:
        print("\n👋 Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        logger.error(f"Unexpected error running server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

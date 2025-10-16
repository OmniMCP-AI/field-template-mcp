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
mcp = FastMCP("MCP Template Server")

# Initialize OpenAI client
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
        logger.warning("OPENAI_API_KEY not found in environment. summarize_text tool will not work.")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")


# Example tool - replace with your own
@mcp.tool()
def hello(name: str) -> str:
    """
    Say hello to someone.

    Args:
        name: The name of the person to greet

    Returns:
        A greeting message
    """
    return f"Hello, {name}!"


@mcp.tool()
def summarize_text(text: str, max_words: int = 50) -> str:
    """
    Summarize a given text to a very short content using LLM.
    
    Args:
        text: The text to summarize
        max_words: Maximum number of words for the summary (default: 50)
    
    Returns:
        A short summary of the text
    """
    if not openai_client:
        return "Error: OpenAI client not initialized. Please set OPENAI_API_KEY in .env file."
    
    try:
        # Get model from environment or use default
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Create the prompt for summarization
        prompt = f"Summarize the following text in {max_words} words or less. Be concise and capture the key points:\n\n{text}"
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_words * 2  # Rough estimate: 1 word ≈ 1-2 tokens
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Successfully summarized text of length {len(text)} to {len(summary)} characters")
        
        return summary
    
    except Exception as e:
        error_msg = f"Error summarizing text: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def main():
    """
    Main entry point for the MCP server.
    Uses FastMCP's native streamable-http transport.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Template Server")
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

    print("🚀 MCP Template Server")
    print("=" * 25)
    print("📋 Server Information:")
    try:
        version = metadata.version("mcp-template")
    except metadata.PackageNotFoundError:
        version = "dev"
    print(f"   📦 Version: {version}")
    print(f"   🌐 Transport: {args.transport}")
    if args.transport == "streamable-http":
        print(f"   🔗 URL: http://0.0.0.0:{args.port}")
    print(f"   🐍 Python: {sys.version.split()[0]}")
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

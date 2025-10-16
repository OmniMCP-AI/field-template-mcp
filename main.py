import argparse
import logging
import sys
from importlib import metadata

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("MCP Template Server")


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
        default=8321,
        help="Port for streamable-http transport (default: 8321)",
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

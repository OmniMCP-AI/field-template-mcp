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

# Set LLM client logger to INFO to see prompts
logging.getLogger("src.services.llm_client").setLevel(logging.INFO)

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


# Import dynamic tool registry
from src.tools.dynamic_registry import get_tool_registry
import inspect
from typing import Optional, Any

# Initialize dynamic tool registry and load all JSON templates
tool_registry = get_tool_registry()

# Dynamically register each tool from JSON configs
for tool_name in tool_registry.template_loader.list_templates():
    # Get the template to extract parameter info
    template = tool_registry.template_loader.get_template(tool_name)
    parameters = template.parameters
    description = template.description

    # Build function code dynamically
    # Create parameter list string
    params_list = []
    for param_name, param_def in parameters.items():
        param_type = param_def.type
        is_required = param_def.required

        # Map JSON types to Python type hints
        if param_type == "array":
            type_hint = "list"
        elif param_type == "object":
            type_hint = "dict"
        elif param_type == "string":
            type_hint = "str"
        elif param_type == "boolean":
            type_hint = "bool"
        elif param_type == "integer":
            type_hint = "int"
        else:
            type_hint = "Any"

        # Add Optional wrapper if not required
        if not is_required:
            params_list.append(f"{param_name}: Optional[{type_hint}] = None")
        else:
            params_list.append(f"{param_name}: {type_hint}")

    params_str = ", ".join(params_list)

    # Build the function dynamically
    func_code = f'''
async def {tool_name}_tool({params_str}):
    """{description}"""
    return await tool_registry.call_tool("{tool_name}", {{k: v for k, v in locals().items()}})
'''

    # Execute the function definition
    exec_globals = {
        'tool_registry': tool_registry,
        'Optional': Optional,
        'Any': Any,
        'list': list,
        'dict': dict,
        'str': str,
        'bool': bool,
        'int': int
    }
    exec(func_code, exec_globals)

    # Get the created function and register it
    tool_func = exec_globals[f'{tool_name}_tool']
    mcp.tool()(tool_func)


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
    tool_names = ", ".join([f"{name}_tool" for name in tool_registry.template_loader.list_templates()])
    print(f"   🛠️  Tools: {tool_names}")
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

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


# Import tools
from src.tools import classify_by_llm as classify_impl
from src.tools import tag_by_llm as tag_impl
from src.tools import extract_by_llm as extract_impl


# Tool 1: classify_by_llm
@mcp.tool()
async def classify_by_llm(
    input: list,
    categories: list[str],
    prompt: str = None,
    args: dict = None
) -> list[dict]:
    """
    Classify each input into exactly ONE best-matching category using LLM semantic understanding.

    <description>
    Performs mutually exclusive classification where each input item is assigned to exactly one
    category from a predefined list. Uses LLM for semantic understanding to handle ambiguous or
    contextual classification tasks. Processes inputs in batch for efficiency.
    </description>

    <use_case>
    - Content categorization (e.g., news articles into topics)
    - Sentiment analysis (positive/negative/neutral)
    - Priority classification (high/medium/low)
    - Department routing (sales/support/technical)
    - Document type identification
    </use_case>

    <limitation>
    - Requires minimum 2 categories
    - Cannot assign multiple categories (use tag_by_llm for multi-label)
    - Classification quality depends on LLM model capability
    - May produce inconsistent results for ambiguous inputs
    - Requires OpenAI API key in environment
    </limitation>

    <failure_cases>
    - Missing or invalid OpenAI API key
    - Categories list has fewer than 2 items
    - Input is not a list
    - API rate limits exceeded
    - Network connectivity issues
    </failure_cases>

    Args:
        input: List of items to classify. Each item can be:
            - Simple values: strings, numbers (auto-assigned IDs starting from 0)
            - Dict format: {"id": <id>, "data": <content>} (explicit IDs)
        categories: List of possible categories (mutually exclusive, minimum 2)
        prompt: Optional custom instructions for classification context
        args: Optional configuration dict:
            - model: str - Override default model (default: gpt-4o-mini)
            - temperature: float - Sampling temperature 0.0-1.0 (default: 0.0)
            - include_scores: bool - Return confidence scores (default: False)
            - allow_none: bool - Allow null result if no match (default: False)
            - fallback_category: str - Category to use if no match (default: None)

    Returns:
        List of dicts with structure:
        [
            {"id": <id>, "result": <category_string>},
            {"id": <id>, "result": {"category": <str>, "score": <float>}},  # if include_scores=True
            {"id": <id>, "result": null, "error": <error_message>}  # if failed
        ]

    Examples:
        >>> # Simple list input
        >>> classify_by_llm(
        ...     input=["Apple releases iPhone", "Lakers win game"],
        ...     categories=["tech", "sports", "politics"]
        ... )
        [{"id": 0, "result": "tech"}, {"id": 1, "result": "sports"}]

        >>> # With explicit IDs and custom prompt
        >>> classify_by_llm(
        ...     input=[{"id": "a1", "data": "Breaking news story"}],
        ...     categories=["urgent", "routine"],
        ...     prompt="Focus on urgency level",
        ...     args={"include_scores": True}
        ... )
        [{"id": "a1", "result": {"category": "urgent", "score": 0.95}}]
    """
    return await classify_impl(input, categories, prompt, args)


# Tool 2: tag_by_llm
@mcp.tool()
async def tag_by_llm(
    input: list,
    tags: list[str],
    prompt: str = None,
    args: dict = None
) -> list[dict]:
    """
    Apply multiple relevant tags from a predefined set to each input using LLM semantic understanding.

    <description>
    Performs multi-label tagging where each input can be assigned zero to many tags from a
    predefined set. Unlike classify_by_llm, tags are non-mutually exclusive - an item can have
    multiple tags or no tags. Uses LLM for semantic understanding to identify relevant tags
    based on content meaning rather than just keyword matching.
    </description>

    <use_case>
    - Content tagging (blog posts, articles, documents)
    - Technology stack identification (programming languages, frameworks)
    - Skill detection from job descriptions or resumes
    - Topic identification (can have multiple topics)
    - Feature flagging (multiple features can apply)
    </use_case>

    <limitation>
    - Requires minimum 1 tag in the predefined set
    - Tag quality depends on LLM model capability
    - May miss relevant tags or apply irrelevant ones
    - Cannot create new tags outside the predefined set
    - Requires OpenAI API key in environment
    </limitation>

    <failure_cases>
    - Missing or invalid OpenAI API key
    - Tags list is empty
    - Input is not a list
    - API rate limits exceeded
    - Network connectivity issues
    - JSON parsing failures from LLM response
    </failure_cases>

    Args:
        input: List of items to tag. Each item can be:
            - Simple values: strings, numbers (auto-assigned IDs)
            - Dict format: {"id": <id>, "data": <content>} (explicit IDs)
        tags: List of possible tags (non-mutually exclusive, minimum 1)
        prompt: Optional custom instructions for tagging context
        args: Optional configuration dict:
            - model: str - Override default model (default: gpt-4o-mini)
            - temperature: float - Sampling temperature 0.0-1.0 (default: 0.0)
            - max_tags: int - Maximum tags per item (default: unlimited)
            - min_relevance: float - Minimum relevance threshold 0-1 (default: 0.0)
            - include_scores: bool - Return relevance scores (default: False)

    Returns:
        List of dicts with structure:
        [
            {"id": <id>, "result": [<tag1>, <tag2>, ...]},  # Array of tag strings
            {"id": <id>, "result": [{"tag": <str>, "score": <float>}, ...]},  # if include_scores=True
            {"id": <id>, "result": []},  # Empty array if no tags match
            {"id": <id>, "result": null, "error": <error_message>}  # if failed
        ]

    Examples:
        >>> # Simple tagging
        >>> tag_by_llm(
        ...     input=["Python REST API", "React app"],
        ...     tags=["python", "javascript", "backend", "frontend"]
        ... )
        [
            {"id": 0, "result": ["python", "backend"]},
            {"id": 1, "result": ["javascript", "frontend"]}
        ]

        >>> # With max_tags limit and scores
        >>> tag_by_llm(
        ...     input=["Full-stack web development project"],
        ...     tags=["python", "javascript", "backend", "frontend", "database"],
        ...     args={"max_tags": 2, "include_scores": True}
        ... )
        [{"id": 0, "result": [{"tag": "backend", "score": 0.9}, {"tag": "frontend", "score": 0.8}]}]
    """
    return await tag_impl(input, tags, prompt, args)


# Tool 3: extract_by_llm
@mcp.tool()
async def extract_by_llm(
    input: list,
    fields: list[str] = None,
    response_format: dict = None,
    args: dict = None
) -> list[dict]:
    """
    Extract specific fields from unstructured text using LLM semantic understanding.

    <description>
    Extracts structured data from unstructured text by identifying and extracting specific fields.
    Supports both simple field lists and complex JSON Schema-based extraction for nested structures.
    Uses LLM semantic understanding to handle variations in formatting, terminology, and context.
    Can extract arrays, nested objects, and enforce type constraints.
    </description>

    <use_case>
    - Extract contact information from emails or documents
    - Parse invoice data (amounts, dates, vendor names)
    - Extract metadata from articles (title, author, date, tags)
    - Pull structured data from semi-structured logs
    - Convert natural language to structured records
    </use_case>

    <limitation>
    - Requires either 'fields' list or 'response_format' schema (not both)
    - Extraction quality depends on LLM model capability
    - May hallucinate data if information not present in input
    - Complex nested schemas may require more powerful models
    - Requires OpenAI API key in environment
    </limitation>

    <failure_cases>
    - Missing or invalid OpenAI API key
    - Both 'fields' and 'response_format' missing
    - Empty 'fields' list provided
    - Invalid JSON Schema in 'response_format'
    - Input is not a list
    - API rate limits exceeded
    - Network connectivity issues
    - LLM returns invalid JSON
    </failure_cases>

    Args:
        input: List of items to extract from. Each item can be:
            - Simple values: strings, numbers (auto-assigned IDs)
            - Dict format: {"id": <id>, "data": <content>} (explicit IDs)
        fields: List of field names to extract (required if response_format not provided)
            - Simple mode: extracts named fields into flat dict
        response_format: JSON Schema for structured output (OpenAI-compatible)
            - Advanced mode: supports nested objects, arrays, type constraints
        args: Optional configuration dict:
            - model: str - Override default model (default: gpt-4o-mini)
            - temperature: float - Sampling temperature 0.0-1.0 (default: 0.0)
            - max_tokens: int - Override max_tokens (default: 1000)
            - prompt: str - Custom extraction instructions

    Returns:
        List of dicts with structure:
        [
            {"id": <id>, "result": {<field1>: <value1>, <field2>: <value2>, ...}},
            {"id": <id>, "result": null, "error": <error_message>}  # if failed
        ]

    Examples:
        >>> # Simple field extraction
        >>> extract_by_llm(
        ...     input=["Article by Wade on 2025-10-12"],
        ...     fields=["author", "date"]
        ... )
        [{"id": 0, "result": {"author": "Wade", "date": "2025-10-12"}}]

        >>> # Structured output with arrays
        >>> extract_by_llm(
        ...     input=["Authors: Wade, Smith. Tags: AI, tech"],
        ...     response_format={
        ...         "type": "object",
        ...         "properties": {
        ...             "authors": {"type": "array", "items": {"type": "string"}},
        ...             "tags": {"type": "array", "items": {"type": "string"}}
        ...         }
        ...     }
        ... )
        [{"id": 0, "result": {"authors": ["Wade", "Smith"], "tags": ["AI", "tech"]}}]

        >>> # With custom extraction prompt
        >>> extract_by_llm(
        ...     input=["Invoice #123: $500 due 2025-12-01"],
        ...     fields=["invoice_number", "amount", "due_date"],
        ...     args={"prompt": "Extract numeric values without currency symbols"}
        ... )
        [{"id": 0, "result": {"invoice_number": "123", "amount": "500", "due_date": "2025-12-01"}}]
    """
    return await extract_impl(input, fields, response_format, args)


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
    print(f"   🛠️  Tools: classify_by_llm, tag_by_llm, extract_by_llm")
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

"""
Compatibility wrapper for extract_by_llm - uses dynamic registry.
This file provides backward compatibility for existing tests.
"""

from typing import List, Dict, Any, Optional
from .dynamic_registry import get_tool_registry


async def extract_by_llm(
    input: List[Any],
    fields: Optional[List[str]] = None,
    response_format: Optional[Dict[str, Any]] = None,
    args: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Extract specific fields from unstructured text using LLM.

    This is a compatibility wrapper that uses the dynamic tool registry.
    """
    registry = get_tool_registry()
    return await registry.call_tool("extract_by_llm", {
        "input": input,
        "fields": fields,
        "response_format": response_format,
        "args": args
    })

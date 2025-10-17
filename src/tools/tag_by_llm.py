"""
Compatibility wrapper for tag_by_llm - uses dynamic registry.
This file provides backward compatibility for existing tests.
"""

from typing import List, Dict, Any, Optional
from .dynamic_registry import get_tool_registry


async def tag_by_llm(
    input: List[Any],
    tags: List[str],
    prompt: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Apply multiple relevant tags from a predefined set.

    This is a compatibility wrapper that uses the dynamic tool registry.
    """
    registry = get_tool_registry()
    return await registry.call_tool("tag_by_llm", {
        "input": input,
        "tags": tags,
        "prompt": prompt,
        "args": args
    })

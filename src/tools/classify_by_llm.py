"""
Compatibility wrapper for classify_by_llm - uses dynamic registry.
This file provides backward compatibility for existing tests.
"""

from typing import List, Dict, Any, Optional
from .dynamic_registry import get_tool_registry


async def classify_by_llm(
    input: List[Any],
    categories: List[str],
    prompt: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Classify each input into exactly ONE best-matching category.

    This is a compatibility wrapper that uses the dynamic tool registry.
    """
    registry = get_tool_registry()
    return await registry.call_tool("classify_by_llm", {
        "input": input,
        "categories": categories,
        "prompt": prompt,
        "args": args
    })

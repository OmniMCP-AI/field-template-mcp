"""Tools package - MCP tool implementations."""

from .llm_tool_executor import LLMToolExecutor
from .template_loader import TemplateLoader, get_template_loader
from .dynamic_registry import DynamicToolRegistry, get_tool_registry

# Compatibility wrappers for existing tests
from .classify_by_llm import classify_by_llm
from .extract_by_llm import extract_by_llm
from .tag_by_llm import tag_by_llm

__all__ = [
    "LLMToolExecutor",
    "TemplateLoader",
    "get_template_loader",
    "DynamicToolRegistry",
    "get_tool_registry",
    "classify_by_llm",
    "extract_by_llm",
    "tag_by_llm",
]

"""
Template Loader - Loads and manages LLM tool templates with Pydantic validation.
"""

import json
from pathlib import Path
from typing import Dict, List

from .models import LLMToolTemplate


class TemplateLoader:
    """
    Loads and validates LLM tool templates using Pydantic.
    Automatic type checking and validation on load!
    """

    def __init__(self, templates_dir: str = None):
        """
        Initialize template loader.

        Args:
            templates_dir: Directory containing template JSON files.
                          Defaults to configs/tools/ in project root.
        """
        if templates_dir is None:
            # Default to configs/tools/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            templates_dir = project_root / "configs" / "tools"

        self.templates_dir = Path(templates_dir)
        self._templates: Dict[str, LLMToolTemplate] = {}
        self._load_all_templates()

    def _load_all_templates(self):
        """Load all JSON templates with Pydantic validation."""
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")

        for json_file in self.templates_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Pydantic validation - automatic type checking!
                template = LLMToolTemplate.model_validate(data)
                self._templates[template.tool_name] = template

            except Exception as e:
                print(f"Warning: Failed to load template {json_file.name}: {e}")

    def get_template(self, tool_name: str) -> LLMToolTemplate:
        """
        Get validated template by tool name.

        Args:
            tool_name: Name of the tool

        Returns:
            LLMToolTemplate Pydantic model

        Raises:
            KeyError: If template not found
        """
        if tool_name not in self._templates:
            raise KeyError(f"Template not found: {tool_name}")

        return self._templates[tool_name]

    def list_templates(self) -> List[str]:
        """
        Get list of all available template names.

        Returns:
            List of tool names
        """
        return list(self._templates.keys())

    def get_all_templates(self) -> Dict[str, LLMToolTemplate]:
        """
        Get all templates.

        Returns:
            Dictionary mapping tool names to LLMToolTemplate models
        """
        return self._templates.copy()

    def reload(self):
        """Reload all templates from disk."""
        self._templates = {}
        self._load_all_templates()


# Global template loader instance
_template_loader = None


def get_template_loader() -> TemplateLoader:
    """
    Get the global template loader instance.

    Returns:
        TemplateLoader instance
    """
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader

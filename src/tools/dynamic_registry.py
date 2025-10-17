"""
Dynamic Tool Registry - Manages dynamic MCP tool registration from JSON templates.
"""

from typing import Dict, Any, List, Callable
from .template_loader import get_template_loader
from .llm_tool_executor import LLMToolExecutor


class DynamicToolRegistry:
    """
    Manages dynamic registration of MCP tools from JSON templates.
    Provides MCP-compatible list_tools and call_tool methods.
    """

    def __init__(self):
        """Initialize the registry and load all templates."""
        self.template_loader = get_template_loader()
        self.executors = {}
        self._initialize_executors()

    def _initialize_executors(self):
        """Create executors for all loaded templates."""
        templates = self.template_loader.get_all_templates()
        for tool_name, template in templates.items():
            self.executors[tool_name] = LLMToolExecutor(template)

    def _generate_mcp_tool_name(self, template: Dict[str, Any]) -> str:
        """
        Generate MCP tool name in camelCase format.

        For now, we use the tool_name directly from template.
        Future: Could implement AI-based generation like in the docs.

        Args:
            template: Tool template

        Returns:
            Tool name in camelCase
        """
        return template["tool_name"]

    def _build_input_schema(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MCP input schema from template parameters.

        Args:
            template: Tool template

        Returns:
            JSON Schema for tool inputs
        """
        parameters = template.get("parameters", {})

        properties = {}
        required = []

        for param_name, param_def in parameters.items():
            prop = {
                "type": param_def.get("type", "string"),
                "description": param_def.get("description", "")
            }

            # Add additional schema properties
            if "items" in param_def:
                prop["items"] = param_def["items"]
            if "properties" in param_def:
                prop["properties"] = param_def["properties"]
            if "minItems" in param_def:
                prop["minItems"] = param_def["minItems"]
            if "default" in param_def:
                prop["default"] = param_def["default"]

            properties[param_name] = prop

            if param_def.get("required", False):
                required.append(param_name)

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema

    def _build_output_schema(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MCP output schema from template.

        Args:
            template: Tool template

        Returns:
            JSON Schema for tool outputs
        """
        output_format = template.get("output_format")

        # If output_format is defined, use it
        if output_format:
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                **output_format
            }

        # Default: no validation
        return None

    def _build_description(self, template: Dict[str, Any]) -> str:
        """
        Build comprehensive tool description.

        Args:
            template: Tool template

        Returns:
            Formatted description string
        """
        description = template.get("description", "")

        # Add use cases, limitations, etc. if available
        examples = template.get("examples", [])

        desc_parts = [description]

        if examples:
            desc_parts.append("\n\nExamples:")
            for i, example in enumerate(examples[:2], 1):  # Limit to 2 examples
                desc_parts.append(f"\n{i}. {example.get('description', 'Example')}")

        return "".join(desc_parts)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools in MCP format.

        Returns:
            List of tool definitions with:
                - name: Tool name
                - description: Tool description
                - inputSchema: JSON Schema for inputs
                - outputSchema: JSON Schema for outputs (optional)
        """
        tools = []

        templates = self.template_loader.get_all_templates()
        for tool_name, template in templates.items():
            tool_def = {
                "name": self._generate_mcp_tool_name(template),
                "description": self._build_description(template),
                "inputSchema": self._build_input_schema(template)
            }

            # Optionally include output schema
            output_schema = self._build_output_schema(template)
            if output_schema:
                tool_def["outputSchema"] = output_schema

            tools.append(tool_def)

        return tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool by name with the given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments as dict

        Returns:
            Tool execution result

        Raises:
            KeyError: If tool not found
        """
        if name not in self.executors:
            raise KeyError(f"Tool not found: {name}")

        executor = self.executors[name]
        return await executor.execute(**arguments)

    def get_tool_function(self, name: str) -> Callable:
        """
        Get a callable function for a tool (for decorator-based registration).

        Args:
            name: Tool name

        Returns:
            Async function that executes the tool
        """
        async def tool_function(**kwargs):
            return await self.call_tool(name, kwargs)

        # Set function metadata
        template = self.template_loader.get_template(name)
        tool_function.__name__ = name
        tool_function.__doc__ = self._build_description(template)

        return tool_function

    def reload_templates(self):
        """Reload all templates and reinitialize executors."""
        self.template_loader.reload()
        self.executors = {}
        self._initialize_executors()


# Global registry instance
_registry = None


def get_tool_registry() -> DynamicToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        DynamicToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = DynamicToolRegistry()
    return _registry

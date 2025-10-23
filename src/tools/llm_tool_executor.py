"""
Simplified LLM Tool Executor - Executes LLM-based tools from templates.

Clean, direct implementation focused on prompt formatting and LLM calling.
Works with the new LLMTool standard from tool.json files.
"""

import re
from typing import Any, Dict, Set

from ..services import InputNormalizer, get_llm_client
from .models import LLMToolTemplate, OperationType


class LLMToolExecutor:
    """
    Simple, direct LLM tool executor.
    Reads template, formats prompts, calls LLM, returns result.
    """

    def __init__(self, template: LLMToolTemplate):
        """
        Initialize executor with a tool template.

        Args:
            template: Tool template with prompt templates and config
        """
        self.template = template

        # Verify operation type
        if template.operation_type != OperationType.LLMTOOL:
            raise ValueError(f"Unsupported operation type: {template.operation_type}")

        # Extract template placeholders from user_prompt
        user_template = getattr(template.prompt_templates, 'user_prompt', None) or template.prompt_templates.user
        self.template_placeholders = self._extract_placeholders(user_template)

    def _extract_placeholders(self, template_str: str) -> Set[str]:
        """
        Extract all {placeholder} names from a template string.

        Args:
            template_str: Template string with {placeholder} patterns

        Returns:
            Set of placeholder names
        """
        # Find all {placeholder} patterns
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, template_str)
        return set(matches)

    async def execute(self, **kwargs) -> Any:
        """
        Execute LLM tool with given parameters.

        Args:
            **kwargs: Tool-specific arguments from inputSchema

        Returns:
            Result wrapped according to outputSchema type
        """
        # Find the main input parameter from template placeholders
        # Priority: look for common input parameter names in template
        input_param_name = None
        input_data = None

        # If not found, use the first template placeholder that exists in kwargs
        for placeholder in self.template_placeholders:
            if placeholder in kwargs and isinstance(kwargs[placeholder], (str, list)):
                input_param_name = placeholder
                input_data = kwargs[placeholder]
                break

        if not input_data:
            raise ValueError(f"Missing required input parameter. Expected one of: {self.template_placeholders}")

        # Check if input is a simple string (not a list)
        single_input = isinstance(input_data, str)

        # Normalize input to list format for processing
        if single_input:
            normalized = [{"id": 0, "data": input_data}]
        else:
            normalized = InputNormalizer.normalize(input_data)

        # Process each input
        results = []
        for item in normalized:
            result = await self._execute_single(item["data"], input_param_name, kwargs)
            results.append({"id": item["id"], "result": result})

        # For single string input, return just the result value
        if single_input and len(results) > 0:
            result = results[0].get("result")

            # MCP requires dict wrapping for non-dict types
            if self.template.output_schema and self.template.output_schema.get("type") == "string":
                return {"result": result}

            if self.template.output_schema and self.template.output_schema.get("type") == "array":
                return {"result": result}

            return result

        return results

    async def _execute_single(self, input_text: str, input_param_name: str, params: Dict[str, Any]) -> str:
        """
        Execute for a single input text.

        Args:
            input_text: Input text to process
            input_param_name: Name of the input parameter in the template
            params: All parameters from tool call

        Returns:
            Result string from LLM
        """
        # Get prompt templates - support both naming conventions
        prompt_templates = self.template.prompt_templates
        system_prompt = getattr(prompt_templates, 'system_prompt', None) or prompt_templates.system
        user_template = getattr(prompt_templates, 'user_prompt', None) or prompt_templates.user

        # Build format variables from template placeholders only
        format_vars = {}

        # Add the main input parameter
        format_vars[input_param_name] = input_text

        # Add all other parameters that are in template placeholders
        for key, value in params.items():
            if key in self.template_placeholders and key not in ["args", "prompt", "LLM_config"] and value is not None:
                # Skip the main input param as we already added it
                if key != input_param_name:
                    format_vars[key] = value

        # Format user prompt
        try:
            user_prompt = user_template.format(**format_vars)
        except KeyError as e:
            raise ValueError(f"Missing required parameter for prompt template: {e}")

        # Add custom prompt if provided
        if params.get("prompt"):
            system_prompt += f"\n\n{params['prompt']}"

        # Merge LLM configuration: executor_config defaults + inputSchema runtime config
        llm_config_defaults = {
            "model": self.template.llm_config.model,
            "temperature": self.template.llm_config.temperature,
            "max_tokens": self.template.llm_config.max_tokens,
        }

        # Merge with runtime LLM_config from inputSchema
        runtime_llm_config = params.get("LLM_config") or {}
        llm_config = {**llm_config_defaults, **runtime_llm_config}

        # Legacy support: args can also override config
        args = params.get("args") or {}
        model = args.get("model", llm_config["model"])
        temperature = args.get("temperature", llm_config["temperature"])
        max_tokens = args.get("max_tokens", llm_config["max_tokens"])

        # Call LLM
        llm_client = get_llm_client()
        response = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.strip()

"""
Simplified LLM Tool Executor - Executes LLM-based tools from templates.

Clean, direct implementation focused on prompt formatting and LLM calling.
Works with the new LLMTool standard from tool.json files.
"""

from typing import Any, Dict

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

    async def execute(self, **kwargs) -> Any:
        """
        Execute LLM tool with given parameters.

        Args:
            **kwargs: Tool-specific arguments from inputSchema

        Returns:
            Result wrapped according to outputSchema type
        """
        input_data = kwargs.get("input") or kwargs.get("input_raw_text")

        if not input_data:
            raise ValueError("Missing required parameter: 'input' or 'input_raw_text'")

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
            result = await self._execute_single(item["data"], kwargs)
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

    async def _execute_single(self, input_text: str, params: Dict[str, Any]) -> str:
        """
        Execute for a single input text.

        Args:
            input_text: Input text to process
            params: All parameters from tool call

        Returns:
            Result string from LLM
        """
        # Get prompt templates
        system_prompt = self.template.prompt_templates.system
        user_template = self.template.prompt_templates.user

        # Build format variables from params
        format_vars = {
            "input": input_text,
            "input_raw_text": input_text,
            "text": input_text,
        }

        # Add all other parameters for formatting
        for key, value in params.items():
            if key not in ["args", "prompt"] and value is not None:
                format_vars[key] = value

        # Format user prompt
        try:
            user_prompt = user_template.format(**format_vars)
        except KeyError as e:
            raise ValueError(f"Missing required parameter for prompt template: {e}")

        # Add custom prompt if provided
        if params.get("prompt"):
            system_prompt += f"\n\n{params['prompt']}"

        # Get model configuration
        args = params.get("args") or {}
        model = args.get("model", self.template.llm_config.model)
        temperature = args.get("temperature", self.template.llm_config.temperature)

        # Call LLM
        llm_client = get_llm_client()
        response = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature
        )

        return response.strip()

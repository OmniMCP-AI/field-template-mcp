"""
Extraction operation strategy.
Extracts item_to_extract from text (simple item_to_extract or structured schema).
"""

import json
from typing import Any, Dict, List

from .base import OperationStrategy
from ..models import LLMToolTemplate
from ..extract_text_util import extract_json_str


class ExtractionOperation(OperationStrategy):
    """
    Handles extraction operations.
    Works for ANY tool with operation_type="extraction".
    Supports both simple field extraction and structured schema.
    """

    async def execute(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        normalized_input: List[Dict[str, Any]],
        **params
    ) -> List[Dict[str, Any]]:
        """Execute field extraction."""

        # Get extraction parameters
        item_to_extract = params.get("item_to_extract")
        items_to_extract = params.get("items_to_extract")
        schema = params.get("response_format")

        # Handle items_to_extract (new plural version)
        if items_to_extract is not None:
            if isinstance(items_to_extract, str):
                # Split comma-separated string into list
                items_list = [item.strip() for item in items_to_extract.split(",")]
            elif isinstance(items_to_extract, list):
                # Already a list
                items_list = items_to_extract
            else:
                raise ValueError("items_to_extract must be a string or list")

            # Extract multiple items and return as list
            results = []
            for item in normalized_input:
                result = await self._extract_items_list(
                    llm_client, template, item, items_list, params
                )
                results.append({"id": item["id"], "result": result})
            return results

        # Handle item_to_extract (original singular version)
        # For simple string field (not comma-separated), just use it as-is
        if isinstance(item_to_extract, str):
            # Single field extraction - no comma separation needed
            field_name = item_to_extract.strip()
        else:
            field_name = None

        # Must have either item_to_extract or schema
        if not field_name and not schema:
            raise ValueError("Either 'item_to_extract', 'items_to_extract', or 'response_format' parameter is required")

        # Determine if using structured output
        use_structured = template.prompt_templates.structured_system is not None and schema

        results = []
        for item in normalized_input:
            if use_structured:
                # Use structured output with schema
                result = await self._extract_structured(
                    llm_client, template, item, schema, params
                )
                # Return JSON string for structured extraction
                result_str = json.dumps(result)
            else:
                # Use simple field extraction - returns plain text value
                result = await self._extract_field_value(
                    llm_client, template, item, field_name, params
                )
                # Return plain text value directly
                result_str = result

            results.append({"id": item["id"], "result": result_str})

        return results

    async def _extract_field_value(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        item: Dict[str, Any],
        field_name: str,
        params: Dict[str, Any]
    ) -> str:
        """Extract a single field value as plain text."""

        # Build prompts from template
        system_prompt = template.prompt_templates.system

        # Prepare format variables - include all params plus standard ones
        format_vars = {
            "item_to_extract": field_name,
            "text": item["data"],
            "input": item["data"],  # Support both 'text' and 'input'
        }

        # Add all other parameters from params (like entity_to_extract, date, etc.)
        for key, value in params.items():
            if key not in ["args", "prompt", "response_format"] and value is not None:
                # Format the value appropriately (e.g., "Date: 2024" or empty string if not provided)
                if key == "date" and value:
                    format_vars[key] = f"Date: {value}\n\n"
                else:
                    format_vars[key] = value

        # Handle optional date field - if not provided, use empty string
        if "date" not in format_vars or not format_vars.get("date"):
            format_vars["date"] = ""

        # Format user prompt with all variables
        user_prompt = template.prompt_templates.user.format(**format_vars)

        # Add custom prompt if provided
        if params.get("prompt"):
            system_prompt += f"\n\n{params['prompt']}"

        # Get model config
        args = params.get("args") or {}
        model = args.get("model", template.llm_config.model)
        temperature = args.get("temperature", template.llm_config.temperature)

        # Call LLM
        response = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature
        )

        # Return the plain text value (strip whitespace)
        return response.strip()

    async def _extract_items_list(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        item: Dict[str, Any],
        items_to_extract: List[str],
        params: Dict[str, Any]
    ) -> List[str]:
        """Extract multiple items and return as list of strings."""

        # Build prompts from template
        system_prompt = template.prompt_templates.system

        # Prepare format variables - include all params plus standard ones
        format_vars = {
            "items_to_extract": ", ".join(items_to_extract),
            "text": item["data"],
            "input": item["data"],  # Support both 'text' and 'input'
        }

        # Add all other parameters from params (like entity_to_extract, date, etc.)
        for key, value in params.items():
            if key not in ["args", "prompt", "response_format", "items_to_extract"] and value is not None:
                # Format the value appropriately (e.g., "Date: 2024" or empty string if not provided)
                if key == "date" and value:
                    format_vars[key] = f"Date: {value}\n\n"
                else:
                    format_vars[key] = value

        # Handle optional date field - if not provided, use empty string
        if "date" not in format_vars or not format_vars.get("date"):
            format_vars["date"] = ""

        # Format user prompt with all variables
        user_prompt = template.prompt_templates.user.format(**format_vars)

        # Add custom prompt if provided
        if params.get("prompt"):
            system_prompt += f"\n\n{params['prompt']}"

        # Get model config
        args = params.get("args") or {}
        model = args.get("model", template.llm_config.model)
        temperature = args.get("temperature", template.llm_config.temperature)

        # Call LLM
        response = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature
        )

        # Parse JSON array response
        try:
            json_str = extract_json_str(response)
            result = json.loads(json_str)

            # Ensure result is a list
            if not isinstance(result, list):
                raise ValueError("Expected list response from LLM")

            return result
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"LLM did not return valid JSON array: {response}") from e

    async def _extract_items(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        item: Dict[str, Any],
        item_to_extract: List[str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract simple item_to_extract from text."""

        # Build prompts from template
        system_prompt = template.prompt_templates.system

        # Format user prompt with item_to_extract and data
        user_prompt = template.prompt_templates.user.format(
            item_to_extract=", ".join(item_to_extract), text=item["data"]
        )

        # Add custom prompt if provided
        if params.get("prompt"):
            system_prompt += f"\n\n{params['prompt']}"

        # Get model config
        args = params.get("args") or {}
        model = args.get("model", template.llm_config.model)
        temperature = args.get("temperature", template.llm_config.temperature)

        # Call LLM
        response = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature
        )

        # Parse JSON response - use robust extraction
        try:
            json_str = extract_json_str(response)
            result = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            # If not valid JSON, try to extract from text
            result = self._parse_text_extraction(response, item_to_extract)

        return result

    async def _extract_structured(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        item: Dict[str, Any],
        schema: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract using structured output with JSON schema."""

        # Use structured system prompt
        system_prompt = template.prompt_templates.structured_system or template.prompt_templates.system

        # Format user prompt - use custom format for schema
        user_prompt = f"Schema:\n{json.dumps(schema, indent=2)}\n\nText:\n{item['data']}\n\nExtracted data (as JSON):"

        # Add custom prompt if provided
        if params.get("prompt"):
            system_prompt += f"\n\n{params['prompt']}"

        # Get model config
        args = params.get("args") or {}
        model = args.get("model", template.llm_config.model)
        temperature = args.get("temperature", template.llm_config.temperature)

        # Call LLM with structured output
        response = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model,
            temperature=temperature
        )

        # Parse JSON response - use robust extraction
        try:
            json_str = extract_json_str(response)
            result = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"LLM did not return valid JSON: {response}") from e

        return result

    def _parse_text_extraction(self, response: str, item_to_extract: List[str]) -> Dict[str, Any]:
        """Fallback: Parse extraction from text if not JSON."""
        result = {}
        lines = response.strip().split("\n")

        for line in lines:
            for field in item_to_extract:
                # Try to find "field: value" pattern
                if line.lower().startswith(field.lower() + ":"):
                    value = line.split(":", 1)[1].strip()
                    result[field] = value
                    break

        return result

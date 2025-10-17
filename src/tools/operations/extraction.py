"""
Extraction operation strategy.
Extracts fields from text (simple fields or structured schema).
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
        fields = params.get("fields")
        schema = params.get("response_format")

        # For simple string field (not comma-separated), just use it as-is
        if isinstance(fields, str):
            # Single field extraction - no comma separation needed
            field_name = fields.strip()
        else:
            field_name = None

        # Must have either fields or schema
        if not field_name and not schema:
            raise ValueError("Either 'fields' or 'response_format' parameter is required")

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

        # Format user prompt with field name and data
        user_prompt = template.prompt_templates.user.format(
            fields=field_name, text=item["data"]
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

        # Return the plain text value (strip whitespace)
        return response.strip()

    async def _extract_fields(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        item: Dict[str, Any],
        fields: List[str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract simple fields from text."""

        # Build prompts from template
        system_prompt = template.prompt_templates.system

        # Format user prompt with fields and data
        user_prompt = template.prompt_templates.user.format(
            fields=", ".join(fields), text=item["data"]
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
            result = self._parse_text_extraction(response, fields)

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

    def _parse_text_extraction(self, response: str, fields: List[str]) -> Dict[str, Any]:
        """Fallback: Parse extraction from text if not JSON."""
        result = {}
        lines = response.strip().split("\n")

        for line in lines:
            for field in fields:
                # Try to find "field: value" pattern
                if line.lower().startswith(field.lower() + ":"):
                    value = line.split(":", 1)[1].strip()
                    result[field] = value
                    break

        return result

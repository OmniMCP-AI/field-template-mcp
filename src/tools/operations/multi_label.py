"""
Multi-label operation strategy.
Picks MULTIPLE options from a list (tag, label, etc.).
"""

from typing import Any, Dict, List

from .base import OperationStrategy
from ..models import LLMToolTemplate


class MultiLabelOperation(OperationStrategy):
    """
    Handles multi-label operations.
    Works for ANY tool with operation_type="multi_label".
    """

    async def execute(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        normalized_input: List[Dict[str, Any]],
        **params
    ) -> List[Dict[str, Any]]:
        """Execute multi-label tagging."""

        # Find the parameter containing choices (tags, labels, options, etc.)
        choices_param = self._find_choices_param(template)
        choices = params.get(choices_param, [])

        # Convert comma-separated string to list
        if isinstance(choices, str):
            choices = [c.strip() for c in choices.split(",") if c.strip()]

        if not choices or len(choices) < 1:
            raise ValueError(f"{choices_param} must have at least 1 item")

        # Get max_tags limit if specified (from args)
        args = params.get("args") or {}
        max_tags = args.get("max_tags")

        results = []
        for item in normalized_input:
            # Build prompts from template
            system_prompt = template.prompt_templates.system

            # Add max_tags instruction if specified
            if max_tags:
                system_prompt += f"\n\nReturn at most {max_tags} labels."

            # Format user prompt with choices and data
            user_prompt = template.prompt_templates.user.format(
                **{choices_param: ", ".join(choices), "text": item["data"]}
            )

            # Add custom prompt if provided
            if params.get("prompt"):
                system_prompt += f"\n\n{params['prompt']}"

            # Get model config from params or template
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

            # Parse response - expect comma-separated list
            result_labels = self._parse_labels(response, choices, max_tags)

            # Return comma-separated string instead of array
            results.append({"id": item["id"], "result": ",".join(result_labels)})

        return results

    def _find_choices_param(self, template: LLMToolTemplate) -> str:
        """Find the parameter that contains the choices list."""
        # Look for array or string parameter (tags, labels, options, etc.)
        for param_name, param_def in template.parameters.items():
            if param_def.type in ("array", "string") and param_name != "input":
                return param_name
        raise ValueError("No choices parameter found in template")

    def _parse_labels(
        self, response: str, valid_choices: List[str], max_tags: int = None
    ) -> List[str]:
        """Parse comma-separated labels from response."""
        # Split by comma and clean up
        labels = [label.strip() for label in response.split(",")]

        # Match to valid choices (case-insensitive)
        matched_labels = []
        for label in labels:
            label_lower = label.lower()
            for choice in valid_choices:
                if choice.lower() == label_lower:
                    matched_labels.append(choice)
                    break

        # Apply max_tags limit
        if max_tags and len(matched_labels) > max_tags:
            matched_labels = matched_labels[:max_tags]

        return matched_labels

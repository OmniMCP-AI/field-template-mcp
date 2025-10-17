"""
Single choice operation strategy.
Picks ONE option from a list (classify, categorize, etc.).
"""

from typing import Any, Dict, List

from .base import OperationStrategy
from ..models import LLMToolTemplate


class SingleChoiceOperation(OperationStrategy):
    """
    Handles single-choice operations.
    Works for ANY tool with operation_type="single_choice".
    """

    async def execute(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        normalized_input: List[Dict[str, Any]],
        **params
    ) -> List[Dict[str, Any]]:
        """Execute single-choice classification."""

        # Find the parameter containing choices (categories, options, labels, etc.)
        choices_param = self._find_choices_param(template)
        choices = params.get(choices_param, [])

        # Convert comma-separated string to list
        if isinstance(choices, str):
            choices = [c.strip() for c in choices.split(",") if c.strip()]

        if not choices or len(choices) < 2:
            raise ValueError(f"{choices_param} must have at least 2 items")

        results = []
        for item in normalized_input:
            # Build prompts from template
            system_prompt = template.prompt_templates.system

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

            # Validate and normalize response
            result = response.strip()
            if result not in choices:
                # Try case-insensitive match
                result = self._match_choice(result, choices)

            results.append({"id": item["id"], "result": result})

        return results

    def _find_choices_param(self, template: LLMToolTemplate) -> str:
        """Find the parameter that contains the choices list."""
        # Look for array or string parameter (categories, tags, options, etc.)
        for param_name, param_def in template.parameters.items():
            if param_def.type in ("array", "string") and param_name != "input":
                return param_name
        raise ValueError("No choices parameter found in template")

    def _match_choice(self, response: str, choices: List[str]) -> str:
        """Try to match response to a valid choice (case-insensitive)."""
        response_lower = response.lower()
        for choice in choices:
            if choice.lower() == response_lower:
                return choice
        # If no match, return original response
        return response

"""
Unified LLM Tool Executor - Executes LLM-based tools from templates.

This module provides a generic execution engine using the Strategy Pattern.
No if-elif chains - operation type determines which strategy to use.
"""

from typing import Any

from ..services import InputNormalizer, get_llm_client
from .models import LLMToolTemplate, OperationType
from .operations import (
    SingleChoiceOperation,
    MultiLabelOperation,
    ExtractionOperation,
)


class LLMToolExecutor:
    """
    Unified executor using Strategy Pattern.
    Completely generic - no tool-specific code, no if-elif chains!
    """

    # Operation strategy registry - maps operation type to strategy
    STRATEGIES = {
        OperationType.SINGLE_CHOICE: SingleChoiceOperation(),
        OperationType.MULTI_LABEL: MultiLabelOperation(),
        OperationType.EXTRACTION: ExtractionOperation(),
    }

    def __init__(self, template: LLMToolTemplate):
        """
        Initialize executor with a tool template.

        Args:
            template: Pydantic model with operation type and configuration
        """
        self.template = template

        # Select strategy based on operation type - NO if-elif needed!
        self.strategy = self.STRATEGIES.get(template.operation_type)
        if not self.strategy:
            raise ValueError(f"Unknown operation type: {template.operation_type}")

    async def execute(self, **kwargs) -> Any:
        """
        Execute using appropriate strategy.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            For single string input: returns single result (string or dict)
            For list input: returns List of {id, result, error?} dicts
        """
        input_data = kwargs.get("input")

        # Check if input is a simple string (not a list)
        single_input = isinstance(input_data, str)

        # Normalize input to list format for processing
        if single_input:
            normalized = [{"id": 0, "data": input_data}]
        else:
            normalized = InputNormalizer.normalize(input_data)

        # Validate parameters
        self.strategy.validate_params(self.template, kwargs)

        # Execute using strategy
        results = await self.strategy.execute(
            llm_client=get_llm_client(),
            template=self.template,
            normalized_input=normalized,
            **kwargs
        )

        # For single string input, return just the result value
        if single_input and len(results) > 0:
            result = results[0].get("result")

            # If output_format is a string type, MCP requires dict wrapping
            if self.template.output_format and self.template.output_format.get("type") == "string":
                return {"result": result}

            return result

        return results

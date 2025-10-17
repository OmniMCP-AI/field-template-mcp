"""
Unified LLM Tool Executor - Executes LLM-based tools from templates.

This module provides a generic execution engine using the Strategy Pattern.
No if-elif chains - operation type determines which strategy to use.
"""

from typing import List, Dict, Any

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

    async def execute(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute using appropriate strategy - NO if-elif chains!

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            List of {id, result, error?} dicts
        """
        # Normalize input
        normalized = InputNormalizer.normalize(kwargs.get("input"))

        # Validate parameters
        self.strategy.validate_params(self.template, kwargs)

        # Execute using strategy - completely generic!
        return await self.strategy.execute(
            llm_client=get_llm_client(),
            template=self.template,
            normalized_input=normalized,
            **kwargs
        )

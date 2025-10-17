"""
Base operation strategy for LLM tools.
All operation types must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..models import LLMToolTemplate


class OperationStrategy(ABC):
    """
    Base class for operation strategies.
    Each strategy implements a specific operation type (classify, tag, extract).
    """

    @abstractmethod
    async def execute(
        self,
        llm_client: Any,
        template: LLMToolTemplate,
        normalized_input: List[Dict[str, Any]],
        **params
    ) -> List[Dict[str, Any]]:
        """
        Execute the operation on normalized input.

        Args:
            llm_client: LLM client for making API calls
            template: Tool template with prompts and config
            normalized_input: List of {"id": str, "data": Any} items
            **params: Additional parameters from tool call

        Returns:
            List of {"id": str, "result": Any} items
        """
        pass

    def validate_params(self, template: LLMToolTemplate, params: Dict[str, Any]) -> None:
        """
        Validate required parameters for this operation.

        Args:
            template: Tool template with parameter definitions
            params: Parameters passed to tool call

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        for param_name, param_def in template.parameters.items():
            if param_def.required and param_name not in params:
                raise ValueError(f"Required parameter '{param_name}' is missing")

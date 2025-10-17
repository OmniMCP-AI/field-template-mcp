"""Operation strategies for LLM tools."""

from .base import OperationStrategy
from .single_choice import SingleChoiceOperation
from .multi_label import MultiLabelOperation
from .extraction import ExtractionOperation

__all__ = [
    "OperationStrategy",
    "SingleChoiceOperation",
    "MultiLabelOperation",
    "ExtractionOperation",
]

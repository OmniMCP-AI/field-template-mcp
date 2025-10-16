"""Core data models for field-template-mcp."""

from typing import Any, Union, Optional, List, Dict
from pydantic import BaseModel, Field


class InputItem(BaseModel):
    """Normalized input item with ID and data."""
    id: Union[int, str] = Field(..., description="Unique identifier for this item")
    data: Any = Field(..., description="The actual data to process")


class OutputItem(BaseModel):
    """Output item with ID, result, and optional error."""
    id: Union[int, str] = Field(..., description="Same ID as input item")
    result: Optional[Any] = Field(None, description="Processing result")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class ProcessMetadata(BaseModel):
    """Metadata about batch processing."""
    total_items: int = Field(..., description="Total number of items processed")
    successful: int = Field(..., description="Number of successful items")
    failed: int = Field(..., description="Number of failed items")
    processing_time_ms: Optional[float] = Field(None, description="Total processing time in milliseconds")


class BatchProcessResult(BaseModel):
    """Complete batch processing result with metadata."""
    results: List[OutputItem] = Field(..., description="List of results")
    metadata: Optional[ProcessMetadata] = Field(None, description="Processing metadata")


class ModelConfig(BaseModel):
    """LLM model configuration."""
    provider: str = Field(default="anthropic", description="LLM provider (anthropic, openai, etc.)")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Model name")
    temperature: float = Field(default=0.0, description="Sampling temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    response_format: Optional[str] = Field(None, description="Response format (e.g., 'json')")

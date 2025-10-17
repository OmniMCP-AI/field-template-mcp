"""
Pydantic models for LLM tool templates.
Provides type safety and validation for tool configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class OperationType(str, Enum):
    """
    Operation types for LLM tools.
    Determines which execution strategy to use.
    """
    SINGLE_CHOICE = "single_choice"      # Pick ONE from list (classify, categorize)
    MULTI_LABEL = "multi_label"          # Pick MULTIPLE from list (tag, label)
    EXTRACTION = "extraction"            # Extract fields from text
    # Easy to extend: RANKING, SCORING, COMPARISON, GENERATION, etc.


class PromptTemplates(BaseModel):
    """Prompt templates with variable placeholders"""
    system: str = Field(description="System prompt with instructions")
    user: str = Field(description="User prompt template with {placeholders}")
    structured_system: Optional[str] = Field(
        default=None,
        description="Alternative system prompt for structured output"
    )


class ModelConfig(BaseModel):
    """LLM model configuration"""
    provider: str = Field(default="openai", description="LLM provider")
    model: str = Field(
        default="openai/gpt-4o-mini",
        description="Model name (e.g., 'openai/gpt-4o-mini', 'anthropic/claude-3-5-sonnet')"
    )
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1000, gt=0, description="Maximum tokens to generate")


class ParameterDef(BaseModel):
    """Parameter definition for tool input"""
    type: str = Field(description="Parameter type (array, object, string, etc.)")
    description: str = Field(description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    items: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Item schema for array types"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Properties for object types"
    )
    default: Optional[Any] = Field(default=None, description="Default value")
    minItems: Optional[int] = Field(default=None, description="Minimum array items")


class LLMToolTemplate(BaseModel):
    """
    Universal LLM tool template.
    Defines everything needed to execute an LLM-based tool.
    """
    tool_name: str = Field(description="Unique tool identifier")
    operation_type: OperationType = Field(
        description="Type of operation - determines execution strategy"
    )
    description: str = Field(description="Tool description for users/LLMs")
    category: Optional[str] = Field(default=None, description="Tool category")
    version: str = Field(default="1.0.0", description="Tool version")

    llm_config: ModelConfig = Field(description="LLM model configuration", alias="model_config")
    prompt_templates: PromptTemplates = Field(description="Prompt templates")

    parameters: Dict[str, ParameterDef] = Field(
        description="Input parameter definitions"
    )
    output_format: Dict[str, Any] = Field(
        description="Expected output JSON schema"
    )

    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Example inputs/outputs"
    )
    tags: List[str] = Field(default_factory=list, description="Tool tags")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True  # Allow using both field name and alias
    )

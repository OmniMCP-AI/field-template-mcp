"""
Pydantic models for LLM tool templates.
Provides type safety and validation for tool configurations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperationType(str, Enum):
    """
    Operation types for tools.
    """

    LLMTOOL = "LLMTool"  # LLM-based tools using prompt templates
    # Future: MCPTOOL, FORMULA, etc.


class PromptTemplates(BaseModel):
    """Prompt templates with variable placeholders"""

    system: str = Field(description="System prompt with instructions")
    user: str = Field(description="User prompt template with {placeholders}")
    structured_system: Optional[str] = Field(
        default=None, description="Alternative system prompt for structured output"
    )


class ModelConfig(BaseModel):
    """LLM model configuration"""

    provider: str = Field(default="openai", description="LLM provider")
    model: str = Field(
        default="openai/gpt-4o-mini",
        description="Model name (e.g., 'openai/gpt-4o-mini', 'anthropic/claude-3-5-sonnet')",
    )
    temperature: float = Field(
        default=0.0, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=1000, gt=0, description="Maximum tokens to generate"
    )


class ParameterDef(BaseModel):
    """Parameter definition for tool input"""

    type: str = Field(description="Parameter type (array, object, string, etc.)")
    description: str = Field(description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    items: Optional[Dict[str, Any]] = Field(
        default=None, description="Item schema for array types"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None, description="Properties for object types"
    )
    default: Optional[Any] = Field(default=None, description="Default value")
    minItems: Optional[int] = Field(default=None, description="Minimum array items")


class LLMToolTemplate(BaseModel):
    """
    Universal LLM tool template matching the new tool.json structure.
    """

    tool_name: str = Field(description="Unique tool identifier", alias="name")
    operation_type: OperationType = Field(description="Type of operation")
    description: str = Field(description="Tool description for users/LLMs")
    category: Optional[str] = Field(default=None, description="Tool category")
    version: str = Field(default="1.0.0", description="Tool version")

    # New structure: executor_config contains prompt_templates and model param definitions
    prompt_templates: PromptTemplates = Field(description="Prompt templates")
    llm_config: ModelConfig = Field(description="LLM model configuration")

    # Parameters extracted from inputSchema
    parameters: Dict[str, ParameterDef] = Field(
        description="Input parameter definitions", default_factory=dict
    )
    output_schema: Dict[str, Any] = Field(
        description="Expected output JSON schema", alias="outputSchema"
    )

    examples: List[Dict[str, Any]] = Field(
        default_factory=list, description="Example inputs/outputs"
    )
    tags: List[str] = Field(default_factory=list, description="Tool tags")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,  # Allow using both field name and alias
    )

    @model_validator(mode="before")
    @classmethod
    def convert_executor_config(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert executor_config structure to the model's expected structure.

        Input tool.json structure (new):
        {
          "executor_config": {
            "prompt_templates": {...},
            "LLM_config": {
              "type": "object",
              "properties": {
                "max_tokens": {"type": "integer", "default": 1000},
                "temperature": {"type": "number", "default": 0.0}
              }
            }
          },
          "inputSchema": {...}
        }

        Input tool.json structure (legacy):
        {
          "executor_config": {
            "prompt_templates": {...},
            "model": {"type": "string", "default": "gpt-4o-mini", ...},
            "temperature": {"type": "number", "default": 0.0, ...},
            "max_tokens": {"type": "integer", "default": 1000, ...}
          },
          "inputSchema": {...}
        }

        Output model structure:
        {
          "prompt_templates": {...},
          "llm_config": {"model": "...", "temperature": ..., "max_tokens": ...},
          "parameters": {...}
        }
        """
        if isinstance(data, dict):
            # Extract executor_config if present
            executor_config = data.get("executor_config", {})

            if executor_config:
                # Extract prompt_templates and normalize naming
                if "prompt_templates" in executor_config:
                    prompt_templates = executor_config["prompt_templates"]
                    # Normalize field names: system_prompt -> system, user_prompt -> user
                    normalized_templates = {}
                    normalized_templates["system"] = prompt_templates.get(
                        "system_prompt"
                    ) or prompt_templates.get("system", "")
                    normalized_templates["user"] = prompt_templates.get(
                        "user_prompt"
                    ) or prompt_templates.get("user", "")
                    if "structured_system" in prompt_templates:
                        normalized_templates["structured_system"] = prompt_templates[
                            "structured_system"
                        ]
                    data["prompt_templates"] = normalized_templates

                # Extract model config - support both new and legacy structures
                llm_config = {
                    "model": "openai/gpt-4o-mini",  # Default values
                    "temperature": 0.0,
                    "max_tokens": 1000,
                }

                # New structure: LLM_config.properties.*
                if "LLM_config" in executor_config and isinstance(
                    executor_config["LLM_config"], dict
                ):
                    llm_config_spec = executor_config["LLM_config"]
                    properties = llm_config_spec.get("properties", {})

                    if "model" in properties:
                        llm_config["model"] = properties["model"].get(
                            "default", "openai/gpt-4o-mini"
                        )
                    if "temperature" in properties:
                        llm_config["temperature"] = properties["temperature"].get(
                            "default", 0.0
                        )
                    if "max_tokens" in properties:
                        llm_config["max_tokens"] = properties["max_tokens"].get(
                            "default", 1000
                        )

                # Legacy structure: direct model/temperature/max_tokens fields
                elif any(
                    k in executor_config for k in ["model", "temperature", "max_tokens"]
                ):
                    if "model" in executor_config and isinstance(
                        executor_config["model"], dict
                    ):
                        llm_config["model"] = executor_config["model"].get(
                            "default", "openai/gpt-4o-mini"
                        )
                    if "temperature" in executor_config and isinstance(
                        executor_config["temperature"], dict
                    ):
                        llm_config["temperature"] = executor_config["temperature"].get(
                            "default", 0.0
                        )
                    if "max_tokens" in executor_config and isinstance(
                        executor_config["max_tokens"], dict
                    ):
                        llm_config["max_tokens"] = executor_config["max_tokens"].get(
                            "default", 1000
                        )

                # Set llm_config
                data["llm_config"] = llm_config

            # Convert inputSchema to parameters
            input_schema = data.get("inputSchema", {})
            if input_schema and "properties" in input_schema:
                parameters = {}
                required_fields = input_schema.get("required", [])

                for param_name, param_schema in input_schema["properties"].items():
                    parameters[param_name] = {
                        "type": param_schema.get("type", "string"),
                        "description": param_schema.get("description", ""),
                        "required": param_name in required_fields,
                        "items": param_schema.get("items"),
                        "properties": param_schema.get("properties"),
                        "default": param_schema.get("default"),
                        "minItems": param_schema.get("minItems"),
                    }

                data["parameters"] = parameters

        return data

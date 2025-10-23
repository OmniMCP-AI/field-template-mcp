"""
LLM Client service using OpenAI API.

Supports OpenAI and OpenAI-compatible APIs.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

# Configure logging
logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-based LLM client with OpenRouter support."""

    def __init__(self, provider: str = "openai"):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider name ("openai")

        Raises:
            ValueError: If API key is missing
        """
        self.provider = "openai"

        # Check if we have API keys available
        openai_key = os.getenv("OPENAI_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")

        if not openai_key and not openrouter_key:
            raise ValueError("Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set")

        # Initialize client (will be set per-request based on model)
        self.openai_client = None
        self.openrouter_client = None

        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)

        if openrouter_key:
            self.openrouter_client = AsyncOpenAI(
                api_key=openrouter_key, base_url="https://openrouter.ai/api/v1"
            )

    def _get_client(self, model: str) -> AsyncOpenAI:
        """
        Get appropriate client based on model name.

        Args:
            model: Model name (e.g., "gpt-4o-mini" or "openai/gpt-4o-mini")

        Returns:
            AsyncOpenAI client instance

        Raises:
            ValueError: If appropriate API key not found
        """
        # If model contains "/", use OpenRouter
        if "/" in model:
            if not self.openrouter_client:
                raise ValueError(
                    "OPENROUTER_API_KEY not set but model requires OpenRouter"
                )
            return self.openrouter_client
        else:
            if not self.openai_client:
                raise ValueError("OPENAI_API_KEY not set but model requires OpenAI")
            return self.openai_client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> str:
        """
        Send chat request to LLM and return text response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (uses gpt-4o-mini if None)
                   For OpenAI: "gpt-4o-mini", "gpt-4o", etc.
                   For OpenRouter: "openai/gpt-4o-mini", "anthropic/claude-3-5-sonnet", etc.
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Example:
            >>> client = LLMClient()
            >>> response = await client.chat([
            ...     {"role": "user", "content": "Hello!"}
            ... ])
        """
        # Use default model if not specified
        if model is None:
            model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

        # Get appropriate client based on model name
        client = self._get_client(model)

        # Log the prompt being sent
        logger.info("=" * 80)
        logger.info(
            f"📤 LLM REQUEST | Model: {model} | Temperature: {temperature} | Max Tokens: {max_tokens}"
        )
        logger.info("-" * 80)
        for i, msg in enumerate(messages, 1):
            logger.info(f"Message {i} [{msg['role'].upper()}]:")
            logger.info(msg["content"])
            logger.info("-" * 80)

        # Call OpenAI API
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response_content = response.choices[0].message.content

        # Log the response
        logger.info("📥 LLM RESPONSE:")
        logger.info(response_content)
        logger.info("=" * 80)

        return response_content

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Get structured JSON output from LLM.

        Args:
            messages: List of message dicts
            schema: JSON Schema defining expected output structure
            model: Model name (uses gpt-4o-mini if None)
                   For OpenAI: "gpt-4o-mini", "gpt-4o", etc.
                   For OpenRouter: "openai/gpt-4o-mini", "anthropic/claude-3-5-sonnet", etc.
            temperature: Sampling temperature

        Returns:
            Parsed JSON object matching the schema

        Example:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"type": "string"},
            ...         "age": {"type": "number"}
            ...     }
            ... }
            >>> result = await client.structured_output(messages, schema)
        """
        if model is None:
            model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

        # Get appropriate client based on model name
        client = self._get_client(model)

        # Add JSON schema instruction to system message
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        # Find or create system message
        modified_messages = []
        system_found = False

        for msg in messages:
            if msg["role"] == "system":
                modified_messages.append(
                    {"role": "system", "content": msg["content"] + schema_instruction}
                )
                system_found = True
            else:
                modified_messages.append(msg)

        if not system_found:
            modified_messages.insert(
                0,
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs valid JSON."
                    + schema_instruction,
                },
            )

        # Log the prompt being sent
        logger.info("=" * 80)
        logger.info(
            f"📤 LLM STRUCTURED REQUEST | Model: {model} | Temperature: {temperature}"
        )
        logger.info("-" * 80)
        for i, msg in enumerate(modified_messages, 1):
            logger.info(f"Message {i} [{msg['role'].upper()}]:")
            logger.info(msg["content"])
            logger.info("-" * 80)

        response = await client.chat.completions.create(
            model=model,
            messages=modified_messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        response_content = response.choices[0].message.content

        # Log the response
        logger.info("📥 LLM STRUCTURED RESPONSE:")
        logger.info(response_content)
        logger.info("=" * 80)

        # Parse JSON response
        return json.loads(response_content)

    def get_default_model(self) -> str:
        """Get default model for current provider."""
        return os.getenv("LLM_MODEL", "openai/gpt-4o-mini")


# Global client instance (initialized on first use)
_global_client: Optional[LLMClient] = None


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """
    Get global LLM client instance.

    Args:
        provider: LLM provider (always "openai")

    Returns:
        LLMClient instance

    Example:
        >>> client = get_llm_client()
        >>> response = await client.chat([{"role": "user", "content": "Hello"}])
    """
    global _global_client

    if _global_client is None:
        # Check for at least one API key
        openai_key = os.getenv("OPENAI_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")

        if not openai_key and not openrouter_key:
            raise ValueError("Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set")

        _global_client = LLMClient("openai")

    return _global_client

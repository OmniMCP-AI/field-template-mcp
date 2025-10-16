"""
LLM Client service using OpenAI API.

Supports OpenAI and OpenAI-compatible APIs.
"""

import os
import json
from typing import List, Dict, Any, Optional

from openai import OpenAI


class LLMClient:
    """OpenAI-based LLM client."""

    def __init__(self, provider: str = "openai"):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider name ("openai")

        Raises:
            ValueError: If API key is missing
        """
        self.provider = "openai"

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> str:
        """
        Send chat request to LLM and return text response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (uses gpt-4o-mini if None)
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
            model = "gpt-4o-mini"

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Get structured JSON output from LLM.

        Args:
            messages: List of message dicts
            schema: JSON Schema defining expected output structure
            model: Model name (uses gpt-4o-mini if None)
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
            model = "gpt-4o-mini"

        # Add JSON schema instruction to system message
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        # Find or create system message
        modified_messages = []
        system_found = False

        for msg in messages:
            if msg["role"] == "system":
                modified_messages.append({
                    "role": "system",
                    "content": msg["content"] + schema_instruction
                })
                system_found = True
            else:
                modified_messages.append(msg)

        if not system_found:
            modified_messages.insert(0, {
                "role": "system",
                "content": "You are a helpful assistant that outputs valid JSON." + schema_instruction
            })

        response = self.client.chat.completions.create(
            model=model,
            messages=modified_messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )

        # Parse JSON response
        return json.loads(response.choices[0].message.content)

    def get_default_model(self) -> str:
        """Get default model for current provider."""
        return "gpt-4o-mini"


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
        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set")

        _global_client = LLMClient("openai")

    return _global_client

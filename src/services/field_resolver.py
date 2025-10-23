"""
Field resolver service.

Handles field reference resolution for multi-input templates.
Supports {$field_name} syntax for referencing other fields in prompts.

Example:
    prompt = "Classify based on:\nName: {$name}\nPerson: {$person}"
    inputs = {"name": "John", "person": "engineer"}
    resolved = FieldResolver.resolve(prompt, inputs)
    # → "Classify based on:\nName: John\nPerson: engineer"
"""

import re
from typing import Any, Dict, List, Optional, Set


class FieldResolver:
    """Resolves field references in prompt templates."""

    # Pattern to match {$field_name}
    FIELD_REFERENCE_PATTERN = r"\{\$(\w+)\}"

    @staticmethod
    def extract_field_references(prompt: str) -> List[str]:
        """
        Extract all field references from a prompt template.

        Args:
            prompt: Prompt template with field references

        Returns:
            List of field names referenced in the prompt

        Examples:
            >>> prompt = "Name: {$name}, Age: {$age}"
            >>> FieldResolver.extract_field_references(prompt)
            ['name', 'age']

            >>> prompt = "Process {$input_data} as {$field_type}"
            >>> FieldResolver.extract_field_references(prompt)
            ['input_data', 'field_type']
        """
        if not prompt:
            return []

        matches = re.findall(FieldResolver.FIELD_REFERENCE_PATTERN, prompt)
        # Remove duplicates while preserving order
        seen: Set[str] = set()
        result = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                result.append(match)
        return result

    @staticmethod
    def resolve(prompt: str, inputs: Dict[str, Any], default: str = "") -> str:
        """
        Replace field references with actual values.

        Args:
            prompt: Prompt template with field references
            inputs: Dictionary of field values
            default: Default value for missing fields (default: empty string)

        Returns:
            Prompt with all field references resolved

        Examples:
            >>> prompt = "Name: {$name}, Age: {$age}"
            >>> inputs = {"name": "John", "age": 30}
            >>> FieldResolver.resolve(prompt, inputs)
            'Name: John, Age: 30'

            >>> # Missing field uses default
            >>> prompt = "Name: {$name}, City: {$city}"
            >>> inputs = {"name": "John"}
            >>> FieldResolver.resolve(prompt, inputs)
            'Name: John, City: '

            >>> # Custom default
            >>> FieldResolver.resolve(prompt, inputs, default="N/A")
            'Name: John, City: N/A'
        """
        if not prompt:
            return prompt

        # Extract all field references
        field_refs = FieldResolver.extract_field_references(prompt)

        # Replace each reference with its value
        resolved = prompt
        for field_name in field_refs:
            placeholder = f"{{${field_name}}}"
            value = inputs.get(field_name, default)

            # Convert value to string if needed
            if value is None:
                str_value = default
            else:
                str_value = str(value)

            resolved = resolved.replace(placeholder, str_value)

        return resolved

    @staticmethod
    def validate_fields(
        prompt: str, available_fields: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Check if all field references in prompt are available.

        Args:
            prompt: Prompt template with field references
            available_fields: Dictionary of available field values

        Returns:
            Tuple of (all_valid, missing_fields)
            - all_valid: True if all referenced fields are available
            - missing_fields: List of field names that are missing

        Examples:
            >>> prompt = "Name: {$name}, Age: {$age}"
            >>> inputs = {"name": "John", "age": 30}
            >>> FieldResolver.validate_fields(prompt, inputs)
            (True, [])

            >>> inputs = {"name": "John"}
            >>> FieldResolver.validate_fields(prompt, inputs)
            (False, ['age'])
        """
        field_refs = FieldResolver.extract_field_references(prompt)
        missing = [field for field in field_refs if field not in available_fields]
        return len(missing) == 0, missing

    @staticmethod
    def has_field_references(prompt: str) -> bool:
        """
        Check if prompt contains any field references.

        Args:
            prompt: Prompt template to check

        Returns:
            True if prompt contains field references, False otherwise

        Examples:
            >>> FieldResolver.has_field_references("Name: {$name}")
            True
            >>> FieldResolver.has_field_references("Simple prompt")
            False
        """
        return bool(re.search(FieldResolver.FIELD_REFERENCE_PATTERN, prompt))

    @staticmethod
    def resolve_dict_fields(
        data: Dict[str, Any],
        inputs: Dict[str, Any],
        fields_to_resolve: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve field references in dictionary values.

        Args:
            data: Dictionary with values that may contain field references
            inputs: Dictionary of field values for resolution
            fields_to_resolve: Optional list of keys to resolve (default: all)

        Returns:
            Dictionary with resolved values

        Examples:
            >>> data = {"prompt": "Name: {$name}", "title": "User: {$user}"}
            >>> inputs = {"name": "John", "user": "john123"}
            >>> FieldResolver.resolve_dict_fields(data, inputs)
            {'prompt': 'Name: John', 'title': 'User: john123'}

            >>> # Resolve only specific fields
            >>> FieldResolver.resolve_dict_fields(data, inputs, ["prompt"])
            {'prompt': 'Name: John', 'title': 'User: {$user}'}
        """
        resolved = {}

        for key, value in data.items():
            # Only resolve specified fields if provided
            if fields_to_resolve and key not in fields_to_resolve:
                resolved[key] = value
                continue

            # Resolve string values
            if isinstance(value, str):
                resolved[key] = FieldResolver.resolve(value, inputs)
            else:
                resolved[key] = value

        return resolved

    @staticmethod
    def create_field_context(inputs: Dict[str, Any]) -> str:
        """
        Create a formatted context string from input fields.

        Useful for providing context to LLM when using multiple fields.

        Args:
            inputs: Dictionary of input fields

        Returns:
            Formatted context string

        Examples:
            >>> inputs = {"name": "John", "age": 30, "city": "NYC"}
            >>> FieldResolver.create_field_context(inputs)
            'name: John\\nage: 30\\ncity: NYC'
        """
        lines = []
        for key, value in inputs.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)


def extract_field_references(prompt: str) -> List[str]:
    """Convenience function for extracting field references."""
    return FieldResolver.extract_field_references(prompt)


def resolve_field_references(
    prompt: str, inputs: Dict[str, Any], default: str = ""
) -> str:
    """Convenience function for resolving field references."""
    return FieldResolver.resolve(prompt, inputs, default)


def has_field_references(prompt: str) -> bool:
    """Convenience function to check for field references."""
    return FieldResolver.has_field_references(prompt)

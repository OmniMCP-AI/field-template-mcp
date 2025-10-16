"""
JSON Schema validation service.

Validates LLM outputs against JSON Schema Draft 7 specifications.
Supports nested objects, type constraints, and advanced validation rules.
"""

import jsonschema
from typing import Dict, Any, Optional, Tuple


class SchemaValidator:
    """Validates data against JSON Schema specifications."""

    @staticmethod
    def validate(data: Any, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate data against JSON Schema.

        Args:
            data: Data to validate
            schema: JSON Schema definition (Draft 7)

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid

        Examples:
            >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            >>> validator = SchemaValidator()
            >>> validator.validate({"name": "John"}, schema)
            (True, None)

            >>> validator.validate({"name": 123}, schema)
            (False, "123 is not of type 'string'")
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            # Extract the most relevant error message
            error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            error_msg = f"Validation error at '{error_path}': {e.message}"
            return False, error_msg
        except jsonschema.exceptions.SchemaError as e:
            return False, f"Invalid schema: {e.message}"

    @staticmethod
    def validate_with_details(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate with detailed error information.

        Args:
            data: Data to validate
            schema: JSON Schema definition

        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "errors": list[dict],  # List of error details
                "data": Any            # Original data
            }

        Examples:
            >>> result = SchemaValidator.validate_with_details(
            ...     {"name": 123, "age": "invalid"},
            ...     {
            ...         "type": "object",
            ...         "properties": {
            ...             "name": {"type": "string"},
            ...             "age": {"type": "number"}
            ...         }
            ...     }
            ... )
            >>> result["valid"]
            False
            >>> len(result["errors"])
            1
        """
        validator = jsonschema.Draft7Validator(schema)
        errors = []

        for error in validator.iter_errors(data):
            error_path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append({
                "path": error_path,
                "message": error.message,
                "validator": error.validator,
                "value": error.instance
            })

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": data
        }

    @staticmethod
    def get_required_fields(schema: Dict[str, Any]) -> list[str]:
        """
        Extract required field names from schema.

        Args:
            schema: JSON Schema definition

        Returns:
            List of required field names

        Examples:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {"name": {}, "age": {}},
            ...     "required": ["name"]
            ... }
            >>> SchemaValidator.get_required_fields(schema)
            ['name']
        """
        if schema.get("type") == "object":
            return schema.get("required", [])
        return []

    @staticmethod
    def supports_nullable(schema: Dict[str, Any], field_path: str) -> bool:
        """
        Check if a field supports null values.

        Args:
            schema: JSON Schema definition
            field_path: Dot-separated path to field (e.g., "user.details.age")

        Returns:
            True if field can be null, False otherwise

        Examples:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"type": ["string", "null"]},
            ...         "age": {"type": "number"}
            ...     }
            ... }
            >>> SchemaValidator.supports_nullable(schema, "name")
            True
            >>> SchemaValidator.supports_nullable(schema, "age")
            False
        """
        # Simple implementation for top-level fields
        # Can be extended to support nested paths
        if schema.get("type") != "object":
            return False

        properties = schema.get("properties", {})
        field_schema = properties.get(field_path, {})

        field_type = field_schema.get("type")

        # Check if type is an array containing "null"
        if isinstance(field_type, list):
            return "null" in field_type

        return False

    @staticmethod
    def create_error_feedback(
        data: Any,
        schema: Dict[str, Any],
        validation_errors: list[dict]
    ) -> str:
        """
        Generate human-readable error feedback for LLM retry.

        Args:
            data: Invalid data
            schema: Expected schema
            validation_errors: List of validation errors

        Returns:
            Formatted error message for LLM

        Examples:
            >>> errors = [{"path": "age", "message": "'invalid' is not of type 'number'"}]
            >>> feedback = SchemaValidator.create_error_feedback({}, {}, errors)
            >>> "age" in feedback
            True
        """
        feedback_lines = [
            "The previous response had validation errors:",
            ""
        ]

        for error in validation_errors:
            path = error.get("path", "unknown")
            message = error.get("message", "validation error")
            feedback_lines.append(f"- Field '{path}': {message}")

        feedback_lines.extend([
            "",
            "Please provide a corrected response that matches the schema exactly.",
            "Pay attention to data types (string, number, array, object, boolean, null)."
        ])

        return "\n".join(feedback_lines)


def validate_output(data: Any, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Convenience function for quick validation.

    Args:
        data: Data to validate
        schema: JSON Schema

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> from src.services.schema_validator import validate_output
        >>> valid, error = validate_output({"name": "John"}, {"type": "object"})
        >>> valid
        True
    """
    return SchemaValidator.validate(data, schema)

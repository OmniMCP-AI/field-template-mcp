"""
Type coercion service.

Handles type conversion for JSON Schema validation:
- String → Number conversion
- String → Date parsing
- String → Boolean conversion
- Enum validation
- Type normalization
"""

from typing import Any, Optional, Union
from datetime import datetime
import re


class TypeCoercer:
    """Coerces values to match JSON Schema type requirements."""

    @staticmethod
    def coerce_to_number(value: Any) -> Optional[Union[int, float]]:
        """
        Coerce value to number.

        Args:
            value: Value to coerce

        Returns:
            Number if successful, None if not coercible

        Examples:
            >>> TypeCoercer.coerce_to_number("123")
            123
            >>> TypeCoercer.coerce_to_number("123.45")
            123.45
            >>> TypeCoercer.coerce_to_number("$1,234.56")
            1234.56
            >>> TypeCoercer.coerce_to_number("invalid")
            None
        """
        if isinstance(value, (int, float)):
            return value

        if value is None:
            return None

        # Convert to string
        str_value = str(value).strip()

        # Remove common currency symbols and thousand separators
        cleaned = re.sub(r'[\$,€£¥]', '', str_value)

        # Handle percentages
        if '%' in cleaned:
            cleaned = cleaned.replace('%', '')
            try:
                return float(cleaned) / 100
            except ValueError:
                return None

        # Try to parse as number
        try:
            # Check if it's an integer
            if '.' not in cleaned:
                return int(cleaned)
            else:
                return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def coerce_to_date(value: Any) -> Optional[str]:
        """
        Coerce value to ISO date string (YYYY-MM-DD).

        Args:
            value: Value to coerce

        Returns:
            ISO date string if successful, None if not coercible

        Examples:
            >>> TypeCoercer.coerce_to_date("2025-10-17")
            '2025-10-17'
            >>> TypeCoercer.coerce_to_date("10/17/2025")
            '2025-10-17'
            >>> TypeCoercer.coerce_to_date("Oct 17, 2025")
            '2025-10-17'
            >>> TypeCoercer.coerce_to_date("invalid")
            None
        """
        if value is None:
            return None

        str_value = str(value).strip()

        # Already in ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', str_value):
            return str_value

        # Try common date formats
        date_formats = [
            '%Y-%m-%d',          # 2025-10-17
            '%m/%d/%Y',          # 10/17/2025
            '%d/%m/%Y',          # 17/10/2025
            '%Y/%m/%d',          # 2025/10/17
            '%b %d, %Y',         # Oct 17, 2025
            '%B %d, %Y',         # October 17, 2025
            '%d %b %Y',          # 17 Oct 2025
            '%d %B %Y',          # 17 October 2025
            '%Y-%m-%dT%H:%M:%S', # ISO datetime
            '%Y-%m-%d %H:%M:%S', # SQL datetime
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(str_value, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    @staticmethod
    def coerce_to_boolean(value: Any) -> Optional[bool]:
        """
        Coerce value to boolean.

        Args:
            value: Value to coerce

        Returns:
            Boolean if successful, None if not coercible

        Examples:
            >>> TypeCoercer.coerce_to_boolean("true")
            True
            >>> TypeCoercer.coerce_to_boolean("yes")
            True
            >>> TypeCoercer.coerce_to_boolean("false")
            False
            >>> TypeCoercer.coerce_to_boolean("no")
            False
            >>> TypeCoercer.coerce_to_boolean(1)
            True
            >>> TypeCoercer.coerce_to_boolean(0)
            False
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return bool(value)

        if value is None:
            return None

        str_value = str(value).strip().lower()

        true_values = {'true', 'yes', 'y', '1', 't', 'on', 'enabled'}
        false_values = {'false', 'no', 'n', '0', 'f', 'off', 'disabled'}

        if str_value in true_values:
            return True
        elif str_value in false_values:
            return False

        return None

    @staticmethod
    def coerce_to_string(value: Any) -> str:
        """
        Coerce value to string.

        Args:
            value: Value to coerce

        Returns:
            String representation

        Examples:
            >>> TypeCoercer.coerce_to_string(123)
            '123'
            >>> TypeCoercer.coerce_to_string(None)
            ''
        """
        if value is None:
            return ''
        return str(value)

    @staticmethod
    def coerce_to_type(value: Any, target_type: str) -> Any:
        """
        Coerce value to target type based on JSON Schema type name.

        Args:
            value: Value to coerce
            target_type: Target type ('string', 'number', 'integer', 'boolean', 'null')

        Returns:
            Coerced value or original value if coercion not applicable

        Examples:
            >>> TypeCoercer.coerce_to_type("123", "number")
            123
            >>> TypeCoercer.coerce_to_type("true", "boolean")
            True
            >>> TypeCoercer.coerce_to_type(123, "string")
            '123'
        """
        if target_type == "string":
            return TypeCoercer.coerce_to_string(value)
        elif target_type in ("number", "integer"):
            coerced = TypeCoercer.coerce_to_number(value)
            return coerced if coerced is not None else value
        elif target_type == "boolean":
            coerced = TypeCoercer.coerce_to_boolean(value)
            return coerced if coerced is not None else value
        elif target_type == "null":
            return None
        else:
            return value

    @staticmethod
    def validate_enum(value: Any, enum_values: list) -> bool:
        """
        Check if value is in enum list.

        Args:
            value: Value to check
            enum_values: List of allowed values

        Returns:
            True if value is in enum, False otherwise

        Examples:
            >>> TypeCoercer.validate_enum("active", ["active", "inactive", "pending"])
            True
            >>> TypeCoercer.validate_enum("deleted", ["active", "inactive", "pending"])
            False
        """
        return value in enum_values

    @staticmethod
    def coerce_enum(value: Any, enum_values: list) -> Optional[Any]:
        """
        Coerce value to match enum (case-insensitive for strings).

        Args:
            value: Value to coerce
            enum_values: List of allowed values

        Returns:
            Matched enum value or None if no match

        Examples:
            >>> TypeCoercer.coerce_enum("ACTIVE", ["active", "inactive"])
            'active'
            >>> TypeCoercer.coerce_enum("unknown", ["active", "inactive"])
            None
        """
        if value in enum_values:
            return value

        # Try case-insensitive string matching
        if isinstance(value, str):
            value_lower = value.lower()
            for enum_val in enum_values:
                if isinstance(enum_val, str) and enum_val.lower() == value_lower:
                    return enum_val

        return None

    @staticmethod
    def coerce_object_to_schema(data: dict, schema: dict) -> dict:
        """
        Coerce all fields in an object to match schema types.

        Args:
            data: Data object to coerce
            schema: JSON Schema with properties

        Returns:
            Coerced data object

        Examples:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "age": {"type": "number"},
            ...         "name": {"type": "string"}
            ...     }
            ... }
            >>> data = {"age": "30", "name": 123}
            >>> TypeCoercer.coerce_object_to_schema(data, schema)
            {'age': 30, 'name': '123'}
        """
        if not isinstance(data, dict) or schema.get("type") != "object":
            return data

        properties = schema.get("properties", {})
        coerced_data = {}

        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")

                # Handle nullable types (e.g., ["string", "null"])
                if isinstance(prop_type, list):
                    if value is None and "null" in prop_type:
                        coerced_data[key] = None
                        continue
                    # Use first non-null type for coercion
                    for t in prop_type:
                        if t != "null":
                            prop_type = t
                            break

                # Handle enums
                if "enum" in prop_schema:
                    coerced_value = TypeCoercer.coerce_enum(value, prop_schema["enum"])
                    coerced_data[key] = coerced_value if coerced_value is not None else value
                # Handle date format
                elif prop_schema.get("format") == "date":
                    coerced_date = TypeCoercer.coerce_to_date(value)
                    coerced_data[key] = coerced_date if coerced_date is not None else value
                # Handle standard types
                elif isinstance(prop_type, str):
                    coerced_data[key] = TypeCoercer.coerce_to_type(value, prop_type)
                else:
                    coerced_data[key] = value
            else:
                coerced_data[key] = value

        return coerced_data


def coerce_to_number(value: Any) -> Optional[Union[int, float]]:
    """Convenience function for number coercion."""
    return TypeCoercer.coerce_to_number(value)


def coerce_to_date(value: Any) -> Optional[str]:
    """Convenience function for date coercion."""
    return TypeCoercer.coerce_to_date(value)


def coerce_to_boolean(value: Any) -> Optional[bool]:
    """Convenience function for boolean coercion."""
    return TypeCoercer.coerce_to_boolean(value)

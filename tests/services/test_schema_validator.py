"""
Test cases for schema_validator.py

Tests JSON Schema validation, nested objects, type checking, and error feedback.
"""

from src.services.schema_validator import SchemaValidator, validate_output


class TestSchemaValidatorBasic:
    """Basic validation tests."""

    def test_simple_object_valid(self):
        """Test valid simple object."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }
        data = {"name": "John", "age": 30}

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True
        assert error is None

    def test_simple_object_invalid_type(self):
        """Test invalid type."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }
        data = {"name": "John", "age": "thirty"}  # age should be number

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is False
        assert error is not None
        assert "age" in error or "thirty" in error

    def test_required_fields_missing(self):
        """Test missing required field."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }
        data = {"age": 30}  # missing required 'name'

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is False
        assert error is not None

    def test_required_fields_present(self):
        """Test with all required fields present."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }
        data = {"name": "John"}  # age is optional

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True


class TestSchemaValidatorNestedObjects:
    """Test nested object validation."""

    def test_nested_object_valid(self):
        """Test valid nested structure."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "details": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "number"},
                        "email": {"type": "string"},
                    },
                },
            },
        }
        data = {"name": "John", "details": {"age": 30, "email": "john@example.com"}}

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True
        assert error is None

    def test_nested_object_invalid(self):
        """Test invalid nested structure."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "details": {
                    "type": "object",
                    "properties": {"age": {"type": "number"}},
                },
            },
        }
        data = {
            "name": "John",
            "details": {
                "age": "invalid"  # should be number
            },
        }

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is False
        assert error is not None


class TestSchemaValidatorArrays:
    """Test array validation."""

    def test_array_of_strings_valid(self):
        """Test valid string array."""
        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }
        data = {"tags": ["python", "javascript", "go"]}

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True

    def test_array_of_strings_invalid(self):
        """Test invalid array items."""
        schema = {
            "type": "object",
            "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
        }
        data = {"tags": ["python", 123, "go"]}  # 123 is not a string

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is False

    def test_array_of_objects_valid(self):
        """Test valid array of objects."""
        schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "number"},
                        },
                    },
                }
            },
        }
        data = {"users": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]}

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True


class TestSchemaValidatorNullable:
    """Test nullable field support."""

    def test_nullable_field_with_null(self):
        """Test nullable field with null value."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": ["string", "null"]}},
        }
        data = {"name": None}

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True

    def test_nullable_field_with_value(self):
        """Test nullable field with actual value."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": ["string", "null"]}},
        }
        data = {"name": "John"}

        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True

    def test_supports_nullable_detection(self):
        """Test nullable field detection."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": ["string", "null"]},
                "age": {"type": "number"},
            },
        }

        assert SchemaValidator.supports_nullable(schema, "name") is True
        assert SchemaValidator.supports_nullable(schema, "age") is False


class TestSchemaValidatorHelpers:
    """Test helper methods."""

    def test_get_required_fields(self):
        """Test required fields extraction."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"},
            },
            "required": ["name", "email"],
        }

        required = SchemaValidator.get_required_fields(schema)
        assert len(required) == 2
        assert "name" in required
        assert "email" in required
        assert "age" not in required

    def test_get_required_fields_empty(self):
        """Test schema with no required fields."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        required = SchemaValidator.get_required_fields(schema)
        assert len(required) == 0

    def test_validate_with_details(self):
        """Test detailed validation results."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }
        data = {"name": 123, "age": "invalid"}

        result = SchemaValidator.validate_with_details(data, schema)
        assert result["valid"] is False
        assert len(result["errors"]) >= 1
        assert result["data"] == data


class TestSchemaValidatorErrorFeedback:
    """Test error feedback generation."""

    def test_create_error_feedback(self):
        """Test error feedback message generation."""
        errors = [
            {"path": "age", "message": "'invalid' is not of type 'number'"},
            {"path": "email", "message": "'bad-email' is not valid"},
        ]

        feedback = SchemaValidator.create_error_feedback({}, {}, errors)

        assert "age" in feedback
        assert "email" in feedback
        assert "validation errors" in feedback
        assert "corrected response" in feedback


class TestValidateOutputConvenience:
    """Test convenience function."""

    def test_validate_output_valid(self):
        """Test convenience function with valid data."""
        valid, error = validate_output(
            {"name": "John"},
            {"type": "object", "properties": {"name": {"type": "string"}}},
        )
        assert valid is True
        assert error is None

    def test_validate_output_invalid(self):
        """Test convenience function with invalid data."""
        valid, error = validate_output(
            {"name": 123},
            {"type": "object", "properties": {"name": {"type": "string"}}},
        )
        assert valid is False
        assert error is not None


class TestComplexSchemas:
    """Test complex real-world schemas."""

    def test_contract_extraction_schema(self):
        """Test contract extraction example from Stage 2.1."""
        schema = {
            "type": "object",
            "properties": {
                "penalty_amount": {"type": ["number", "null"]},
                "delivery_date": {"type": ["string", "null"], "format": "date"},
                "parties": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["parties"],
        }

        # Valid data
        data = {
            "penalty_amount": 5000.00,
            "delivery_date": "2025-12-31",
            "parties": ["Company A", "Company B"],
        }
        valid, error = SchemaValidator.validate(data, schema)
        assert valid is True

        # With nulls
        data_with_nulls = {
            "penalty_amount": None,
            "delivery_date": None,
            "parties": ["Company A"],
        }
        valid, error = SchemaValidator.validate(data_with_nulls, schema)
        assert valid is True

        # Missing required field
        data_missing = {
            "penalty_amount": 5000.00,
            "delivery_date": "2025-12-31",
            # missing 'parties'
        }
        valid, error = SchemaValidator.validate(data_missing, schema)
        assert valid is False

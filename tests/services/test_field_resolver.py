"""
Test cases for field_resolver.py

Tests field reference extraction, resolution, and validation.
"""

from src.services.field_resolver import (
    FieldResolver,
    extract_field_references,
    resolve_field_references,
)


class TestFieldReferenceExtraction:
    """Test field reference extraction."""

    def test_extract_single_field(self):
        """Test extracting single field reference."""
        prompt = "Name: {$name}"
        refs = FieldResolver.extract_field_references(prompt)
        assert refs == ["name"]

    def test_extract_multiple_fields(self):
        """Test extracting multiple field references."""
        prompt = "Name: {$name}, Age: {$age}, City: {$city}"
        refs = FieldResolver.extract_field_references(prompt)
        assert refs == ["name", "age", "city"]

    def test_extract_duplicate_fields(self):
        """Test duplicate field references (should deduplicate)."""
        prompt = "{$name} is {$age} years old. {$name} lives in {$city}."
        refs = FieldResolver.extract_field_references(prompt)
        assert refs == ["name", "age", "city"]
        assert refs.count("name") == 1  # Deduplicated

    def test_extract_no_fields(self):
        """Test prompt with no field references."""
        prompt = "This is a simple prompt with no field references"
        refs = FieldResolver.extract_field_references(prompt)
        assert refs == []

    def test_extract_empty_prompt(self):
        """Test empty prompt."""
        refs = FieldResolver.extract_field_references("")
        assert refs == []

    def test_extract_with_underscores(self):
        """Test field names with underscores."""
        prompt = "Data: {$input_data}, Type: {$field_type}"
        refs = FieldResolver.extract_field_references(prompt)
        assert "input_data" in refs
        assert "field_type" in refs


class TestFieldResolution:
    """Test field reference resolution."""

    def test_resolve_single_field(self):
        """Test resolving single field."""
        prompt = "Name: {$name}"
        inputs = {"name": "John"}
        resolved = FieldResolver.resolve(prompt, inputs)
        assert resolved == "Name: John"

    def test_resolve_multiple_fields(self):
        """Test resolving multiple fields."""
        prompt = "Name: {$name}, Age: {$age}"
        inputs = {"name": "John", "age": 30}
        resolved = FieldResolver.resolve(prompt, inputs)
        assert resolved == "Name: John, Age: 30"

    def test_resolve_missing_field_default(self):
        """Test missing field uses default (empty string)."""
        prompt = "Name: {$name}, City: {$city}"
        inputs = {"name": "John"}
        resolved = FieldResolver.resolve(prompt, inputs)
        assert resolved == "Name: John, City: "

    def test_resolve_missing_field_custom_default(self):
        """Test missing field with custom default."""
        prompt = "Name: {$name}, City: {$city}"
        inputs = {"name": "John"}
        resolved = FieldResolver.resolve(prompt, inputs, default="N/A")
        assert resolved == "Name: John, City: N/A"

    def test_resolve_numeric_value(self):
        """Test resolving numeric values."""
        prompt = "Age: {$age}"
        inputs = {"age": 30}
        resolved = FieldResolver.resolve(prompt, inputs)
        assert resolved == "Age: 30"

    def test_resolve_none_value(self):
        """Test resolving None value."""
        prompt = "Value: {$value}"
        inputs = {"value": None}
        resolved = FieldResolver.resolve(prompt, inputs)
        assert resolved == "Value: "

    def test_resolve_empty_prompt(self):
        """Test resolving empty prompt."""
        resolved = FieldResolver.resolve("", {})
        assert resolved == ""


class TestFieldValidation:
    """Test field reference validation."""

    def test_validate_all_fields_present(self):
        """Test validation when all fields are present."""
        prompt = "Name: {$name}, Age: {$age}"
        inputs = {"name": "John", "age": 30}
        valid, missing = FieldResolver.validate_fields(prompt, inputs)
        assert valid is True
        assert missing == []

    def test_validate_missing_fields(self):
        """Test validation when fields are missing."""
        prompt = "Name: {$name}, Age: {$age}, City: {$city}"
        inputs = {"name": "John"}
        valid, missing = FieldResolver.validate_fields(prompt, inputs)
        assert valid is False
        assert set(missing) == {"age", "city"}

    def test_validate_no_references(self):
        """Test validation with no field references."""
        prompt = "Simple prompt"
        inputs = {}
        valid, missing = FieldResolver.validate_fields(prompt, inputs)
        assert valid is True
        assert missing == []


class TestFieldReferenceDetection:
    """Test field reference detection."""

    def test_has_references_true(self):
        """Test detecting field references."""
        assert FieldResolver.has_field_references("{$name}") is True
        assert FieldResolver.has_field_references("Name: {$name}, Age: {$age}") is True

    def test_has_references_false(self):
        """Test no field references."""
        assert FieldResolver.has_field_references("Simple prompt") is False
        assert FieldResolver.has_field_references("") is False
        assert (
            FieldResolver.has_field_references("Use {brackets} but not field refs")
            is False
        )


class TestDictFieldResolution:
    """Test dictionary field resolution."""

    def test_resolve_dict_all_fields(self):
        """Test resolving all string fields in dict."""
        data = {"prompt": "Name: {$name}", "title": "User: {$user}", "count": 5}
        inputs = {"name": "John", "user": "john123"}
        resolved = FieldResolver.resolve_dict_fields(data, inputs)

        assert resolved["prompt"] == "Name: John"
        assert resolved["title"] == "User: john123"
        assert resolved["count"] == 5  # Non-string unchanged

    def test_resolve_dict_specific_fields(self):
        """Test resolving only specific fields."""
        data = {"prompt": "Name: {$name}", "title": "User: {$user}"}
        inputs = {"name": "John", "user": "john123"}
        resolved = FieldResolver.resolve_dict_fields(
            data, inputs, fields_to_resolve=["prompt"]
        )

        assert resolved["prompt"] == "Name: John"
        assert resolved["title"] == "User: {$user}"  # Not resolved


class TestFieldContext:
    """Test field context creation."""

    def test_create_context(self):
        """Test creating formatted field context."""
        inputs = {"name": "John", "age": 30, "city": "NYC"}
        context = FieldResolver.create_field_context(inputs)

        assert "name: John" in context
        assert "age: 30" in context
        assert "city: NYC" in context

    def test_create_context_empty(self):
        """Test creating context with empty inputs."""
        context = FieldResolver.create_field_context({})
        assert context == ""


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_extract_convenience(self):
        """Test extract_field_references convenience function."""
        refs = extract_field_references("Name: {$name}")
        assert refs == ["name"]

    def test_resolve_convenience(self):
        """Test resolve_field_references convenience function."""
        resolved = resolve_field_references("Name: {$name}", {"name": "John"})
        assert resolved == "Name: John"


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_gender_classification_example(self):
        """Test gender classification example from Stage 2.2."""
        prompt_template = "Classify gender based on:\nName: {$name}\nPerson: {$person}\n\nReturn: male, female, or unknown"
        inputs = {"name": "John", "person": "engineer"}

        # Extract references
        refs = FieldResolver.extract_field_references(prompt_template)
        assert set(refs) == {"name", "person"}

        # Resolve
        resolved = FieldResolver.resolve(prompt_template, inputs)
        assert "Name: John" in resolved
        assert "Person: engineer" in resolved

        # Validate
        valid, missing = FieldResolver.validate_fields(prompt_template, inputs)
        assert valid is True

    def test_format_field_example(self):
        """Test format field example from Stage 2.2."""
        prompt_template = "Format {$input_data} as {$field_type}.\n\nValid types: number, currency, percentage, date"
        inputs = {"input_data": "1234.56", "field_type": "currency"}

        resolved = FieldResolver.resolve(prompt_template, inputs)
        assert "Format 1234.56 as currency" in resolved

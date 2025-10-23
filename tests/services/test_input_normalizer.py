"""
Test cases for InputNormalizer service.

Tests the core functionality of normalizing various input formats
to the standard {id, data} format for batch processing.

From SPECIFICATION.md:
- Simple list: ["text1", "text2"] → [{"id": 0, "data": "text1"}, {"id": 1, "data": "text2"}]
- Dict format: [{"id": "custom", "data": "text"}] → preserved as-is
- Mixed types: Support str, int, float, dict, bool, None
"""

import pytest


@pytest.fixture
def input_normalizer():
    """
    Fixture that provides the InputNormalizer class.
    """
    from src.services.input_normalizer import InputNormalizer

    return InputNormalizer


class TestInputNormalizerBasic:
    """Basic normalization functionality."""

    def test_simple_string_list(self, input_normalizer):
        """
        Test normalizing simple string list.

        Input: ["text1", "text2", "text3"]
        Output: [{"id": 0, "data": "text1"}, {"id": 1, "data": "text2"}, {"id": 2, "data": "text3"}]
        """
        input_data = ["text1", "text2", "text3"]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 3

        assert result[0]["id"] == 0
        assert result[0]["data"] == "text1"

        assert result[1]["id"] == 1
        assert result[1]["data"] == "text2"

        assert result[2]["id"] == 2
        assert result[2]["data"] == "text3"

    def test_already_normalized_dict_format(self, input_normalizer):
        """
        Test that already normalized dicts are preserved.

        Input: [{"id": "custom", "data": "text"}]
        Output: [{"id": "custom", "data": "text"}] (unchanged)
        """
        input_data = [
            {"id": "custom_1", "data": "text1"},
            {"id": 0, "data": "text2"},
            {"id": "article_1", "data": "text3"},
        ]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 3

        assert result[0]["id"] == "custom_1"
        assert result[0]["data"] == "text1"

        assert result[1]["id"] == 0
        assert result[1]["data"] == "text2"

        assert result[2]["id"] == "article_1"
        assert result[2]["data"] == "text3"

    def test_empty_list(self, input_normalizer):
        """Test normalizing empty list."""
        result = input_normalizer.normalize([])
        assert result == []

    def test_single_item(self, input_normalizer):
        """Test normalizing single item."""
        result = input_normalizer.normalize(["single"])

        assert len(result) == 1
        assert result[0]["id"] == 0
        assert result[0]["data"] == "single"


class TestInputNormalizerMixedFormats:
    """Tests for mixed input formats."""

    def test_mixed_strings_and_dicts(self, input_normalizer):
        """
        Test mixing simple strings and dict format.

        From SPECIFICATION.md example:
        Input: [
            "First article",
            {"id": "custom_1", "data": "Second article"},
            "Third article",
            {"id": 99, "data": "Fourth article"}
        ]
        """
        input_data = [
            "First article",  # Simple string → id: 0
            {"id": "custom_1", "data": "Second article"},  # Dict preserved
            "Third article",  # Simple string → id: 1
            {"id": 99, "data": "Fourth article"},  # Dict preserved
        ]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 4

        # First: auto-assigned ID 0
        assert result[0]["id"] == 0
        assert result[0]["data"] == "First article"

        # Second: custom ID preserved
        assert result[1]["id"] == "custom_1"
        assert result[1]["data"] == "Second article"

        # Third: auto-assigned ID 1 (continues from simple items only)
        assert result[2]["id"] == 1
        assert result[2]["data"] == "Third article"

        # Fourth: custom numeric ID preserved
        assert result[3]["id"] == 99
        assert result[3]["data"] == "Fourth article"

    def test_id_auto_assignment_skips_dict_items(self, input_normalizer):
        """Test that auto-assignment only counts simple items, not dicts."""
        input_data = [
            "item0",  # id: 0
            {"id": "skip", "data": "item"},  # custom id
            "item1",  # id: 1 (not 2, because dict doesn't count)
            {"id": "skip2", "data": "item"},  # custom id
            "item2",  # id: 2
        ]
        result = input_normalizer.normalize(input_data)

        assert result[0]["id"] == 0
        assert result[1]["id"] == "skip"
        assert result[2]["id"] == 1
        assert result[3]["id"] == "skip2"
        assert result[4]["id"] == 2


class TestInputNormalizerTypeHandling:
    """Tests for different data types."""

    def test_numeric_inputs(self, input_normalizer):
        """
        Test normalizing numeric inputs.

        From SPECIFICATION.md: Support int, float types
        """
        input_data = [123, 45.67, 0, -10]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 4

        assert result[0]["id"] == 0
        assert result[0]["data"] == 123

        assert result[1]["id"] == 1
        assert result[1]["data"] == 45.67

        assert result[2]["id"] == 2
        assert result[2]["data"] == 0

        assert result[3]["id"] == 3
        assert result[3]["data"] == -10

    def test_boolean_inputs(self, input_normalizer):
        """Test normalizing boolean inputs."""
        input_data = [True, False, True]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 3

        assert result[0]["data"] is True
        assert result[1]["data"] is False
        assert result[2]["data"] is True

    def test_none_inputs(self, input_normalizer):
        """Test normalizing None/null inputs."""
        input_data = [None, "text", None]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 3

        assert result[0]["data"] is None
        assert result[1]["data"] == "text"
        assert result[2]["data"] is None

    def test_mixed_types(self, input_normalizer):
        """
        Test heterogeneous list with different types.

        From SPECIFICATION.md: "Type flexibility: Support heterogeneous input types"
        """
        input_data = ["string", 123, 45.67, True, None, {"nested": "dict"}]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 6

        assert result[0]["data"] == "string"
        assert result[1]["data"] == 123
        assert result[2]["data"] == 45.67
        assert result[3]["data"] is True
        assert result[4]["data"] is None
        assert result[5]["data"] == {"nested": "dict"}


class TestInputNormalizerDictVariations:
    """Tests for various dict input formats."""

    def test_dict_without_id_field(self, input_normalizer):
        """
        Test dict without 'id' field gets auto-assigned ID.

        Input: [{"data": "text"}]
        Should wrap entire dict as data: [{"id": 0, "data": {"data": "text"}}]
        """
        input_data = [{"data": "text1"}, {"data": "text2"}]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 2
        assert result[0]["id"] == 0
        assert result[0]["data"] == {"data": "text1"}
        assert result[1]["id"] == 1
        assert result[1]["data"] == {"data": "text2"}

    def test_dict_with_id_but_no_data_field(self, input_normalizer):
        """
        Test dict with 'id' but no 'data' field.

        Might treat whole dict as data, or raise error depending on implementation.
        """
        input_data = [{"id": "custom", "content": "some text"}]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 1
        assert result[0]["id"] == "custom"
        # Implementation choice: might wrap whole dict in data, or extract content
        assert "data" in result[0]

    def test_dict_with_extra_fields(self, input_normalizer):
        """Test dict with extra fields beyond id and data."""
        input_data = [
            {"id": "custom", "data": "text", "metadata": "extra", "timestamp": 123}
        ]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 1
        assert result[0]["id"] == "custom"
        assert result[0]["data"] == "text"
        # Extra fields might be preserved or stripped depending on implementation

    def test_nested_dict_as_data(self, input_normalizer):
        """Test dict with nested object as data."""
        input_data = [
            {"id": 0, "data": {"nested": "content", "more": {"deeply": "nested"}}}
        ]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 1
        assert result[0]["id"] == 0
        assert isinstance(result[0]["data"], dict)
        assert result[0]["data"]["nested"] == "content"


class TestInputNormalizerEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_unicode_strings(self, input_normalizer):
        """Test normalizing unicode strings."""
        input_data = ["Hello", "世界", "مرحبا", "🚀"]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 4
        assert result[0]["data"] == "Hello"
        assert result[1]["data"] == "世界"
        assert result[2]["data"] == "مرحبا"
        assert result[3]["data"] == "🚀"

    def test_empty_strings(self, input_normalizer):
        """Test normalizing empty strings."""
        input_data = ["", "text", ""]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 3
        assert result[0]["data"] == ""
        assert result[1]["data"] == "text"
        assert result[2]["data"] == ""

    def test_very_long_list(self, input_normalizer):
        """Test normalizing large list."""
        input_data = [f"item_{i}" for i in range(1000)]
        result = input_normalizer.normalize(input_data)

        assert len(result) == 1000
        assert result[0]["id"] == 0
        assert result[999]["id"] == 999
        assert result[500]["data"] == "item_500"

    def test_duplicate_custom_ids(self, input_normalizer):
        """
        Test behavior with duplicate custom IDs.

        This might be allowed or might raise error depending on implementation.
        """
        input_data = [{"id": "dup", "data": "first"}, {"id": "dup", "data": "second"}]

        # Implementation might allow duplicates or raise error
        try:
            result = input_normalizer.normalize(input_data)
            # If allowed, both should be present
            assert len(result) == 2
            assert result[0]["id"] == "dup"
            assert result[1]["id"] == "dup"
        except ValueError:
            # Or might raise error for duplicates
            pass

    def test_invalid_id_types(self, input_normalizer):
        """Test with unusual ID types."""
        input_data = [
            {"id": None, "data": "text1"},  # None as ID
            {"id": [], "data": "text2"},  # List as ID
            {"id": {}, "data": "text3"},  # Dict as ID
        ]

        # Should either auto-assign IDs or raise error
        try:
            result = input_normalizer.normalize(input_data)
            assert len(result) == 3
        except (ValueError, TypeError):
            pass

    def test_non_list_input_raises_error(self, input_normalizer):
        """Test that non-list input raises TypeError."""
        with pytest.raises(TypeError):
            input_normalizer.normalize("not a list")

        with pytest.raises(TypeError):
            input_normalizer.normalize({"not": "list"})

        with pytest.raises(TypeError):
            input_normalizer.normalize(123)


class TestInputNormalizerPreserveOrder:
    """Tests to verify order is preserved."""

    def test_order_preserved_simple_list(self, input_normalizer):
        """Test that order is preserved for simple list."""
        input_data = ["z", "a", "m", "b"]
        result = input_normalizer.normalize(input_data)

        assert [item["data"] for item in result] == ["z", "a", "m", "b"]

    def test_order_preserved_mixed_format(self, input_normalizer):
        """Test that order is preserved for mixed format."""
        input_data = [
            "first",
            {"id": "custom", "data": "second"},
            "third",
            {"id": 99, "data": "fourth"},
        ]
        result = input_normalizer.normalize(input_data)

        assert result[0]["data"] == "first"
        assert result[1]["data"] == "second"
        assert result[2]["data"] == "third"
        assert result[3]["data"] == "fourth"

    def test_order_preserved_with_ids(self, input_normalizer):
        """Test that custom IDs don't affect order."""
        input_data = [
            {"id": "z", "data": "Last alphabetically"},
            {"id": "a", "data": "First alphabetically"},
            {"id": "m", "data": "Middle alphabetically"},
        ]
        result = input_normalizer.normalize(input_data)

        # Order should match input (z, a, m), not sorted
        assert [item["id"] for item in result] == ["z", "a", "m"]


class TestInputNormalizerOutputValidation:
    """Tests to verify output format is correct."""

    def test_output_has_required_fields(self, input_normalizer):
        """Test that all output items have 'id' and 'data' fields."""
        input_data = ["text1", 123, {"id": "custom", "data": "text2"}]
        result = input_normalizer.normalize(input_data)

        for item in result:
            assert "id" in item
            assert "data" in item
            assert isinstance(item, dict)

    def test_output_ids_are_valid_types(self, input_normalizer):
        """Test that output IDs are int or str."""
        input_data = ["text", {"id": "custom", "data": "text"}, "more"]
        result = input_normalizer.normalize(input_data)

        for item in result:
            assert isinstance(item["id"], (int, str))

    def test_output_is_list_of_dicts(self, input_normalizer):
        """Test that output is always list of dicts."""
        input_data = ["text"]
        result = input_normalizer.normalize(input_data)

        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)


class TestInputNormalizerStateless:
    """Tests to verify normalizer is stateless."""

    def test_multiple_calls_independent(self, input_normalizer):
        """Test that multiple calls don't affect each other."""
        input1 = ["a", "b"]
        input2 = ["c", "d", "e"]

        result1 = input_normalizer.normalize(input1)
        result2 = input_normalizer.normalize(input2)

        # First call should have IDs 0, 1
        assert result1[0]["id"] == 0
        assert result1[1]["id"] == 1

        # Second call should start fresh at 0, 1, 2
        assert result2[0]["id"] == 0
        assert result2[1]["id"] == 1
        assert result2[2]["id"] == 2

    def test_same_input_twice_gives_same_result(self, input_normalizer):
        """Test that normalizing same input twice gives same result."""
        input_data = ["x", "y", "z"]

        result1 = input_normalizer.normalize(input_data)
        result2 = input_normalizer.normalize(input_data)

        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

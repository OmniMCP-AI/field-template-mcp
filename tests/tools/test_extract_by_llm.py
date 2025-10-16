"""
Test cases for extract_by_llm tool.

Based on SPECIFICATION.md examples and requirements:
- Batch-first processing (always lists)
- ID tracking for input/output mapping
- Extract specific fields from unstructured text
- Support both simple list and dict format
- Support both fields parameter and response_format (structured output)
- Error handling for failed items
"""

import pytest
from typing import List, Dict, Any


@pytest.fixture
def extract_by_llm():
    """
    Fixture that provides the extract_by_llm function.
    """
    from src.tools.extract_by_llm import extract_by_llm
    return extract_by_llm


class TestExtractByLLMBasicFields:
    """Basic extraction with fields parameter."""

    @pytest.mark.asyncio
    async def test_multi_field_extraction(self, extract_by_llm):
        """
        Test 1: Extract multiple fields from text.

        From SPECIFICATION.md:
        extract_by_llm(
            input=["Article text about AI... by Wade on 2025-10-12"],
            fields=["title", "author", "date"]
        )
        """
        result = await extract_by_llm(
            input=[
                "Article text about AI advances... by Wade on 2025-10-12",
                "Tech news story about startups... by Jones on 2025-10-13"
            ],
            fields=["title", "author", "date"]
        )

        assert len(result) == 2

        # Verify first result
        assert result[0]["id"] == 0
        assert isinstance(result[0]["result"], dict)
        assert "title" in result[0]["result"]
        assert "author" in result[0]["result"]
        assert "date" in result[0]["result"]

        # Semantic checks
        assert "Wade" in result[0]["result"]["author"]
        assert "2025-10-12" in result[0]["result"]["date"]

        # Verify second result
        assert result[1]["id"] == 1
        assert "Jones" in result[1]["result"]["author"]
        assert "2025-10-13" in result[1]["result"]["date"]

    @pytest.mark.asyncio
    async def test_single_field_extraction_returns_dict(self, extract_by_llm):
        """
        Test 2: Single field extraction still returns dict.

        From SPECIFICATION.md:
        extract_by_llm(
            input=["Long article... nvidia hit all time high... by Wade..."],
            fields=["title"]
        )
        → [{"id": 0, "result": {"title": "nvidia hit all time high"}}]
        """
        result = await extract_by_llm(
            input=["Long article... nvidia hit all time high... by Wade..."],
            fields=["title"]
        )

        assert len(result) == 1
        assert result[0]["id"] == 0

        # Single field still returns dict (not string)
        assert isinstance(result[0]["result"], dict)
        assert "title" in result[0]["result"]
        assert "nvidia" in result[0]["result"]["title"].lower()

    @pytest.mark.asyncio
    async def test_explicit_ids(self, extract_by_llm):
        """
        Test 3: Extraction with explicit IDs.

        From SPECIFICATION.md:
        extract_by_llm(
            input=[
                {"id": "article_1", "data": "Long article text..."},
                {"id": "article_2", "data": "Another article..."}
            ],
            fields=["title"]
        )
        """
        result = await extract_by_llm(
            input=[
                {"id": "article_1", "data": "Long article about AI..."},
                {"id": "article_2", "data": "Another article about tech..."}
            ],
            fields=["title"]
        )

        assert len(result) == 2
        assert result[0]["id"] == "article_1"
        assert result[1]["id"] == "article_2"

        assert isinstance(result[0]["result"], dict)
        assert isinstance(result[1]["result"], dict)


class TestExtractByLLMWithArgs:
    """Tests with args parameter for configuration."""

    @pytest.mark.asyncio
    async def test_with_custom_prompt_instructions(self, extract_by_llm):
        """
        Test 4: Custom extraction instructions.

        From SPECIFICATION.md:
        extract_by_llm(
            input=["Article with multiple people mentioned..."],
            fields=["primary_author"],
            args={"prompt": "Extract only the primary author, not co-authors"}
        )
        """
        result = await extract_by_llm(
            input=["Article by John Doe with contributions from Jane Smith and Bob Wilson"],
            fields=["primary_author"],
            args={"prompt": "Extract only the primary author (first mentioned), not co-authors"}
        )

        assert len(result) == 1
        assert "primary_author" in result[0]["result"]
        # Should only extract John Doe, not others
        assert "John Doe" in result[0]["result"]["primary_author"]
        assert "Jane" not in result[0]["result"]["primary_author"]

    @pytest.mark.asyncio
    async def test_custom_model_and_temperature(self, extract_by_llm):
        """Test custom model and temperature."""
        result = await extract_by_llm(
            input=["Article about tech"],
            fields=["title"],
            args={
                "model": "gpt-4o-mini",
                "temperature": 0,
                "max_tokens": 500
            }
        )

        assert len(result) == 1
        assert isinstance(result[0]["result"], dict)

    @pytest.mark.asyncio
    async def test_fallback_value_on_failure(self, extract_by_llm):
        """Test fallback value when extraction fails."""
        result = await extract_by_llm(
            input=["Text with no author information"],
            fields=["author", "date"],
            args={"fallback": "N/A"}
        )

        assert len(result) == 1
        # Failed extractions should use fallback
        assert result[0]["result"]["author"] == "N/A" or result[0]["result"]["author"] is None


class TestExtractByLLMStructuredOutput:
    """Tests with response_format (structured output)."""

    @pytest.mark.asyncio
    async def test_response_format_with_arrays(self, extract_by_llm):
        """
        Test 5: Structured output with array fields.

        From SPECIFICATION.md:
        extract_by_llm(
            input=["Article with multiple authors and tags"],
            response_format={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "authors": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["title", "authors"]
            }
        )
        """
        result = await extract_by_llm(
            input=["Article about AI titled 'Machine Learning Advances' by Wade and Smith. Tags: AI, tech, ML"],
            response_format={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "authors": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "published_date": {
                        "type": "string",
                        "format": "date"
                    }
                },
                "required": ["title", "authors"]
            }
        )

        assert len(result) == 1
        assert isinstance(result[0]["result"], dict)

        # Required fields
        assert "title" in result[0]["result"]
        assert "authors" in result[0]["result"]

        # Authors should be array
        assert isinstance(result[0]["result"]["authors"], list)
        assert "Wade" in result[0]["result"]["authors"]
        assert "Smith" in result[0]["result"]["authors"]

        # Tags should be array
        assert "tags" in result[0]["result"]
        assert isinstance(result[0]["result"]["tags"], list)
        assert "AI" in result[0]["result"]["tags"]

    @pytest.mark.asyncio
    async def test_response_format_nested_objects(self, extract_by_llm):
        """
        Test 6: Complex nested object extraction.

        From SPECIFICATION.md:
        extract_by_llm(
            input=["iPhone 15 Pro - $999 - In stock - 256GB, 512GB - Color: Blue, Black - Rating: 4.8 (1234 reviews)"],
            response_format={...nested structure...}
        )
        """
        result = await extract_by_llm(
            input=["iPhone 15 Pro - $999 - In stock - 256GB, 512GB - Color: Blue, Black - Rating: 4.8 (1234 reviews)"],
            response_format={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "availability": {
                        "type": "string",
                        "enum": ["in_stock", "out_of_stock", "preorder"]
                    },
                    "variants": {
                        "type": "object",
                        "properties": {
                            "storage": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "colors": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "rating": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "number", "minimum": 0, "maximum": 5},
                            "review_count": {"type": "integer", "minimum": 0}
                        }
                    }
                },
                "required": ["name", "price"]
            }
        )

        assert len(result) == 1
        res = result[0]["result"]

        # Required fields
        assert res["name"] == "iPhone 15 Pro"
        assert res["price"] == 999

        # Enum validation
        assert res["availability"] == "in_stock"

        # Nested objects
        assert isinstance(res["variants"], dict)
        assert res["variants"]["storage"] == ["256GB", "512GB"]
        assert set(res["variants"]["colors"]) == {"Blue", "Black"}

        assert isinstance(res["rating"], dict)
        assert res["rating"]["score"] == 4.8
        assert res["rating"]["review_count"] == 1234

    @pytest.mark.asyncio
    async def test_response_format_no_fields_needed(self, extract_by_llm):
        """
        Test that with response_format, fields parameter is optional.

        From SPECIFICATION.md:
        "Note: No fields parameter needed - schema defines everything!"
        """
        result = await extract_by_llm(
            input=["Article by Wade on 2025-10-12"],
            # No fields parameter!
            response_format={
                "type": "object",
                "properties": {
                    "author": {"type": "string"},
                    "date": {"type": "string"}
                },
                "required": ["author", "date"]
            }
        )

        assert len(result) == 1
        assert "author" in result[0]["result"]
        assert "date" in result[0]["result"]

    @pytest.mark.asyncio
    async def test_fields_and_response_format_both_provided(self, extract_by_llm):
        """Test that response_format takes precedence if both provided."""
        result = await extract_by_llm(
            input=["Article by Wade"],
            fields=["title"],  # Provide fields
            response_format={  # But also provide response_format
                "type": "object",
                "properties": {
                    "author": {"type": "string"}
                },
                "required": ["author"]
            }
        )

        assert len(result) == 1
        # response_format should take precedence
        assert "author" in result[0]["result"]


class TestExtractByLLMBatchProcessing:
    """Tests for batch processing capabilities."""

    @pytest.mark.asyncio
    async def test_large_batch_extraction(self, extract_by_llm):
        """Test batch extraction with many items."""
        inputs = [f"Article {i} by Author{i} on 2025-10-{10+i}" for i in range(50)]

        result = await extract_by_llm(
            input=inputs,
            fields=["author", "date"]
        )

        assert len(result) == 50

        # Verify all have IDs and results
        assert all("id" in item for item in result)
        assert all("result" in item for item in result)
        assert all(isinstance(item["result"], dict) for item in result)

        # Verify ID sequence
        assert [item["id"] for item in result] == list(range(50))

        # Spot check a few
        assert "Author0" in result[0]["result"]["author"]
        assert "Author25" in result[25]["result"]["author"]

    @pytest.mark.asyncio
    async def test_mixed_input_formats(self, extract_by_llm):
        """Test mixing simple strings and dicts with IDs."""
        result = await extract_by_llm(
            input=[
                "Article by Wade",  # Simple string
                {"id": "custom_1", "data": "Article by Jones"},  # Custom ID
                "Article by Smith",  # Simple string
                {"id": 99, "data": "Article by Brown"}  # Numeric custom ID
            ],
            fields=["author"]
        )

        assert len(result) == 4

        # Verify IDs
        assert result[0]["id"] == 0
        assert result[1]["id"] == "custom_1"
        assert result[2]["id"] == 1
        assert result[3]["id"] == 99

    @pytest.mark.asyncio
    async def test_preserve_order(self, extract_by_llm):
        """Test that output order matches input order."""
        input_data = [
            {"id": "z", "data": "Article by Wade"},
            {"id": "a", "data": "Article by Jones"},
            {"id": "m", "data": "Article by Smith"}
        ]

        result = await extract_by_llm(
            input=input_data,
            fields=["author"]
        )

        # Order should match (z, a, m)
        assert [item["id"] for item in result] == ["z", "a", "m"]


class TestExtractByLLMErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_extraction_failure(self, extract_by_llm):
        """Test handling when extraction fails."""
        result = await extract_by_llm(
            input=[
                "Valid article by Wade on 2025-10-12",
                "Invalid content with no extractable info",
                "Another valid article by Jones"
            ],
            fields=["author", "date"]
        )

        assert len(result) == 3

        # First should succeed
        assert result[0]["result"] is not None
        assert "author" in result[0]["result"]

        # Second might fail
        assert (
            "error" in result[1] or
            result[1]["result"]["author"] is None or
            result[1]["result"]["author"] == ""
        )

        # Third should succeed
        assert result[2]["result"] is not None

    @pytest.mark.asyncio
    async def test_empty_input_list(self, extract_by_llm):
        """Test with empty input list."""
        result = await extract_by_llm(
            input=[],
            fields=["title"]
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_missing_both_fields_and_response_format(self, extract_by_llm):
        """Test that missing both fields and response_format raises error."""
        with pytest.raises(ValueError, match="fields.*response_format"):
            await extract_by_llm(
                input=["Some text"]
                # Missing both fields and response_format
            )

    @pytest.mark.asyncio
    async def test_invalid_response_format_schema(self, extract_by_llm):
        """Test with invalid JSON schema in response_format."""
        with pytest.raises(ValueError):
            await extract_by_llm(
                input=["Text"],
                response_format={
                    "invalid": "schema"  # Not valid JSON Schema
                }
            )

    @pytest.mark.asyncio
    async def test_empty_fields_list(self, extract_by_llm):
        """Test with empty fields list."""
        with pytest.raises(ValueError, match="fields.*empty"):
            await extract_by_llm(
                input=["Text"],
                fields=[]  # Empty list
            )

    @pytest.mark.asyncio
    async def test_invalid_input_type(self, extract_by_llm):
        """Test that non-list input raises error."""
        with pytest.raises(TypeError):
            await extract_by_llm(
                input="Not a list",
                fields=["title"]
            )


class TestExtractByLLMEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_extract_from_structured_dict_input(self, extract_by_llm):
        """Test extraction from dict input (not just string)."""
        result = await extract_by_llm(
            input=[
                {"id": 0, "data": {"text": "Article by Wade", "metadata": "extra"}},
            ],
            fields=["author"]
        )

        assert len(result) == 1
        # Should handle dict input by converting to string or extracting text field

    @pytest.mark.asyncio
    async def test_extract_from_numeric_input(self, extract_by_llm):
        """Test extraction from numeric input (coerced to string)."""
        result = await extract_by_llm(
            input=[12345],
            fields=["number_type"]
        )

        assert len(result) == 1
        # Should handle numeric input

    @pytest.mark.asyncio
    async def test_unicode_content(self, extract_by_llm):
        """Test extraction with unicode content."""
        result = await extract_by_llm(
            input=["文章作者：张三，日期：2025-10-12"],
            fields=["author", "date"]
        )

        assert len(result) == 1
        assert "张三" in result[0]["result"]["author"]

    @pytest.mark.asyncio
    async def test_very_long_text(self, extract_by_llm):
        """Test extraction from very long text."""
        long_text = "Article by Wade. " * 1000 + "Published on 2025-10-12"

        result = await extract_by_llm(
            input=[long_text],
            fields=["author", "date"]
        )

        assert len(result) == 1
        assert "Wade" in result[0]["result"]["author"]
        assert "2025-10-12" in result[0]["result"]["date"]

    @pytest.mark.asyncio
    async def test_extract_multiple_values_of_same_field(self, extract_by_llm):
        """Test extracting field that appears multiple times."""
        result = await extract_by_llm(
            input=["Co-authored by Wade, Jones, and Smith"],
            response_format={
                "type": "object",
                "properties": {
                    "authors": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["authors"]
            }
        )

        assert len(result) == 1
        assert len(result[0]["result"]["authors"]) == 3
        assert "Wade" in result[0]["result"]["authors"]
        assert "Jones" in result[0]["result"]["authors"]
        assert "Smith" in result[0]["result"]["authors"]

    @pytest.mark.asyncio
    async def test_extract_with_type_constraints(self, extract_by_llm):
        """Test that type constraints are enforced."""
        result = await extract_by_llm(
            input=["Price: $999, Rating: 4.5 stars, In stock"],
            response_format={
                "type": "object",
                "properties": {
                    "price": {"type": "number"},
                    "rating": {"type": "number", "minimum": 0, "maximum": 5},
                    "in_stock": {"type": "boolean"}
                }
            }
        )

        assert len(result) == 1
        assert isinstance(result[0]["result"]["price"], (int, float))
        assert result[0]["result"]["price"] == 999
        assert isinstance(result[0]["result"]["rating"], (int, float))
        assert 0 <= result[0]["result"]["rating"] <= 5
        assert isinstance(result[0]["result"]["in_stock"], bool)
        assert result[0]["result"]["in_stock"] is True

    @pytest.mark.asyncio
    async def test_optional_vs_required_fields(self, extract_by_llm):
        """Test that required fields are enforced."""
        result = await extract_by_llm(
            input=["Article by Wade"],  # No date
            response_format={
                "type": "object",
                "properties": {
                    "author": {"type": "string"},
                    "date": {"type": "string"}
                },
                "required": ["author"]  # Only author required
            }
        )

        assert len(result) == 1
        # Author is required
        assert "author" in result[0]["result"]
        assert result[0]["result"]["author"] is not None

        # Date is optional, might be null
        assert "date" in result[0]["result"] or result[0]["result"].get("date") is None

    @pytest.mark.asyncio
    async def test_extract_with_enum_constraint(self, extract_by_llm):
        """Test enum constraint in response_format."""
        result = await extract_by_llm(
            input=["Product is currently in stock"],
            response_format={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["in_stock", "out_of_stock", "preorder"]
                    }
                },
                "required": ["status"]
            }
        )

        assert len(result) == 1
        assert result[0]["result"]["status"] in ["in_stock", "out_of_stock", "preorder"]
        assert result[0]["result"]["status"] == "in_stock"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

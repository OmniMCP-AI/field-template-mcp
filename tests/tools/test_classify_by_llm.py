"""
Test cases for classify_by_llm tool.

Based on SPECIFICATION.md examples and requirements:
- Batch-first processing (always lists)
- ID tracking for input/output mapping
- Mutually exclusive classification (exactly ONE category)
- Support both simple list and dict format
- Error handling for failed items
"""

import pytest
from typing import List, Dict, Any


@pytest.fixture
def classify_by_llm():
    """
    Fixture that provides the classify_by_llm function.
    """
    from src.tools.classify_by_llm import classify_by_llm
    return classify_by_llm


class TestClassifyByLLMBasic:
    """Basic classification functionality tests."""

    @pytest.mark.asyncio
    async def test_basic_classification_with_explicit_ids(self, classify_by_llm):
        """
        Test 1: Basic classification with explicit IDs.

        From SPECIFICATION.md:
        classify_by_llm(
            input=[
                {"id": 0, "data": "What to know about Trump's $20B bailout for Argentina"},
                {"id": 1, "data": "Lakers win championship"}
            ],
            categories=["entertainment", "economy", "policy", "sports"]
        )
        """
        result = await classify_by_llm(
            input=[
                {"id": 0, "data": "What to know about Trump's $20B bailout for Argentina"},
                {"id": 1, "data": "Lakers win championship"}
            ],
            categories=["entertainment", "economy", "policy", "sports"]
        )

        # Verify structure
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify first result
        assert result[0]["id"] == 0
        assert result[0]["result"] in ["entertainment", "economy", "policy", "sports"]
        assert "error" not in result[0] or result[0]["error"] is None

        # Verify second result
        assert result[1]["id"] == 1
        assert result[1]["result"] in ["entertainment", "economy", "policy", "sports"]
        assert "error" not in result[1] or result[1]["error"] is None

        # Verify semantic correctness (if LLM works correctly)
        # Note: These might fail with simple mock, but should pass with real LLM
        assert result[0]["result"] in ["economy", "policy"]  # Argentina bailout
        assert result[1]["result"] == "sports"  # Lakers

    @pytest.mark.asyncio
    async def test_simple_list_auto_assigned_ids(self, classify_by_llm):
        """
        Test 2: Simple list input with auto-assigned IDs.

        From SPECIFICATION.md:
        classify_by_llm(
            input=["Apple releases new iPhone", "Lakers win game"],
            categories=["tech", "sports", "politics"]
        )
        """
        result = await classify_by_llm(
            input=["Apple releases new iPhone", "Lakers win game"],
            categories=["tech", "sports", "politics"]
        )

        assert len(result) == 2

        # Auto-assigned IDs should be 0, 1
        assert result[0]["id"] == 0
        assert result[1]["id"] == 1

        # Verify categories
        assert result[0]["result"] in ["tech", "sports", "politics"]
        assert result[1]["result"] in ["tech", "sports", "politics"]

        # Semantic check
        assert result[0]["result"] == "tech"
        assert result[1]["result"] == "sports"

    @pytest.mark.asyncio
    async def test_single_item_classification(self, classify_by_llm):
        """Test classification with single item (still returns list)."""
        result = await classify_by_llm(
            input=["Bitcoin reaches new all-time high"],
            categories=["tech", "finance", "sports", "entertainment"]
        )

        assert len(result) == 1
        assert result[0]["id"] == 0
        assert result[0]["result"] in ["tech", "finance", "sports", "entertainment"]
        assert result[0]["result"] in ["tech", "finance"]  # Should be one of these


class TestClassifyByLLMWithPrompt:
    """Tests with custom prompts for context."""

    @pytest.mark.asyncio
    async def test_with_custom_prompt(self, classify_by_llm):
        """
        Test 3: Classification with custom prompt.

        From SPECIFICATION.md:
        classify_by_llm(
            input=["Article mentions both AI and policy but focuses on regulation"],
            categories=["tech", "policy", "business"],
            prompt="Classify based on the primary focus, not just mentions"
        )
        """
        result = await classify_by_llm(
            input=["Article mentions both AI and policy but focuses on regulation"],
            categories=["tech", "policy", "business"],
            prompt="Classify based on the primary focus, not just mentions"
        )

        assert len(result) == 1
        assert result[0]["result"] == "policy"  # Should focus on regulation, not AI

    @pytest.mark.asyncio
    async def test_ambiguous_content_with_guidance(self, classify_by_llm):
        """Test that prompt helps with ambiguous content."""
        result = await classify_by_llm(
            input=["Startup raises $50M for AI product"],
            categories=["tech", "business", "finance"],
            prompt="Focus on the main action or event"
        )

        assert len(result) == 1
        # Could be business (fundraising) or tech (AI product)
        # Prompt should guide to focus on the action (fundraising)
        assert result[0]["result"] in ["business", "finance"]


class TestClassifyByLLMWithArgs:
    """Tests with args parameter for configuration."""

    @pytest.mark.asyncio
    async def test_with_confidence_scores(self, classify_by_llm):
        """
        Test 4: Classification with confidence scores.

        From SPECIFICATION.md:
        classify_by_llm(
            input=[{"id": "article_1", "data": "Apple releases new iPhone"}],
            categories=["tech", "business", "sports"],
            args={"include_scores": True}
        )
        """
        result = await classify_by_llm(
            input=[{"id": "article_1", "data": "Apple releases new iPhone"}],
            categories=["tech", "business", "sports"],
            args={"include_scores": True}
        )

        assert len(result) == 1
        assert result[0]["id"] == "article_1"

        # With include_scores=True, result should be a dict
        assert isinstance(result[0]["result"], dict)
        assert "category" in result[0]["result"]
        assert "score" in result[0]["result"]

        assert result[0]["result"]["category"] in ["tech", "business", "sports"]
        assert isinstance(result[0]["result"]["score"], (int, float))
        assert 0 <= result[0]["result"]["score"] <= 1

    @pytest.mark.asyncio
    async def test_allow_none_for_no_match(self, classify_by_llm):
        """
        Test 5: Handle no good match with allow_none.

        From SPECIFICATION.md:
        classify_by_llm(
            input=["Random unrelated content"],
            categories=["tech", "sports", "politics"],
            args={"allow_none": True}
        )
        """
        result = await classify_by_llm(
            input=["Random unrelated content about gardening"],
            categories=["tech", "sports", "politics"],
            args={"allow_none": True}
        )

        assert len(result) == 1
        assert result[0]["result"] is None

    @pytest.mark.asyncio
    async def test_fallback_category(self, classify_by_llm):
        """
        Test 6: Use fallback category when no good match.

        From SPECIFICATION.md:
        classify_by_llm(
            input=["Random unrelated content"],
            categories=["tech", "sports", "politics"],
            args={"fallback_category": "other"}
        )
        """
        result = await classify_by_llm(
            input=["Random unrelated content about cooking"],
            categories=["tech", "sports", "politics"],
            args={"fallback_category": "other"}
        )

        assert len(result) == 1
        assert result[0]["result"] == "other"

    @pytest.mark.asyncio
    async def test_custom_model_and_temperature(self, classify_by_llm):
        """Test custom model and temperature in args."""
        result = await classify_by_llm(
            input=["Tech news article"],
            categories=["tech", "business"],
            args={
                "model": "gpt-4o-mini",
                "temperature": 0.1
            }
        )

        assert len(result) == 1
        assert result[0]["result"] in ["tech", "business"]


class TestClassifyByLLMErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_partial_failure(self, classify_by_llm):
        """
        Test 10: Error handling - some items fail.

        From SPECIFICATION.md:
        # Should have error marker for failed item
        """
        result = await classify_by_llm(
            input=[
                "Valid tech content",
                "",  # Empty string might fail
                "Valid sports content"
            ],
            categories=["tech", "sports"]
        )

        assert len(result) == 3

        # First and third should succeed
        assert result[0]["result"] is not None
        assert result[2]["result"] is not None

        # Second might have error (or fallback result)
        # At least one of these should be true:
        assert (
            "error" in result[1] and result[1]["error"] is not None
        ) or (
            result[1]["result"] is not None
        )

    @pytest.mark.asyncio
    async def test_empty_input_list(self, classify_by_llm):
        """Test with empty input list."""
        result = await classify_by_llm(
            input=[],
            categories=["tech", "sports"]
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_single_category_error(self, classify_by_llm):
        """Test that single category raises error (need at least 2)."""
        with pytest.raises(ValueError, match="at least 2 categories"):
            await classify_by_llm(
                input=["Some content"],
                categories=["tech"]  # Only 1 category
            )

    @pytest.mark.asyncio
    async def test_missing_categories_error(self, classify_by_llm):
        """Test that missing categories raises error."""
        with pytest.raises((TypeError, ValueError)):
            await classify_by_llm(
                input=["Some content"]
                # Missing categories parameter
            )

    @pytest.mark.asyncio
    async def test_invalid_input_type(self, classify_by_llm):
        """Test that non-list input raises error."""
        with pytest.raises(TypeError):
            await classify_by_llm(
                input="Not a list",  # Should be list
                categories=["tech", "sports"]
            )


class TestClassifyByLLMBatchProcessing:
    """Tests for batch processing capabilities."""

    @pytest.mark.asyncio
    async def test_large_batch(self, classify_by_llm):
        """
        Test 11: Batch processing with 100 items.

        From SPECIFICATION.md:
        result = await tag_by_llm(
            input=[f"Article {i} about tech" for i in range(100)],
            tags=["tech", "business", "sports"]
        )
        """
        result = await classify_by_llm(
            input=[f"Article {i} about technology" for i in range(100)],
            categories=["tech", "business", "sports"]
        )

        assert len(result) == 100

        # Verify all have IDs
        assert all("id" in item for item in result)

        # Verify all have results (or errors)
        assert all(
            "result" in item or "error" in item
            for item in result
        )

        # Verify ID sequence
        assert [item["id"] for item in result] == list(range(100))

    @pytest.mark.asyncio
    async def test_mixed_types_in_batch(self, classify_by_llm):
        """Test batch with mixed input types (string, dict with id)."""
        result = await classify_by_llm(
            input=[
                "First article",  # String
                {"id": "custom_1", "data": "Second article"},  # Dict with custom ID
                "Third article",  # String
                {"id": 99, "data": "Fourth article"}  # Dict with numeric ID
            ],
            categories=["tech", "sports", "business"]
        )

        assert len(result) == 4

        # Verify IDs
        assert result[0]["id"] == 0  # Auto-assigned
        assert result[1]["id"] == "custom_1"  # Custom string ID
        assert result[2]["id"] == 1  # Auto-assigned (continues from 0)
        assert result[3]["id"] == 99  # Custom numeric ID

    @pytest.mark.asyncio
    async def test_preserve_order(self, classify_by_llm):
        """Test that output order matches input order."""
        input_data = [
            {"id": "z", "data": "Last alphabetically"},
            {"id": "a", "data": "First alphabetically"},
            {"id": "m", "data": "Middle alphabetically"}
        ]

        result = await classify_by_llm(
            input=input_data,
            categories=["tech", "sports"]
        )

        # Output order should match input order (z, a, m)
        assert [item["id"] for item in result] == ["z", "a", "m"]


class TestClassifyByLLMEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_numeric_input_data(self, classify_by_llm):
        """Test classification with numeric input (should be coerced to string)."""
        result = await classify_by_llm(
            input=[12345, 67890],
            categories=["even", "odd"]
        )

        assert len(result) == 2
        # Should handle numeric input gracefully

    @pytest.mark.asyncio
    async def test_very_long_text(self, classify_by_llm):
        """Test with very long input text."""
        long_text = "Technology innovation " * 1000  # Very long

        result = await classify_by_llm(
            input=[long_text],
            categories=["tech", "sports"]
        )

        assert len(result) == 1
        assert result[0]["result"] in ["tech", "sports"]

    @pytest.mark.asyncio
    async def test_unicode_and_special_chars(self, classify_by_llm):
        """Test with unicode and special characters."""
        result = await classify_by_llm(
            input=[
                "科技新闻 (Tech news in Chinese)",
                "Café ☕ opens new location",
                "🚀 SpaceX launch"
            ],
            categories=["tech", "business", "food", "space"]
        )

        assert len(result) == 3
        assert all("result" in item for item in result)

    @pytest.mark.asyncio
    async def test_categories_with_spaces_and_special_chars(self, classify_by_llm):
        """Test categories with spaces and special characters."""
        result = await classify_by_llm(
            input=["Article about AI"],
            categories=["Machine Learning", "Web Dev", "Mobile Apps"]
        )

        assert len(result) == 1
        assert result[0]["result"] in ["Machine Learning", "Web Dev", "Mobile Apps"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

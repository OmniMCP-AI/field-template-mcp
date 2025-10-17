"""
Test cases for classify_by_llm tool.

Simplified single input/output format:
- Input: single string (not array)
- Categories: comma-separated string (not array)
- Output: single category string (not array)
"""

import pytest


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
    async def test_basic_classification(self, classify_by_llm):
        """Test basic single input classification."""
        result = await classify_by_llm(
            input="What to know about Trump's $20B bailout for Argentina",
            categories="entertainment,economy,policy,sports"
        )

        # Verify result is a string
        assert isinstance(result, str)
        assert result in ["entertainment", "economy", "policy", "sports"]
        # Semantic check
        assert result in ["economy", "policy"]

    @pytest.mark.asyncio
    async def test_simple_classification(self, classify_by_llm):
        """Test simple classification."""
        result = await classify_by_llm(
            input="Apple releases new iPhone",
            categories="tech,sports,politics"
        )

        assert isinstance(result, str)
        assert result in ["tech", "sports", "politics"]
        assert result == "tech"

    @pytest.mark.asyncio
    async def test_another_classification(self, classify_by_llm):
        """Test another classification."""
        result = await classify_by_llm(
            input="Lakers win game",
            categories="tech,sports,politics"
        )

        assert isinstance(result, str)
        assert result == "sports"


class TestClassifyByLLMWithPrompt:
    """Tests with custom prompts for context."""

    @pytest.mark.asyncio
    async def test_with_custom_prompt(self, classify_by_llm):
        """Test classification with custom prompt."""
        result = await classify_by_llm(
            input="Article mentions both AI and policy but focuses on regulation",
            categories="tech,policy,business",
            prompt="Classify based on the primary focus, not just mentions"
        )

        assert isinstance(result, str)
        assert result == "policy"


class TestClassifyByLLMErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_single_category_error(self, classify_by_llm):
        """Test that single category raises error (need at least 2)."""
        with pytest.raises(ValueError, match="at least 2 categories"):
            await classify_by_llm(
                input="Some content",
                categories="tech"  # Only 1 category
            )

    @pytest.mark.asyncio
    async def test_missing_categories_error(self, classify_by_llm):
        """Test that missing categories raises error."""
        with pytest.raises((TypeError, ValueError)):
            await classify_by_llm(
                input="Some content"
                # Missing categories parameter
            )

    @pytest.mark.asyncio
    async def test_unicode_and_special_chars(self, classify_by_llm):
        """Test with unicode and special characters."""
        result = await classify_by_llm(
            input="科技新闻 (Tech news in Chinese)",
            categories="tech,business,food,space"
        )

        assert isinstance(result, str)
        assert result in ["tech", "business", "food", "space"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Test cases for extract_by_llm tool.

Simplified single input/output format:
- Input: single string (not array)
- item_to_extract: single field name (not array, not comma-separated)
- Output: plain text value (not JSON)
"""

import pytest


@pytest.fixture
def extract_by_llm():
    """
    Fixture that provides the extract_by_llm function.
    """
    from src.tools.extract_by_llm import extract_by_llm
    return extract_by_llm


class TestExtractByLLMBasic:
    """Basic extraction with single field."""

    @pytest.mark.asyncio
    async def test_extract_author(self, extract_by_llm):
        """Test extracting author field."""
        result = await extract_by_llm(
            input="Article by Wade on 2025-10-12 about AI",
            item_to_extract="author"
        )

        # Result should be a plain string
        assert isinstance(result, str)
        assert "Wade" in result

    @pytest.mark.asyncio
    async def test_extract_date(self, extract_by_llm):
        """Test extracting date field."""
        result = await extract_by_llm(
            input="Article by Wade on 2025-10-12 about AI",
            item_to_extract="date"
        )

        assert isinstance(result, str)
        assert "2025-10-12" in result

    @pytest.mark.asyncio
    async def test_extract_topic(self, extract_by_llm):
        """Test extracting topic field."""
        result = await extract_by_llm(
            input="Blog post about machine learning published yesterday",
            item_to_extract="topic"
        )

        assert isinstance(result, str)
        assert "machine learning" in result.lower()


class TestExtractByLLMWithArgs:
    """Tests with args parameter for configuration."""

    @pytest.mark.asyncio
    async def test_with_custom_prompt_instructions(self, extract_by_llm):
        """Test custom extraction instructions."""
        result = await extract_by_llm(
            input="Article by John Doe with contributions from Jane Smith and Bob Wilson",
            item_to_extract="primary_author",
            args={"prompt": "Extract only the primary author (first mentioned), not co-authors"}
        )

        assert isinstance(result, str)
        assert "John Doe" in result
        assert "Jane" not in result


class TestExtractByLLMErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_missing_items_error(self, extract_by_llm):
        """Test that missing items parameter raises error."""
        with pytest.raises((TypeError, ValueError)):
            await extract_by_llm(
                input="Some text"
                # Missing items parameter
            )

    @pytest.mark.asyncio
    async def test_unicode_content(self, extract_by_llm):
        """Test extraction with unicode content."""
        result = await extract_by_llm(
            input="文章作者：张三，日期：2025-10-12",
            item_to_extract="author"
        )

        assert isinstance(result, str)
        assert "张三" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

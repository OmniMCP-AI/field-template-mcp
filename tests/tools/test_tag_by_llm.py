"""
Test cases for tag_by_llm tool.

Simplified single input/output format:
- Input: single string (not array)
- Tags: comma-separated string (not array)
- Output: comma-separated string of relevant tags
"""

import pytest


@pytest.fixture
def tag_by_llm():
    """
    Fixture that provides the tag_by_llm function.
    """
    from src.tools.tag_by_llm import tag_by_llm
    return tag_by_llm


class TestTagByLLMBasic:
    """Basic tagging functionality tests."""

    @pytest.mark.asyncio
    async def test_basic_tagging_multiple_tags(self, tag_by_llm):
        """Test basic tagging returning multiple tags."""
        result = await tag_by_llm(
            input="Building a REST API with Python and PostgreSQL",
            tags="AI,backend,frontend,database,operations"
        )

        assert isinstance(result, str)

        # Parse comma-separated result
        result_tags = [t.strip() for t in result.split(",") if t.strip()]

        # Should return backend and database
        assert "backend" in result_tags
        assert "database" in result_tags

        # Should NOT return unrelated tags
        assert "frontend" not in result_tags
        assert "AI" not in result_tags

    @pytest.mark.asyncio
    async def test_simple_tagging(self, tag_by_llm):
        """Test simple tagging."""
        result = await tag_by_llm(
            input="Python REST API",
            tags="python,javascript,database,backend,frontend"
        )

        assert isinstance(result, str)
        result_tags = [t.strip() for t in result.split(",") if t.strip()]

        assert "python" in result_tags
        assert "backend" in result_tags

    @pytest.mark.asyncio
    async def test_no_matching_tags_empty_string(self, tag_by_llm):
        """Test that no matching tags returns empty string."""
        result = await tag_by_llm(
            input="Article about gardening and flowers",
            tags="AI,backend,frontend,database"
        )

        assert isinstance(result, str)
        assert result == "" or result.strip() == ""


class TestTagByLLMWithPrompt:
    """Tests with custom prompts for context."""

    @pytest.mark.asyncio
    async def test_with_custom_prompt(self, tag_by_llm):
        """Test tagging with custom prompt."""
        result = await tag_by_llm(
            input="Building a machine learning API with FastAPI and deploying to AWS",
            tags="python,AI,backend,frontend,cloud,database",
            prompt="Tag based on the main technologies and domains involved"
        )

        result_tags = [t.strip() for t in result.split(",") if t.strip()]

        # Should include main technologies
        assert "python" in result_tags
        assert "AI" in result_tags
        assert "backend" in result_tags
        assert "cloud" in result_tags


class TestTagByLLMErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_missing_tags_error(self, tag_by_llm):
        """Test that missing tags parameter raises error."""
        with pytest.raises((TypeError, ValueError)):
            await tag_by_llm(
                input="Some content"
                # Missing tags parameter
            )

    @pytest.mark.asyncio
    async def test_unicode_in_content(self, tag_by_llm):
        """Test with unicode characters."""
        result = await tag_by_llm(
            input="机器学习和人工智能 (Machine Learning and AI)",
            tags="AI,机器学习,backend,数据库"
        )

        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

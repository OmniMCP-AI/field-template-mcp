"""
Test cases for tag_by_llm tool.

Based on SPECIFICATION.md examples and requirements:
- Batch-first processing (always lists)
- ID tracking for input/output mapping
- Multi-label tagging (0-N tags per item, non-mutually exclusive)
- Support both simple list and dict format
- Error handling for failed items
"""

import pytest
from typing import List, Dict, Any


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
        """
        Test 1: Basic tagging returning multiple tags.

        From SPECIFICATION.md:
        tag_by_llm(
            input=[{"id": 0, "data": "Building a REST API with Python and PostgreSQL"}],
            tags=["AI", "backend", "frontend", "database", "operations"]
        )
        → [{"id": 0, "result": ["backend", "database"]}]
        """
        result = await tag_by_llm(
            input=[{"id": 0, "data": "Building a REST API with Python and PostgreSQL"}],
            tags=["AI", "backend", "frontend", "database", "operations"]
        )

        assert len(result) == 1
        assert result[0]["id"] == 0
        assert isinstance(result[0]["result"], list)

        # Should return backend and database
        assert "backend" in result[0]["result"]
        assert "database" in result[0]["result"]

        # Should NOT return unrelated tags
        assert "frontend" not in result[0]["result"]
        assert "AI" not in result[0]["result"]

    @pytest.mark.asyncio
    async def test_simple_list_auto_assigned_ids(self, tag_by_llm):
        """
        Test 2: Simple list input with auto-assigned IDs.

        From SPECIFICATION.md:
        tag_by_llm(
            input=["Python REST API", "React frontend app", "PostgreSQL database"],
            tags=["python", "javascript", "database", "backend", "frontend"]
        )
        """
        result = await tag_by_llm(
            input=["Python REST API", "React frontend app", "PostgreSQL database"],
            tags=["python", "javascript", "database", "backend", "frontend"]
        )

        assert len(result) == 3

        # Verify IDs
        assert result[0]["id"] == 0
        assert result[1]["id"] == 1
        assert result[2]["id"] == 2

        # Verify results are lists
        assert isinstance(result[0]["result"], list)
        assert isinstance(result[1]["result"], list)
        assert isinstance(result[2]["result"], list)

        # Semantic checks
        assert "python" in result[0]["result"]
        assert "backend" in result[0]["result"]

        assert "javascript" in result[1]["result"]
        assert "frontend" in result[1]["result"]

        assert "database" in result[2]["result"]

    @pytest.mark.asyncio
    async def test_no_matching_tags_empty_list(self, tag_by_llm):
        """
        Test 3: No matching tags returns empty list.

        From SPECIFICATION.md:
        tag_by_llm(
            input=["Generic unrelated content"],
            tags=["AI", "backend", "frontend"]
        )
        → [{"id": 0, "result": []}]
        """
        result = await tag_by_llm(
            input=["Article about gardening and flowers"],
            tags=["AI", "backend", "frontend", "database"]
        )

        assert len(result) == 1
        assert result[0]["result"] == []

    @pytest.mark.asyncio
    async def test_single_tag_match(self, tag_by_llm):
        """Test content that matches only one tag."""
        result = await tag_by_llm(
            input=["PostgreSQL database tutorial"],
            tags=["python", "javascript", "database", "backend", "frontend"]
        )

        assert len(result) == 1
        assert "database" in result[0]["result"]
        # Might also have backend, but definitely has database


class TestTagByLLMWithPrompt:
    """Tests with custom prompts for context."""

    @pytest.mark.asyncio
    async def test_with_custom_prompt(self, tag_by_llm):
        """
        Test 4: Tagging with custom prompt.

        From SPECIFICATION.md:
        tag_by_llm(
            input=["Building a machine learning API with FastAPI and deploying to AWS"],
            tags=["python", "AI", "backend", "frontend", "cloud", "database"],
            prompt="Tag based on the main technologies and domains involved"
        )
        """
        result = await tag_by_llm(
            input=["Building a machine learning API with FastAPI and deploying to AWS"],
            tags=["python", "AI", "backend", "frontend", "cloud", "database"],
            prompt="Tag based on the main technologies and domains involved"
        )

        assert len(result) == 1

        # Should include main technologies
        assert "python" in result[0]["result"]
        assert "AI" in result[0]["result"]
        assert "backend" in result[0]["result"]
        assert "cloud" in result[0]["result"]

        # Should NOT include unrelated
        assert "frontend" not in result[0]["result"]
        assert "database" not in result[0]["result"]

    @pytest.mark.asyncio
    async def test_prompt_for_explicit_mentions_only(self, tag_by_llm):
        """
        Test 5: Custom prompt to filter by explicit mentions.

        From SPECIFICATION.md:
        tag_by_llm(
            input=["This project needs Python, Docker, and Kubernetes experience"],
            tags=["python", "java", "docker", "kubernetes", "terraform", "ansible"],
            prompt="Tag only the explicitly required skills"
        )
        """
        result = await tag_by_llm(
            input=["This project needs Python, Docker, and Kubernetes experience"],
            tags=["python", "java", "docker", "kubernetes", "terraform", "ansible"],
            prompt="Tag only the explicitly required skills",
            args={"min_relevance": 0.8}
        )

        assert len(result) == 1

        # Should only include explicitly mentioned
        assert "python" in result[0]["result"]
        assert "docker" in result[0]["result"]
        assert "kubernetes" in result[0]["result"]

        # Should NOT include non-mentioned
        assert "java" not in result[0]["result"]
        assert "terraform" not in result[0]["result"]


class TestTagByLLMWithArgs:
    """Tests with args parameter for configuration."""

    @pytest.mark.asyncio
    async def test_max_tags_limit(self, tag_by_llm):
        """
        Test 6: Limit maximum tags with max_tags.

        From SPECIFICATION.md:
        tag_by_llm(
            input=[{"id": "article_1", "data": "Python web development tutorial"}],
            tags=["python", "java", "javascript", "go"],
            args={"max_tags": 2, "include_scores": True}
        )
        """
        result = await tag_by_llm(
            input=["Python JavaScript full-stack web development with React and Django"],
            tags=["python", "javascript", "java", "go", "rust"],
            args={"max_tags": 2}
        )

        assert len(result) == 1
        assert isinstance(result[0]["result"], list)
        assert len(result[0]["result"]) <= 2

        # Should be most relevant tags
        # Python and JavaScript should be top 2
        tags = result[0]["result"]
        assert "python" in tags or "javascript" in tags

    @pytest.mark.asyncio
    async def test_include_scores(self, tag_by_llm):
        """
        Test 7: Include relevance scores with tags.

        From SPECIFICATION.md:
        Result format with include_scores:
        [{
            "id": "article_1",
            "result": [
                {"tag": "python", "score": 0.9},
                {"tag": "javascript", "score": 0.6}
            ]
        }]
        """
        result = await tag_by_llm(
            input=[{"id": "article_1", "data": "Python web development tutorial"}],
            tags=["python", "java", "javascript", "go"],
            args={"include_scores": True, "max_tags": 2}
        )

        assert len(result) == 1
        assert result[0]["id"] == "article_1"
        assert isinstance(result[0]["result"], list)

        # Each result item should be a dict with tag and score
        for item in result[0]["result"]:
            assert isinstance(item, dict)
            assert "tag" in item
            assert "score" in item
            assert isinstance(item["tag"], str)
            assert isinstance(item["score"], (int, float))
            assert 0 <= item["score"] <= 1

        # Tags should be sorted by score (highest first)
        scores = [item["score"] for item in result[0]["result"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_min_relevance_threshold(self, tag_by_llm):
        """Test min_relevance filters low-relevance tags."""
        result = await tag_by_llm(
            input=["Python programming with brief mention of databases"],
            tags=["python", "javascript", "database", "backend"],
            args={"min_relevance": 0.7}  # Only high-relevance tags
        )

        assert len(result) == 1
        # Should include python (high relevance)
        assert "python" in result[0]["result"]
        # May or may not include database (depends on relevance score)

    @pytest.mark.asyncio
    async def test_custom_model(self, tag_by_llm):
        """Test custom model selection."""
        result = await tag_by_llm(
            input=["Tech article"],
            tags=["tech", "business"],
            args={"model": "gpt-4o-mini", "temperature": 0}
        )

        assert len(result) == 1
        assert isinstance(result[0]["result"], list)


class TestTagByLLMBatchProcessing:
    """Tests for batch processing capabilities."""

    @pytest.mark.asyncio
    async def test_multiple_inputs_with_explicit_ids(self, tag_by_llm):
        """
        Test 8: Multiple inputs with custom IDs.

        From SPECIFICATION.md:
        tag_by_llm(
            input=[
                {"id": "proj_1", "data": "Machine learning backend service"},
                {"id": "proj_2", "data": "React mobile app"}
            ],
            tags=["AI", "backend", "frontend", "mobile"]
        )
        """
        result = await tag_by_llm(
            input=[
                {"id": "proj_1", "data": "Machine learning backend service"},
                {"id": "proj_2", "data": "React mobile app"}
            ],
            tags=["AI", "backend", "frontend", "mobile"]
        )

        assert len(result) == 2

        # Verify IDs
        assert result[0]["id"] == "proj_1"
        assert result[1]["id"] == "proj_2"

        # Verify first project tags
        assert "AI" in result[0]["result"]
        assert "backend" in result[0]["result"]
        assert "mobile" not in result[0]["result"]

        # Verify second project tags
        assert "frontend" in result[1]["result"]
        assert "mobile" in result[1]["result"]
        assert "AI" not in result[1]["result"]

    @pytest.mark.asyncio
    async def test_large_batch(self, tag_by_llm):
        """Test batch processing with 100 items."""
        result = await tag_by_llm(
            input=[f"Article {i} about Python programming" for i in range(100)],
            tags=["python", "javascript", "java", "backend", "frontend"]
        )

        assert len(result) == 100

        # Verify all have IDs and results
        assert all("id" in item for item in result)
        assert all("result" in item for item in result)
        assert all(isinstance(item["result"], list) for item in result)

        # Verify ID sequence
        assert [item["id"] for item in result] == list(range(100))

        # Most should have "python" tag
        python_count = sum(1 for item in result if "python" in item["result"])
        assert python_count > 90  # At least 90% should detect "python"

    @pytest.mark.asyncio
    async def test_mixed_content_batch(self, tag_by_llm):
        """Test batch with diverse content."""
        result = await tag_by_llm(
            input=[
                "Python backend API",
                "React frontend app",
                "Machine learning model",
                "PostgreSQL database",
                "Kubernetes deployment"
            ],
            tags=["python", "javascript", "AI", "database", "backend", "frontend", "cloud"]
        )

        assert len(result) == 5

        # Each should have different tag combinations
        assert "python" in result[0]["result"]
        assert "backend" in result[0]["result"]

        assert "javascript" in result[1]["result"]
        assert "frontend" in result[1]["result"]

        assert "AI" in result[2]["result"]
        assert "database" in result[3]["result"]
        assert "cloud" in result[4]["result"]


class TestTagByLLMErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_input_list(self, tag_by_llm):
        """Test with empty input list."""
        result = await tag_by_llm(
            input=[],
            tags=["python", "javascript"]
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_empty_string_input(self, tag_by_llm):
        """Test with empty string in input."""
        result = await tag_by_llm(
            input=["", "Valid content"],
            tags=["python", "javascript"]
        )

        assert len(result) == 2

        # Empty string should return empty tags or error
        assert (
            result[0]["result"] == [] or
            ("error" in result[0] and result[0]["error"] is not None)
        )

        # Valid content should have result
        assert isinstance(result[1]["result"], list)

    @pytest.mark.asyncio
    async def test_single_tag_list(self, tag_by_llm):
        """Test with only one tag (should still work, unlike classify)."""
        result = await tag_by_llm(
            input=["Python programming"],
            tags=["python"]  # Only 1 tag is okay for tagging
        )

        assert len(result) == 1
        # Should either match or not
        assert result[0]["result"] == ["python"] or result[0]["result"] == []

    @pytest.mark.asyncio
    async def test_missing_tags_error(self, tag_by_llm):
        """Test that missing tags parameter raises error."""
        with pytest.raises((TypeError, ValueError)):
            await tag_by_llm(
                input=["Some content"]
                # Missing tags parameter
            )

    @pytest.mark.asyncio
    async def test_invalid_input_type(self, tag_by_llm):
        """Test that non-list input raises error."""
        with pytest.raises(TypeError):
            await tag_by_llm(
                input="Not a list",
                tags=["python", "javascript"]
            )

    @pytest.mark.asyncio
    async def test_partial_failure_in_batch(self, tag_by_llm):
        """Test that some items can fail without breaking batch."""
        result = await tag_by_llm(
            input=[
                "Valid content about Python",
                None,  # Might cause error
                "Valid content about JavaScript"
            ],
            tags=["python", "javascript", "java"]
        )

        assert len(result) == 3

        # First and third should succeed
        assert isinstance(result[0]["result"], list)
        assert isinstance(result[2]["result"], list)

        # Second might have error
        assert (
            "error" in result[1] or
            result[1]["result"] == []
        )


class TestTagByLLMEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_overlapping_content(self, tag_by_llm):
        """Test content that could match multiple tags."""
        result = await tag_by_llm(
            input=["Full-stack Python and JavaScript web development with databases"],
            tags=["python", "javascript", "backend", "frontend", "database", "fullstack"]
        )

        assert len(result) == 1

        # Should match multiple relevant tags
        tags = result[0]["result"]
        assert len(tags) >= 3  # Should have at least 3 tags
        assert "python" in tags
        assert "javascript" in tags

    @pytest.mark.asyncio
    async def test_tags_case_sensitivity(self, tag_by_llm):
        """Test that tag matching respects case."""
        result = await tag_by_llm(
            input=["Python programming"],
            tags=["Python", "python", "PYTHON"]  # Different cases
        )

        assert len(result) == 1
        # Should match at least one variant
        assert len(result[0]["result"]) >= 1

    @pytest.mark.asyncio
    async def test_unicode_in_tags_and_content(self, tag_by_llm):
        """Test with unicode characters."""
        result = await tag_by_llm(
            input=["机器学习和人工智能 (Machine Learning and AI)"],
            tags=["AI", "机器学习", "backend", "数据库"]
        )

        assert len(result) == 1
        assert isinstance(result[0]["result"], list)

    @pytest.mark.asyncio
    async def test_very_long_tag_list(self, tag_by_llm):
        """Test with many tags."""
        tags = [f"tag_{i}" for i in range(100)]  # 100 tags

        result = await tag_by_llm(
            input=["Content mentioning tag_5 and tag_42"],
            tags=tags
        )

        assert len(result) == 1
        # Should work with many tags
        assert isinstance(result[0]["result"], list)

    @pytest.mark.asyncio
    async def test_numeric_input_coercion(self, tag_by_llm):
        """Test tagging numeric input (coerced to string)."""
        result = await tag_by_llm(
            input=[12345, 67890],
            tags=["number", "even", "odd"]
        )

        assert len(result) == 2
        assert isinstance(result[0]["result"], list)
        assert isinstance(result[1]["result"], list)

    @pytest.mark.asyncio
    async def test_preserve_order(self, tag_by_llm):
        """Test that output order matches input order."""
        input_data = [
            {"id": "z", "data": "Python"},
            {"id": "a", "data": "JavaScript"},
            {"id": "m", "data": "Java"}
        ]

        result = await tag_by_llm(
            input=input_data,
            tags=["python", "javascript", "java"]
        )

        # Output order should match input (z, a, m)
        assert [item["id"] for item in result] == ["z", "a", "m"]

    @pytest.mark.asyncio
    async def test_all_tags_match(self, tag_by_llm):
        """Test content that matches all tags."""
        result = await tag_by_llm(
            input=["Python JavaScript Java programming languages"],
            tags=["python", "javascript", "java"]
        )

        assert len(result) == 1
        # Should return all three tags
        assert len(result[0]["result"]) == 3
        assert set(result[0]["result"]) == {"python", "javascript", "java"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

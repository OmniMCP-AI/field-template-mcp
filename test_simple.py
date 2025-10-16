#!/usr/bin/env python3
"""
Simple test script for the AI Field Template MCP tools.
Run without pytest - just plain Python async functions.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import tools
from src.tools.classify_by_llm import classify_by_llm
from src.tools.tag_by_llm import tag_by_llm
from src.tools.extract_by_llm import extract_by_llm
from src.services.input_normalizer import InputNormalizer


def print_test(name, passed, details=""):
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"  {details}")


async def test_input_normalizer():
    """Test InputNormalizer basic functionality."""
    print("\n=== Testing InputNormalizer ===")

    # Test 1: Simple string list
    result = InputNormalizer.normalize(["text1", "text2", "text3"])
    passed = (
        len(result) == 3 and
        result[0]["id"] == 0 and result[0]["data"] == "text1" and
        result[1]["id"] == 1 and result[1]["data"] == "text2" and
        result[2]["id"] == 2 and result[2]["data"] == "text3"
    )
    print_test("Simple string list normalization", passed)

    # Test 2: Dict format with explicit IDs
    result = InputNormalizer.normalize([
        {"id": "a1", "data": "content1"},
        {"id": "a2", "data": "content2"}
    ])
    passed = (
        len(result) == 2 and
        result[0]["id"] == "a1" and result[0]["data"] == "content1" and
        result[1]["id"] == "a2" and result[1]["data"] == "content2"
    )
    print_test("Dict format with explicit IDs", passed)

    # Test 3: Mixed formats
    result = InputNormalizer.normalize([
        "simple text",
        {"id": "custom", "data": "custom data"},
        123
    ])
    passed = (
        len(result) == 3 and
        result[0]["id"] == 0 and result[0]["data"] == "simple text" and
        result[1]["id"] == "custom" and result[1]["data"] == "custom data" and
        result[2]["id"] == 1 and result[2]["data"] == 123
    )
    print_test("Mixed formats", passed)


async def test_classify_by_llm():
    """Test classify_by_llm tool."""
    print("\n=== Testing classify_by_llm ===")

    # Test 1: Basic classification
    try:
        result = await classify_by_llm(
            input=["Apple releases new iPhone 15", "Lakers win NBA championship"],
            categories=["tech", "sports", "politics", "entertainment"]
        )
        passed = (
            len(result) == 2 and
            "id" in result[0] and "result" in result[0] and
            "id" in result[1] and "result" in result[1] and
            result[0]["result"] in ["tech", "sports", "politics", "entertainment"] and
            result[1]["result"] in ["tech", "sports", "politics", "entertainment"]
        )
        print_test("Basic classification", passed,
                  f"Results: [{result[0]['result']}, {result[1]['result']}]")
    except Exception as e:
        print_test("Basic classification", False, f"Error: {e}")

    # Test 2: With custom prompt
    try:
        result = await classify_by_llm(
            input=["Python machine learning tutorial"],
            categories=["programming", "hardware", "design"],
            prompt="Focus on the primary topic of the content"
        )
        passed = (
            len(result) == 1 and
            result[0]["result"] in ["programming", "hardware", "design"]
        )
        print_test("Classification with custom prompt", passed,
                  f"Result: {result[0]['result']}")
    except Exception as e:
        print_test("Classification with custom prompt", False, f"Error: {e}")


async def test_tag_by_llm():
    """Test tag_by_llm tool."""
    print("\n=== Testing tag_by_llm ===")

    # Test 1: Basic tagging
    try:
        result = await tag_by_llm(
            input=["Building a REST API with Python and PostgreSQL"],
            tags=["python", "javascript", "backend", "frontend", "database", "AI"]
        )
        passed = (
            len(result) == 1 and
            "id" in result[0] and "result" in result[0] and
            isinstance(result[0]["result"], list) and
            len(result[0]["result"]) > 0
        )
        print_test("Basic tagging", passed,
                  f"Tags: {result[0]['result']}")
    except Exception as e:
        print_test("Basic tagging", False, f"Error: {e}")

    # Test 2: Multiple inputs
    try:
        result = await tag_by_llm(
            input=["Python web scraping", "React component design"],
            tags=["python", "javascript", "backend", "frontend"]
        )
        passed = (
            len(result) == 2 and
            isinstance(result[0]["result"], list) and
            isinstance(result[1]["result"], list)
        )
        print_test("Multiple input tagging", passed,
                  f"Results: {[r['result'] for r in result]}")
    except Exception as e:
        print_test("Multiple input tagging", False, f"Error: {e}")


async def test_extract_by_llm():
    """Test extract_by_llm tool."""
    print("\n=== Testing extract_by_llm ===")

    # Test 1: Simple field extraction
    try:
        result = await extract_by_llm(
            input=["Article written by John Smith on 2025-10-12 about AI"],
            fields=["author", "date", "topic"]
        )
        passed = (
            len(result) == 1 and
            "id" in result[0] and "result" in result[0] and
            isinstance(result[0]["result"], dict) and
            "author" in result[0]["result"] and
            "date" in result[0]["result"]
        )
        print_test("Simple field extraction", passed,
                  f"Extracted: {result[0]['result']}")
    except Exception as e:
        print_test("Simple field extraction", False, f"Error: {e}")

    # Test 2: Structured output with arrays
    try:
        result = await extract_by_llm(
            input=["Authors: Wade and Smith. Tags: AI, machine learning, python"],
            response_format={
                "type": "object",
                "properties": {
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["authors", "tags"]
            }
        )
        passed = (
            len(result) == 1 and
            "authors" in result[0]["result"] and
            "tags" in result[0]["result"] and
            isinstance(result[0]["result"]["authors"], list) and
            isinstance(result[0]["result"]["tags"], list)
        )
        print_test("Structured output extraction", passed,
                  f"Extracted: {result[0]['result']}")
    except Exception as e:
        print_test("Structured output extraction", False, f"Error: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Field Template MCP - Simple Test Suite")
    print("=" * 60)

    # Test InputNormalizer (no API calls)
    await test_input_normalizer()

    # Test LLM tools (requires API key)
    print("\n" + "=" * 60)
    print("Testing LLM Tools (requires OPENAI_API_KEY)")
    print("=" * 60)

    try:
        await test_classify_by_llm()
        await test_tag_by_llm()
        await test_extract_by_llm()
    except Exception as e:
        print(f"\n✗ LLM tests failed: {e}")
        print("Make sure OPENAI_API_KEY is set in .env file")

    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

"""
Integration test to verify the dynamic tool system works end-to-end.
"""

import asyncio
from src.tools import classify_by_llm, extract_by_llm, tag_by_llm


async def test_classify():
    """Test classify_by_llm through dynamic registry."""
    result = await classify_by_llm(
        input=["Apple releases iPhone", "Lakers win game"],
        categories=["tech", "sports", "politics"]
    )
    print("✅ classify_by_llm test passed")
    print(f"   Result: {result}")
    return result


async def test_extract():
    """Test extract_by_llm through dynamic registry."""
    result = await extract_by_llm(
        input=["Article by Wade on 2025-10-12"],
        fields=["author", "date"]
    )
    print("✅ extract_by_llm test passed")
    print(f"   Result: {result}")
    return result


async def test_tag():
    """Test tag_by_llm through dynamic registry."""
    result = await tag_by_llm(
        input=["Python REST API"],
        tags=["python", "javascript", "backend", "frontend"]
    )
    print("✅ tag_by_llm test passed")
    print(f"   Result: {result}")
    return result


async def main():
    """Run all integration tests."""
    print("🧪 Running integration tests for dynamic tool system\n")

    try:
        await test_classify()
        print()
        await test_extract()
        print()
        await test_tag()
        print()
        print("🎉 All integration tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

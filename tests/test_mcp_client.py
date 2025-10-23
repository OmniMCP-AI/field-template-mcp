#!/usr/bin/env python3
"""
Field Template MCP Server Integration Tests

Test Functions:
- test_list_tools: Test MCP tool discovery
- test_classify: Test the classify tool
- test_tag: Test the tag tool
- test_extract: Test the extract tool
- test_extract_items_by_entity: Test the extract_items_by_entity tool

Usage:
    # Run all tests (local)
    python tests/test_mcp_client.py --env=local --test=all

    # Run tests on prod environment
    python tests/test_mcp_client.py --env=prod --test=all

    # Run specific test
    python tests/test_mcp_client.py --env=local --test=list_tools
    python tests/test_mcp_client.py --env=local --test=classify
    python tests/test_mcp_client.py --env=prod --test=tag
    python tests/test_mcp_client.py --env=local --test=extract
    python tests/test_mcp_client.py --env=local --test=extract_items

    # Run with custom URL
    python tests/test_mcp_client.py --env=remote --url=https://your-server.com/sse --test=all

Environment Variables Required:
- OPENAI_API_KEY (for LLM tools)
- OPENAI_BASE_URL (optional, for OpenRouter or custom endpoints)
- LLM_MODEL (optional, default: gpt-4o-mini)
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client import streamable_http

# Load environment variables
load_dotenv()


async def test_list_tools(url):
    """Test listing available MCP tools"""
    print("🚀 Testing MCP Tool Discovery")
    print("=" * 60)

    async with streamable_http.streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("\n🛠️  Listing available MCP tools")
            tools = await session.list_tools()
            print(f"✅ Found {len(tools.tools)} available tools:\n")
            for i, tool in enumerate(tools.tools, 1):
                print(f"   {i}. {tool.name}")
                print(f"      Input Schema: {tool.inputSchema}")
                print(f"      Description: {tool.description[:150]}...")
                print(f"      Output Schema: {tool.outputSchema}")
                print()

            print("✅ Tool discovery test completed!\n")


async def test_classify(url):
    """Test the classify tool"""
    print("🚀 Testing classify Tool")
    print("=" * 60)

    async with streamable_http.streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Classify news article
            print("\n📰 Test 1: Classifying news article")
            classify_res = await session.call_tool(
                "classify",
                {
                    "input_raw_text": "Apple releases new iPhone with AI features",
                    "categories": "tech,sports,politics",
                },
            )

            if classify_res.isError:
                print(
                    f"❌ Error: {classify_res.content[0].text if classify_res.content else 'Unknown error'}"
                )
            else:
                result_text = (
                    classify_res.content[0].text if classify_res.content else None
                )
                print(f"✅ Result: {result_text}")

            # Test 2: Classify with custom prompt
            print("\n📝 Test 2: Classifying with custom prompt")
            classify_res2 = await session.call_tool(
                "classify",
                {
                    "input_raw_text": "It's a sunny day",
                    "categories": "good_weather,bad_weather",
                    "prompt": "Classify weather descriptions",
                },
            )

            if classify_res2.isError:
                print(
                    f"❌ Error: {classify_res2.content[0].text if classify_res2.content else 'Unknown error'}"
                )
            else:
                result_text = (
                    classify_res2.content[0].text if classify_res2.content else None
                )
                print(f"✅ Result: {result_text}")

            print("\n✅ classify tool test completed!")


async def test_tag(url):
    """Test the tag tool"""
    print("🚀 Testing tag Tool")
    print("=" * 60)

    async with streamable_http.streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Tag programming project
            print("\n💻 Test 1: Tagging programming project")
            tag_res = await session.call_tool(
                "tag",
                {
                    "input_raw_text": "Python REST API with FastAPI",
                    "tags": "python,javascript,typescript,backend,frontend,fullstack",
                },
            )

            if tag_res.isError:
                print(
                    f"❌ Error: {tag_res.content[0].text if tag_res.content else 'Unknown error'}"
                )
            else:
                result_text = tag_res.content[0].text if tag_res.content else None
                print(f"✅ Result: {result_text}")

            # Test 2: Tag with max_tags limit
            print("\n🏷️  Test 2: Tagging with max_tags=2")
            tag_res2 = await session.call_tool(
                "tag",
                {
                    "input_raw_text": "Machine learning project with Python, TensorFlow, Docker, and REST API",
                    "tags": "python,machine-learning,docker,api,tensorflow",
                    "args": {"max_tags": 2},
                },
            )

            if tag_res2.isError:
                print(
                    f"❌ Error: {tag_res2.content[0].text if tag_res2.content else 'Unknown error'}"
                )
            else:
                result_text = tag_res2.content[0].text if tag_res2.content else None
                print(f"✅ Result: {result_text} (max 2 tags)")

            print("\n✅ tag tool test completed!")


async def test_extract(url):
    """Test the extract tool"""
    print("🚀 Testing extract Tool")
    print("=" * 60)

    async with streamable_http.streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Extract item_to_extract from text
            print("\n📄 Test 1: Extracting item_to_extract from text")
            extract_res = await session.call_tool(
                "extract",
                {
                    "input_raw_text": "Article by John Smith published on 2025-01-15 about AI",
                    # "item_to_extract": "author,date,topic"
                    "item_to_extract": "date",
                },
            )

            if extract_res.isError:
                print(
                    f"❌ Error: {extract_res.content[0].text if extract_res.content else 'Unknown error'}"
                )
            else:
                result_text = (
                    extract_res.content[0].text if extract_res.content else None
                )
                print(f"✅ Result: {result_text}")

            # Test 2: Extract another example
            print("\n🔍 Test 2: Extracting from blog post")
            extract_res2 = await session.call_tool(
                "extract",
                {
                    "input_raw_text": "Blog post by Jane Doe from 2025-02-20 covering machine learning",
                    "item_to_extract": "author",  # ,date,topic
                },
            )

            if extract_res2.isError:
                print(
                    f"❌ Error: {extract_res2.content[0].text if extract_res2.content else 'Unknown error'}"
                )
            else:
                result_text = (
                    extract_res2.content[0].text if extract_res2.content else None
                )
                print(f"✅ Result: {result_text}")

            print("\n✅ extract tool test completed!")


async def test_extract_items_by_entity(url):
    """Test the extract_items_by_entity tool"""
    print("🚀 Testing extract_items_by_entity Tool")
    print("=" * 60)

    # Read the Tesla article
    test_article_path = os.path.join(
        os.path.dirname(__file__), "test-tesla-article.txt"
    )
    with open(test_article_path, "r") as f:
        tesla_article = f.read()

    async with streamable_http.streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Extract single item for Tesla
            print("\n📊 Test 1: Extract single item (EVs sold) for Tesla")
            result1 = await session.call_tool(
                "extract_items_by_entity",
                {
                    "input": tesla_article,
                    "entity_to_extract": "Tesla",
                    "items_to_extract": "EVs sold globally",
                },
            )

            if result1.isError:
                print(
                    f"❌ Error: {result1.content[0].text if result1.content else 'Unknown error'}"
                )
            else:
                result_text = result1.content[0].text if result1.content else None
                print(f"✅ Result: {result_text}")

            # Test 2: Extract multiple items with comma-separated string
            print("\n🔋 Test 2: Extract multiple items (comma-separated) for Tesla")
            result2 = await session.call_tool(
                "extract_items_by_entity",
                {
                    "input": tesla_article,
                    "entity_to_extract": "Tesla",
                    "items_to_extract": "EVs sold globally,renewable energy usage",
                },
            )

            if result2.isError:
                print(
                    f"❌ Error: {result2.content[0].text if result2.content else 'Unknown error'}"
                )
            else:
                result_text = result2.content[0].text if result2.content else None
                print(f"✅ Result: {result_text}")

            # Test 3: Extract with date filter
            print("\n♻️  Test 3: Extract with date filter for Tesla")
            result3 = await session.call_tool(
                "extract_items_by_entity",
                {
                    "input": tesla_article,
                    "entity_to_extract": "Tesla",
                    "items_to_extract": "battery recycling throughput growth",
                    "date": "2024",
                },
            )

            if result3.isError:
                print(
                    f"❌ Error: {result3.content[0].text if result3.content else 'Unknown error'}"
                )
            else:
                result_text = result3.content[0].text if result3.content else None
                print(f"✅ Result: {result_text}")

            # Test 4: Extract multiple items including water usage and CO2
            print("\n💧 Test 4: Extract water usage and CO2 emissions for Tesla")
            result4 = await session.call_tool(
                "extract_items_by_entity",
                {
                    "input": tesla_article,
                    "entity_to_extract": "Tesla",
                    "items_to_extract": "water use per vehicle,CO2 emissions avoided",
                },
            )

            if result4.isError:
                print(
                    f"❌ Error: {result4.content[0].text if result4.content else 'Unknown error'}"
                )
            else:
                result_text = result4.content[0].text if result4.content else None
                print(f"✅ Result: {result_text}")

            print("\n✅ extract_items_by_entity tool test completed!")


async def test_all(url):
    """Run all tests"""
    print("🧪 Running ALL Tests")
    print("=" * 60)

    await test_list_tools(url)
    print("\n" + "=" * 60 + "\n")

    await test_classify(url)
    print("\n" + "=" * 60 + "\n")

    await test_tag(url)
    print("\n" + "=" * 60 + "\n")

    await test_extract(url)
    print("\n" + "=" * 60 + "\n")

    # await test_extract_items_by_entity(url)

    print("\n✅ All tests completed!")


def main():
    parser = argparse.ArgumentParser(description="Test Field Template MCP Server")
    parser.add_argument(
        "--env",
        choices=["local", "prod", "remote"],
        default="local",
        help="Environment to use: local (127.0.0.1:8322), prod (omnimcp.ai), or remote (custom URL)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="",
        help="Custom server URL (required for --env=remote)",
    )
    parser.add_argument(
        "--test",
        choices=["all", "list_tools", "classify", "tag", "extract", "extract_items"],
        default="all",
        help="Which test to run",
    )

    args = parser.parse_args()

    # Determine URL
    if args.env == "local":
        # FastMCP streamable-http uses /mcp endpoint
        url = "http://127.0.0.1:8322/mcp"
    elif args.env == "prod":
        url = "https://be-dev.omnimcp.ai/api/v1/mcp/a6ebdc49-50e7-4c54-8d2a-639f10098a63/68f1a606ca402315fcf9cc90/sse"
    elif args.env == "remote":
        if not args.url:
            print("❌ Error: --url required for remote environment")
            return
        url = args.url

    print(f"🔗 Using {args.env} environment: {url}")
    print(f"🧪 Running test: {args.test}\n")

    # Run selected test
    if args.test == "all":
        asyncio.run(test_all(url))
    elif args.test == "list_tools":
        asyncio.run(test_list_tools(url))
    elif args.test == "classify":
        asyncio.run(test_classify(url))
    elif args.test == "tag":
        asyncio.run(test_tag(url))
    elif args.test == "extract":
        asyncio.run(test_extract(url))
    elif args.test == "extract_items":
        asyncio.run(test_extract_items_by_entity(url))


if __name__ == "__main__":
    main()

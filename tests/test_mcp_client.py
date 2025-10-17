#!/usr/bin/env python3
"""
Field Template MCP Server Integration Tests

Test Functions:
- test_classify: Test the classify_by_llm tool
- test_tag: Test the tag_by_llm tool
- test_extract: Test the extract_by_llm tool

Usage:
    # Run all tests (local)
    python tests/test_mcp_client.py --env=local --test=all
    
    # Run tests on prod environment
    python tests/test_mcp_client.py --env=prod --test=all

    # Run specific test
    python tests/test_mcp_client.py --env=local --test=classify
    python tests/test_mcp_client.py --env=prod --test=tag
    python tests/test_mcp_client.py --env=local --test=extract
    
    # Run with custom URL
    python tests/test_mcp_client.py --env=remote --url=https://your-server.com/sse --test=all

Environment Variables Required:
- OPENAI_API_KEY (for LLM tools)
- OPENAI_BASE_URL (optional, for OpenRouter or custom endpoints)
- LLM_MODEL (optional, default: gpt-4o-mini)
"""

import asyncio
import json
import os
import argparse

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
load_dotenv()


async def test_classify(url):
    """Test the classify_by_llm tool"""
    print("🚀 Testing classify_by_llm Tool")
    print("=" * 60)

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: List available tools
            print("\n🛠️  Test 1: Listing available MCP tools")
            tools = await session.list_tools()
            print(f"✅ Found {len(tools.tools)} available tools:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"   {i:2d}. {tool.name}: {tool.description[:80]}...")

            # Test 2: Classify news articles
            print("\n📰 Test 2: Classifying news articles")
            classify_res = await session.call_tool(
                "classify_by_llm_tool",
                {
                    "input": [
                        "Apple releases new iPhone with AI features",
                        "Lakers win championship game",
                        "Senate passes new healthcare bill"
                    ],
                    "categories": ["tech", "sports", "politics"]
                }
            )

            if classify_res.isError:
                print(f"❌ Error: {classify_res.content[0].text if classify_res.content else 'Unknown error'}")
            else:
                result_text = classify_res.content[0].text if classify_res.content else None
                print(f"📦 Raw response: {result_text[:200] if result_text else 'None'}...")
                if result_text:
                    result = json.loads(result_text)
                    print(f"✅ Result:")
                    for item in result:
                        print(f"   ID {item['id']}: {item['result']}")
                else:
                    print(f"❌ No response content received")

            # Test 3: Classify with custom prompt
            print("\n📝 Test 3: Classifying with custom prompt")
            classify_res2 = await session.call_tool(
                "classify_by_llm_tool",
                {
                    "input": ["It's a sunny day", "Heavy rain expected"],
                    "categories": ["good_weather", "bad_weather"],
                    "prompt": "Classify weather descriptions"
                }
            )

            if classify_res2.isError:
                print(f"❌ Error: {classify_res2.content[0].text if classify_res2.content else 'Unknown error'}")
            else:
                result_text = classify_res2.content[0].text if classify_res2.content else None
                if result_text:
                    result = json.loads(result_text)
                    print(f"✅ Result:")
                    for item in result:
                        print(f"   ID {item['id']}: {item['result']}")
                else:
                    print(f"❌ No response content received")

            print("\n✅ classify_by_llm test completed!")


async def test_tag(url):
    """Test the tag_by_llm tool"""
    print("🚀 Testing tag_by_llm Tool")
    print("=" * 60)

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Tag programming projects
            print("\n💻 Test 1: Tagging programming projects")
            tag_res = await session.call_tool(
                "tag_by_llm_tool",
                {
                    "input": [
                        "Python REST API with FastAPI",
                        "React frontend with TypeScript",
                        "Full-stack Next.js application"
                    ],
                    "tags": ["python", "javascript", "typescript", "backend", "frontend", "fullstack"]
                }
            )

            if tag_res.isError:
                print(f"❌ Error: {tag_res.content[0].text if tag_res.content else 'Unknown error'}")
            else:
                result = json.loads(tag_res.content[0].text) if tag_res.content else None
                print(f"✅ Result:")
                for item in result:
                    print(f"   ID {item['id']}: tags = {item['result']}")

            # Test 2: Tag with max_tags limit
            print("\n🏷️  Test 2: Tagging with max_tags=2")
            tag_res2 = await session.call_tool(
                "tag_by_llm_tool",
                {
                    "input": ["Machine learning project with Python, TensorFlow, Docker, and REST API"],
                    "tags": ["python", "machine-learning", "docker", "api", "tensorflow"],
                    "args": {"max_tags": 2}
                }
            )

            if tag_res2.isError:
                print(f"❌ Error: {tag_res2.content[0].text if tag_res2.content else 'Unknown error'}")
            else:
                result = json.loads(tag_res2.content[0].text) if tag_res2.content else None
                print(f"✅ Result:")
                for item in result:
                    print(f"   ID {item['id']}: tags = {item['result']} (max 2)")

            print("\n✅ tag_by_llm test completed!")


async def test_extract(url):
    """Test the extract_by_llm tool"""
    print("🚀 Testing extract_by_llm Tool")
    print("=" * 60)

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Extract fields from text
            print("\n📄 Test 1: Extracting fields from text")
            extract_res = await session.call_tool(
                "extract_by_llm_tool",
                {
                    "input": [
                        "Article by John Smith published on 2025-01-15 about AI",
                        "Blog post by Jane Doe from 2025-02-20 covering machine learning"
                    ],
                    "fields": ["author", "date", "topic"]
                }
            )

            if extract_res.isError:
                print(f"❌ Error: {extract_res.content[0].text if extract_res.content else 'Unknown error'}")
            else:
                result = json.loads(extract_res.content[0].text) if extract_res.content else None
                print(f"✅ Result:")
                for item in result:
                    print(f"   ID {item['id']}: {item['result']}")

            # Test 2: Extract with response_format
            print("\n🔍 Test 2: Extracting with structured response format")
            extract_res2 = await session.call_tool(
                "extract_by_llm_tool",
                {
                    "input": ["Contributors: Alice, Bob, Charlie. Tags: python, api, testing"],
                    "response_format": {
                        "type": "object",
                        "properties": {
                            "contributors": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                }
            )

            if extract_res2.isError:
                print(f"❌ Error: {extract_res2.content[0].text if extract_res2.content else 'Unknown error'}")
            else:
                result = json.loads(extract_res2.content[0].text) if extract_res2.content else None
                print(f"✅ Result:")
                for item in result:
                    print(f"   ID {item['id']}: {item['result']}")

            print("\n✅ extract_by_llm test completed!")


async def test_all(url):
    """Run all tests"""
    print("🧪 Running ALL Tests")
    print("=" * 60)
    
    await test_classify(url)
    print("\n" + "=" * 60 + "\n")
    
    await test_tag(url)
    print("\n" + "=" * 60 + "\n")
    
    await test_extract(url)
    
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
        choices=["all", "classify", "tag", "extract"],
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
    elif args.test == "classify":
        asyncio.run(test_classify(url))
    elif args.test == "tag":
        asyncio.run(test_tag(url))
    elif args.test == "extract":
        asyncio.run(test_extract(url))


if __name__ == "__main__":
    main()

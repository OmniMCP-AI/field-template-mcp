#!/usr/bin/env python3
"""
MCP Template Server Integration Tests

Test Functions:
- test_hello: Test the hello tool
- test_summarize_text: Test the summarize_text tool with LLM

Usage:
    # Run all tests
    python test/test_mcp_client.py --env=local --test=all

    # Run specific test
    python test/test_mcp_client.py --env=local --test=hello
    python test/test_mcp_client.py --env=local --test=summarize

Environment Variables Required:
- OPENAI_API_KEY (for summarize_text tool)
- OPENAI_BASE_URL (optional, for OpenRouter or custom endpoints)
- OPENAI_MODEL (optional, default: gpt-4o-mini)
"""

import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables
load_dotenv()


async def test_hello(url):
    """Test the hello tool"""
    print("🚀 Testing Hello Tool")
    print("=" * 60)

    async with streamablehttp_client(url=url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: List available tools
            print("\n🛠️  Test 1: Listing available MCP tools")
            tools = await session.list_tools()
            print(f"✅ Found {len(tools.tools)} available tools:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"   {i:2d}. {tool.name}: {tool.description[:80]}...")

            # Test 2: Call hello tool
            print("\n👋 Test 2: Calling hello tool")
            hello_res = await session.call_tool("hello", {"name": "World"})
            
            if hello_res.isError:
                print(f"❌ Error: {hello_res.content[0].text if hello_res.content else 'Unknown error'}")
            else:
                result = hello_res.content[0].text if hello_res.content else None
                print(f"✅ Result: {result}")

            # Test 3: Call hello with different name
            print("\n👋 Test 3: Calling hello tool with custom name")
            hello_res2 = await session.call_tool("hello", {"name": "MCP Template"})
            
            if hello_res2.isError:
                print(f"❌ Error: {hello_res2.content[0].text if hello_res2.content else 'Unknown error'}")
            else:
                result = hello_res2.content[0].text if hello_res2.content else None
                print(f"✅ Result: {result}")

            print("\n✅ Hello tool test completed!")


async def test_summarize_text(url):
    """Test the summarize_text tool"""
    print("🚀 Testing Summarize Text Tool")
    print("=" * 60)

    async with streamablehttp_client(url=url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1: Summarize a short text
            print("\n📝 Test 1: Summarizing a short text")
            short_text = """
            The Model Context Protocol (MCP) is an open protocol that enables seamless integration 
            between LLM applications and external data sources and tools. Whether you're building 
            an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, 
            MCP provides a standardized way to connect LLMs with the context they need.
            """
            
            print(f"   Original text length: {len(short_text)} characters")
            
            summarize_res = await session.call_tool(
                "summarize_text",
                {"text": short_text, "max_words": 30}
            )
            
            if summarize_res.isError:
                print(f"❌ Error: {summarize_res.content[0].text if summarize_res.content else 'Unknown error'}")
            else:
                result = summarize_res.content[0].text if summarize_res.content else None
                print(f"✅ Summary: {result}")
                if result:
                    print(f"   Summary length: {len(result)} characters")

            # Test 2: Summarize a longer text
            print("\n📝 Test 2: Summarizing a longer text")
            long_text = """
            Artificial Intelligence (AI) has revolutionized numerous industries and continues to 
            reshape our world in unprecedented ways. From healthcare to finance, transportation to 
            entertainment, AI technologies are being deployed to solve complex problems and enhance 
            human capabilities. Machine learning, a subset of AI, enables systems to learn from data 
            and improve their performance over time without explicit programming. Deep learning, 
            inspired by the structure of the human brain, has achieved remarkable breakthroughs in 
            image recognition, natural language processing, and game playing. However, the rapid 
            advancement of AI also raises important ethical questions about privacy, bias, job 
            displacement, and the future role of humans in an increasingly automated world. As we 
            continue to develop more sophisticated AI systems, it becomes crucial to establish 
            guidelines and regulations that ensure these technologies are used responsibly and 
            for the benefit of all humanity.
            """
            
            print(f"   Original text length: {len(long_text)} characters")
            
            summarize_res2 = await session.call_tool(
                "summarize_text",
                {"text": long_text, "max_words": 50}
            )
            
            if summarize_res2.isError:
                print(f"❌ Error: {summarize_res2.content[0].text if summarize_res2.content else 'Unknown error'}")
            else:
                result = summarize_res2.content[0].text if summarize_res2.content else None
                print(f"✅ Summary: {result}")
                if result:
                    print(f"   Summary length: {len(result)} characters")
                    # Count words
                    word_count = len(result.split())
                    print(f"   Summary word count: {word_count} words")

            # Test 3: Summarize with very short limit
            print("\n📝 Test 3: Summarizing with very short limit (20 words)")
            
            summarize_res3 = await session.call_tool(
                "summarize_text",
                {"text": long_text, "max_words": 20}
            )
            
            if summarize_res3.isError:
                print(f"❌ Error: {summarize_res3.content[0].text if summarize_res3.content else 'Unknown error'}")
            else:
                result = summarize_res3.content[0].text if summarize_res3.content else None
                print(f"✅ Summary: {result}")
                if result:
                    word_count = len(result.split())
                    print(f"   Summary word count: {word_count} words")

            # Test 4: Test with default max_words parameter
            print("\n📝 Test 4: Summarizing with default max_words (50)")
            
            summarize_res4 = await session.call_tool(
                "summarize_text",
                {"text": short_text}  # No max_words specified, should use default
            )
            
            if summarize_res4.isError:
                print(f"❌ Error: {summarize_res4.content[0].text if summarize_res4.content else 'Unknown error'}")
            else:
                result = summarize_res4.content[0].text if summarize_res4.content else None
                print(f"✅ Summary: {result}")

            print("\n✅ Summarize text tool test completed!")


async def test_all(url):
    """Run all tests"""
    print("🎯 Running All Tests")
    print("=" * 80)
    
    await test_hello(url)
    print("\n" + "=" * 80 + "\n")
    await test_summarize_text(url)
    
    print("\n" + "=" * 80)
    print("🎉 ALL TESTS COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test MCP Template Server")
    parser.add_argument(
        "--env",
        choices=["local", "remote"],
        default="local",
        help="Environment to use: local (127.0.0.1:8321) or remote (custom URL)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="",
        help="Custom URL for remote environment",
    )
    parser.add_argument(
        "--test",
        choices=["all", "hello", "summarize"],
        default="all",
        help="Which test to run: all (default), hello, or summarize",
    )
    args = parser.parse_args()

    # Set endpoint based on environment argument
    if args.env == "local":
        endpoint = "http://127.0.0.1:8322"
    else:
        endpoint = args.url if args.url else "http://127.0.0.1:8322"

    print(f"🔗 Using {args.env} environment: {endpoint}")
    print(f"🧪 Running test: {args.test}")
    print()

    # Check for required environment variables if testing summarize
    if args.test in ["all", "summarize"]:
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  WARNING: OPENAI_API_KEY not found in environment")
            print("   The summarize_text test will fail without it")
            print("   Please set it in .env file or environment variables")
            print()

    # Run the selected test(s)
    test_url = f"{endpoint}/mcp"
    
    if args.test == "all":
        asyncio.run(test_all(test_url))
    elif args.test == "hello":
        asyncio.run(test_hello(test_url))
    elif args.test == "summarize":
        asyncio.run(test_summarize_text(test_url))

